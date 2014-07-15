# -*- coding: utf-8 -*-
"""
This example demonstrates the ability to link the axes of views together
Views can be linked manually using the context menu, but only if they are given 
names.
"""

import initExample ## Add path to library (just for examples; you do not need this)


from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg

#QtGui.QApplication.setGraphicsSystem('raster')
app = QtGui.QApplication([])
#mw = QtGui.QMainWindow()
#mw.resize(800,800)

x = np.linspace(-50, 50, 1000)
y = np.sin(x) / x

win = pg.GraphicsWindow(title="pyqtgraph example: Linked Views")
win.resize(800,600)

win.addLabel("Linked Views", colspan=2)
win.nextRow()

p1 = win.addPlot(x=x, y=y, name="Plot1", title="Plot1")
p2 = win.addPlot(x=x, y=y, name="Plot2", title="Plot2: Y linked with Plot1")
p2.setLabel('bottom', "Label to test offset")
p2.setYLink('Plot1')  ## test linking by name


## create plots 3 and 4 out of order
p4 = win.addPlot(x=x, y=y, name="Plot4", title="Plot4: X -> Plot3 (deferred), Y -> Plot1", row=2, col=1)
p4.setXLink('Plot3')  ## Plot3 has not been created yet, but this should still work anyway.
p4.setYLink(p1)
p3 = win.addPlot(x=x, y=y, name="Plot3", title="Plot3: X linked with Plot1", row=2, col=0)
p3.setXLink(p1)
p3.setLabel('left', "Label to test offset")
#QtGui.QApplication.processEvents()


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

