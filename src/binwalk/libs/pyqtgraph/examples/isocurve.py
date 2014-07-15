# -*- coding: utf-8 -*-
"""
Tests use of IsoCurve item displayed with image
"""


import initExample ## Add path to library (just for examples; you do not need this)


from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import scipy.ndimage as ndi

app = QtGui.QApplication([])

## make pretty looping data
frames = 200
data = np.random.normal(size=(frames,30,30), loc=0, scale=100)
data = np.concatenate([data, data], axis=0)
data = ndi.gaussian_filter(data, (10, 10, 10))[frames/2:frames + frames/2]
data[:, 15:16, 15:17] += 1

win = pg.GraphicsWindow()
win.setWindowTitle('pyqtgraph example: Isocurve')
vb = win.addViewBox()
img = pg.ImageItem(data[0])
vb.addItem(img)
vb.setAspectLocked()

## generate empty curves
curves = []
levels = np.linspace(data.min(), data.max(), 10)
for i in range(len(levels)):
    v = levels[i]
    ## generate isocurve with automatic color selection
    c = pg.IsocurveItem(level=v, pen=(i, len(levels)*1.5))
    c.setParentItem(img)  ## make sure isocurve is always correctly displayed over image
    c.setZValue(10)
    curves.append(c)

## animate!
ptr = 0
imgLevels = (data.min(), data.max() * 2)
def update():
    global data, curves, img, ptr, imgLevels
    ptr = (ptr + 1) % data.shape[0]
    data[ptr]
    img.setImage(data[ptr], levels=imgLevels)
    for c in curves:
        c.setData(data[ptr])

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(50)
    
## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
