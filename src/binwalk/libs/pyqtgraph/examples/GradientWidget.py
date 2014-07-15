# -*- coding: utf-8 -*-
"""
Demonstrates the appearance / interactivity of GradientWidget
(without actually doing anything useful with it)

"""
import initExample ## Add path to library (just for examples; you do not need this)

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np



app = QtGui.QApplication([])
w = QtGui.QMainWindow()
w.show()
w.setWindowTitle('pyqtgraph example: GradientWidget')
w.resize(400,400)
cw = QtGui.QWidget()
w.setCentralWidget(cw)

l = QtGui.QGridLayout()
l.setSpacing(0)
cw.setLayout(l)

w1 = pg.GradientWidget(orientation='top')
w2 = pg.GradientWidget(orientation='right', allowAdd=False)
#w2.setTickColor(1, QtGui.QColor(255,255,255))
w3 = pg.GradientWidget(orientation='bottom')
w4 = pg.GradientWidget(orientation='left')
w4.loadPreset('spectrum')
label = QtGui.QLabel("""
- Click a triangle to change its color
- Drag triangles to move
- Click in an empty area to add a new color
    (adding is disabled for the right-side widget)
- Right click a triangle to remove
""")

l.addWidget(w1, 0, 1)
l.addWidget(w2, 1, 2)
l.addWidget(w3, 2, 1)
l.addWidget(w4, 1, 0)
l.addWidget(label, 1, 1)


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()



