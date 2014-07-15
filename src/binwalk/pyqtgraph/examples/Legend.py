# -*- coding: utf-8 -*-
"""
Demonstrates basic use of LegendItem

"""
import initExample ## Add path to library (just for examples; you do not need this)

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

plt = pg.plot()
plt.setWindowTitle('pyqtgraph example: Legend')
plt.addLegend()
#l = pg.LegendItem((100,60), offset=(70,30))  # args are (size, offset)
#l.setParentItem(plt.graphicsItem())   # Note we do NOT call plt.addItem in this case

c1 = plt.plot([1,3,2,4], pen='r', name='red plot')
c2 = plt.plot([2,1,4,3], pen='g', fillLevel=0, fillBrush=(255,255,255,30), name='green plot')
#l.addItem(c1, 'red plot')
#l.addItem(c2, 'green plot')


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
