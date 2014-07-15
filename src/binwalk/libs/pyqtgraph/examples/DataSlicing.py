# -*- coding: utf-8 -*-
"""
Demonstrate a simple data-slicing task: given 3D data (displayed at top), select 
a 2D plane and interpolate data along that plane to generate a slice image 
(displayed at bottom). 


"""

## Add path to library (just for examples; you do not need this)
import initExample

import numpy as np
import scipy
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg

app = QtGui.QApplication([])

## Create window with two ImageView widgets
win = QtGui.QMainWindow()
win.resize(800,800)
win.setWindowTitle('pyqtgraph example: DataSlicing')
cw = QtGui.QWidget()
win.setCentralWidget(cw)
l = QtGui.QGridLayout()
cw.setLayout(l)
imv1 = pg.ImageView()
imv2 = pg.ImageView()
l.addWidget(imv1, 0, 0)
l.addWidget(imv2, 1, 0)
win.show()

roi = pg.LineSegmentROI([[10, 64], [120,64]], pen='r')
imv1.addItem(roi)

x1 = np.linspace(-30, 10, 128)[:, np.newaxis, np.newaxis]
x2 = np.linspace(-20, 20, 128)[:, np.newaxis, np.newaxis]
y = np.linspace(-30, 10, 128)[np.newaxis, :, np.newaxis]
z = np.linspace(-20, 20, 128)[np.newaxis, np.newaxis, :]
d1 = np.sqrt(x1**2 + y**2 + z**2)
d2 = 2*np.sqrt(x1[::-1]**2 + y**2 + z**2)
d3 = 4*np.sqrt(x2**2 + y[:,::-1]**2 + z**2)
data = (np.sin(d1) / d1**2) + (np.sin(d2) / d2**2) + (np.sin(d3) / d3**2)

def update():
    global data, imv1, imv2
    d2 = roi.getArrayRegion(data, imv1.imageItem, axes=(1,2))
    imv2.setImage(d2)
    
roi.sigRegionChanged.connect(update)


## Display the data
imv1.setImage(data)
imv1.setHistogramRange(-0.01, 0.01)
imv1.setLevels(-0.003, 0.003)

update()

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
