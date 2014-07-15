

from .GraphicsObject import *
import pyqtgraph.functions as fn
from pyqtgraph.Qt import QtGui, QtCore


class IsocurveItem(GraphicsObject):
    """
    **Bases:** :class:`GraphicsObject <pyqtgraph.GraphicsObject>`
    
    Item displaying an isocurve of a 2D array.To align this item correctly with an 
    ImageItem,call isocurve.setParentItem(image)
    """
    

    def __init__(self, data=None, level=0, pen='w'):
        """
        Create a new isocurve item. 
        
        ============= ===============================================================
        **Arguments**
        data          A 2-dimensional ndarray. Can be initialized as None, and set 
                      later using :func:`setData <pyqtgraph.IsocurveItem.setData>`
        level         The cutoff value at which to draw the isocurve.
        pen           The color of the curve item. Can be anything valid for 
                      :func:`mkPen <pyqtgraph.mkPen>`
        ============= ===============================================================
        """
        GraphicsObject.__init__(self)

        self.level = level
        self.data = None
        self.path = None
        self.setPen(pen)
        self.setData(data, level)
        
        

        #if data is not None and level is not None:
            #self.updateLines(data, level)
            
    
    def setData(self, data, level=None):
        """
        Set the data/image to draw isocurves for.
        
        ============= ========================================================================
        **Arguments**
        data          A 2-dimensional ndarray.
        level         The cutoff value at which to draw the curve. If level is not specified,
                      the previously set level is used.
        ============= ========================================================================
        """
        if level is None:
            level = self.level
        self.level = level
        self.data = data
        self.path = None
        self.prepareGeometryChange()
        self.update()
        

    def setLevel(self, level):
        """Set the level at which the isocurve is drawn."""
        self.level = level
        self.path = None
        self.update()
    

    def setPen(self, *args, **kwargs):
        """Set the pen used to draw the isocurve. Arguments can be any that are valid 
        for :func:`mkPen <pyqtgraph.mkPen>`"""
        self.pen = fn.mkPen(*args, **kwargs)
        self.update()

    def setBrush(self, *args, **kwargs):
        """Set the brush used to draw the isocurve. Arguments can be any that are valid 
        for :func:`mkBrush <pyqtgraph.mkBrush>`"""
        self.brush = fn.mkBrush(*args, **kwargs)
        self.update()

        
    def updateLines(self, data, level):
        ##print "data:", data
        ##print "level", level
        #lines = fn.isocurve(data, level)
        ##print len(lines)
        #self.path = QtGui.QPainterPath()
        #for line in lines:
            #self.path.moveTo(*line[0])
            #self.path.lineTo(*line[1])
        #self.update()
        self.setData(data, level)

    def boundingRect(self):
        if self.data is None:
            return QtCore.QRectF()
        if self.path is None:
            self.generatePath()
        return self.path.boundingRect()
    
    def generatePath(self):
        if self.data is None:
            self.path = None
            return
        lines = fn.isocurve(self.data, self.level, connected=True, extendToEdge=True)
        self.path = QtGui.QPainterPath()
        for line in lines:
            self.path.moveTo(*line[0])
            for p in line[1:]:
                self.path.lineTo(*p)
    
    def paint(self, p, *args):
        if self.data is None:
            return
        if self.path is None:
            self.generatePath()
        p.setPen(self.pen)
        p.drawPath(self.path)
    