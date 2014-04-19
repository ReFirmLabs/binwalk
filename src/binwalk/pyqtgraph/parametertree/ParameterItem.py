from pyqtgraph.Qt import QtGui, QtCore
import os, weakref, re

class ParameterItem(QtGui.QTreeWidgetItem):
    """
    Abstract ParameterTree item. 
    Used to represent the state of a Parameter from within a ParameterTree.
    
    - Sets first column of item to name
    - generates context menu if item is renamable or removable
    - handles child added / removed events
    - provides virtual functions for handling changes from parameter
    
    For more ParameterItem types, see ParameterTree.parameterTypes module.
    """
    
    def __init__(self, param, depth=0):
        QtGui.QTreeWidgetItem.__init__(self, [param.name(), ''])
        
        self.param = param
        self.param.registerItem(self)  ## let parameter know this item is connected to it (for debugging)
        self.depth = depth
        
        param.sigValueChanged.connect(self.valueChanged)
        param.sigChildAdded.connect(self.childAdded)
        param.sigChildRemoved.connect(self.childRemoved)
        param.sigNameChanged.connect(self.nameChanged)
        param.sigLimitsChanged.connect(self.limitsChanged)
        param.sigDefaultChanged.connect(self.defaultChanged)
        param.sigOptionsChanged.connect(self.optsChanged)
        param.sigParentChanged.connect(self.parentChanged)
        
        
        opts = param.opts
        
        ## Generate context menu for renaming/removing parameter
        self.contextMenu = QtGui.QMenu()
        self.contextMenu.addSeparator()
        flags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
        if opts.get('renamable', False):
            flags |= QtCore.Qt.ItemIsEditable
            self.contextMenu.addAction('Rename').triggered.connect(self.editName)
        if opts.get('removable', False):
            self.contextMenu.addAction("Remove").triggered.connect(self.requestRemove)
        
        ## handle movable / dropEnabled options
        if opts.get('movable', False):
            flags |= QtCore.Qt.ItemIsDragEnabled
        if opts.get('dropEnabled', False):
            flags |= QtCore.Qt.ItemIsDropEnabled
        self.setFlags(flags)
        
        ## flag used internally during name editing
        self.ignoreNameColumnChange = False
    
    
    def valueChanged(self, param, val):
        ## called when the parameter's value has changed
        pass
    
    def isFocusable(self):
        """Return True if this item should be included in the tab-focus order"""
        return False
        
    def setFocus(self):
        """Give input focus to this item.
        Can be reimplemented to display editor widgets, etc.
        """
        pass
    
    def focusNext(self, forward=True):
        """Give focus to the next (or previous) focusable item in the parameter tree"""
        self.treeWidget().focusNext(self, forward=forward)
        
    
    def treeWidgetChanged(self):
        """Called when this item is added or removed from a tree.
        Expansion, visibility, and column widgets must all be configured AFTER 
        the item is added to a tree, not during __init__.
        """
        self.setHidden(not self.param.opts.get('visible', True))
        self.setExpanded(self.param.opts.get('expanded', True))
        
    def childAdded(self, param, child, pos):
        item = child.makeTreeItem(depth=self.depth+1)
        self.insertChild(pos, item)
        item.treeWidgetChanged()
        
        for i, ch in enumerate(child):
            item.childAdded(child, ch, i)
        
    def childRemoved(self, param, child):
        for i in range(self.childCount()):
            item = self.child(i)
            if item.param is child:
                self.takeChild(i)
                break
                
    def parentChanged(self, param, parent):
        ## called when the parameter's parent has changed.
        pass
                
    def contextMenuEvent(self, ev):
        if not self.param.opts.get('removable', False) and not self.param.opts.get('renamable', False):
            return
            
        self.contextMenu.popup(ev.globalPos())
        
    def columnChangedEvent(self, col):
        """Called when the text in a column has been edited.
        By default, we only use changes to column 0 to rename the parameter.
        """
        if col == 0:
            if self.ignoreNameColumnChange:
                return
            try:
                newName = self.param.setName(str(self.text(col)))
            except:
                self.setText(0, self.param.name())
                raise
                
            try:
                self.ignoreNameColumnChange = True
                self.nameChanged(self, newName)  ## If the parameter rejects the name change, we need to set it back.
            finally:
                self.ignoreNameColumnChange = False
                
    def nameChanged(self, param, name):
        ## called when the parameter's name has changed.
        self.setText(0, name)

    def limitsChanged(self, param, limits):
        """Called when the parameter's limits have changed"""
        pass
    
    def defaultChanged(self, param, default):
        """Called when the parameter's default value has changed"""
        pass

    def optsChanged(self, param, opts):
        """Called when any options are changed that are not
        name, value, default, or limits"""
        #print opts
        if 'visible' in opts:
            self.setHidden(not opts['visible'])
        
    def editName(self):
        self.treeWidget().editItem(self, 0)
        
    def selected(self, sel):
        """Called when this item has been selected (sel=True) OR deselected (sel=False)"""
        pass

    def requestRemove(self):
        ## called when remove is selected from the context menu.
        ## we need to delay removal until the action is complete
        ## since destroying the menu in mid-action will cause a crash.
        QtCore.QTimer.singleShot(0, self.param.remove)

    ## for python 3 support, we need to redefine hash and eq methods.
    def __hash__(self):
        return id(self)

    def __eq__(self, x):
        return x is self
