# -*- coding: utf-8 -*-
## Add path to library (just for examples; you do not need this)                                                                           
import initExample

import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg


app = QtGui.QApplication([])
mw = pg.GraphicsView()
mw.resize(800,800)
mw.show()

#ts = pg.TickSliderItem()
#mw.setCentralItem(ts)
#ts.addTick(0.5, 'r')
#ts.addTick(0.9, 'b')

ge = pg.GradientEditorItem()
mw.setCentralItem(ge)


## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
