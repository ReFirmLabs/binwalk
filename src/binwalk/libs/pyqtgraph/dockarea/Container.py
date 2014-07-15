# -*- coding: utf-8 -*-
from pyqtgraph.Qt import QtCore, QtGui
import weakref

class Container(object):
    #sigStretchChanged = QtCore.Signal()  ## can't do this here; not a QObject.
    
    def __init__(self, area):
        object.__init__(self)
        self.area = area
        self._container = None
        self._stretch = (10, 10)
        self.stretches = weakref.WeakKeyDictionary()
        
    def container(self):
        return self._container
        
    def containerChanged(self, c):
        self._container = c

    def type(self):
        return None

    def insert(self, new, pos=None, neighbor=None):
        if not isinstance(new, list):
            new = [new]
        if neighbor is None:
            if pos == 'before':
                index = 0
            else:
                index = self.count()
        else:
            index = self.indexOf(neighbor)
            if index == -1:
                index = 0
            if pos == 'after':
                index += 1
                
        for n in new:
            #print "change container", n, " -> ", self
            n.containerChanged(self)
            #print "insert", n, " -> ", self, index
            self._insertItem(n, index)
            index += 1
            n.sigStretchChanged.connect(self.childStretchChanged)
        #print "child added", self
        self.updateStretch()
            
    def apoptose(self, propagate=True):
        ##if there is only one (or zero) item in this container, disappear.
        cont = self._container
        c = self.count()
        if c > 1:
            return
        if self.count() == 1:  ## if there is one item, give it to the parent container (unless this is the top)
            if self is self.area.topContainer:
                return
            self.container().insert(self.widget(0), 'before', self)
        #print "apoptose:", self
        self.close()
        if propagate and cont is not None:
            cont.apoptose()
        
    def close(self):
        self.area = None
        self._container = None
        self.setParent(None)
        
    def childEvent(self, ev):
        ch = ev.child()
        if ev.removed() and hasattr(ch, 'sigStretchChanged'):
            #print "Child", ev.child(), "removed, updating", self
            try:
                ch.sigStretchChanged.disconnect(self.childStretchChanged)
            except:
                pass
            self.updateStretch()
        
    def childStretchChanged(self):
        #print "child", QtCore.QObject.sender(self), "changed shape, updating", self
        self.updateStretch()
        
    def setStretch(self, x=None, y=None):
        #print "setStretch", self, x, y
        self._stretch = (x, y)
        self.sigStretchChanged.emit()

    def updateStretch(self):
        ###Set the stretch values for this container to reflect its contents
        pass
        
        
    def stretch(self):
        """Return the stretch factors for this container"""
        return self._stretch
            

class SplitContainer(Container, QtGui.QSplitter):
    """Horizontal or vertical splitter with some changes:
     - save/restore works correctly
    """
    sigStretchChanged = QtCore.Signal()
    
    def __init__(self, area, orientation):
        QtGui.QSplitter.__init__(self)
        self.setOrientation(orientation)
        Container.__init__(self, area)
        #self.splitterMoved.connect(self.restretchChildren)
        
    def _insertItem(self, item, index):
        self.insertWidget(index, item)
        item.show()  ## need to show since it may have been previously hidden by tab
        
    def saveState(self):
        sizes = self.sizes()
        if all([x == 0 for x in sizes]):
            sizes = [10] * len(sizes)
        return {'sizes': sizes}
        
    def restoreState(self, state):
        sizes = state['sizes']
        self.setSizes(sizes)
        for i in range(len(sizes)):
            self.setStretchFactor(i, sizes[i])

    def childEvent(self, ev):
        QtGui.QSplitter.childEvent(self, ev)
        Container.childEvent(self, ev)

    #def restretchChildren(self):
        #sizes = self.sizes()
        #tot = sum(sizes)
        
        
        

class HContainer(SplitContainer):
    def __init__(self, area):
        SplitContainer.__init__(self, area, QtCore.Qt.Horizontal)
        
    def type(self):
        return 'horizontal'
        
    def updateStretch(self):
        ##Set the stretch values for this container to reflect its contents
        #print "updateStretch", self
        x = 0
        y = 0
        sizes = []
        for i in range(self.count()):
            wx, wy = self.widget(i).stretch()
            x += wx
            y = max(y, wy)
            sizes.append(wx)
            #print "  child", self.widget(i), wx, wy
        self.setStretch(x, y)
        #print sizes
        
        tot = float(sum(sizes))
        if tot == 0:
            scale = 1.0
        else:
            scale = self.width() / tot
        self.setSizes([int(s*scale) for s in sizes])
        


class VContainer(SplitContainer):
    def __init__(self, area):
        SplitContainer.__init__(self, area, QtCore.Qt.Vertical)
        
    def type(self):
        return 'vertical'

    def updateStretch(self):
        ##Set the stretch values for this container to reflect its contents
        #print "updateStretch", self
        x = 0
        y = 0
        sizes = []
        for i in range(self.count()):
            wx, wy = self.widget(i).stretch()
            y += wy
            x = max(x, wx)
            sizes.append(wy)
            #print "  child", self.widget(i), wx, wy
        self.setStretch(x, y)

        #print sizes
        tot = float(sum(sizes))
        if tot == 0:
            scale = 1.0
        else:
            scale = self.height() / tot
        self.setSizes([int(s*scale) for s in sizes])


class TContainer(Container, QtGui.QWidget):
    sigStretchChanged = QtCore.Signal()
    def __init__(self, area):
        QtGui.QWidget.__init__(self)
        Container.__init__(self, area)
        self.layout = QtGui.QGridLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)
        
        self.hTabLayout = QtGui.QHBoxLayout()
        self.hTabBox = QtGui.QWidget()
        self.hTabBox.setLayout(self.hTabLayout)
        self.hTabLayout.setSpacing(2)
        self.hTabLayout.setContentsMargins(0,0,0,0)
        self.layout.addWidget(self.hTabBox, 0, 1)

        self.stack = QtGui.QStackedWidget()
        self.layout.addWidget(self.stack, 1, 1)
        self.stack.childEvent = self.stackChildEvent


        self.setLayout(self.layout)
        for n in ['count', 'widget', 'indexOf']:
            setattr(self, n, getattr(self.stack, n))


    def _insertItem(self, item, index):
        if not isinstance(item, Dock.Dock):
            raise Exception("Tab containers may hold only docks, not other containers.")
        self.stack.insertWidget(index, item)
        self.hTabLayout.insertWidget(index, item.label)
        #QtCore.QObject.connect(item.label, QtCore.SIGNAL('clicked'), self.tabClicked)
        item.label.sigClicked.connect(self.tabClicked)
        self.tabClicked(item.label)
        
    def tabClicked(self, tab, ev=None):
        if ev is None or ev.button() == QtCore.Qt.LeftButton:
            for i in range(self.count()):
                w = self.widget(i)
                if w is tab.dock:
                    w.label.setDim(False)
                    self.stack.setCurrentIndex(i)
                else:
                    w.label.setDim(True)
        
    def type(self):
        return 'tab'

    def saveState(self):
        return {'index': self.stack.currentIndex()}
        
    def restoreState(self, state):
        self.stack.setCurrentIndex(state['index'])
        
    def updateStretch(self):
        ##Set the stretch values for this container to reflect its contents
        x = 0
        y = 0
        for i in range(self.count()):
            wx, wy = self.widget(i).stretch()
            x = max(x, wx)
            y = max(y, wy)
        self.setStretch(x, y)
        
    def stackChildEvent(self, ev):
        QtGui.QStackedWidget.childEvent(self.stack, ev)
        Container.childEvent(self, ev)
        
from . import Dock
