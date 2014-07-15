# -*- coding: utf-8 -*-
"""
JoystickButton is a button with x/y values. When the button is depressed and the
mouse dragged, the x/y values change to follow the mouse.
When the mouse button is released, the x/y values change to 0,0 (rather like 
letting go of the joystick).
"""

import initExample ## Add path to library (just for examples; you do not need this)

from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg


app = QtGui.QApplication([])
mw = QtGui.QMainWindow()
mw.resize(300,50)
mw.setWindowTitle('pyqtgraph example: JoystickButton')
cw = QtGui.QWidget()
mw.setCentralWidget(cw)
layout = QtGui.QGridLayout()
cw.setLayout(layout)
mw.show()

l1 = pg.ValueLabel(siPrefix=True, suffix='m')
l2 = pg.ValueLabel(siPrefix=True, suffix='m')
jb = pg.JoystickButton()
jb.setFixedWidth(30)
jb.setFixedHeight(30)


layout.addWidget(l1, 0, 0)
layout.addWidget(l2, 0, 1)
layout.addWidget(jb, 0, 2)

x = 0
y = 0
def update():
    global x, y, l1, l2, jb
    dx, dy = jb.getState()
    x += dx * 1e-3
    y += dy * 1e-3
    l1.setValue(x)
    l2.setValue(y)
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(30)
    
    


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
