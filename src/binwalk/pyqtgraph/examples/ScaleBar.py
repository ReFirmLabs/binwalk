# -*- coding: utf-8 -*-
"""
Demonstrates ScaleBar
"""
import initExample ## Add path to library (just for examples; you do not need this)

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

pg.mkQApp()
win = pg.GraphicsWindow()
win.setWindowTitle('pyqtgraph example: ScaleBar')

vb = win.addViewBox()
vb.setAspectLocked()

img = pg.ImageItem()
img.setImage(np.random.normal(size=(100,100)))
img.scale(0.01, 0.01)
vb.addItem(img)

scale = pg.ScaleBar(size=0.1)
scale.setParentItem(vb)
scale.anchor((1, 1), (1, 1), offset=(-20, -20))

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
