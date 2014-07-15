from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph.functions as fn
import pyqtgraph as pg
from .GraphicsWidget import GraphicsWidget
from .GraphicsWidgetAnchor import GraphicsWidgetAnchor


__all__ = ['LabelItem']

class LabelItem(GraphicsWidget, GraphicsWidgetAnchor):
    """
    GraphicsWidget displaying text.
    Used mainly as axis labels, titles, etc.
    
    Note: To display text inside a scaled view (ViewBox, PlotWidget, etc) use TextItem
    """
    
    
    def __init__(self, text=' ', parent=None, angle=0, **args):
        GraphicsWidget.__init__(self, parent)
        GraphicsWidgetAnchor.__init__(self)
        self.item = QtGui.QGraphicsTextItem(self)
        self.opts = {
            'color': None,
            'justify': 'center'
        }
        self.opts.update(args)
        self._sizeHint = {}
        self.setText(text)
        self.setAngle(angle)
            
    def setAttr(self, attr, value):
        """Set default text properties. See setText() for accepted parameters."""
        self.opts[attr] = value
        
    def setText(self, text, **args):
        """Set the text and text properties in the label. Accepts optional arguments for auto-generating
        a CSS style string:

        ==================== ==============================
        **Style Arguments:**
        color                (str) example: 'CCFF00'
        size                 (str) example: '8pt'
        bold                 (bool)
        italic               (bool)
        ==================== ==============================
        """
        self.text = text
        opts = self.opts
        for k in args:
            opts[k] = args[k]
        
        optlist = []
        
        color = self.opts['color']
        if color is None:
            color = pg.getConfigOption('foreground')
        color = fn.mkColor(color)
        optlist.append('color: #' + fn.colorStr(color)[:6])
        if 'size' in opts:
            optlist.append('font-size: ' + opts['size'])
        if 'bold' in opts and opts['bold'] in [True, False]:
            optlist.append('font-weight: ' + {True:'bold', False:'normal'}[opts['bold']])
        if 'italic' in opts and opts['italic'] in [True, False]:
            optlist.append('font-style: ' + {True:'italic', False:'normal'}[opts['italic']])
        full = "<span style='%s'>%s</span>" % ('; '.join(optlist), text)
        #print full
        self.item.setHtml(full)
        self.updateMin()
        self.resizeEvent(None)
        self.updateGeometry()
        
    def resizeEvent(self, ev):
        #c1 = self.boundingRect().center()
        #c2 = self.item.mapToParent(self.item.boundingRect().center()) # + self.item.pos()
        #dif = c1 - c2
        #self.item.moveBy(dif.x(), dif.y())
        #print c1, c2, dif, self.item.pos()
        self.item.setPos(0,0)
        bounds = self.itemRect()
        left = self.mapFromItem(self.item, QtCore.QPointF(0,0)) - self.mapFromItem(self.item, QtCore.QPointF(1,0))
        rect = self.rect()
        
        if self.opts['justify'] == 'left':
            if left.x() != 0:
                bounds.moveLeft(rect.left())
            if left.y() < 0:
                bounds.moveTop(rect.top())
            elif left.y() > 0:
                bounds.moveBottom(rect.bottom())
                
        elif self.opts['justify'] == 'center':
            bounds.moveCenter(rect.center())
            #bounds = self.itemRect()
            #self.item.setPos(self.width()/2. - bounds.width()/2., 0)
        elif self.opts['justify'] == 'right':
            if left.x() != 0:
                bounds.moveRight(rect.right())
            if left.y() < 0:
                bounds.moveBottom(rect.bottom())
            elif left.y() > 0:
                bounds.moveTop(rect.top())
            #bounds = self.itemRect()
            #self.item.setPos(self.width() - bounds.width(), 0)
            
        self.item.setPos(bounds.topLeft() - self.itemRect().topLeft())
        self.updateMin()
        
    def setAngle(self, angle):
        self.angle = angle
        self.item.resetTransform()
        self.item.rotate(angle)
        self.updateMin()
        
        
    def updateMin(self):
        bounds = self.itemRect()
        self.setMinimumWidth(bounds.width())
        self.setMinimumHeight(bounds.height())
        
        self._sizeHint = {
            QtCore.Qt.MinimumSize: (bounds.width(), bounds.height()),
            QtCore.Qt.PreferredSize: (bounds.width(), bounds.height()),
            QtCore.Qt.MaximumSize: (-1, -1),  #bounds.width()*2, bounds.height()*2),
            QtCore.Qt.MinimumDescent: (0, 0)  ##?? what is this?
        }
        self.updateGeometry()
        
    def sizeHint(self, hint, constraint):
        if hint not in self._sizeHint:
            return QtCore.QSizeF(0, 0)
        return QtCore.QSizeF(*self._sizeHint[hint])
        
    def itemRect(self):
        return self.item.mapRectToParent(self.item.boundingRect())
        
    #def paint(self, p, *args):
        #p.setPen(fn.mkPen('r'))
        #p.drawRect(self.rect())
        #p.setPen(fn.mkPen('g'))
        #p.drawRect(self.itemRect())
        
