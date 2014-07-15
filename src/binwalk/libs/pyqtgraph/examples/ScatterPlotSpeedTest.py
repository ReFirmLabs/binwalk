#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
For testing rapid updates of ScatterPlotItem under various conditions.

(Scatter plots are still rather slow to draw; expect about 20fps)
"""



## Add path to library (just for examples; you do not need this)
import initExample


from pyqtgraph.Qt import QtGui, QtCore, USE_PYSIDE
import numpy as np
import pyqtgraph as pg
from pyqtgraph.ptime import time
#QtGui.QApplication.setGraphicsSystem('raster')
app = QtGui.QApplication([])
#mw = QtGui.QMainWindow()
#mw.resize(800,800)
if USE_PYSIDE:
    from ScatterPlotSpeedTestTemplate_pyside import Ui_Form
else:
    from ScatterPlotSpeedTestTemplate_pyqt import Ui_Form

win = QtGui.QWidget()
win.setWindowTitle('pyqtgraph example: ScatterPlotSpeedTest')
ui = Ui_Form()
ui.setupUi(win)
win.show()

p = ui.plot

data = np.random.normal(size=(50,500), scale=100)
sizeArray = (np.random.random(500) * 20.).astype(int)
ptr = 0
lastTime = time()
fps = None
def update():
    global curve, data, ptr, p, lastTime, fps
    p.clear()
    if ui.randCheck.isChecked():
        size = sizeArray
    else:
        size = ui.sizeSpin.value()
    curve = pg.ScatterPlotItem(x=data[ptr%50], y=data[(ptr+1)%50], pen='w', brush='b', size=size, pxMode=ui.pixelModeCheck.isChecked())
    p.addItem(curve)
    ptr += 1
    now = time()
    dt = now - lastTime
    lastTime = now
    if fps is None:
        fps = 1.0/dt
    else:
        s = np.clip(dt*3., 0, 1)
        fps = fps * (1-s) + (1.0/dt) * s
    p.setTitle('%0.2f fps' % fps)
    p.repaint()
    #app.processEvents()  ## force complete redraw for every plot
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)
    


## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
