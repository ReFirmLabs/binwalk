# -*- coding: utf-8 -*-
"""
Test programmatically setting log transformation modes.
"""
import initExample ## Add path to library (just for examples; you do not need this)

import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg


app = QtGui.QApplication([])

w = pg.GraphicsWindow()
w.setWindowTitle('pyqtgraph example: logAxis')
p1 = w.addPlot(0,0, title="X Semilog")
p2 = w.addPlot(1,0, title="Y Semilog")
p3 = w.addPlot(2,0, title="XY Log")
p1.showGrid(True, True)
p2.showGrid(True, True)
p3.showGrid(True, True)
p1.setLogMode(True, False)
p2.setLogMode(False, True)
p3.setLogMode(True, True)
w.show()

y = np.random.normal(size=1000)
x = np.linspace(0, 1, 1000)
p1.plot(x, y)
p2.plot(x, y)
p3.plot(x, y)



#p.getAxis('bottom').setLogMode(True)


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
