# -*- coding: utf-8 -*-
"""
Use a HistogramLUTWidget to control the contrast / coloration of an image.
"""

## Add path to library (just for examples; you do not need this)                                                                           
import initExample

import numpy as np
import scipy.ndimage as ndi
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg


app = QtGui.QApplication([])
win = QtGui.QMainWindow()
win.resize(800,600)
win.show()
win.setWindowTitle('pyqtgraph example: Histogram LUT')

cw = QtGui.QWidget()
win.setCentralWidget(cw)

l = QtGui.QGridLayout()
cw.setLayout(l)
l.setSpacing(0)

v = pg.GraphicsView()
vb = pg.ViewBox()
vb.setAspectLocked()
v.setCentralItem(vb)
l.addWidget(v, 0, 0)

w = pg.HistogramLUTWidget()
l.addWidget(w, 0, 1)

data = ndi.gaussian_filter(np.random.normal(size=(256, 256)), (20, 20))
for i in range(32):
    for j in range(32):
        data[i*8, j*8] += .1
img = pg.ImageItem(data)
#data2 = np.zeros((2,) + data.shape + (2,))
#data2[0,:,:,0] = data  ## make non-contiguous array for testing purposes
#img = pg.ImageItem(data2[0,:,:,0])
vb.addItem(img)
vb.autoRange()

w.setImageItem(img)


## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
