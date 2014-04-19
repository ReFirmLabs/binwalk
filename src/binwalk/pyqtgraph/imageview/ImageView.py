# -*- coding: utf-8 -*-
"""
ImageView.py -  Widget for basic image dispay and analysis
Copyright 2010  Luke Campagnola
Distributed under MIT/X11 license. See license.txt for more infomation.

Widget used for displaying 2D or 3D data. Features:
  - float or int (including 16-bit int) image display via ImageItem
  - zoom/pan via GraphicsView
  - black/white level controls
  - time slider for 3D data sets
  - ROI plotting
  - Image normalization through a variety of methods
"""
from pyqtgraph.Qt import QtCore, QtGui, USE_PYSIDE

if USE_PYSIDE:
    from .ImageViewTemplate_pyside import *
else:
    from .ImageViewTemplate_pyqt import *
    
from pyqtgraph.graphicsItems.ImageItem import *
from pyqtgraph.graphicsItems.ROI import *
from pyqtgraph.graphicsItems.LinearRegionItem import *
from pyqtgraph.graphicsItems.InfiniteLine import *
from pyqtgraph.graphicsItems.ViewBox import *
#from widgets import ROI
import sys
#from numpy import ndarray
import pyqtgraph.ptime as ptime
import numpy as np
import pyqtgraph.debug as debug

from pyqtgraph.SignalProxy import SignalProxy

#try:
    #import pyqtgraph.metaarray as metaarray
    #HAVE_METAARRAY = True
#except:
    #HAVE_METAARRAY = False
    

class PlotROI(ROI):
    def __init__(self, size):
        ROI.__init__(self, pos=[0,0], size=size) #, scaleSnap=True, translateSnap=True)
        self.addScaleHandle([1, 1], [0, 0])
        self.addRotateHandle([0, 0], [0.5, 0.5])


class ImageView(QtGui.QWidget):
    """
    Widget used for display and analysis of image data.
    Implements many features:
    
    * Displays 2D and 3D image data. For 3D data, a z-axis
      slider is displayed allowing the user to select which frame is displayed.
    * Displays histogram of image data with movable region defining the dark/light levels
    * Editable gradient provides a color lookup table 
    * Frame slider may also be moved using left/right arrow keys as well as pgup, pgdn, home, and end.
    * Basic analysis features including:
    
        * ROI and embedded plot for measuring image values across frames
        * Image normalization / background subtraction 
    
    Basic Usage::
    
        imv = pg.ImageView()
        imv.show()
        imv.setImage(data)
    """
    sigTimeChanged = QtCore.Signal(object, object)
    sigProcessingChanged = QtCore.Signal(object)
    
    def __init__(self, parent=None, name="ImageView", view=None, imageItem=None, *args):
        """
        By default, this class creates an :class:`ImageItem <pyqtgraph.ImageItem>` to display image data
        and a :class:`ViewBox <pyqtgraph.ViewBox>` to contain the ImageItem. Custom items may be given instead 
        by specifying the *view* and/or *imageItem* arguments.
        """
        QtGui.QWidget.__init__(self, parent, *args)
        self.levelMax = 4096
        self.levelMin = 0
        self.name = name
        self.image = None
        self.axes = {}
        self.imageDisp = None
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.scene = self.ui.graphicsView.scene()
        
        self.ignoreTimeLine = False
        
        if view is None:
            self.view = ViewBox()
        else:
            self.view = view
        self.ui.graphicsView.setCentralItem(self.view)
        self.view.setAspectLocked(True)
        self.view.invertY()
        
        if imageItem is None:
            self.imageItem = ImageItem()
        else:
            self.imageItem = imageItem
        self.view.addItem(self.imageItem)
        self.currentIndex = 0
        
        self.ui.histogram.setImageItem(self.imageItem)
        
        self.ui.normGroup.hide()

        self.roi = PlotROI(10)
        self.roi.setZValue(20)
        self.view.addItem(self.roi)
        self.roi.hide()
        self.normRoi = PlotROI(10)
        self.normRoi.setPen(QtGui.QPen(QtGui.QColor(255,255,0)))
        self.normRoi.setZValue(20)
        self.view.addItem(self.normRoi)
        self.normRoi.hide()
        self.roiCurve = self.ui.roiPlot.plot()
        self.timeLine = InfiniteLine(0, movable=True)
        self.timeLine.setPen(QtGui.QPen(QtGui.QColor(255, 255, 0, 200)))
        self.timeLine.setZValue(1)
        self.ui.roiPlot.addItem(self.timeLine)
        self.ui.splitter.setSizes([self.height()-35, 35])
        self.ui.roiPlot.hideAxis('left')
        
        self.keysPressed = {}
        self.playTimer = QtCore.QTimer()
        self.playRate = 0
        self.lastPlayTime = 0
        
        self.normRgn = LinearRegionItem()
        self.normRgn.setZValue(0)
        self.ui.roiPlot.addItem(self.normRgn)
        self.normRgn.hide()
            
        ## wrap functions from view box
        for fn in ['addItem', 'removeItem']:
            setattr(self, fn, getattr(self.view, fn))

        ## wrap functions from histogram
        for fn in ['setHistogramRange', 'autoHistogramRange', 'getLookupTable', 'getLevels']:
            setattr(self, fn, getattr(self.ui.histogram, fn))

        self.timeLine.sigPositionChanged.connect(self.timeLineChanged)
        self.ui.roiBtn.clicked.connect(self.roiClicked)
        self.roi.sigRegionChanged.connect(self.roiChanged)
        self.ui.normBtn.toggled.connect(self.normToggled)
        self.ui.normDivideRadio.clicked.connect(self.normRadioChanged)
        self.ui.normSubtractRadio.clicked.connect(self.normRadioChanged)
        self.ui.normOffRadio.clicked.connect(self.normRadioChanged)
        self.ui.normROICheck.clicked.connect(self.updateNorm)
        self.ui.normFrameCheck.clicked.connect(self.updateNorm)
        self.ui.normTimeRangeCheck.clicked.connect(self.updateNorm)
        self.playTimer.timeout.connect(self.timeout)
        
        self.normProxy = SignalProxy(self.normRgn.sigRegionChanged, slot=self.updateNorm)
        self.normRoi.sigRegionChangeFinished.connect(self.updateNorm)
        
        self.ui.roiPlot.registerPlot(self.name + '_ROI')
        
        self.noRepeatKeys = [QtCore.Qt.Key_Right, QtCore.Qt.Key_Left, QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown]
        
        self.roiClicked() ## initialize roi plot to correct shape / visibility

    def setImage(self, img, autoRange=True, autoLevels=True, levels=None, axes=None, xvals=None, pos=None, scale=None, transform=None, autoHistogramRange=True):
        """
        Set the image to be displayed in the widget.
        
        ================== =======================================================================
        **Arguments:**
        img                (numpy array) the image to be displayed.
        xvals              (numpy array) 1D array of z-axis values corresponding to the third axis
                           in a 3D image. For video, this array should contain the time of each frame.
        autoRange          (bool) whether to scale/pan the view to fit the image.
        autoLevels         (bool) whether to update the white/black levels to fit the image.
        levels             (min, max); the white and black level values to use.
        axes               Dictionary indicating the interpretation for each axis.
                           This is only needed to override the default guess. Format is::
                       
                               {'t':0, 'x':1, 'y':2, 'c':3};
        
        pos                Change the position of the displayed image
        scale              Change the scale of the displayed image
        transform          Set the transform of the displayed image. This option overrides *pos*
                           and *scale*.
        autoHistogramRange If True, the histogram y-range is automatically scaled to fit the
                           image data.
        ================== =======================================================================
        """
        prof = debug.Profiler('ImageView.setImage', disabled=True)
        
        if hasattr(img, 'implements') and img.implements('MetaArray'):
            img = img.asarray()
        
        if not isinstance(img, np.ndarray):
            raise Exception("Image must be specified as ndarray.")
        self.image = img
        
        if xvals is not None:
            self.tVals = xvals
        elif hasattr(img, 'xvals'):
            try:
                self.tVals = img.xvals(0)
            except:
                self.tVals = np.arange(img.shape[0])
        else:
            self.tVals = np.arange(img.shape[0])
        
        prof.mark('1')
        
        if axes is None:
            if img.ndim == 2:
                self.axes = {'t': None, 'x': 0, 'y': 1, 'c': None}
            elif img.ndim == 3:
                if img.shape[2] <= 4:
                    self.axes = {'t': None, 'x': 0, 'y': 1, 'c': 2}
                else:
                    self.axes = {'t': 0, 'x': 1, 'y': 2, 'c': None}
            elif img.ndim == 4:
                self.axes = {'t': 0, 'x': 1, 'y': 2, 'c': 3}
            else:
                raise Exception("Can not interpret image with dimensions %s" % (str(img.shape)))
        elif isinstance(axes, dict):
            self.axes = axes.copy()
        elif isinstance(axes, list) or isinstance(axes, tuple):
            self.axes = {}
            for i in range(len(axes)):
                self.axes[axes[i]] = i
        else:
            raise Exception("Can not interpret axis specification %s. Must be like {'t': 2, 'x': 0, 'y': 1} or ('t', 'x', 'y', 'c')" % (str(axes)))
            
        for x in ['t', 'x', 'y', 'c']:
            self.axes[x] = self.axes.get(x, None)
        prof.mark('2')
            
        self.imageDisp = None
        
        
        prof.mark('3')
        
        self.currentIndex = 0
        self.updateImage(autoHistogramRange=autoHistogramRange)
        if levels is None and autoLevels:
            self.autoLevels()
        if levels is not None:  ## this does nothing since getProcessedImage sets these values again.
            self.setLevels(*levels)
            
        if self.ui.roiBtn.isChecked():
            self.roiChanged()
        prof.mark('4')
            
            
        if self.axes['t'] is not None:
            #self.ui.roiPlot.show()
            self.ui.roiPlot.setXRange(self.tVals.min(), self.tVals.max())
            self.timeLine.setValue(0)
            #self.ui.roiPlot.setMouseEnabled(False, False)
            if len(self.tVals) > 1:
                start = self.tVals.min()
                stop = self.tVals.max() + abs(self.tVals[-1] - self.tVals[0]) * 0.02
            elif len(self.tVals) == 1:
                start = self.tVals[0] - 0.5
                stop = self.tVals[0] + 0.5
            else:
                start = 0
                stop = 1
            for s in [self.timeLine, self.normRgn]:
                s.setBounds([start, stop])
        #else:
            #self.ui.roiPlot.hide()
        prof.mark('5')
            
        self.imageItem.resetTransform()
        if scale is not None:
            self.imageItem.scale(*scale)
        if pos is not None:
            self.imageItem.setPos(*pos)
        if transform is not None:
            self.imageItem.setTransform(transform)
        prof.mark('6')
            
        if autoRange:
            self.autoRange()
        self.roiClicked()
        prof.mark('7')
        prof.finish()

        
    def play(self, rate):
        """Begin automatically stepping frames forward at the given rate (in fps).
        This can also be accessed by pressing the spacebar."""
        #print "play:", rate
        self.playRate = rate
        if rate == 0:
            self.playTimer.stop()
            return
            
        self.lastPlayTime = ptime.time()
        if not self.playTimer.isActive():
            self.playTimer.start(16)
            
    def autoLevels(self):
        """Set the min/max intensity levels automatically to match the image data."""
        self.setLevels(self.levelMin, self.levelMax)

    def setLevels(self, min, max):
        """Set the min/max (bright and dark) levels."""
        self.ui.histogram.setLevels(min, max)

    def autoRange(self):
        """Auto scale and pan the view around the image."""
        image = self.getProcessedImage()
        self.view.autoRange()
        
    def getProcessedImage(self):
        """Returns the image data after it has been processed by any normalization options in use.
        This method also sets the attributes self.levelMin and self.levelMax 
        to indicate the range of data in the image."""
        if self.imageDisp is None:
            image = self.normalize(self.image)
            self.imageDisp = image
            self.levelMin, self.levelMax = list(map(float, ImageView.quickMinMax(self.imageDisp)))
            
        return self.imageDisp
        
        
    def close(self):
        """Closes the widget nicely, making sure to clear the graphics scene and release memory."""
        self.ui.roiPlot.close()
        self.ui.graphicsView.close()
        self.scene.clear()
        del self.image
        del self.imageDisp
        self.setParent(None)
        
    def keyPressEvent(self, ev):
        #print ev.key()
        if ev.key() == QtCore.Qt.Key_Space:
            if self.playRate == 0:
                fps = (self.getProcessedImage().shape[0]-1) / (self.tVals[-1] - self.tVals[0])
                self.play(fps)
                #print fps
            else:
                self.play(0)
            ev.accept()
        elif ev.key() == QtCore.Qt.Key_Home:
            self.setCurrentIndex(0)
            self.play(0)
            ev.accept()
        elif ev.key() == QtCore.Qt.Key_End:
            self.setCurrentIndex(self.getProcessedImage().shape[0]-1)
            self.play(0)
            ev.accept()
        elif ev.key() in self.noRepeatKeys:
            ev.accept()
            if ev.isAutoRepeat():
                return
            self.keysPressed[ev.key()] = 1
            self.evalKeyState()
        else:
            QtGui.QWidget.keyPressEvent(self, ev)

    def keyReleaseEvent(self, ev):
        if ev.key() in [QtCore.Qt.Key_Space, QtCore.Qt.Key_Home, QtCore.Qt.Key_End]:
            ev.accept()
        elif ev.key() in self.noRepeatKeys:
            ev.accept()
            if ev.isAutoRepeat():
                return
            try:
                del self.keysPressed[ev.key()]
            except:
                self.keysPressed = {}
            self.evalKeyState()
        else:
            QtGui.QWidget.keyReleaseEvent(self, ev)
        
        
    def evalKeyState(self):
        if len(self.keysPressed) == 1:
            key = list(self.keysPressed.keys())[0]
            if key == QtCore.Qt.Key_Right:
                self.play(20)
                self.jumpFrames(1)
                self.lastPlayTime = ptime.time() + 0.2  ## 2ms wait before start
                                                        ## This happens *after* jumpFrames, since it might take longer than 2ms
            elif key == QtCore.Qt.Key_Left:
                self.play(-20)
                self.jumpFrames(-1)
                self.lastPlayTime = ptime.time() + 0.2
            elif key == QtCore.Qt.Key_Up:
                self.play(-100)
            elif key == QtCore.Qt.Key_Down:
                self.play(100)
            elif key == QtCore.Qt.Key_PageUp:
                self.play(-1000)
            elif key == QtCore.Qt.Key_PageDown:
                self.play(1000)
        else:
            self.play(0)
        
        
    def timeout(self):
        now = ptime.time()
        dt = now - self.lastPlayTime
        if dt < 0:
            return
        n = int(self.playRate * dt)
        #print n, dt
        if n != 0:
            #print n, dt, self.lastPlayTime
            self.lastPlayTime += (float(n)/self.playRate)
            if self.currentIndex+n > self.image.shape[0]:
                self.play(0)
            self.jumpFrames(n)
        
    def setCurrentIndex(self, ind):
        """Set the currently displayed frame index."""
        self.currentIndex = np.clip(ind, 0, self.getProcessedImage().shape[0]-1)
        self.updateImage()
        self.ignoreTimeLine = True
        self.timeLine.setValue(self.tVals[self.currentIndex])
        self.ignoreTimeLine = False

    def jumpFrames(self, n):
        """Move video frame ahead n frames (may be negative)"""
        if self.axes['t'] is not None:
            self.setCurrentIndex(self.currentIndex + n)

    def normRadioChanged(self):
        self.imageDisp = None
        self.updateImage()
        self.autoLevels()
        self.roiChanged()
        self.sigProcessingChanged.emit(self)
        
    
    def updateNorm(self):
        if self.ui.normTimeRangeCheck.isChecked():
            #print "show!"
            self.normRgn.show()
        else:
            self.normRgn.hide()
        
        if self.ui.normROICheck.isChecked():
            #print "show!"
            self.normRoi.show()
        else:
            self.normRoi.hide()
        
        if not self.ui.normOffRadio.isChecked():
            self.imageDisp = None
            self.updateImage()
            self.autoLevels()
            self.roiChanged()
            self.sigProcessingChanged.emit(self)

    def normToggled(self, b):
        self.ui.normGroup.setVisible(b)
        self.normRoi.setVisible(b and self.ui.normROICheck.isChecked())
        self.normRgn.setVisible(b and self.ui.normTimeRangeCheck.isChecked())

    def hasTimeAxis(self):
        return 't' in self.axes and self.axes['t'] is not None

    def roiClicked(self):
        showRoiPlot = False
        if self.ui.roiBtn.isChecked():
            showRoiPlot = True
            self.roi.show()
            #self.ui.roiPlot.show()
            self.ui.roiPlot.setMouseEnabled(True, True)
            self.ui.splitter.setSizes([self.height()*0.6, self.height()*0.4])
            self.roiCurve.show()
            self.roiChanged()
            self.ui.roiPlot.showAxis('left')
        else:
            self.roi.hide()
            self.ui.roiPlot.setMouseEnabled(False, False)
            self.roiCurve.hide()
            self.ui.roiPlot.hideAxis('left')
            
        if self.hasTimeAxis():
            showRoiPlot = True
            mn = self.tVals.min()
            mx = self.tVals.max()
            self.ui.roiPlot.setXRange(mn, mx, padding=0.01)
            self.timeLine.show()
            self.timeLine.setBounds([mn, mx])
            self.ui.roiPlot.show()
            if not self.ui.roiBtn.isChecked():
                self.ui.splitter.setSizes([self.height()-35, 35])
        else:
            self.timeLine.hide()
            #self.ui.roiPlot.hide()
            
        self.ui.roiPlot.setVisible(showRoiPlot)

    def roiChanged(self):
        if self.image is None:
            return
            
        image = self.getProcessedImage()
        if image.ndim == 2:
            axes = (0, 1)
        elif image.ndim == 3:
            axes = (1, 2)
        else:
            return
        data, coords = self.roi.getArrayRegion(image.view(np.ndarray), self.imageItem, axes, returnMappedCoords=True)
        if data is not None:
            while data.ndim > 1:
                data = data.mean(axis=1)
            if image.ndim == 3:
                self.roiCurve.setData(y=data, x=self.tVals)
            else:
                while coords.ndim > 2:
                    coords = coords[:,:,0]
                coords = coords - coords[:,0,np.newaxis]
                xvals = (coords**2).sum(axis=0) ** 0.5
                self.roiCurve.setData(y=data, x=xvals)
                
            #self.ui.roiPlot.replot()


    @staticmethod
    def quickMinMax(data):
        while data.size > 1e6:
            ax = np.argmax(data.shape)
            sl = [slice(None)] * data.ndim
            sl[ax] = slice(None, None, 2)
            data = data[sl]
        return data.min(), data.max()

    def normalize(self, image):
        
        if self.ui.normOffRadio.isChecked():
            return image
            
        div = self.ui.normDivideRadio.isChecked()
        norm = image.view(np.ndarray).copy()
        #if div:
            #norm = ones(image.shape)
        #else:
            #norm = zeros(image.shape)
        if div:
            norm = norm.astype(np.float32)
            
        if self.ui.normTimeRangeCheck.isChecked() and image.ndim == 3:
            (sind, start) = self.timeIndex(self.normRgn.lines[0])
            (eind, end) = self.timeIndex(self.normRgn.lines[1])
            #print start, end, sind, eind
            n = image[sind:eind+1].mean(axis=0)
            n.shape = (1,) + n.shape
            if div:
                norm /= n
            else:
                norm -= n
                
        if self.ui.normFrameCheck.isChecked() and image.ndim == 3:
            n = image.mean(axis=1).mean(axis=1)
            n.shape = n.shape + (1, 1)
            if div:
                norm /= n
            else:
                norm -= n
            
        if self.ui.normROICheck.isChecked() and image.ndim == 3:
            n = self.normRoi.getArrayRegion(norm, self.imageItem, (1, 2)).mean(axis=1).mean(axis=1)
            n = n[:,np.newaxis,np.newaxis]
            #print start, end, sind, eind
            if div:
                norm /= n
            else:
                norm -= n
                
        return norm
        
    def timeLineChanged(self):
        #(ind, time) = self.timeIndex(self.ui.timeSlider)
        if self.ignoreTimeLine:
            return
        self.play(0)
        (ind, time) = self.timeIndex(self.timeLine)
        if ind != self.currentIndex:
            self.currentIndex = ind
            self.updateImage()
        #self.timeLine.setPos(time)
        #self.emit(QtCore.SIGNAL('timeChanged'), ind, time)
        self.sigTimeChanged.emit(ind, time)

    def updateImage(self, autoHistogramRange=True):
        ## Redraw image on screen
        if self.image is None:
            return
            
        image = self.getProcessedImage()
        
        if autoHistogramRange:
            self.ui.histogram.setHistogramRange(self.levelMin, self.levelMax)
        if self.axes['t'] is None:
            self.imageItem.updateImage(image)
        else:
            self.ui.roiPlot.show()
            self.imageItem.updateImage(image[self.currentIndex])
            
            
    def timeIndex(self, slider):
        ## Return the time and frame index indicated by a slider
        if self.image is None:
            return (0,0)
        
        t = slider.value()
        
        xv = self.tVals
        if xv is None:
            ind = int(t)
        else:
            if len(xv) < 2:
                return (0,0)
            totTime = xv[-1] + (xv[-1]-xv[-2])
            inds = np.argwhere(xv < t)
            if len(inds) < 1:
                return (0,t)
            ind = inds[-1,0]
        return ind, t

    def getView(self):
        """Return the ViewBox (or other compatible object) which displays the ImageItem"""
        return self.view
        
    def getImageItem(self):
        """Return the ImageItem for this ImageView."""
        return self.imageItem
        
    def getRoiPlot(self):
        """Return the ROI PlotWidget for this ImageView"""
        return self.ui.roiPlot
       
    def getHistogramWidget(self):
        """Return the HistogramLUTWidget for this ImageView"""
        return self.ui.histogram
