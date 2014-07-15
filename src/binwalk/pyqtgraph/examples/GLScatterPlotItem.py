# -*- coding: utf-8 -*-
"""
Demonstrates use of GLScatterPlotItem with rapidly-updating plots.

"""

## Add path to library (just for examples; you do not need this)
import initExample

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.opengl as gl
import numpy as np

app = QtGui.QApplication([])
w = gl.GLViewWidget()
w.opts['distance'] = 20
w.show()
w.setWindowTitle('pyqtgraph example: GLScatterPlotItem')

g = gl.GLGridItem()
w.addItem(g)


##
##  First example is a set of points with pxMode=False
##  These demonstrate the ability to have points with real size down to a very small scale 
## 
pos = np.empty((53, 3))
size = np.empty((53))
color = np.empty((53, 4))
pos[0] = (1,0,0); size[0] = 0.5;   color[0] = (1.0, 0.0, 0.0, 0.5)
pos[1] = (0,1,0); size[1] = 0.2;   color[1] = (0.0, 0.0, 1.0, 0.5)
pos[2] = (0,0,1); size[2] = 2./3.; color[2] = (0.0, 1.0, 0.0, 0.5)

z = 0.5
d = 6.0
for i in range(3,53):
    pos[i] = (0,0,z)
    size[i] = 2./d
    color[i] = (0.0, 1.0, 0.0, 0.5)
    z *= 0.5
    d *= 2.0
    
sp1 = gl.GLScatterPlotItem(pos=pos, size=size, color=color, pxMode=False)
sp1.translate(5,5,0)
w.addItem(sp1)


##
##  Second example shows a volume of points with rapidly updating color
##  and pxMode=True
##

pos = np.random.random(size=(100000,3))
pos *= [10,-10,10]
pos[0] = (0,0,0)
color = np.ones((pos.shape[0], 4))
d2 = (pos**2).sum(axis=1)**0.5
size = np.random.random(size=pos.shape[0])*10
sp2 = gl.GLScatterPlotItem(pos=pos, color=(1,1,1,1), size=size)
phase = 0.

w.addItem(sp2)


##
##  Third example shows a grid of points with rapidly updating position
##  and pxMode = False
##

pos3 = np.zeros((100,100,3))
pos3[:,:,:2] = np.mgrid[:100, :100].transpose(1,2,0) * [-0.1,0.1]
pos3 = pos3.reshape(10000,3)
d3 = (pos3**2).sum(axis=1)**0.5

sp3 = gl.GLScatterPlotItem(pos=pos3, color=(1,1,1,.3), size=0.1, pxMode=False)

w.addItem(sp3)


def update():
    ## update volume colors
    global phase, sp2, d2
    s = -np.cos(d2*2+phase)
    color = np.empty((len(d2),4), dtype=np.float32)
    color[:,3] = np.clip(s * 0.1, 0, 1)
    color[:,0] = np.clip(s * 3.0, 0, 1)
    color[:,1] = np.clip(s * 1.0, 0, 1)
    color[:,2] = np.clip(s ** 3, 0, 1)
    sp2.setData(color=color)
    phase -= 0.1
    
    ## update surface positions and colors
    global sp3, d3, pos3
    z = -np.cos(d3*2+phase)
    pos3[:,2] = z
    color = np.empty((len(d3),4), dtype=np.float32)
    color[:,3] = 0.3
    color[:,0] = np.clip(z * 3.0, 0, 1)
    color[:,1] = np.clip(z * 1.0, 0, 1)
    color[:,2] = np.clip(z ** 3, 0, 1)
    sp3.setData(pos=pos3, color=color)
    
t = QtCore.QTimer()
t.timeout.connect(update)
t.start(50)


## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
