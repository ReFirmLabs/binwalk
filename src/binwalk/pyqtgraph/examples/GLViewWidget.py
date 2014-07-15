# -*- coding: utf-8 -*-
"""
Very basic 3D graphics example; create a view widget and add a few items.

"""
## Add path to library (just for examples; you do not need this)
import initExample

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.opengl as gl

app = QtGui.QApplication([])
w = gl.GLViewWidget()
w.opts['distance'] = 20
w.show()
w.setWindowTitle('pyqtgraph example: GLViewWidget')

ax = gl.GLAxisItem()
ax.setSize(5,5,5)
w.addItem(ax)

b = gl.GLBoxItem()
w.addItem(b)

ax2 = gl.GLAxisItem()
ax2.setParentItem(b)

b.translate(1,1,1)

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
