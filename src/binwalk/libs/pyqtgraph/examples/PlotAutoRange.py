# -*- coding: utf-8 -*-

"""
This example demonstrates the different auto-ranging capabilities of ViewBoxes
"""

import initExample ## Add path to library (just for examples; you do not need this)


from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg

#QtGui.QApplication.setGraphicsSystem('raster')
app = QtGui.QApplication([])
#mw = QtGui.QMainWindow()
#mw.resize(800,800)

win = pg.GraphicsWindow(title="Plot auto-range examples")
win.resize(800,600)
win.setWindowTitle('pyqtgraph example: PlotAutoRange')

d = np.random.normal(size=100)
d[50:54] += 10
p1 = win.addPlot(title="95th percentile range", y=d)
p1.enableAutoRange('y', 0.95)


p2 = win.addPlot(title="Auto Pan Only")
p2.setAutoPan(y=True)
curve = p2.plot()
def update():
    t = pg.time()
    
    data = np.ones(100) * np.sin(t)
    data[50:60] += np.sin(t)
    global curve
    curve.setData(data)
    
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(50)


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

