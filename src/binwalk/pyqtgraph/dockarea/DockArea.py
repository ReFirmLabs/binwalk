# -*- coding: utf-8 -*-
from pyqtgraph.Qt import QtCore, QtGui
from .Container import *
from .DockDrop import *
from .Dock import Dock
import pyqtgraph.debug as debug
import weakref

## TODO:
# - containers should be drop areas, not docks. (but every slot within a container must have its own drop areas?)
# - drop between tabs
# - nest splitters inside tab boxes, etc.




class DockArea(Container, QtGui.QWidget, DockDrop):
    def __init__(self, temporary=False, home=None):
        Container.__init__(self, self)
        QtGui.QWidget.__init__(self)
        DockDrop.__init__(self, allowedAreas=['left', 'right', 'top', 'bottom'])
        self.layout = QtGui.QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.docks = weakref.WeakValueDictionary()
        self.topContainer = None
        self.raiseOverlay()
        self.temporary = temporary
        self.tempAreas = []
        self.home = home
        
    def type(self):
        return "top"
        
    def addDock(self, dock=None, position='bottom', relativeTo=None, **kwds):
        """Adds a dock to this area.
        
        =========== =================================================================
        Arguments:
        dock        The new Dock object to add. If None, then a new Dock will be 
                    created.
        position    'bottom', 'top', 'left', 'right', 'above', or 'below'
        relativeTo  If relativeTo is None, then the new Dock is added to fill an 
                    entire edge of the window. If relativeTo is another Dock, then 
                    the new Dock is placed adjacent to it (or in a tabbed 
                    configuration for 'above' and 'below'). 
        =========== =================================================================
        
        All extra keyword arguments are passed to Dock.__init__() if *dock* is
        None.        
        """
        if dock is None:
            dock = Dock(**kwds)
        
        
        ## Determine the container to insert this dock into.
        ## If there is no neighbor, then the container is the top.
        if relativeTo is None or relativeTo is self:
            if self.topContainer is None:
                container = self
                neighbor = None
            else:
                container = self.topContainer
                neighbor = None
        else:
            if isinstance(relativeTo, basestring):
                relativeTo = self.docks[relativeTo]
            container = self.getContainer(relativeTo)
            neighbor = relativeTo
        
        ## what container type do we need?
        neededContainer = {
            'bottom': 'vertical',
            'top': 'vertical',
            'left': 'horizontal',
            'right': 'horizontal',
            'above': 'tab',
            'below': 'tab'
        }[position]
        
        ## Can't insert new containers into a tab container; insert outside instead.
        if neededContainer != container.type() and container.type() == 'tab':
            neighbor = container
            container = container.container()
            
        ## Decide if the container we have is suitable.
        ## If not, insert a new container inside.
        if neededContainer != container.type():
            if neighbor is None:
                container = self.addContainer(neededContainer, self.topContainer)
            else:
                container = self.addContainer(neededContainer, neighbor)
            
        ## Insert the new dock before/after its neighbor
        insertPos = {
            'bottom': 'after',
            'top': 'before',
            'left': 'before',
            'right': 'after',
            'above': 'before',
            'below': 'after'
        }[position]
        #print "request insert", dock, insertPos, neighbor
        container.insert(dock, insertPos, neighbor)
        dock.area = self
        self.docks[dock.name()] = dock
        
        return dock
        
    def moveDock(self, dock, position, neighbor):
        """
        Move an existing Dock to a new location. 
        """
        old = dock.container()
        ## Moving to the edge of a tabbed dock causes a drop outside the tab box
        if position in ['left', 'right', 'top', 'bottom'] and neighbor is not None and neighbor.container() is not None and neighbor.container().type() == 'tab':
            neighbor = neighbor.container()
        self.addDock(dock, position, neighbor)
        old.apoptose()
        
    def getContainer(self, obj):
        if obj is None:
            return self
        return obj.container()
        
    def makeContainer(self, typ):
        if typ == 'vertical':
            new = VContainer(self)
        elif typ == 'horizontal':
            new = HContainer(self)
        elif typ == 'tab':
            new = TContainer(self)
        return new
        
    def addContainer(self, typ, obj):
        """Add a new container around obj"""
        new = self.makeContainer(typ)
        
        container = self.getContainer(obj)
        container.insert(new, 'before', obj)
        #print "Add container:", new, " -> ", container
        if obj is not None:
            new.insert(obj)
        self.raiseOverlay()
        return new
    
    def insert(self, new, pos=None, neighbor=None):
        if self.topContainer is not None:
            self.topContainer.containerChanged(None)
        self.layout.addWidget(new)
        self.topContainer = new
        #print self, "set top:", new
        new._container = self
        self.raiseOverlay()
        #print "Insert top:", new
        
    def count(self):
        if self.topContainer is None:
            return 0
        return 1
        
        
    #def paintEvent(self, ev):
        #self.drawDockOverlay()
        
    def resizeEvent(self, ev):
        self.resizeOverlay(self.size())
        
    def addTempArea(self):
        if self.home is None:
            area = DockArea(temporary=True, home=self)
            self.tempAreas.append(area)
            win = QtGui.QMainWindow()
            win.setCentralWidget(area)
            area.win = win
            win.show()
        else:
            area = self.home.addTempArea()
        #print "added temp area", area, area.window()
        return area
        
    def floatDock(self, dock):
        """Removes *dock* from this DockArea and places it in a new window."""
        area = self.addTempArea()
        area.win.resize(dock.size())
        area.moveDock(dock, 'top', None)
        
        
    def removeTempArea(self, area):
        self.tempAreas.remove(area)
        #print "close window", area.window()
        area.window().close()
        
    def saveState(self):
        """
        Return a serialized (storable) representation of the state of
        all Docks in this DockArea."""
        state = {'main': self.childState(self.topContainer), 'float': []}
        for a in self.tempAreas:
            geo = a.win.geometry()
            geo = (geo.x(), geo.y(), geo.width(), geo.height())
            state['float'].append((a.saveState(), geo))
        return state
        
    def childState(self, obj):
        if isinstance(obj, Dock):
            return ('dock', obj.name(), {})
        else:
            childs = []
            for i in range(obj.count()):
                childs.append(self.childState(obj.widget(i)))
            return (obj.type(), childs, obj.saveState())
        
        
    def restoreState(self, state):
        """
        Restore Dock configuration as generated by saveState.
        
        Note that this function does not create any Docks--it will only 
        restore the arrangement of an existing set of Docks.
        
        """
        
        ## 1) make dict of all docks and list of existing containers
        containers, docks = self.findAll()
        oldTemps = self.tempAreas[:]
        #print "found docks:", docks
        
        ## 2) create container structure, move docks into new containers
        self.buildFromState(state['main'], docks, self)
        
        ## 3) create floating areas, populate
        for s in state['float']:
            a = self.addTempArea()
            a.buildFromState(s[0]['main'], docks, a)
            a.win.setGeometry(*s[1])
        
        ## 4) Add any remaining docks to the bottom
        for d in docks.values():
            self.moveDock(d, 'below', None)
        
        #print "\nKill old containers:"
        ## 5) kill old containers
        for c in containers:
            c.close()
        for a in oldTemps:
            a.apoptose()


    def buildFromState(self, state, docks, root, depth=0):
        typ, contents, state = state
        pfx = "  " * depth
        if typ == 'dock':
            try:
                obj = docks[contents]
                del docks[contents]
            except KeyError:
                raise Exception('Cannot restore dock state; no dock with name "%s"' % contents)
        else:
            obj = self.makeContainer(typ)
            
        root.insert(obj, 'after')
        #print pfx+"Add:", obj, " -> ", root
        
        if typ != 'dock':
            for o in contents:
                self.buildFromState(o, docks, obj, depth+1)
            obj.apoptose(propagate=False)
            obj.restoreState(state)  ## this has to be done later?
        

    def findAll(self, obj=None, c=None, d=None):
        if obj is None:
            obj = self.topContainer
        
        ## check all temp areas first
        if c is None:
            c = []
            d = {}
            for a in self.tempAreas:
                c1, d1 = a.findAll()
                c.extend(c1)
                d.update(d1)
        
        if isinstance(obj, Dock):
            d[obj.name()] = obj
        elif obj is not None:
            c.append(obj)
            for i in range(obj.count()):
                o2 = obj.widget(i)
                c2, d2 = self.findAll(o2)
                c.extend(c2)
                d.update(d2)
        return (c, d)

    def apoptose(self):
        #print "apoptose area:", self.temporary, self.topContainer, self.topContainer.count()
        if self.temporary and self.topContainer.count() == 0:
            self.topContainer = None
            self.home.removeTempArea(self)
            #self.close()
            
    ## PySide bug: We need to explicitly redefine these methods
    ## or else drag/drop events will not be delivered.
    def dragEnterEvent(self, *args):
        DockDrop.dragEnterEvent(self, *args)

    def dragMoveEvent(self, *args):
        DockDrop.dragMoveEvent(self, *args)

    def dragLeaveEvent(self, *args):
        DockDrop.dragLeaveEvent(self, *args)

    def dropEvent(self, *args):
        DockDrop.dropEvent(self, *args)

        
        
