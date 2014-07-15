# -*- coding: utf-8 -*-
"""
Demonstrates a variety of uses for ROI. This class provides a user-adjustable
region of interest marker. It is possible to customize the layout and 
function of the scale/rotate handles in very flexible ways. 
"""

import initExample ## Add path to library (just for examples; you do not need this)

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np


## Create image to display
arr = np.ones((100, 100), dtype=float)
arr[45:55, 45:55] = 0
arr[25, :] = 5
arr[:, 25] = 5
arr[75, :] = 5
arr[:, 75] = 5
arr[50, :] = 10
arr[:, 50] = 10
arr += np.sin(np.linspace(0, 20, 100)).reshape(1, 100)
arr += np.random.normal(size=(100,100))


## create GUI
app = QtGui.QApplication([])
w = pg.GraphicsWindow(size=(1000,800), border=True)
w.setWindowTitle('pyqtgraph example: ROI Examples')

text = """Data Selection From Image.<br>\n
Drag an ROI or its handles to update the selected image.<br>
Hold CTRL while dragging to snap to pixel boundaries<br>
and 15-degree rotation angles.
"""
w1 = w.addLayout(row=0, col=0)
label1 = w1.addLabel(text, row=0, col=0)
v1a = w1.addViewBox(row=1, col=0, lockAspect=True)
v1b = w1.addViewBox(row=2, col=0, lockAspect=True)
img1a = pg.ImageItem(arr)
v1a.addItem(img1a)
img1b = pg.ImageItem()
v1b.addItem(img1b)
v1a.disableAutoRange('xy')
v1b.disableAutoRange('xy')
v1a.autoRange()
v1b.autoRange()

rois = []
rois.append(pg.RectROI([20, 20], [20, 20], pen=(0,9)))
rois[-1].addRotateHandle([1,0], [0.5, 0.5])
rois.append(pg.LineROI([0, 60], [20, 80], width=5, pen=(1,9)))
rois.append(pg.MultiRectROI([[20, 90], [50, 60], [60, 90]], width=5, pen=(2,9)))
rois.append(pg.EllipseROI([60, 10], [30, 20], pen=(3,9)))
rois.append(pg.CircleROI([80, 50], [20, 20], pen=(4,9)))
#rois.append(pg.LineSegmentROI([[110, 50], [20, 20]], pen=(5,9)))
rois.append(pg.PolyLineROI([[80, 60], [90, 30], [60, 40]], pen=(6,9), closed=True))

def update(roi):
    img1b.setImage(roi.getArrayRegion(arr, img1a), levels=(0, arr.max()))
    v1b.autoRange()
    
for roi in rois:
    roi.sigRegionChanged.connect(update)
    v1a.addItem(roi)

update(rois[-1])
    


text = """User-Modifiable ROIs<br>
Click on a line segment to add a new handle.
Right click on a handle to remove.
"""
w2 = w.addLayout(row=0, col=1)
label2 = w2.addLabel(text, row=0, col=0)
v2a = w2.addViewBox(row=1, col=0, lockAspect=True)
r2a = pg.PolyLineROI([[0,0], [10,10], [10,30], [30,10]], closed=True)
v2a.addItem(r2a)
r2b = pg.PolyLineROI([[0,-20], [10,-10], [10,-30]], closed=False)
v2a.addItem(r2b)
v2a.disableAutoRange('xy')
#v2b.disableAutoRange('xy')
v2a.autoRange()
#v2b.autoRange()

text = """Building custom ROI types<Br>
ROIs can be built with a variety of different handle types<br>
that scale and rotate the roi around an arbitrary center location
"""
w3 = w.addLayout(row=1, col=0)
label3 = w3.addLabel(text, row=0, col=0)
v3 = w3.addViewBox(row=1, col=0, lockAspect=True)

r3a = pg.ROI([0,0], [10,10])
v3.addItem(r3a)
## handles scaling horizontally around center
r3a.addScaleHandle([1, 0.5], [0.5, 0.5])
r3a.addScaleHandle([0, 0.5], [0.5, 0.5])

## handles scaling vertically from opposite edge
r3a.addScaleHandle([0.5, 0], [0.5, 1])
r3a.addScaleHandle([0.5, 1], [0.5, 0])

## handles scaling both vertically and horizontally
r3a.addScaleHandle([1, 1], [0, 0])
r3a.addScaleHandle([0, 0], [1, 1])

r3b = pg.ROI([20,0], [10,10])
v3.addItem(r3b)
## handles rotating around center
r3b.addRotateHandle([1, 1], [0.5, 0.5])
r3b.addRotateHandle([0, 0], [0.5, 0.5])

## handles rotating around opposite corner
r3b.addRotateHandle([1, 0], [0, 1])
r3b.addRotateHandle([0, 1], [1, 0])

## handles rotating/scaling around center
r3b.addScaleRotateHandle([0, 0.5], [0.5, 0.5])
r3b.addScaleRotateHandle([1, 0.5], [0.5, 0.5])

v3.disableAutoRange('xy')
v3.autoRange()


text = """Transforming objects with ROI"""
w4 = w.addLayout(row=1, col=1)
label4 = w4.addLabel(text, row=0, col=0)
v4 = w4.addViewBox(row=1, col=0, lockAspect=True)
g = pg.GridItem()
v4.addItem(g)
r4 = pg.ROI([0,0], [100,100])
r4.addRotateHandle([1,0], [0.5, 0.5])
r4.addRotateHandle([0,1], [0.5, 0.5])
img4 = pg.ImageItem(arr)
v4.addItem(r4)
img4.setParentItem(r4)

v4.disableAutoRange('xy')
v4.autoRange()








## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
