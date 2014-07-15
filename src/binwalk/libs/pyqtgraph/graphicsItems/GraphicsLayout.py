from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph.functions as fn
from .GraphicsWidget import GraphicsWidget
## Must be imported at the end to avoid cyclic-dependency hell:
from .ViewBox import ViewBox
from .PlotItem import PlotItem
from .LabelItem import LabelItem

__all__ = ['GraphicsLayout']
class GraphicsLayout(GraphicsWidget):
    """
    Used for laying out GraphicsWidgets in a grid.
    This is usually created automatically as part of a :class:`GraphicsWindow <pyqtgraph.GraphicsWindow>` or :class:`GraphicsLayoutWidget <pyqtgraph.GraphicsLayoutWidget>`.
    """


    def __init__(self, parent=None, border=None):
        GraphicsWidget.__init__(self, parent)
        if border is True:
            border = (100,100,100)
        self.border = border
        self.layout = QtGui.QGraphicsGridLayout()
        self.setLayout(self.layout)
        self.items = {}  ## item: [(row, col), (row, col), ...]  lists all cells occupied by the item
        self.rows = {}   ## row: {col1: item1, col2: item2, ...}    maps cell location to item
        self.currentRow = 0
        self.currentCol = 0
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding))
    
    #def resizeEvent(self, ev):
        #ret = GraphicsWidget.resizeEvent(self, ev)
        #print self.pos(), self.mapToDevice(self.rect().topLeft())
        #return ret
    
    def nextRow(self):
        """Advance to next row for automatic item placement"""
        self.currentRow += 1
        self.currentCol = -1
        self.nextColumn()
        
    def nextColumn(self):
        """Advance to next available column
        (generally only for internal use--called by addItem)"""
        self.currentCol += 1
        while self.getItem(self.currentRow, self.currentCol) is not None:
            self.currentCol += 1
        
    def nextCol(self, *args, **kargs):
        """Alias of nextColumn"""
        return self.nextColumn(*args, **kargs)
        
    def addPlot(self, row=None, col=None, rowspan=1, colspan=1, **kargs):
        """
        Create a PlotItem and place it in the next available cell (or in the cell specified)
        All extra keyword arguments are passed to :func:`PlotItem.__init__ <pyqtgraph.PlotItem.__init__>`
        Returns the created item.
        """
        plot = PlotItem(**kargs)
        self.addItem(plot, row, col, rowspan, colspan)
        return plot
        
    def addViewBox(self, row=None, col=None, rowspan=1, colspan=1, **kargs):
        """
        Create a ViewBox and place it in the next available cell (or in the cell specified)
        All extra keyword arguments are passed to :func:`ViewBox.__init__ <pyqtgraph.ViewBox.__init__>`
        Returns the created item.
        """
        vb = ViewBox(**kargs)
        self.addItem(vb, row, col, rowspan, colspan)
        return vb
        
    def addLabel(self, text=' ', row=None, col=None, rowspan=1, colspan=1, **kargs):
        """
        Create a LabelItem with *text* and place it in the next available cell (or in the cell specified)
        All extra keyword arguments are passed to :func:`LabelItem.__init__ <pyqtgraph.LabelItem.__init__>`
        Returns the created item.
        
        To create a vertical label, use *angle* = -90.
        """
        text = LabelItem(text, **kargs)
        self.addItem(text, row, col, rowspan, colspan)
        return text
        
    def addLayout(self, row=None, col=None, rowspan=1, colspan=1, **kargs):
        """
        Create an empty GraphicsLayout and place it in the next available cell (or in the cell specified)
        All extra keyword arguments are passed to :func:`GraphicsLayout.__init__ <pyqtgraph.GraphicsLayout.__init__>`
        Returns the created item.
        """
        layout = GraphicsLayout(**kargs)
        self.addItem(layout, row, col, rowspan, colspan)
        return layout
        
    def addItem(self, item, row=None, col=None, rowspan=1, colspan=1):
        """
        Add an item to the layout and place it in the next available cell (or in the cell specified).
        The item must be an instance of a QGraphicsWidget subclass.
        """
        if row is None:
            row = self.currentRow
        if col is None:
            col = self.currentCol
            
        self.items[item] = []
        for i in range(rowspan):
            for j in range(colspan):
                row2 = row + i
                col2 = col + j
                if row2 not in self.rows:
                    self.rows[row2] = {}
                self.rows[row2][col2] = item
                self.items[item].append((row2, col2))
        
        self.layout.addItem(item, row, col, rowspan, colspan)
        self.nextColumn()

    def getItem(self, row, col):
        """Return the item in (*row*, *col*). If the cell is empty, return None."""
        return self.rows.get(row, {}).get(col, None)

    def boundingRect(self):
        return self.rect()
        
    def paint(self, p, *args):
        if self.border is None:
            return
        p.setPen(fn.mkPen(self.border))
        for i in self.items:
            r = i.mapRectToParent(i.boundingRect())
            p.drawRect(r)
    
    def itemIndex(self, item):
        for i in range(self.layout.count()):
            if self.layout.itemAt(i).graphicsItem() is item:
                return i
        raise Exception("Could not determine index of item " + str(item))
    
    def removeItem(self, item):
        """Remove *item* from the layout."""
        ind = self.itemIndex(item)
        self.layout.removeAt(ind)
        self.scene().removeItem(item)
        
        for r,c in self.items[item]:
            del self.rows[r][c]
        del self.items[item]
        self.update()
    
    def clear(self):
        items = []
        for i in list(self.items.keys()):
            self.removeItem(i)


