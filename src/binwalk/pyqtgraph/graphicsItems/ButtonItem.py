from pyqtgraph.Qt import QtGui, QtCore
from .GraphicsObject import GraphicsObject

__all__ = ['ButtonItem']
class ButtonItem(GraphicsObject):
    """Button graphicsItem displaying an image."""
    
    clicked = QtCore.Signal(object)
    
    def __init__(self, imageFile=None, width=None, parentItem=None, pixmap=None):
        self.enabled = True
        GraphicsObject.__init__(self)
        if imageFile is not None:
            self.setImageFile(imageFile)
        elif pixmap is not None:
            self.setPixmap(pixmap)
            
        if width is not None:
            s = float(width) / self.pixmap.width()
            self.scale(s, s)
        if parentItem is not None:
            self.setParentItem(parentItem)
        self.setOpacity(0.7)
        
    def setImageFile(self, imageFile):        
        self.setPixmap(QtGui.QPixmap(imageFile))
        
    def setPixmap(self, pixmap):
        self.pixmap = pixmap
        self.update()
        
    def mouseClickEvent(self, ev):
        if self.enabled:
            self.clicked.emit(self)
        
    def mouseHoverEvent(self, ev):
        if not self.enabled:
            return
        if ev.isEnter():
            self.setOpacity(1.0)
        else:
            self.setOpacity(0.7)

    def disable(self):
        self.enabled = False
        self.setOpacity(0.4)
        
    def enable(self):
        self.enabled = True
        self.setOpacity(0.7)
        
    def paint(self, p, *args):
        p.setRenderHint(p.Antialiasing)
        p.drawPixmap(0, 0, self.pixmap)
        
    def boundingRect(self):
        return QtCore.QRectF(self.pixmap.rect())
        
