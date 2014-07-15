# -*- coding: utf-8 -*-
"""
Display an animated arrowhead following a curve.
This example uses the CurveArrow class, which is a combination
of ArrowItem and CurvePoint. 

To place a static arrow anywhere in a scene, use ArrowItem.
To attach other types of item to a curve, use CurvePoint.
"""

import initExample ## Add path to library (just for examples; you do not need this)

import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg


app = QtGui.QApplication([])

w = QtGui.QMainWindow()
cw = pg.GraphicsLayoutWidget()
w.show()
w.resize(400,600)
w.setCentralWidget(cw)
w.setWindowTitle('pyqtgraph example: Arrow')

p = cw.addPlot(row=0, col=0)
p2 = cw.addPlot(row=1, col=0)

## variety of arrow shapes
a1 = pg.ArrowItem(angle=-160, tipAngle=60, headLen=40, tailLen=40, tailWidth=20, pen={'color': 'w', 'width': 3})
a2 = pg.ArrowItem(angle=-120, tipAngle=30, baseAngle=20, headLen=40, tailLen=40, tailWidth=8, pen=None, brush='y')
a3 = pg.ArrowItem(angle=-60, tipAngle=30, baseAngle=20, headLen=40, tailLen=None, brush=None)
a4 = pg.ArrowItem(angle=-20, tipAngle=30, baseAngle=-30, headLen=40, tailLen=None)
a2.setPos(10,0)
a3.setPos(20,0)
a4.setPos(30,0)
p.addItem(a1)
p.addItem(a2)
p.addItem(a3)
p.addItem(a4)
p.setRange(QtCore.QRectF(-20, -10, 60, 20))


## Animated arrow following curve
c = p2.plot(x=np.sin(np.linspace(0, 2*np.pi, 1000)), y=np.cos(np.linspace(0, 6*np.pi, 1000)))
a = pg.CurveArrow(c)
p2.addItem(a)
anim = a.makeAnimation(loop=-1)
anim.start()

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
