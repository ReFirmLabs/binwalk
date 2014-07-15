#!/usr/bin/python
# -*- coding: utf-8 -*-
## Add path to library (just for examples; you do not need this)
import initExample


from scipy import random
from numpy import linspace
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
from pyqtgraph import MultiPlotWidget
try:
    from metaarray import *
except:
    print("MultiPlot is only used with MetaArray for now (and you do not have the metaarray package)")
    exit()
    
app = QtGui.QApplication([])
mw = QtGui.QMainWindow()
mw.resize(800,800)
pw = MultiPlotWidget()
mw.setCentralWidget(pw)
mw.show()

ma = MetaArray(random.random((3, 1000)), info=[{'name': 'Signal', 'cols': [{'name': 'Col1'}, {'name': 'Col2'}, {'name': 'Col3'}]}, {'name': 'Time', 'vals': linspace(0., 1., 1000)}])
pw.plot(ma)

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

