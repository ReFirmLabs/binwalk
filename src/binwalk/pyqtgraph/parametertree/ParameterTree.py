from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.widgets.TreeWidget import TreeWidget
import os, weakref, re
from .ParameterItem import ParameterItem
#import functions as fn
        
            

class ParameterTree(TreeWidget):
    """Widget used to display or control data from a ParameterSet"""
    
    def __init__(self, parent=None, showHeader=True):
        TreeWidget.__init__(self, parent)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setHorizontalScrollMode(self.ScrollPerPixel)
        self.setAnimated(False)
        self.setColumnCount(2)
        self.setHeaderLabels(["Parameter", "Value"])
        self.setAlternatingRowColors(True)
        self.paramSet = None
        self.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.setHeaderHidden(not showHeader)
        self.itemChanged.connect(self.itemChangedEvent)
        self.lastSel = None
        self.setRootIsDecorated(False)
        
    def setParameters(self, param, showTop=True):
        self.clear()
        self.addParameters(param, showTop=showTop)
        
    def addParameters(self, param, root=None, depth=0, showTop=True):
        item = param.makeTreeItem(depth=depth)
        if root is None:
            root = self.invisibleRootItem()
            ## Hide top-level item
            if not showTop:
                item.setText(0, '')
                item.setSizeHint(0, QtCore.QSize(1,1))
                item.setSizeHint(1, QtCore.QSize(1,1))
                depth -= 1
        root.addChild(item)
        item.treeWidgetChanged()
            
        for ch in param:
            self.addParameters(ch, root=item, depth=depth+1)

    def clear(self):
        self.invisibleRootItem().takeChildren()
        
            
    def focusNext(self, item, forward=True):
        ## Give input focus to the next (or previous) item after 'item'
        while True:
            parent = item.parent()
            if parent is None:
                return
            nextItem = self.nextFocusableChild(parent, item, forward=forward)
            if nextItem is not None:
                nextItem.setFocus()
                self.setCurrentItem(nextItem)
                return
            item = parent

    def focusPrevious(self, item):
        self.focusNext(item, forward=False)

    def nextFocusableChild(self, root, startItem=None, forward=True):
        if startItem is None:
            if forward:
                index = 0
            else:
                index = root.childCount()-1
        else:
            if forward:
                index = root.indexOfChild(startItem) + 1
            else:
                index = root.indexOfChild(startItem) - 1
            
        if forward:
            inds = list(range(index, root.childCount()))
        else:
            inds = list(range(index, -1, -1))
            
        for i in inds:
            item = root.child(i)
            if hasattr(item, 'isFocusable') and item.isFocusable():
                return item
            else:
                item = self.nextFocusableChild(item, forward=forward)
                if item is not None:
                    return item
        return None

    def contextMenuEvent(self, ev):
        item = self.currentItem()
        if hasattr(item, 'contextMenuEvent'):
            item.contextMenuEvent(ev)
            
    def itemChangedEvent(self, item, col):
        if hasattr(item, 'columnChangedEvent'):
            item.columnChangedEvent(col)
            
    def selectionChanged(self, *args):
        sel = self.selectedItems()
        if len(sel) != 1:
            sel = None
        if self.lastSel is not None and isinstance(self.lastSel, ParameterItem):
            self.lastSel.selected(False)
        if sel is None:
            self.lastSel = None
            return
        self.lastSel = sel[0]
        if hasattr(sel[0], 'selected'):
            sel[0].selected(True)
        return TreeWidget.selectionChanged(self, *args)
        
    def wheelEvent(self, ev):
        self.clearSelection()
        return TreeWidget.wheelEvent(self, ev)
