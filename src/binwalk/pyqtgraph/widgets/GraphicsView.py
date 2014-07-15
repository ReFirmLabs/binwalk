# -*- coding: utf-8 -*-
"""
GraphicsView.py -   Extension of QGraphicsView
Copyright 2010  Luke Campagnola
Distributed under MIT/X11 license. See license.txt for more infomation.
"""

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg

try:
    from pyqtgraph.Qt import QtOpenGL
    HAVE_OPENGL = True
except ImportError:
    HAVE_OPENGL = False

from pyqtgraph.Point import Point
import sys, os
from .FileDialog import FileDialog
from pyqtgraph.GraphicsScene import GraphicsScene
import numpy as np
import pyqtgraph.functions as fn
import pyqtgraph.debug as debug
import pyqtgraph 

__all__ = ['GraphicsView']

class GraphicsView(QtGui.QGraphicsView):
    """Re-implementation of QGraphicsView that removes scrollbars and allows unambiguous control of the 
    viewed coordinate range. Also automatically creates a GraphicsScene and a central QGraphicsWidget
    that is automatically scaled to the full view geometry.
    
    This widget is the basis for :class:`PlotWidget <pyqtgraph.PlotWidget>`, 
    :class:`GraphicsLayoutWidget <pyqtgraph.GraphicsLayoutWidget>`, and the view widget in
    :class:`ImageView <pyqtgraph.ImageView>`.
    
    By default, the view coordinate system matches the widget's pixel coordinates and 
    automatically updates when the view is resized. This can be overridden by setting 
    autoPixelRange=False. The exact visible range can be set with setRange().
    
    The view can be panned using the middle mouse button and scaled using the right mouse button if
    enabled via enableMouse()  (but ordinarily, we use ViewBox for this functionality)."""
    
    sigRangeChanged = QtCore.Signal(object, object)
    sigTransformChanged = QtCore.Signal(object)
    sigMouseReleased = QtCore.Signal(object)
    sigSceneMouseMoved = QtCore.Signal(object)
    #sigRegionChanged = QtCore.Signal(object)
    sigScaleChanged = QtCore.Signal(object)
    lastFileDir = None
    
    def __init__(self, parent=None, useOpenGL=None, background='default'):
        """
        ============  ============================================================
        Arguments:
        parent        Optional parent widget
        useOpenGL     If True, the GraphicsView will use OpenGL to do all of its
                      rendering. This can improve performance on some systems,
                      but may also introduce bugs (the combination of 
                      QGraphicsView and QGLWidget is still an 'experimental' 
                      feature of Qt)
        background    Set the background color of the GraphicsView. Accepts any
                      single argument accepted by 
                      :func:`mkColor <pyqtgraph.mkColor>`. By 
                      default, the background color is determined using the
                      'backgroundColor' configuration option (see 
                      :func:`setConfigOption <pyqtgraph.setConfigOption>`.
        ============  ============================================================
        """
        
        self.closed = False
        
        QtGui.QGraphicsView.__init__(self, parent)
        
        if useOpenGL is None:
            useOpenGL = pyqtgraph.getConfigOption('useOpenGL')
        
        self.useOpenGL(useOpenGL)
        
        self.setCacheMode(self.CacheBackground)
        
        ## This might help, but it's probably dangerous in the general case..
        #self.setOptimizationFlag(self.DontSavePainterState, True)
        
        self.setBackgroundRole(QtGui.QPalette.NoRole)
        self.setBackground(background)
        
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFrameShape(QtGui.QFrame.NoFrame)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QtGui.QGraphicsView.NoAnchor)
        self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)
        self.setViewportUpdateMode(QtGui.QGraphicsView.MinimalViewportUpdate)
        
        
        self.lockedViewports = []
        self.lastMousePos = None
        self.setMouseTracking(True)
        self.aspectLocked = False
        self.range = QtCore.QRectF(0, 0, 1, 1)
        self.autoPixelRange = True
        self.currentItem = None
        self.clearMouse()
        self.updateMatrix()
        self.sceneObj = GraphicsScene()
        self.setScene(self.sceneObj)
        
        ## Workaround for PySide crash
        ## This ensures that the scene will outlive the view.
        if pyqtgraph.Qt.USE_PYSIDE:
            self.sceneObj._view_ref_workaround = self
        
        ## by default we set up a central widget with a grid layout.
        ## this can be replaced if needed.
        self.centralWidget = None
        self.setCentralItem(QtGui.QGraphicsWidget())
        self.centralLayout = QtGui.QGraphicsGridLayout()
        self.centralWidget.setLayout(self.centralLayout)
        
        self.mouseEnabled = False
        self.scaleCenter = False  ## should scaling center around view center (True) or mouse click (False)
        self.clickAccepted = False
        
    def setAntialiasing(self, aa):
        """Enable or disable default antialiasing.
        Note that this will only affect items that do not specify their own antialiasing options."""
        if aa:
            self.setRenderHints(self.renderHints() | QtGui.QPainter.Antialiasing)
        else:
            self.setRenderHints(self.renderHints() & ~QtGui.QPainter.Antialiasing)
        
    def setBackground(self, background):
        """
        Set the background color of the GraphicsView.
        To use the defaults specified py pyqtgraph.setConfigOption, use background='default'.
        To make the background transparent, use background=None.
        """
        self._background = background
        if background == 'default':
            background = pyqtgraph.getConfigOption('background')
        brush = fn.mkBrush(background)
        self.setBackgroundBrush(brush)
    
    def paintEvent(self, ev):
        self.scene().prepareForPaint()
        #print "GV: paint", ev.rect()
        return QtGui.QGraphicsView.paintEvent(self, ev)
    
    def render(self, *args, **kwds):
        self.scene().prepareForPaint()
        return QtGui.QGraphicsView.render(self, *args, **kwds)
        
    
    def close(self):
        self.centralWidget = None
        self.scene().clear()
        self.currentItem = None
        self.sceneObj = None
        self.closed = True
        self.setViewport(None)
        
    def useOpenGL(self, b=True):
        if b:
            if not HAVE_OPENGL:
                raise Exception("Requested to use OpenGL with QGraphicsView, but QtOpenGL module is not available.")
            v = QtOpenGL.QGLWidget()
        else:
            v = QtGui.QWidget()
            
        self.setViewport(v)
            
    def keyPressEvent(self, ev):
        self.scene().keyPressEvent(ev)  ## bypass view, hand event directly to scene
                                        ## (view likes to eat arrow key events)
        
        
    def setCentralItem(self, item):
        return self.setCentralWidget(item)
        
    def setCentralWidget(self, item):
        """Sets a QGraphicsWidget to automatically fill the entire view (the item will be automatically
        resize whenever the GraphicsView is resized)."""
        if self.centralWidget is not None:
            self.scene().removeItem(self.centralWidget)
        self.centralWidget = item
        if item is not None:
            self.sceneObj.addItem(item)
            self.resizeEvent(None)
        
    def addItem(self, *args):
        return self.scene().addItem(*args)
        
    def removeItem(self, *args):
        return self.scene().removeItem(*args)
        
    def enableMouse(self, b=True):
        self.mouseEnabled = b
        self.autoPixelRange = (not b)
        
    def clearMouse(self):
        self.mouseTrail = []
        self.lastButtonReleased = None
    
    def resizeEvent(self, ev):
        if self.closed:
            return
        if self.autoPixelRange:
            self.range = QtCore.QRectF(0, 0, self.size().width(), self.size().height())
        GraphicsView.setRange(self, self.range, padding=0, disableAutoPixel=False)  ## we do this because some subclasses like to redefine setRange in an incompatible way.
        self.updateMatrix()
    
    def updateMatrix(self, propagate=True):
        self.setSceneRect(self.range)
        if self.autoPixelRange:
            self.resetTransform()
        else:
            if self.aspectLocked:
                self.fitInView(self.range, QtCore.Qt.KeepAspectRatio)
            else:
                self.fitInView(self.range, QtCore.Qt.IgnoreAspectRatio)
            
        self.sigRangeChanged.emit(self, self.range)
        self.sigTransformChanged.emit(self)
        
        if propagate:
            for v in self.lockedViewports:
                v.setXRange(self.range, padding=0)
        
    def viewRect(self):
        """Return the boundaries of the view in scene coordinates"""
        ## easier to just return self.range ?
        r = QtCore.QRectF(self.rect())
        return self.viewportTransform().inverted()[0].mapRect(r)

    def visibleRange(self):
        ## for backward compatibility
        return self.viewRect()

    def translate(self, dx, dy):
        self.range.adjust(dx, dy, dx, dy)
        self.updateMatrix()
    
    def scale(self, sx, sy, center=None):
        scale = [sx, sy]
        if self.aspectLocked:
            scale[0] = scale[1]
        
        if self.scaleCenter:
            center = None
        if center is None:
            center = self.range.center()
            
        w = self.range.width()  / scale[0]
        h = self.range.height() / scale[1]
        self.range = QtCore.QRectF(center.x() - (center.x()-self.range.left()) / scale[0], center.y() - (center.y()-self.range.top())  /scale[1], w, h)
        
        
        self.updateMatrix()
        self.sigScaleChanged.emit(self)

    def setRange(self, newRect=None, padding=0.05, lockAspect=None, propagate=True, disableAutoPixel=True):
        if disableAutoPixel:
            self.autoPixelRange=False
        if newRect is None:
            newRect = self.visibleRange()
            padding = 0
        
        padding = Point(padding)
        newRect = QtCore.QRectF(newRect)
        pw = newRect.width() * padding[0]
        ph = newRect.height() * padding[1]
        newRect = newRect.adjusted(-pw, -ph, pw, ph)
        scaleChanged = False
        if self.range.width() != newRect.width() or self.range.height() != newRect.height():
            scaleChanged = True
        self.range = newRect
        #print "New Range:", self.range
        if self.centralWidget is not None:
            self.centralWidget.setGeometry(self.range)
        self.updateMatrix(propagate)
        if scaleChanged:
            self.sigScaleChanged.emit(self)

    def scaleToImage(self, image):
        """Scales such that pixels in image are the same size as screen pixels. This may result in a significant performance increase."""
        pxSize = image.pixelSize()
        image.setPxMode(True)
        try:
            self.sigScaleChanged.disconnect(image.setScaledMode)
        except TypeError:
            pass
        tl = image.sceneBoundingRect().topLeft()
        w = self.size().width() * pxSize[0]
        h = self.size().height() * pxSize[1]
        range = QtCore.QRectF(tl.x(), tl.y(), w, h)
        GraphicsView.setRange(self, range, padding=0)
        self.sigScaleChanged.connect(image.setScaledMode)
        
        
        
    def lockXRange(self, v1):
        if not v1 in self.lockedViewports:
            self.lockedViewports.append(v1)
        
    def setXRange(self, r, padding=0.05):
        r1 = QtCore.QRectF(self.range)
        r1.setLeft(r.left())
        r1.setRight(r.right())
        GraphicsView.setRange(self, r1, padding=[padding, 0], propagate=False)
        
    def setYRange(self, r, padding=0.05):
        r1 = QtCore.QRectF(self.range)
        r1.setTop(r.top())
        r1.setBottom(r.bottom())
        GraphicsView.setRange(self, r1, padding=[0, padding], propagate=False)
        
    def wheelEvent(self, ev):
        QtGui.QGraphicsView.wheelEvent(self, ev)
        if not self.mouseEnabled:
            return
        sc = 1.001 ** ev.delta()
        #self.scale *= sc
        #self.updateMatrix()
        self.scale(sc, sc)
        
    def setAspectLocked(self, s):
        self.aspectLocked = s
        
    def leaveEvent(self, ev):
        self.scene().leaveEvent(ev)  ## inform scene when mouse leaves
        
    def mousePressEvent(self, ev):
        QtGui.QGraphicsView.mousePressEvent(self, ev)
        

        if not self.mouseEnabled:
            return
        self.lastMousePos = Point(ev.pos())
        self.mousePressPos = ev.pos()
        self.clickAccepted = ev.isAccepted()
        if not self.clickAccepted:
            self.scene().clearSelection()
        return   ## Everything below disabled for now..
        
    def mouseReleaseEvent(self, ev):
        QtGui.QGraphicsView.mouseReleaseEvent(self, ev)
        if not self.mouseEnabled:
            return 
        self.sigMouseReleased.emit(ev)
        self.lastButtonReleased = ev.button()
        return   ## Everything below disabled for now..
        
    def mouseMoveEvent(self, ev):
        if self.lastMousePos is None:
            self.lastMousePos = Point(ev.pos())
        delta = Point(ev.pos() - self.lastMousePos)
        self.lastMousePos = Point(ev.pos())

        QtGui.QGraphicsView.mouseMoveEvent(self, ev)
        if not self.mouseEnabled:
            return
        self.sigSceneMouseMoved.emit(self.mapToScene(ev.pos()))
            
        if self.clickAccepted:  ## Ignore event if an item in the scene has already claimed it.
            return
        
        if ev.buttons() == QtCore.Qt.RightButton:
            delta = Point(np.clip(delta[0], -50, 50), np.clip(-delta[1], -50, 50))
            scale = 1.01 ** delta
            self.scale(scale[0], scale[1], center=self.mapToScene(self.mousePressPos))
            self.sigRangeChanged.emit(self, self.range)

        elif ev.buttons() in [QtCore.Qt.MidButton, QtCore.Qt.LeftButton]:  ## Allow panning by left or mid button.
            px = self.pixelSize()
            tr = -delta * px
            
            self.translate(tr[0], tr[1])
            self.sigRangeChanged.emit(self, self.range)
        
    def pixelSize(self):
        """Return vector with the length and width of one view pixel in scene coordinates"""
        p0 = Point(0,0)
        p1 = Point(1,1)
        tr = self.transform().inverted()[0]
        p01 = tr.map(p0)
        p11 = tr.map(p1)
        return Point(p11 - p01)
        
    def dragEnterEvent(self, ev):
        ev.ignore()  ## not sure why, but for some reason this class likes to consume drag events
        

