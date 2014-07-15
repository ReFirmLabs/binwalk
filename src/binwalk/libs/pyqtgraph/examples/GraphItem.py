# -*- coding: utf-8 -*-
"""
Simple example of GraphItem use.
"""


import initExample ## Add path to library (just for examples; you do not need this)

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

w = pg.GraphicsWindow()
w.setWindowTitle('pyqtgraph example: GraphItem')
v = w.addViewBox()
v.setAspectLocked()

g = pg.GraphItem()
v.addItem(g)

## Define positions of nodes
pos = np.array([
    [0,0],
    [10,0],
    [0,10],
    [10,10],
    [5,5],
    [15,5]
    ])
    
## Define the set of connections in the graph
adj = np.array([
    [0,1],
    [1,3],
    [3,2],
    [2,0],
    [1,5],
    [3,5],
    ])
    
## Define the symbol to use for each node (this is optional)
symbols = ['o','o','o','o','t','+']

## Define the line style for each connection (this is optional)
lines = np.array([
    (255,0,0,255,1),
    (255,0,255,255,2),
    (255,0,255,255,3),
    (255,255,0,255,2),
    (255,0,0,255,1),
    (255,255,255,255,4),
    ], dtype=[('red',np.ubyte),('green',np.ubyte),('blue',np.ubyte),('alpha',np.ubyte),('width',float)])

## Update the graph
g.setData(pos=pos, adj=adj, pen=lines, size=1, symbol=symbols, pxMode=False)




## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
