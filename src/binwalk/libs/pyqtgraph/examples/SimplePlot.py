import initExample ## Add path to library (just for examples; you do not need this)

from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
plt = pg.plot(np.random.normal(size=100), title="Simplest possible plotting example")
plt.getAxis('bottom').setTicks([[(x*20, str(x*20)) for x in range(6)]])
## Start Qt event loop unless running in interactive mode or using pyside.
ex = pg.exporters.SVGExporter.SVGExporter(plt.plotItem.scene())
ex.export('/home/luke/tmp/test.svg')

if __name__ == '__main__':
    import sys
    if sys.flags.interactive != 1 or not hasattr(QtCore, 'PYQT_VERSION'):
        pg.QtGui.QApplication.exec_()
