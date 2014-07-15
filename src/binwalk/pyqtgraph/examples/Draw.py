# -*- coding: utf-8 -*-
"""
Demonstrate ability of ImageItem to be used as a canvas for painting with
the mouse.

"""

import initExample ## Add path to library (just for examples; you do not need this)


from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import pyqtgraph as pg

app = QtGui.QApplication([])

## Create window with GraphicsView widget
w = pg.GraphicsView()
w.show()
w.resize(800,800)
w.setWindowTitle('pyqtgraph example: Draw')

view = pg.ViewBox()
w.setCentralItem(view)

## lock the aspect ratio
view.setAspectLocked(True)

## Create image item
img = pg.ImageItem(np.zeros((200,200)))
view.addItem(img)

## Set initial view bounds
view.setRange(QtCore.QRectF(0, 0, 200, 200))

## start drawing with 3x3 brush
kern = np.array([
    [0.0, 0.5, 0.0],
    [0.5, 1.0, 0.5],
    [0.0, 0.5, 0.0]
])
img.setDrawKernel(kern, mask=kern, center=(1,1), mode='add')
img.setLevels([0, 10])

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
