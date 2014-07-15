from pyqtgraph.Qt import QtGui, QtCore
try:
    from pyqtgraph.Qt import QtOpenGL
    HAVE_OPENGL = True
except:
    HAVE_OPENGL = False
    
import numpy as np
from .GraphicsObject import GraphicsObject
import pyqtgraph.functions as fn
from pyqtgraph import debug
from pyqtgraph.Point import Point
import pyqtgraph as pg
import struct, sys

__all__ = ['PlotCurveItem']
class PlotCurveItem(GraphicsObject):
    
    
    """
    Class representing a single plot curve. Instances of this class are created
    automatically as part of PlotDataItem; these rarely need to be instantiated
    directly.
    
    Features:
    
    - Fast data update
    - Fill under curve
    - Mouse interaction
    
    ====================  ===============================================
    **Signals:**
    sigPlotChanged(self)  Emitted when the data being plotted has changed
    sigClicked(self)      Emitted when the curve is clicked
    ====================  ===============================================
    """
    
    sigPlotChanged = QtCore.Signal(object)
    sigClicked = QtCore.Signal(object)
    
    def __init__(self, *args, **kargs):
        """
        Forwards all arguments to :func:`setData <pyqtgraph.PlotCurveItem.setData>`.
        
        Some extra arguments are accepted as well:
        
        ==============  =======================================================
        **Arguments:**
        parent          The parent GraphicsObject (optional)
        clickable       If True, the item will emit sigClicked when it is 
                        clicked on. Defaults to False.
        ==============  =======================================================
        """
        GraphicsObject.__init__(self, kargs.get('parent', None))
        self.clear()
        self.path = None
        self.fillPath = None
        self._boundsCache = [None, None]
            
        ## this is disastrous for performance.
        #self.setCacheMode(QtGui.QGraphicsItem.DeviceCoordinateCache)
        
        self.metaData = {}
        self.opts = {
            'pen': fn.mkPen('w'),
            'shadowPen': None,
            'fillLevel': None,
            'brush': None,
            'stepMode': False,
            'name': None,
            'antialias': pg.getConfigOption('antialias'),\
            'connect': 'all',
        }
        self.setClickable(kargs.get('clickable', False))
        self.setData(*args, **kargs)
        
    def implements(self, interface=None):
        ints = ['plotData']
        if interface is None:
            return ints
        return interface in ints
    
    def setClickable(self, s):
        """Sets whether the item responds to mouse clicks."""
        self.clickable = s
        
        
    def getData(self):
        return self.xData, self.yData
        
    def dataBounds(self, ax, frac=1.0, orthoRange=None):
        ## Need this to run as fast as possible.
        ## check cache first:
        cache = self._boundsCache[ax]
        if cache is not None and cache[0] == (frac, orthoRange):
            return cache[1]
        
        (x, y) = self.getData()
        if x is None or len(x) == 0:
            return (None, None)
            
        if ax == 0:
            d = x
            d2 = y
        elif ax == 1:
            d = y
            d2 = x

        ## If an orthogonal range is specified, mask the data now
        if orthoRange is not None:
            mask = (d2 >= orthoRange[0]) * (d2 <= orthoRange[1])
            d = d[mask]
            #d2 = d2[mask]
            
        if len(d) == 0:
            return (None, None)

        ## Get min/max (or percentiles) of the requested data range
        if frac >= 1.0:
            b = (np.nanmin(d), np.nanmax(d))
        elif frac <= 0.0:
            raise Exception("Value for parameter 'frac' must be > 0. (got %s)" % str(frac))
        else:
            mask = np.isfinite(d)
            d = d[mask]
            b = np.percentile(d, [50 * (1 - frac), 50 * (1 + frac)])

        ## adjust for fill level
        if ax == 1 and self.opts['fillLevel'] is not None:
            b = (min(b[0], self.opts['fillLevel']), max(b[1], self.opts['fillLevel']))
            
        ## Add pen width only if it is non-cosmetic.
        pen = self.opts['pen']
        spen = self.opts['shadowPen']
        if not pen.isCosmetic():
            b = (b[0] - pen.widthF()*0.7072, b[1] + pen.widthF()*0.7072)
        if spen is not None and not spen.isCosmetic() and spen.style() != QtCore.Qt.NoPen:
            b = (b[0] - spen.widthF()*0.7072, b[1] + spen.widthF()*0.7072)
            
        self._boundsCache[ax] = [(frac, orthoRange), b]
        return b
            
    def pixelPadding(self):
        pen = self.opts['pen']
        spen = self.opts['shadowPen']
        w = 0
        if pen.isCosmetic():
            w += pen.widthF()*0.7072
        if spen is not None and spen.isCosmetic() and spen.style() != QtCore.Qt.NoPen:
            w = max(w, spen.widthF()*0.7072)
        return w

    def boundingRect(self):
        if self._boundingRect is None:
            (xmn, xmx) = self.dataBounds(ax=0)
            (ymn, ymx) = self.dataBounds(ax=1)
            if xmn is None:
                return QtCore.QRectF()
            
            px = py = 0.0
            pxPad = self.pixelPadding()
            if pxPad > 0:
                # determine length of pixel in local x, y directions    
                px, py = self.pixelVectors()
                px = 0 if px is None else px.length()
                py = 0 if py is None else py.length()
                
                # return bounds expanded by pixel size
                px *= pxPad
                py *= pxPad
            #px += self._maxSpotWidth * 0.5
            #py += self._maxSpotWidth * 0.5
            self._boundingRect = QtCore.QRectF(xmn-px, ymn-py, (2*px)+xmx-xmn, (2*py)+ymx-ymn)
        return self._boundingRect
    
    def viewTransformChanged(self):
        self.invalidateBounds()
        self.prepareGeometryChange()
        
    #def boundingRect(self):
        #if self._boundingRect is None:
            #(x, y) = self.getData()
            #if x is None or y is None or len(x) == 0 or len(y) == 0:
                #return QtCore.QRectF()
                
                
            #if self.opts['shadowPen'] is not None:
                #lineWidth = (max(self.opts['pen'].width(), self.opts['shadowPen'].width()) + 1)
            #else:
                #lineWidth = (self.opts['pen'].width()+1)
                
            
            #pixels = self.pixelVectors()
            #if pixels == (None, None):
                #pixels = [Point(0,0), Point(0,0)]
                
            #xmin = x.min()
            #xmax = x.max()
            #ymin = y.min()
            #ymax = y.max()
            
            #if self.opts['fillLevel'] is not None:
                #ymin = min(ymin, self.opts['fillLevel'])
                #ymax = max(ymax, self.opts['fillLevel'])
                
            #xmin -= pixels[0].x() * lineWidth
            #xmax += pixels[0].x() * lineWidth
            #ymin -= abs(pixels[1].y()) * lineWidth
            #ymax += abs(pixels[1].y()) * lineWidth
            
            #self._boundingRect = QtCore.QRectF(xmin, ymin, xmax-xmin, ymax-ymin)
        #return self._boundingRect

        
    def invalidateBounds(self):
        self._boundingRect = None
        self._boundsCache = [None, None]
            
    def setPen(self, *args, **kargs):
        """Set the pen used to draw the curve."""
        self.opts['pen'] = fn.mkPen(*args, **kargs)
        self.invalidateBounds()
        self.update()
        
    def setShadowPen(self, *args, **kargs):
        """Set the shadow pen used to draw behind tyhe primary pen.
        This pen must have a larger width than the primary 
        pen to be visible.
        """
        self.opts['shadowPen'] = fn.mkPen(*args, **kargs)
        self.invalidateBounds()
        self.update()

    def setBrush(self, *args, **kargs):
        """Set the brush used when filling the area under the curve"""
        self.opts['brush'] = fn.mkBrush(*args, **kargs)
        self.invalidateBounds()
        self.update()
        
    def setFillLevel(self, level):
        """Set the level filled to when filling under the curve"""
        self.opts['fillLevel'] = level
        self.fillPath = None
        self.invalidateBounds()
        self.update()

    def setData(self, *args, **kargs):
        """
        ==============  ========================================================
        **Arguments:**
        x, y            (numpy arrays) Data to show 
        pen             Pen to use when drawing. Any single argument accepted by
                        :func:`mkPen <pyqtgraph.mkPen>` is allowed.
        shadowPen       Pen for drawing behind the primary pen. Usually this
                        is used to emphasize the curve by providing a 
                        high-contrast border. Any single argument accepted by
                        :func:`mkPen <pyqtgraph.mkPen>` is allowed.
        fillLevel       (float or None) Fill the area 'under' the curve to
                        *fillLevel*
        brush           QBrush to use when filling. Any single argument accepted
                        by :func:`mkBrush <pyqtgraph.mkBrush>` is allowed.
        antialias       (bool) Whether to use antialiasing when drawing. This
                        is disabled by default because it decreases performance.
        stepMode        If True, two orthogonal lines are drawn for each sample
                        as steps. This is commonly used when drawing histograms.
                        Note that in this case, len(x) == len(y) + 1
        connect         Argument specifying how vertexes should be connected
                        by line segments. Default is "all", indicating full
                        connection. "pairs" causes only even-numbered segments
                        to be drawn. "finite" causes segments to be omitted if
                        they are attached to nan or inf values. For any other
                        connectivity, specify an array of boolean values.
        ==============  ========================================================
        
        If non-keyword arguments are used, they will be interpreted as
        setData(y) for a single argument and setData(x, y) for two
        arguments.
        
        
        """
        self.updateData(*args, **kargs)
        
    def updateData(self, *args, **kargs):
        prof = debug.Profiler('PlotCurveItem.updateData', disabled=True)

        if len(args) == 1:
            kargs['y'] = args[0]
        elif len(args) == 2:
            kargs['x'] = args[0]
            kargs['y'] = args[1]
        
        if 'y' not in kargs or kargs['y'] is None:
            kargs['y'] = np.array([])
        if 'x' not in kargs or kargs['x'] is None:
            kargs['x'] = np.arange(len(kargs['y']))
            
        for k in ['x', 'y']:
            data = kargs[k]
            if isinstance(data, list):
                data = np.array(data)
                kargs[k] = data
            if not isinstance(data, np.ndarray) or data.ndim > 1:
                raise Exception("Plot data must be 1D ndarray.")
            if 'complex' in str(data.dtype):
                raise Exception("Can not plot complex data types.")
            
        prof.mark("data checks")
        
        #self.setCacheMode(QtGui.QGraphicsItem.NoCache)  ## Disabling and re-enabling the cache works around a bug in Qt 4.6 causing the cached results to display incorrectly
                                                        ##    Test this bug with test_PlotWidget and zoom in on the animated plot
        self.invalidateBounds()
        self.prepareGeometryChange()
        self.informViewBoundsChanged()
        self.yData = kargs['y'].view(np.ndarray)
        self.xData = kargs['x'].view(np.ndarray)
        
        prof.mark('copy')
        
        if 'stepMode' in kargs:
            self.opts['stepMode'] = kargs['stepMode']
        
        if self.opts['stepMode'] is True:
            if len(self.xData) != len(self.yData)+1:  ## allow difference of 1 for step mode plots
                raise Exception("len(X) must be len(Y)+1 since stepMode=True (got %s and %s)" % (self.xData.shape, self.yData.shape))
        else:
            if self.xData.shape != self.yData.shape:  ## allow difference of 1 for step mode plots
                raise Exception("X and Y arrays must be the same shape--got %s and %s." % (self.xData.shape, self.yData.shape))
        
        self.path = None
        self.fillPath = None
        #self.xDisp = self.yDisp = None
        
        if 'name' in kargs:
            self.opts['name'] = kargs['name']
        if 'connect' in kargs:
            self.opts['connect'] = kargs['connect']
        if 'pen' in kargs:
            self.setPen(kargs['pen'])
        if 'shadowPen' in kargs:
            self.setShadowPen(kargs['shadowPen'])
        if 'fillLevel' in kargs:
            self.setFillLevel(kargs['fillLevel'])
        if 'brush' in kargs:
            self.setBrush(kargs['brush'])
        if 'antialias' in kargs:
            self.opts['antialias'] = kargs['antialias']
        
        
        prof.mark('set')
        self.update()
        prof.mark('update')
        self.sigPlotChanged.emit(self)
        prof.mark('emit')
        prof.finish()
        
    def generatePath(self, x, y):
        if self.opts['stepMode']:
            ## each value in the x/y arrays generates 2 points.
            x2 = np.empty((len(x),2), dtype=x.dtype)
            x2[:] = x[:,np.newaxis]
            if self.opts['fillLevel'] is None:
                x = x2.reshape(x2.size)[1:-1]
                y2 = np.empty((len(y),2), dtype=y.dtype)
                y2[:] = y[:,np.newaxis]
                y = y2.reshape(y2.size)
            else:
                ## If we have a fill level, add two extra points at either end
                x = x2.reshape(x2.size)
                y2 = np.empty((len(y)+2,2), dtype=y.dtype)
                y2[1:-1] = y[:,np.newaxis]
                y = y2.reshape(y2.size)[1:-1]
                y[0] = self.opts['fillLevel']
                y[-1] = self.opts['fillLevel']
        
        path = fn.arrayToQPath(x, y, connect=self.opts['connect'])
        
        return path


    def shape(self):
        if self.path is None:
            try:
                self.path = self.generatePath(*self.getData())
            except:
                return QtGui.QPainterPath()
        return self.path

    @pg.debug.warnOnException  ## raising an exception here causes crash
    def paint(self, p, opt, widget):
        prof = debug.Profiler('PlotCurveItem.paint '+str(id(self)), disabled=True)
        if self.xData is None:
            return
        
        if HAVE_OPENGL and pg.getConfigOption('enableExperimental') and isinstance(widget, QtOpenGL.QGLWidget):
            self.paintGL(p, opt, widget)
            return
        
        x = None
        y = None
        if self.path is None:
            x,y = self.getData()
            if x is None or len(x) == 0 or y is None or len(y) == 0:
                return
            self.path = self.generatePath(x,y)
            self.fillPath = None
            
        path = self.path
        prof.mark('generate path')
        
        if self._exportOpts is not False:
            aa = self._exportOpts.get('antialias', True)
        else:
            aa = self.opts['antialias']
        
        p.setRenderHint(p.Antialiasing, aa)
        
            
        if self.opts['brush'] is not None and self.opts['fillLevel'] is not None:
            if self.fillPath is None:
                if x is None:
                    x,y = self.getData()
                p2 = QtGui.QPainterPath(self.path)
                p2.lineTo(x[-1], self.opts['fillLevel'])
                p2.lineTo(x[0], self.opts['fillLevel'])
                p2.lineTo(x[0], y[0])
                p2.closeSubpath()
                self.fillPath = p2
                
            prof.mark('generate fill path')
            p.fillPath(self.fillPath, self.opts['brush'])
            prof.mark('draw fill path')
            
        sp = fn.mkPen(self.opts['shadowPen'])
        cp = fn.mkPen(self.opts['pen'])
 
        ## Copy pens and apply alpha adjustment
        #sp = QtGui.QPen(self.opts['shadowPen'])
        #cp = QtGui.QPen(self.opts['pen'])
        #for pen in [sp, cp]:
            #if pen is None:
                #continue
            #c = pen.color()
            #c.setAlpha(c.alpha() * self.opts['alphaHint'])
            #pen.setColor(c)
            ##pen.setCosmetic(True)
            
            
            
        if sp is not None and sp.style() != QtCore.Qt.NoPen:
            p.setPen(sp)
            p.drawPath(path)
        p.setPen(cp)
        p.drawPath(path)
        prof.mark('drawPath')
        
        #print "Render hints:", int(p.renderHints())
        prof.finish()
        #p.setPen(QtGui.QPen(QtGui.QColor(255,0,0)))
        #p.drawRect(self.boundingRect())
        
    def paintGL(self, p, opt, widget):
        p.beginNativePainting()
        import OpenGL.GL as gl
        
        ## set clipping viewport
        view = self.getViewBox()
        if view is not None:
            rect = view.mapRectToItem(self, view.boundingRect())
            #gl.glViewport(int(rect.x()), int(rect.y()), int(rect.width()), int(rect.height()))
            
            #gl.glTranslate(-rect.x(), -rect.y(), 0)
            
            gl.glEnable(gl.GL_STENCIL_TEST)
            gl.glColorMask(gl.GL_FALSE, gl.GL_FALSE, gl.GL_FALSE, gl.GL_FALSE) # disable drawing to frame buffer
            gl.glDepthMask(gl.GL_FALSE)  # disable drawing to depth buffer
            gl.glStencilFunc(gl.GL_NEVER, 1, 0xFF)  
            gl.glStencilOp(gl.GL_REPLACE, gl.GL_KEEP, gl.GL_KEEP)  
            
            ## draw stencil pattern
            gl.glStencilMask(0xFF);
            gl.glClear(gl.GL_STENCIL_BUFFER_BIT)
            gl.glBegin(gl.GL_TRIANGLES)
            gl.glVertex2f(rect.x(), rect.y())
            gl.glVertex2f(rect.x()+rect.width(), rect.y())
            gl.glVertex2f(rect.x(), rect.y()+rect.height())
            gl.glVertex2f(rect.x()+rect.width(), rect.y()+rect.height())
            gl.glVertex2f(rect.x()+rect.width(), rect.y())
            gl.glVertex2f(rect.x(), rect.y()+rect.height())
            gl.glEnd()
                       
            gl.glColorMask(gl.GL_TRUE, gl.GL_TRUE, gl.GL_TRUE, gl.GL_TRUE)
            gl.glDepthMask(gl.GL_TRUE)
            gl.glStencilMask(0x00)
            gl.glStencilFunc(gl.GL_EQUAL, 1, 0xFF)
            
        try:
            x, y = self.getData()
            pos = np.empty((len(x), 2))
            pos[:,0] = x
            pos[:,1] = y
            gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
            try:
                gl.glVertexPointerf(pos)
                pen = fn.mkPen(self.opts['pen'])
                color = pen.color()
                gl.glColor4f(color.red()/255., color.green()/255., color.blue()/255., color.alpha()/255.)
                width = pen.width()
                if pen.isCosmetic() and width < 1:
                    width = 1
                gl.glPointSize(width)
                gl.glEnable(gl.GL_LINE_SMOOTH)
                gl.glEnable(gl.GL_BLEND)
                gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
                gl.glHint(gl.GL_LINE_SMOOTH_HINT, gl.GL_NICEST);
                gl.glDrawArrays(gl.GL_LINE_STRIP, 0, pos.size / pos.shape[-1])
            finally:
                gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        finally:
            p.endNativePainting()
        
    def clear(self):
        self.xData = None  ## raw values
        self.yData = None
        self.xDisp = None  ## display values (after log / fft)
        self.yDisp = None
        self.path = None
        #del self.xData, self.yData, self.xDisp, self.yDisp, self.path
        
    def mouseClickEvent(self, ev):
        if not self.clickable or ev.button() != QtCore.Qt.LeftButton:
            return
        ev.accept()
        self.sigClicked.emit(self)


class ROIPlotItem(PlotCurveItem):
    """Plot curve that monitors an ROI and image for changes to automatically replot."""
    def __init__(self, roi, data, img, axes=(0,1), xVals=None, color=None):
        self.roi = roi
        self.roiData = data
        self.roiImg = img
        self.axes = axes
        self.xVals = xVals
        PlotCurveItem.__init__(self, self.getRoiData(), x=self.xVals, color=color)
        #roi.connect(roi, QtCore.SIGNAL('regionChanged'), self.roiChangedEvent)
        roi.sigRegionChanged.connect(self.roiChangedEvent)
        #self.roiChangedEvent()
        
    def getRoiData(self):
        d = self.roi.getArrayRegion(self.roiData, self.roiImg, axes=self.axes)
        if d is None:
            return
        while d.ndim > 1:
            d = d.mean(axis=1)
        return d
        
    def roiChangedEvent(self):
        d = self.getRoiData()
        self.updateData(d, self.xVals)

