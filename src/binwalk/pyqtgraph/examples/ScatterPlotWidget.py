# -*- coding: utf-8 -*-
import initExample ## Add path to library (just for examples; you do not need this)

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

pg.mkQApp()

spw = pg.ScatterPlotWidget()
spw.show()

data = np.array([
    (1, 1, 3, 4, 'x'),
    (2, 3, 3, 7, 'y'),
    (3, 2, 5, 2, 'z'),
    (4, 4, 6, 9, 'z'),
    (5, 3, 6, 7, 'x'),
    (6, 5, 4, 6, 'x'),
    (7, 5, 8, 2, 'z'),
    (8, 1, 2, 4, 'x'),
    (9, 2, 3, 7, 'z'),
    (0, 6, 0, 2, 'z'),
    (1, 3, 1, 2, 'z'),
    (2, 5, 4, 6, 'y'),
    (3, 4, 8, 1, 'y'),
    (4, 7, 6, 8, 'z'),
    (5, 8, 7, 4, 'y'),
    (6, 1, 2, 3, 'y'),
    (7, 5, 3, 9, 'z'),
    (8, 9, 3, 1, 'x'),
    (9, 2, 6, 2, 'z'),
    (0, 3, 4, 6, 'x'),
    (1, 5, 9, 3, 'y'),
    ], dtype=[('col1', float), ('col2', float), ('col3', int), ('col4', int), ('col5', 'S10')])

spw.setFields([
    ('col1', {'units': 'm'}),
    ('col2', {'units': 'm'}),
    ('col3', {}),
    ('col4', {}),
    ('col5', {'mode': 'enum', 'values': ['x', 'y', 'z']}),
    ])
    
spw.setData(data)


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
