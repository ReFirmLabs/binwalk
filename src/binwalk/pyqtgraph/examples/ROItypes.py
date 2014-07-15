#!/usr/bin/python -i
# -*- coding: utf-8 -*-
## Add path to library (just for examples; you do not need this)
import initExample


from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import pyqtgraph as pg

## create GUI
app = QtGui.QApplication([])

w = pg.GraphicsWindow(size=(800,800), border=True)

v = w.addViewBox(colspan=2)

#w = QtGui.QMainWindow()
#w.resize(800,800)
#v = pg.GraphicsView()
v.invertY(True)  ## Images usually have their Y-axis pointing downward
v.setAspectLocked(True)
#v.enableMouse(True)
#v.autoPixelScale = False
#w.setCentralWidget(v)
#s = v.scene()
#v.setRange(QtCore.QRectF(-2, -2, 220, 220))


## Create image to display
arr = np.ones((100, 100), dtype=float)
arr[45:55, 45:55] = 0
arr[25, :] = 5
arr[:, 25] = 5
arr[75, :] = 5
arr[:, 75] = 5
arr[50, :] = 10
arr[:, 50] = 10

## Create image items, add to scene and set position 
im1 = pg.ImageItem(arr)
im2 = pg.ImageItem(arr)
v.addItem(im1)
v.addItem(im2)
im2.moveBy(110, 20)
v.setRange(QtCore.QRectF(0, 0, 200, 120))

im3 = pg.ImageItem()
v2 = w.addViewBox(1,0)
v2.addItem(im3)
v2.setRange(QtCore.QRectF(0, 0, 60, 60))
v2.invertY(True)
v2.setAspectLocked(True)
#im3.moveBy(0, 130)
im3.setZValue(10)

im4 = pg.ImageItem()
v3 = w.addViewBox(1,1)
v3.addItem(im4)
v3.setRange(QtCore.QRectF(0, 0, 60, 60))
v3.invertY(True)
v3.setAspectLocked(True)
#im4.moveBy(110, 130)
im4.setZValue(10)

## create the plot
pi1 = w.addPlot(2,0, colspan=2)
#pi1 = pg.PlotItem()
#s.addItem(pi1)
#pi1.scale(0.5, 0.5)
#pi1.setGeometry(0, 170, 300, 100)

lastRoi = None

def updateRoi(roi):
    global im1, im2, im3, im4, arr, lastRoi
    if roi is None:
        return
    lastRoi = roi
    arr1 = roi.getArrayRegion(im1.image, img=im1)
    im3.setImage(arr1)
    arr2 = roi.getArrayRegion(im2.image, img=im2)
    im4.setImage(arr2)
    updateRoiPlot(roi, arr1)
    
def updateRoiPlot(roi, data=None):
    if data is None:
        data = roi.getArrayRegion(im1.image, img=im1)
    if data is not None:
        roi.curve.setData(data.mean(axis=1))


## Create a variety of different ROI types
rois = []
rois.append(pg.TestROI([0,  0], [20, 20], maxBounds=QtCore.QRectF(-10, -10, 230, 140), pen=(0,9)))
rois.append(pg.LineROI([0,  0], [20, 20], width=5, pen=(1,9)))
rois.append(pg.MultiLineROI([[0, 50], [50, 60], [60, 30]], width=5, pen=(2,9)))
rois.append(pg.EllipseROI([110, 10], [30, 20], pen=(3,9)))
rois.append(pg.CircleROI([110, 50], [20, 20], pen=(4,9)))
rois.append(pg.PolygonROI([[2,0], [2.1,0], [2,.1]], pen=(5,9)))
#rois.append(SpiralROI([20,30], [1,1], pen=mkPen(0)))

## Add each ROI to the scene and link its data to a plot curve with the same color
for r in rois:
    v.addItem(r)
    c = pi1.plot(pen=r.pen)
    r.curve = c
    r.sigRegionChanged.connect(updateRoi)

def updateImage():
    global im1, arr, lastRoi
    r = abs(np.random.normal(loc=0, scale=(arr.max()-arr.min())*0.1, size=arr.shape))
    im1.updateImage(arr + r)
    updateRoi(lastRoi)
    for r in rois:
        updateRoiPlot(r)
    
## Rapidly update one of the images with random noise    
t = QtCore.QTimer()
t.timeout.connect(updateImage)
t.start(50)



## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
