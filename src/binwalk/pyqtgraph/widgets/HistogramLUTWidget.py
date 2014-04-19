"""
Widget displaying an image histogram along with gradient editor. Can be used to adjust the appearance of images.
This is a wrapper around HistogramLUTItem
"""

from pyqtgraph.Qt import QtGui, QtCore
from .GraphicsView import GraphicsView
from pyqtgraph.graphicsItems.HistogramLUTItem import HistogramLUTItem

__all__ = ['HistogramLUTWidget']


class HistogramLUTWidget(GraphicsView):
    
    def __init__(self, parent=None,  *args, **kargs):
        background = kargs.get('background', 'default')
        GraphicsView.__init__(self, parent, useOpenGL=False, background=background)
        self.item = HistogramLUTItem(*args, **kargs)
        self.setCentralItem(self.item)
        self.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        self.setMinimumWidth(95)
        

    def sizeHint(self):
        return QtCore.QSize(115, 200)
    
    

    def __getattr__(self, attr):
        return getattr(self.item, attr)



