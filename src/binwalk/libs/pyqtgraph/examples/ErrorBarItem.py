# -*- coding: utf-8 -*-
"""
Demonstrates basic use of ErrorBarItem

"""

import initExample ## Add path to library (just for examples; you do not need this)

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
import numpy as np

import pyqtgraph as pg
import numpy as np

pg.setConfigOptions(antialias=True)

x = np.arange(10)
y = np.arange(10) %3
top = np.linspace(1.0, 3.0, 10)
bottom = np.linspace(2, 0.5, 10)

plt = pg.plot()
plt.setWindowTitle('pyqtgraph example: ErrorBarItem')
err = pg.ErrorBarItem(x=x, y=y, top=top, bottom=bottom, beam=0.5)
plt.addItem(err)
plt.plot(x, y, symbol='o', pen={'color': 0.8, 'width': 2})

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
