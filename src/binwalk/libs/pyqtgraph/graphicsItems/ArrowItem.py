from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph.functions as fn
import numpy as np
__all__ = ['ArrowItem']

class ArrowItem(QtGui.QGraphicsPathItem):
    """
    For displaying scale-invariant arrows.
    For arrows pointing to a location on a curve, see CurveArrow
    
    """
    
    
    def __init__(self, **opts):
        """
        Arrows can be initialized with any keyword arguments accepted by 
        the setStyle() method.
        """
        QtGui.QGraphicsPathItem.__init__(self, opts.get('parent', None))
        if 'size' in opts:
            opts['headLen'] = opts['size']
        if 'width' in opts:
            opts['headWidth'] = opts['width']
        defOpts = {
            'pxMode': True,
            'angle': -150,   ## If the angle is 0, the arrow points left
            'pos': (0,0),
            'headLen': 20,
            'tipAngle': 25,
            'baseAngle': 0,
            'tailLen': None,
            'tailWidth': 3,
            'pen': (200,200,200),
            'brush': (50,50,200),
        }
        defOpts.update(opts)
        
        self.setStyle(**defOpts)
        
        self.setPen(fn.mkPen(defOpts['pen']))
        self.setBrush(fn.mkBrush(defOpts['brush']))
        
        self.rotate(self.opts['angle'])
        self.moveBy(*self.opts['pos'])
    
    def setStyle(self, **opts):
        """
        Changes the appearance of the arrow.
        All arguments are optional:
        
        ================= =================================================
        Keyword Arguments
        angle             Orientation of the arrow in degrees. Default is
                          0; arrow pointing to the left.
        headLen           Length of the arrow head, from tip to base.
                          default=20
        headWidth         Width of the arrow head at its base.
        tipAngle          Angle of the tip of the arrow in degrees. Smaller
                          values make a 'sharper' arrow. If tipAngle is 
                          specified, ot overrides headWidth. default=25
        baseAngle         Angle of the base of the arrow head. Default is
                          0, which means that the base of the arrow head
                          is perpendicular to the arrow shaft.
        tailLen           Length of the arrow tail, measured from the base
                          of the arrow head to the tip of the tail. If
                          this value is None, no tail will be drawn.
                          default=None
        tailWidth         Width of the tail. default=3
        pen               The pen used to draw the outline of the arrow.
        brush             The brush used to fill the arrow.
        ================= =================================================
        """
        self.opts = opts
        
        opt = dict([(k,self.opts[k]) for k in ['headLen', 'tipAngle', 'baseAngle', 'tailLen', 'tailWidth']])
        self.path = fn.makeArrowPath(**opt)
        self.setPath(self.path)
        
        if opts['pxMode']:
            self.setFlags(self.flags() | self.ItemIgnoresTransformations)
        else:
            self.setFlags(self.flags() & ~self.ItemIgnoresTransformations)
        
    def paint(self, p, *args):
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        QtGui.QGraphicsPathItem.paint(self, p, *args)
        
        #p.setPen(fn.mkPen('r'))
        #p.setBrush(fn.mkBrush(None))
        #p.drawRect(self.boundingRect())

    def shape(self):
        #if not self.opts['pxMode']:
            #return QtGui.QGraphicsPathItem.shape(self)
        return self.path
    
    ## dataBounds and pixelPadding methods are provided to ensure ViewBox can
    ## properly auto-range 
    def dataBounds(self, ax, frac, orthoRange=None):
        pw = 0
        pen = self.pen()
        if not pen.isCosmetic():
            pw = pen.width() * 0.7072
        if self.opts['pxMode']:
            return [0,0]
        else:
            br = self.boundingRect()
            if ax == 0:
                return [br.left()-pw, br.right()+pw]
            else:
                return [br.top()-pw, br.bottom()+pw]
        
    def pixelPadding(self):
        pad = 0
        if self.opts['pxMode']:
            br = self.boundingRect()
            pad += (br.width()**2 + br.height()**2) ** 0.5
        pen = self.pen()
        if pen.isCosmetic():
            pad += max(1, pen.width()) * 0.7072
        return pad
        
        
    