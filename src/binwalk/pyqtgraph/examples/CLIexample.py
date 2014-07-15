"""
Display a plot and an image with minimal setup. 

pg.plot() and pg.image() are indended to be used from an interactive prompt
to allow easy data inspection (but note that PySide unfortunately does not
call the Qt event loop while the interactive prompt is running, in this case
it is necessary to call QApplication.exec_() to make the windows appear).
"""
import initExample ## Add path to library (just for examples; you do not need this)


import numpy as np
import pyqtgraph as pg

data = np.random.normal(size=1000)
pg.plot(data, title="Simplest possible plotting example")

data = np.random.normal(size=(500,500))
pg.image(data, title="Simplest possible image example")


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if sys.flags.interactive != 1 or not hasattr(QtCore, 'PYQT_VERSION'):
        pg.QtGui.QApplication.exec_()
