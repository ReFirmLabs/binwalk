from pyqtgraph.Qt import QtGui, QtCore
from .UIGraphicsItem import *
import pyqtgraph.functions as fn

__all__ = ['GradientLegend']

class GradientLegend(UIGraphicsItem):
    """
    Draws a color gradient rectangle along with text labels denoting the value at specific 
    points along the gradient.
    """
    
    def __init__(self, size, offset):
        self.size = size
        self.offset = offset
        UIGraphicsItem.__init__(self)
        self.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        self.brush = QtGui.QBrush(QtGui.QColor(200,0,0))
        self.pen = QtGui.QPen(QtGui.QColor(0,0,0))
        self.labels = {'max': 1, 'min': 0}
        self.gradient = QtGui.QLinearGradient()
        self.gradient.setColorAt(0, QtGui.QColor(0,0,0))
        self.gradient.setColorAt(1, QtGui.QColor(255,0,0))
        
    def setGradient(self, g):
        self.gradient = g
        self.update()
        
    def setIntColorScale(self, minVal, maxVal, *args, **kargs):
        colors = [fn.intColor(i, maxVal-minVal, *args, **kargs) for i in range(minVal, maxVal)]
        g = QtGui.QLinearGradient()
        for i in range(len(colors)):
            x = float(i)/len(colors)
            g.setColorAt(x, colors[i])
        self.setGradient(g)
        if 'labels' not in kargs:
            self.setLabels({str(minVal/10.): 0, str(maxVal): 1})
        else:
            self.setLabels({kargs['labels'][0]:0, kargs['labels'][1]:1})
        
    def setLabels(self, l):
        """Defines labels to appear next to the color scale. Accepts a dict of {text: value} pairs"""
        self.labels = l
        self.update()
        
    def paint(self, p, opt, widget):
        UIGraphicsItem.paint(self, p, opt, widget)
        rect = self.boundingRect()   ## Boundaries of visible area in scene coords.
        unit = self.pixelSize()       ## Size of one view pixel in scene coords.
        if unit[0] is None:  
            return
        
        ## determine max width of all labels
        labelWidth = 0
        labelHeight = 0
        for k in self.labels:
            b = p.boundingRect(QtCore.QRectF(0, 0, 0, 0), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, str(k))
            labelWidth = max(labelWidth, b.width())
            labelHeight = max(labelHeight, b.height())
            
        labelWidth *= unit[0]
        labelHeight *= unit[1]
        
        textPadding = 2  # in px
        
        if self.offset[0] < 0:
            x3 = rect.right() + unit[0] * self.offset[0]
            x2 = x3 - labelWidth - unit[0]*textPadding*2
            x1 = x2 - unit[0] * self.size[0]
        else:
            x1 = rect.left() + unit[0] * self.offset[0]
            x2 = x1 + unit[0] * self.size[0]
            x3 = x2 + labelWidth + unit[0]*textPadding*2
        if self.offset[1] < 0:
            y2 = rect.top() - unit[1] * self.offset[1]
            y1 = y2 + unit[1] * self.size[1]
        else:
            y1 = rect.bottom() - unit[1] * self.offset[1]
            y2 = y1 - unit[1] * self.size[1]
        self.b = [x1,x2,x3,y1,y2,labelWidth]
            
        ## Draw background
        p.setPen(self.pen)
        p.setBrush(QtGui.QBrush(QtGui.QColor(255,255,255,100)))
        rect = QtCore.QRectF(
            QtCore.QPointF(x1 - unit[0]*textPadding, y1 + labelHeight/2 + unit[1]*textPadding), 
            QtCore.QPointF(x3, y2 - labelHeight/2 - unit[1]*textPadding)
        )
        p.drawRect(rect)
        
        
        ## Have to scale painter so that text and gradients are correct size. Bleh.
        p.scale(unit[0], unit[1])
        
        ## Draw color bar
        self.gradient.setStart(0, y1/unit[1])
        self.gradient.setFinalStop(0, y2/unit[1])
        p.setBrush(self.gradient)
        rect = QtCore.QRectF(
            QtCore.QPointF(x1/unit[0], y1/unit[1]), 
            QtCore.QPointF(x2/unit[0], y2/unit[1])
        )
        p.drawRect(rect)
        
        
        ## draw labels
        p.setPen(QtGui.QPen(QtGui.QColor(0,0,0)))
        tx = x2 + unit[0]*textPadding
        lh = labelHeight/unit[1]
        for k in self.labels:
            y = y1 + self.labels[k] * (y2-y1)
            p.drawText(QtCore.QRectF(tx/unit[0], y/unit[1] - lh/2.0, 1000, lh), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, str(k))
        
        
