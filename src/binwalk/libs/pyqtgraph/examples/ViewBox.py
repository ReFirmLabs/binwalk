#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
ViewBox is the general-purpose graphical container that allows the user to 
zoom / pan to inspect any area of a 2D coordinate system. 

This unimaginative example demonstrates the constrution of a ViewBox-based
plot area with axes, very similar to the way PlotItem is built.
"""


## Add path to library (just for examples; you do not need this)
import initExample

## This example uses a ViewBox to create a PlotWidget-like interface

#from scipy import random
import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg

app = QtGui.QApplication([])
mw = QtGui.QMainWindow()
mw.setWindowTitle('pyqtgraph example: ViewBox')
mw.show()
mw.resize(800, 600)

gv = pg.GraphicsView()
mw.setCentralWidget(gv)
l = QtGui.QGraphicsGridLayout()
l.setHorizontalSpacing(0)
l.setVerticalSpacing(0)

vb = pg.ViewBox()

p1 = pg.PlotDataItem()
vb.addItem(p1)

## Just something to play with inside the ViewBox
class movableRect(QtGui.QGraphicsRectItem):
    def __init__(self, *args):
        QtGui.QGraphicsRectItem.__init__(self, *args)
        self.setAcceptHoverEvents(True)
    def hoverEnterEvent(self, ev):
        self.savedPen = self.pen()
        self.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255)))
        ev.ignore()
    def hoverLeaveEvent(self, ev):
        self.setPen(self.savedPen)
        ev.ignore()
    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            ev.accept()
            self.pressDelta = self.mapToParent(ev.pos()) - self.pos()
        else:
            ev.ignore()     
    def mouseMoveEvent(self, ev):
        self.setPos(self.mapToParent(ev.pos()) - self.pressDelta)
        
rect = movableRect(QtCore.QRectF(0, 0, 1, 1))
rect.setPen(QtGui.QPen(QtGui.QColor(100, 200, 100)))
vb.addItem(rect)

l.addItem(vb, 0, 1)
gv.centralWidget.setLayout(l)


xScale = pg.AxisItem(orientation='bottom', linkView=vb)
l.addItem(xScale, 1, 1)
yScale = pg.AxisItem(orientation='left', linkView=vb)
l.addItem(yScale, 0, 0)

xScale.setLabel(text="<span style='color: #ff0000; font-weight: bold'>X</span> <i>Axis</i>", units="s")
yScale.setLabel('Y Axis', units='V')

def rand(n):
    data = np.random.random(n)
    data[int(n*0.1):int(n*0.13)] += .5
    data[int(n*0.18)] += 2
    data[int(n*0.1):int(n*0.13)] *= 5
    data[int(n*0.18)] *= 20
    return data, np.arange(n, n+len(data)) / float(n)
    

def updateData():
    yd, xd = rand(10000)
    p1.setData(y=yd, x=xd)

yd, xd = rand(10000)
updateData()
vb.autoRange()

t = QtCore.QTimer()
t.timeout.connect(updateData)
t.start(50)

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
