# -*- coding: utf-8 -*-

"""
Simple use of DataTreeWidget to display a structure of nested dicts, lists, and arrays
"""

import initExample ## Add path to library (just for examples; you do not need this)

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np


app = QtGui.QApplication([])
d = {
    'list1': [1,2,3,4,5,6, {'nested1': 'aaaaa', 'nested2': 'bbbbb'}, "seven"],
    'dict1': {
        'x': 1,
        'y': 2,
        'z': 'three'
    },
    'array1 (20x20)': np.ones((10,10))
}

tree = pg.DataTreeWidget(data=d)
tree.show()
tree.setWindowTitle('pyqtgraph example: DataTreeWidget')
tree.resize(600,600)


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()