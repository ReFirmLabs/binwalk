# -*- coding: utf-8 -*-
"""
Tests the speed of image updates for an ImageItem and RawImageWidget.
The speed will generally depend on the type of data being shown, whether
it is being scaled and/or converted by lookup table, and whether OpenGL
is used by the view widget
"""


import initExample ## Add path to library (just for examples; you do not need this)


from pyqtgraph.Qt import QtGui, QtCore, USE_PYSIDE
import numpy as np
import pyqtgraph as pg
import scipy.ndimage as ndi
import pyqtgraph.ptime as ptime

if USE_PYSIDE:
    import VideoTemplate_pyside as VideoTemplate
else:
    import VideoTemplate_pyqt as VideoTemplate
    

#QtGui.QApplication.setGraphicsSystem('raster')
app = QtGui.QApplication([])
#mw = QtGui.QMainWindow()
#mw.resize(800,800)

win = QtGui.QMainWindow()
win.setWindowTitle('pyqtgraph example: VideoSpeedTest')
ui = VideoTemplate.Ui_MainWindow()
ui.setupUi(win)
win.show()
ui.maxSpin1.setOpts(value=255, step=1)
ui.minSpin1.setOpts(value=0, step=1)

#ui.graphicsView.useOpenGL()  ## buggy, but you can try it if you need extra speed.

vb = pg.ViewBox()
ui.graphicsView.setCentralItem(vb)
vb.setAspectLocked()
img = pg.ImageItem()
vb.addItem(img)
vb.setRange(QtCore.QRectF(0, 0, 512, 512))

LUT = None
def updateLUT():
    global LUT, ui
    dtype = ui.dtypeCombo.currentText()
    if dtype == 'uint8':
        n = 256
    else:
        n = 4096
    LUT = ui.gradient.getLookupTable(n, alpha=ui.alphaCheck.isChecked())
ui.gradient.sigGradientChanged.connect(updateLUT)
updateLUT()

ui.alphaCheck.toggled.connect(updateLUT)

def updateScale():
    global ui
    spins = [ui.minSpin1, ui.maxSpin1, ui.minSpin2, ui.maxSpin2, ui.minSpin3, ui.maxSpin3]
    if ui.rgbLevelsCheck.isChecked():
        for s in spins[2:]:
            s.setEnabled(True)
    else:
        for s in spins[2:]:
            s.setEnabled(False)
ui.rgbLevelsCheck.toggled.connect(updateScale)
    
cache = {}
def mkData():
    global data, cache, ui
    dtype = (ui.dtypeCombo.currentText(), ui.rgbCheck.isChecked())
    if dtype not in cache:
        if dtype[0] == 'uint8':
            dt = np.uint8
            loc = 128
            scale = 64
            mx = 255
        elif dtype[0] == 'uint16':
            dt = np.uint16
            loc = 4096
            scale = 1024
            mx = 2**16
        elif dtype[0] == 'float':
            dt = np.float
            loc = 1.0
            scale = 0.1
        
        if ui.rgbCheck.isChecked():
            data = np.random.normal(size=(20,512,512,3), loc=loc, scale=scale)
            data = ndi.gaussian_filter(data, (0, 6, 6, 0))
        else:
            data = np.random.normal(size=(20,512,512), loc=loc, scale=scale)
            data = ndi.gaussian_filter(data, (0, 6, 6))
        if dtype[0] != 'float':
            data = np.clip(data, 0, mx)
        data = data.astype(dt)
        cache[dtype] = data
        
    data = cache[dtype]
    updateLUT()
mkData()
ui.dtypeCombo.currentIndexChanged.connect(mkData)
ui.rgbCheck.toggled.connect(mkData)

ptr = 0
lastTime = ptime.time()
fps = None
def update():
    global ui, ptr, lastTime, fps, LUT, img
    if ui.lutCheck.isChecked():
        useLut = LUT
    else:
        useLut = None

    if ui.scaleCheck.isChecked():
        if ui.rgbLevelsCheck.isChecked():
            useScale = [
                [ui.minSpin1.value(), ui.maxSpin1.value()], 
                [ui.minSpin2.value(), ui.maxSpin2.value()], 
                [ui.minSpin3.value(), ui.maxSpin3.value()]]
        else:
            useScale = [ui.minSpin1.value(), ui.maxSpin1.value()]
    else:
        useScale = None

    if ui.rawRadio.isChecked():
        ui.rawImg.setImage(data[ptr%data.shape[0]], lut=useLut, levels=useScale)
        ui.stack.setCurrentIndex(1)
    elif ui.rawGLRadio.isChecked():
        ui.rawGLImg.setImage(data[ptr%data.shape[0]], lut=useLut, levels=useScale)
        ui.stack.setCurrentIndex(2)
    else:
        img.setImage(data[ptr%data.shape[0]], autoLevels=False, levels=useScale, lut=useLut)
        ui.stack.setCurrentIndex(0)
        #img.setImage(data[ptr%data.shape[0]], autoRange=False)
        
    ptr += 1
    now = ptime.time()
    dt = now - lastTime
    lastTime = now
    if fps is None:
        fps = 1.0/dt
    else:
        s = np.clip(dt*3., 0, 1)
        fps = fps * (1-s) + (1.0/dt) * s
    ui.fpsLabel.setText('%0.2f fps' % fps)
    app.processEvents()  ## force complete redraw for every plot
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)
    


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
