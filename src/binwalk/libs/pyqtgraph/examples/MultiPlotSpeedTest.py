#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Test the speed of rapidly updating multiple plot curves
"""

## Add path to library (just for examples; you do not need this)
import initExample


from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from pyqtgraph.ptime import time
#QtGui.QApplication.setGraphicsSystem('raster')
app = QtGui.QApplication([])
#mw = QtGui.QMainWindow()
#mw.resize(800,800)

p = pg.plot()
p.setWindowTitle('pyqtgraph example: MultiPlotSpeedTest')
#p.setRange(QtCore.QRectF(0, -10, 5000, 20)) 
p.setLabel('bottom', 'Index', units='B')

nPlots = 10
#curves = [p.plot(pen=(i,nPlots*1.3)) for i in range(nPlots)]
curves = [pg.PlotCurveItem(pen=(i,nPlots*1.3)) for i in range(nPlots)]
for c in curves:
    p.addItem(c)

rgn = pg.LinearRegionItem([1,100])
p.addItem(rgn)


data = np.random.normal(size=(53,5000/nPlots))
ptr = 0
lastTime = time()
fps = None
count = 0
def update():
    global curve, data, ptr, p, lastTime, fps, nPlots, count
    count += 1
    #print "---------", count
    for i in range(nPlots):
        curves[i].setData(i+data[(ptr+i)%data.shape[0]])
    #print "   setData done."
    ptr += nPlots
    now = time()
    dt = now - lastTime
    lastTime = now
    if fps is None:
        fps = 1.0/dt
    else:
        s = np.clip(dt*3., 0, 1)
        fps = fps * (1-s) + (1.0/dt) * s
    p.setTitle('%0.2f fps' % fps)
    #app.processEvents()  ## force complete redraw for every plot
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)
    


## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
