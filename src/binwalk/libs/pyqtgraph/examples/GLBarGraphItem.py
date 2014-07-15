# -*- coding: utf-8 -*-
"""
Demonstrate use of GLLinePlotItem to draw cross-sections of a surface.

"""
## Add path to library (just for examples; you do not need this)
import initExample

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.opengl as gl
import pyqtgraph as pg
import numpy as np

app = QtGui.QApplication([])
w = gl.GLViewWidget()
w.opts['distance'] = 40
w.show()
w.setWindowTitle('pyqtgraph example: GLBarGraphItem')

gx = gl.GLGridItem()
gx.rotate(90, 0, 1, 0)
gx.translate(-10, 0, 10)
w.addItem(gx)
gy = gl.GLGridItem()
gy.rotate(90, 1, 0, 0)
gy.translate(0, -10, 10)
w.addItem(gy)
gz = gl.GLGridItem()
gz.translate(0, 0, 0)
w.addItem(gz)

# regular grid of starting positions
pos = np.mgrid[0:10, 0:10, 0:1].reshape(3,10,10).transpose(1,2,0)
# fixed widths, random heights
size = np.empty((10,10,3))
size[...,0:2] = 0.4
size[...,2] = np.random.normal(size=(10,10))

bg = gl.GLBarGraphItem(pos, size)
w.addItem(bg)


## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
