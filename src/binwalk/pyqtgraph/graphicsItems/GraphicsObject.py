from pyqtgraph.Qt import QtGui, QtCore, USE_PYSIDE
if not USE_PYSIDE:
    import sip
from .GraphicsItem import GraphicsItem

__all__ = ['GraphicsObject']
class GraphicsObject(GraphicsItem, QtGui.QGraphicsObject):
    """
    **Bases:** :class:`GraphicsItem <pyqtgraph.graphicsItems.GraphicsItem>`, :class:`QtGui.QGraphicsObject`

    Extension of QGraphicsObject with some useful methods (provided by :class:`GraphicsItem <pyqtgraph.graphicsItems.GraphicsItem>`)
    """
    _qtBaseClass = QtGui.QGraphicsObject
    def __init__(self, *args):
        self.__inform_view_on_changes = True
        QtGui.QGraphicsObject.__init__(self, *args)
        self.setFlag(self.ItemSendsGeometryChanges)
        GraphicsItem.__init__(self)
        
    def itemChange(self, change, value):
        ret = QtGui.QGraphicsObject.itemChange(self, change, value)
        if change in [self.ItemParentHasChanged, self.ItemSceneHasChanged]:
            self.parentChanged()
        if self.__inform_view_on_changes and change in [self.ItemPositionHasChanged, self.ItemTransformHasChanged]:
            self.informViewBoundsChanged()
            
        ## workaround for pyqt bug:
        ## http://www.riverbankcomputing.com/pipermail/pyqt/2012-August/031818.html
        if not USE_PYSIDE and change == self.ItemParentChange and isinstance(ret, QtGui.QGraphicsItem):
            ret = sip.cast(ret, QtGui.QGraphicsItem)

        return ret
