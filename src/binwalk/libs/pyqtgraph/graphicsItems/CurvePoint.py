from pyqtgraph.Qt import QtGui, QtCore
from . import ArrowItem
import numpy as np
from pyqtgraph.Point import Point
import weakref
from .GraphicsObject import GraphicsObject

__all__ = ['CurvePoint', 'CurveArrow']
class CurvePoint(GraphicsObject):
    """A GraphicsItem that sets its location to a point on a PlotCurveItem.
    Also rotates to be tangent to the curve.
    The position along the curve is a Qt property, and thus can be easily animated.
    
    Note: This class does not display anything; see CurveArrow for an applied example
    """
    
    def __init__(self, curve, index=0, pos=None, rotate=True):
        """Position can be set either as an index referring to the sample number or
        the position 0.0 - 1.0
        If *rotate* is True, then the item rotates to match the tangent of the curve.
        """
        
        GraphicsObject.__init__(self)
        #QObjectWorkaround.__init__(self)
        self._rotate = rotate
        self.curve = weakref.ref(curve)
        self.setParentItem(curve)
        self.setProperty('position', 0.0)
        self.setProperty('index', 0)
        
        if hasattr(self, 'ItemHasNoContents'):
            self.setFlags(self.flags() | self.ItemHasNoContents)
        
        if pos is not None:
            self.setPos(pos)
        else:
            self.setIndex(index)
            
    def setPos(self, pos):
        self.setProperty('position', float(pos))## cannot use numpy types here, MUST be python float.
        
    def setIndex(self, index):
        self.setProperty('index', int(index))  ## cannot use numpy types here, MUST be python int.
        
    def event(self, ev):
        if not isinstance(ev, QtCore.QDynamicPropertyChangeEvent) or self.curve() is None:
            return False
            
        if ev.propertyName() == 'index':
            index = self.property('index')
            if 'QVariant' in repr(index):
                index = index.toInt()[0]
        elif ev.propertyName() == 'position':
            index = None
        else:
            return False
            
        (x, y) = self.curve().getData()
        if index is None:
            #print ev.propertyName(), self.property('position').toDouble()[0], self.property('position').typeName()
            pos = self.property('position')
            if 'QVariant' in repr(pos):   ## need to support 2 APIs  :(
                pos = pos.toDouble()[0]
            index = (len(x)-1) * np.clip(pos, 0.0, 1.0)
            
        if index != int(index):  ## interpolate floating-point values
            i1 = int(index)
            i2 = np.clip(i1+1, 0, len(x)-1)
            s2 = index-i1
            s1 = 1.0-s2
            newPos = (x[i1]*s1+x[i2]*s2, y[i1]*s1+y[i2]*s2)
        else:
            index = int(index)
            i1 = np.clip(index-1, 0, len(x)-1)
            i2 = np.clip(index+1, 0, len(x)-1)
            newPos = (x[index], y[index])
            
        p1 = self.parentItem().mapToScene(QtCore.QPointF(x[i1], y[i1]))
        p2 = self.parentItem().mapToScene(QtCore.QPointF(x[i2], y[i2]))
        ang = np.arctan2(p2.y()-p1.y(), p2.x()-p1.x()) ## returns radians
        self.resetTransform()
        if self._rotate:
            self.rotate(180+ ang * 180 / np.pi) ## takes degrees
        QtGui.QGraphicsItem.setPos(self, *newPos)
        return True
        
    def boundingRect(self):
        return QtCore.QRectF()
        
    def paint(self, *args):
        pass
    
    def makeAnimation(self, prop='position', start=0.0, end=1.0, duration=10000, loop=1):
        anim = QtCore.QPropertyAnimation(self, prop)
        anim.setDuration(duration)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setLoopCount(loop)
        return anim


class CurveArrow(CurvePoint):
    """Provides an arrow that points to any specific sample on a PlotCurveItem.
    Provides properties that can be animated."""
    
    def __init__(self, curve, index=0, pos=None, **opts):
        CurvePoint.__init__(self, curve, index=index, pos=pos)
        if opts.get('pxMode', True):
            opts['pxMode'] = False
            self.setFlags(self.flags() | self.ItemIgnoresTransformations)
        opts['angle'] = 0
        self.arrow = ArrowItem.ArrowItem(**opts)
        self.arrow.setParentItem(self)
        
    def setStyle(**opts):
        return self.arrow.setStyle(**opts)
        
