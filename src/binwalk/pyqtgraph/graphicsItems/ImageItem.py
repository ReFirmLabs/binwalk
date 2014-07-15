from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import collections
import pyqtgraph.functions as fn
import pyqtgraph.debug as debug
from .GraphicsObject import GraphicsObject

__all__ = ['ImageItem']
class ImageItem(GraphicsObject):
    """
    **Bases:** :class:`GraphicsObject <pyqtgraph.GraphicsObject>`
    
    GraphicsObject displaying an image. Optimized for rapid update (ie video display).
    This item displays either a 2D numpy array (height, width) or
    a 3D array (height, width, RGBa). This array is optionally scaled (see 
    :func:`setLevels <pyqtgraph.ImageItem.setLevels>`) and/or colored
    with a lookup table (see :func:`setLookupTable <pyqtgraph.ImageItem.setLookupTable>`)
    before being displayed.
    
    ImageItem is frequently used in conjunction with 
    :class:`HistogramLUTItem <pyqtgraph.HistogramLUTItem>` or 
    :class:`HistogramLUTWidget <pyqtgraph.HistogramLUTWidget>` to provide a GUI
    for controlling the levels and lookup table used to display the image.
    """
    
    
    sigImageChanged = QtCore.Signal()
    sigRemoveRequested = QtCore.Signal(object)  # self; emitted when 'remove' is selected from context menu
    
    def __init__(self, image=None, **kargs):
        """
        See :func:`setImage <pyqtgraph.ImageItem.setImage>` for all allowed initialization arguments.
        """
        GraphicsObject.__init__(self)
        #self.pixmapItem = QtGui.QGraphicsPixmapItem(self)
        #self.qimage = QtGui.QImage()
        #self._pixmap = None
        self.menu = None
        self.image = None   ## original image data
        self.qimage = None  ## rendered image for display
        #self.clipMask = None
        
        self.paintMode = None
        
        self.levels = None  ## [min, max] or [[redMin, redMax], ...]
        self.lut = None
        
        #self.clipLevel = None
        self.drawKernel = None
        self.border = None
        self.removable = False
        
        if image is not None:
            self.setImage(image, **kargs)
        else:
            self.setOpts(**kargs)

    def setCompositionMode(self, mode):
        """Change the composition mode of the item (see QPainter::CompositionMode
        in the Qt documentation). This is useful when overlaying multiple ImageItems.
        
        ============================================  ============================================================
        **Most common arguments:**
        QtGui.QPainter.CompositionMode_SourceOver     Default; image replaces the background if it
                                                      is opaque. Otherwise, it uses the alpha channel to blend
                                                      the image with the background.
        QtGui.QPainter.CompositionMode_Overlay        The image color is mixed with the background color to 
                                                      reflect the lightness or darkness of the background.
        QtGui.QPainter.CompositionMode_Plus           Both the alpha and color of the image and background pixels 
                                                      are added together.
        QtGui.QPainter.CompositionMode_Multiply       The output is the image color multiplied by the background.
        ============================================  ============================================================
        """
        self.paintMode = mode
        self.update()

    ## use setOpacity instead.
    #def setAlpha(self, alpha):
        #self.setOpacity(alpha)
        #self.updateImage()
        
    def setBorder(self, b):
        self.border = fn.mkPen(b)
        self.update()
        
    def width(self):
        if self.image is None:
            return None
        return self.image.shape[0]
        
    def height(self):
        if self.image is None:
            return None
        return self.image.shape[1]

    def boundingRect(self):
        if self.image is None:
            return QtCore.QRectF(0., 0., 0., 0.)
        return QtCore.QRectF(0., 0., float(self.width()), float(self.height()))

    #def setClipLevel(self, level=None):
        #self.clipLevel = level
        #self.updateImage()
        
    #def paint(self, p, opt, widget):
        #pass
        #if self.pixmap is not None:
            #p.drawPixmap(0, 0, self.pixmap)
            #print "paint"

    def setLevels(self, levels, update=True):
        """
        Set image scaling levels. Can be one of:
        
        * [blackLevel, whiteLevel]
        * [[minRed, maxRed], [minGreen, maxGreen], [minBlue, maxBlue]]
            
        Only the first format is compatible with lookup tables. See :func:`makeARGB <pyqtgraph.makeARGB>`
        for more details on how levels are applied.
        """
        self.levels = levels
        if update:
            self.updateImage()
        
    def getLevels(self):
        return self.levels
        #return self.whiteLevel, self.blackLevel

    def setLookupTable(self, lut, update=True):
        """
        Set the lookup table (numpy array) to use for this image. (see 
        :func:`makeARGB <pyqtgraph.makeARGB>` for more information on how this is used).
        Optionally, lut can be a callable that accepts the current image as an 
        argument and returns the lookup table to use.
        
        Ordinarily, this table is supplied by a :class:`HistogramLUTItem <pyqtgraph.HistogramLUTItem>`
        or :class:`GradientEditorItem <pyqtgraph.GradientEditorItem>`.
        """
        self.lut = lut
        if update:
            self.updateImage()

    def setOpts(self, update=True, **kargs):
        if 'lut' in kargs:
            self.setLookupTable(kargs['lut'], update=update)
        if 'levels' in kargs:
            self.setLevels(kargs['levels'], update=update)
        #if 'clipLevel' in kargs:
            #self.setClipLevel(kargs['clipLevel'])
        if 'opacity' in kargs:
            self.setOpacity(kargs['opacity'])
        if 'compositionMode' in kargs:
            self.setCompositionMode(kargs['compositionMode'])
        if 'border' in kargs:
            self.setBorder(kargs['border'])
        if 'removable' in kargs:
            self.removable = kargs['removable']
            self.menu = None

    def setRect(self, rect):
        """Scale and translate the image to fit within rect (must be a QRect or QRectF)."""
        self.resetTransform()
        self.translate(rect.left(), rect.top())
        self.scale(rect.width() / self.width(), rect.height() / self.height())

    def setImage(self, image=None, autoLevels=None, **kargs):
        """
        Update the image displayed by this item. For more information on how the image
        is processed before displaying, see :func:`makeARGB <pyqtgraph.makeARGB>`
        
        =================  =========================================================================
        **Arguments:**
        image              (numpy array) Specifies the image data. May be 2D (width, height) or 
                           3D (width, height, RGBa). The array dtype must be integer or floating
                           point of any bit depth. For 3D arrays, the third dimension must
                           be of length 3 (RGB) or 4 (RGBA).
        autoLevels         (bool) If True, this forces the image to automatically select 
                           levels based on the maximum and minimum values in the data.
                           By default, this argument is true unless the levels argument is
                           given.
        lut                (numpy array) The color lookup table to use when displaying the image.
                           See :func:`setLookupTable <pyqtgraph.ImageItem.setLookupTable>`.
        levels             (min, max) The minimum and maximum values to use when rescaling the image
                           data. By default, this will be set to the minimum and maximum values 
                           in the image. If the image array has dtype uint8, no rescaling is necessary.
        opacity            (float 0.0-1.0)
        compositionMode    see :func:`setCompositionMode <pyqtgraph.ImageItem.setCompositionMode>`
        border             Sets the pen used when drawing the image border. Default is None.
        =================  =========================================================================
        """
        prof = debug.Profiler('ImageItem.setImage', disabled=True)
        
        gotNewData = False
        if image is None:
            if self.image is None:
                return
        else:
            gotNewData = True
            shapeChanged = (self.image is None or image.shape != self.image.shape)
            self.image = image.view(np.ndarray)
            if shapeChanged:
                self.prepareGeometryChange()
                self.informViewBoundsChanged()
                
        prof.mark('1')
            
        if autoLevels is None:
            if 'levels' in kargs:
                autoLevels = False
            else:
                autoLevels = True
        if autoLevels:
            img = self.image
            while img.size > 2**16:
                img = img[::2, ::2]
            mn, mx = img.min(), img.max()
            if mn == mx:
                mn = 0
                mx = 255
            kargs['levels'] = [mn,mx]
        prof.mark('2')
        
        self.setOpts(update=False, **kargs)
        prof.mark('3')
        
        self.qimage = None
        self.update()
        prof.mark('4')

        if gotNewData:
            self.sigImageChanged.emit()


        prof.finish()



    def updateImage(self, *args, **kargs):
        ## used for re-rendering qimage from self.image.
        
        ## can we make any assumptions here that speed things up?
        ## dtype, range, size are all the same?
        defaults = {
            'autoLevels': False,
        }
        defaults.update(kargs)
        return self.setImage(*args, **defaults)
        
        


    def render(self):
        prof = debug.Profiler('ImageItem.render', disabled=True)
        if self.image is None or self.image.size == 0:
            return
        if isinstance(self.lut, collections.Callable):
            lut = self.lut(self.image)
        else:
            lut = self.lut
        #print lut.shape
        #print self.lut
            
        argb, alpha = fn.makeARGB(self.image, lut=lut, levels=self.levels)
        self.qimage = fn.makeQImage(argb, alpha)
        prof.finish()
    

    def paint(self, p, *args):
        prof = debug.Profiler('ImageItem.paint', disabled=True)
        if self.image is None:
            return
        if self.qimage is None:
            self.render()
            if self.qimage is None:
                return
            prof.mark('render QImage')
        if self.paintMode is not None:
            p.setCompositionMode(self.paintMode)
            prof.mark('set comp mode')
        
        p.drawImage(QtCore.QPointF(0,0), self.qimage)
        prof.mark('p.drawImage')
        if self.border is not None:
            p.setPen(self.border)
            p.drawRect(self.boundingRect())
        prof.finish()

    def save(self, fileName, *args):
        """Save this image to file. Note that this saves the visible image (after scale/color changes), not the original data."""
        if self.qimage is None:
            self.render()
        self.qimage.save(fileName, *args)

    def getHistogram(self, bins=500, step=3):
        """Returns x and y arrays containing the histogram values for the current image.
        The step argument causes pixels to be skipped when computing the histogram to save time.
        This method is also used when automatically computing levels.
        """
        if self.image is None:
            return None,None
        stepData = self.image[::step, ::step]
        hist = np.histogram(stepData, bins=bins)
        return hist[1][:-1], hist[0]

    def setPxMode(self, b):
        """
        Set whether the item ignores transformations and draws directly to screen pixels.
        If True, the item will not inherit any scale or rotation transformations from its
        parent items, but its position will be transformed as usual.
        (see GraphicsItem::ItemIgnoresTransformations in the Qt documentation)
        """
        self.setFlag(self.ItemIgnoresTransformations, b)
    
    def setScaledMode(self):
        self.setPxMode(False)

    def getPixmap(self):
        if self.qimage is None:
            self.render()
            if self.qimage is None:
                return None
        return QtGui.QPixmap.fromImage(self.qimage)
    
    def pixelSize(self):
        """return scene-size of a single pixel in the image"""
        br = self.sceneBoundingRect()
        if self.image is None:
            return 1,1
        return br.width()/self.width(), br.height()/self.height()

    #def mousePressEvent(self, ev):
        #if self.drawKernel is not None and ev.button() == QtCore.Qt.LeftButton:
            #self.drawAt(ev.pos(), ev)
            #ev.accept()
        #else:
            #ev.ignore()
        
    #def mouseMoveEvent(self, ev):
        ##print "mouse move", ev.pos()
        #if self.drawKernel is not None:
            #self.drawAt(ev.pos(), ev)
    
    #def mouseReleaseEvent(self, ev):
        #pass

    def mouseDragEvent(self, ev):
        if ev.button() != QtCore.Qt.LeftButton:
            ev.ignore()
            return
        elif self.drawKernel is not None:
            ev.accept()
            self.drawAt(ev.pos(), ev)

    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            if self.raiseContextMenu(ev):
                ev.accept()
        if self.drawKernel is not None and ev.button() == QtCore.Qt.LeftButton:
            self.drawAt(ev.pos(), ev)

    def raiseContextMenu(self, ev):
        menu = self.getMenu()
        if menu is None:
            return False
        menu = self.scene().addParentContextMenus(self, menu, ev)
        pos = ev.screenPos()
        menu.popup(QtCore.QPoint(pos.x(), pos.y()))
        return True

    def getMenu(self):
        if self.menu is None:
            if not self.removable:
                return None
            self.menu = QtGui.QMenu()
            self.menu.setTitle("Image")
            remAct = QtGui.QAction("Remove image", self.menu)
            remAct.triggered.connect(self.removeClicked)
            self.menu.addAction(remAct)
            self.menu.remAct = remAct
        return self.menu
        
        
    def hoverEvent(self, ev):
        if not ev.isExit() and self.drawKernel is not None and ev.acceptDrags(QtCore.Qt.LeftButton):
            ev.acceptClicks(QtCore.Qt.LeftButton) ## we don't use the click, but we also don't want anyone else to use it.
            ev.acceptClicks(QtCore.Qt.RightButton)
            #self.box.setBrush(fn.mkBrush('w'))
        elif not ev.isExit() and self.removable:
            ev.acceptClicks(QtCore.Qt.RightButton)  ## accept context menu clicks
        #else:
            #self.box.setBrush(self.brush)
        #self.update()


        
    def tabletEvent(self, ev):
        print(ev.device())
        print(ev.pointerType())
        print(ev.pressure())
    
    def drawAt(self, pos, ev=None):
        pos = [int(pos.x()), int(pos.y())]
        dk = self.drawKernel
        kc = self.drawKernelCenter
        sx = [0,dk.shape[0]]
        sy = [0,dk.shape[1]]
        tx = [pos[0] - kc[0], pos[0] - kc[0]+ dk.shape[0]]
        ty = [pos[1] - kc[1], pos[1] - kc[1]+ dk.shape[1]]
        
        for i in [0,1]:
            dx1 = -min(0, tx[i])
            dx2 = min(0, self.image.shape[0]-tx[i])
            tx[i] += dx1+dx2
            sx[i] += dx1+dx2

            dy1 = -min(0, ty[i])
            dy2 = min(0, self.image.shape[1]-ty[i])
            ty[i] += dy1+dy2
            sy[i] += dy1+dy2

        ts = (slice(tx[0],tx[1]), slice(ty[0],ty[1]))
        ss = (slice(sx[0],sx[1]), slice(sy[0],sy[1]))
        mask = self.drawMask
        src = dk
        
        if isinstance(self.drawMode, collections.Callable):
            self.drawMode(dk, self.image, mask, ss, ts, ev)
        else:
            src = src[ss]
            if self.drawMode == 'set':
                if mask is not None:
                    mask = mask[ss]
                    self.image[ts] = self.image[ts] * (1-mask) + src * mask
                else:
                    self.image[ts] = src
            elif self.drawMode == 'add':
                self.image[ts] += src
            else:
                raise Exception("Unknown draw mode '%s'" % self.drawMode)
            self.updateImage()
        
    def setDrawKernel(self, kernel=None, mask=None, center=(0,0), mode='set'):
        self.drawKernel = kernel
        self.drawKernelCenter = center
        self.drawMode = mode
        self.drawMask = mask

    def removeClicked(self):
        ## Send remove event only after we have exited the menu event handler
        self.removeTimer = QtCore.QTimer()
        self.removeTimer.timeout.connect(lambda: self.sigRemoveRequested.emit(self))
        self.removeTimer.start(0)

