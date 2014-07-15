from pyqtgraph.Qt import QtGui
from pyqtgraph.graphicsItems.GraphicsLayout import GraphicsLayout
from .GraphicsView import GraphicsView

__all__ = ['GraphicsLayoutWidget']
class GraphicsLayoutWidget(GraphicsView):
    def __init__(self, parent=None, **kargs):
        GraphicsView.__init__(self, parent)
        self.ci = GraphicsLayout(**kargs)
        for n in ['nextRow', 'nextCol', 'nextColumn', 'addPlot', 'addViewBox', 'addItem', 'getItem', 'addLabel', 'addLayout', 'addLabel', 'addViewBox', 'removeItem', 'itemIndex', 'clear']:
            setattr(self, n, getattr(self.ci, n))
        self.setCentralItem(self.ci)
