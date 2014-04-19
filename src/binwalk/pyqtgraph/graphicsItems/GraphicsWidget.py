from pyqtgraph.Qt import QtGui, QtCore  
from pyqtgraph.GraphicsScene import GraphicsScene
from .GraphicsItem import GraphicsItem

__all__ = ['GraphicsWidget']

class GraphicsWidget(GraphicsItem, QtGui.QGraphicsWidget):
    
    _qtBaseClass = QtGui.QGraphicsWidget
    def __init__(self, *args, **kargs):
        """
        **Bases:** :class:`GraphicsItem <pyqtgraph.GraphicsItem>`, :class:`QtGui.QGraphicsWidget`
        
        Extends QGraphicsWidget with several helpful methods and workarounds for PyQt bugs. 
        Most of the extra functionality is inherited from :class:`GraphicsItem <pyqtgraph.GraphicsItem>`.
        """
        QtGui.QGraphicsWidget.__init__(self, *args, **kargs)
        GraphicsItem.__init__(self)
        
        ## done by GraphicsItem init
        #GraphicsScene.registerObject(self)  ## workaround for pyqt bug in graphicsscene.items()

    # Removed due to https://bugreports.qt-project.org/browse/PYSIDE-86
    #def itemChange(self, change, value):
        ## BEWARE: Calling QGraphicsWidget.itemChange can lead to crashing!
        ##ret = QtGui.QGraphicsWidget.itemChange(self, change, value)  ## segv occurs here
        ## The default behavior is just to return the value argument, so we'll do that
        ## without calling the original method.
        #ret = value
        #if change in [self.ItemParentHasChanged, self.ItemSceneHasChanged]:
            #self._updateView()
        #return ret

    def setFixedHeight(self, h):
        self.setMaximumHeight(h)
        self.setMinimumHeight(h)

    def setFixedWidth(self, h):
        self.setMaximumWidth(h)
        self.setMinimumWidth(h)
        
    def height(self):
        return self.geometry().height()
    
    def width(self):
        return self.geometry().width()

    def boundingRect(self):
        br = self.mapRectFromParent(self.geometry()).normalized()
        #print "bounds:", br
        return br
        
    def shape(self):  ## No idea why this is necessary, but rotated items do not receive clicks otherwise.
        p = QtGui.QPainterPath()
        p.addRect(self.boundingRect())
        #print "shape:", p.boundingRect()
        return p


