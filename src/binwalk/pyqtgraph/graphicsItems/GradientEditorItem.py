from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.python2_3 import sortList
import pyqtgraph.functions as fn
from .GraphicsObject import GraphicsObject
from .GraphicsWidget import GraphicsWidget
import weakref
from pyqtgraph.pgcollections import OrderedDict
from pyqtgraph.colormap import ColorMap

import numpy as np

__all__ = ['TickSliderItem', 'GradientEditorItem']


Gradients = OrderedDict([
    ('thermal', {'ticks': [(0.3333, (185, 0, 0, 255)), (0.6666, (255, 220, 0, 255)), (1, (255, 255, 255, 255)), (0, (0, 0, 0, 255))], 'mode': 'rgb'}),
    ('flame', {'ticks': [(0.2, (7, 0, 220, 255)), (0.5, (236, 0, 134, 255)), (0.8, (246, 246, 0, 255)), (1.0, (255, 255, 255, 255)), (0.0, (0, 0, 0, 255))], 'mode': 'rgb'}),
    ('yellowy', {'ticks': [(0.0, (0, 0, 0, 255)), (0.2328863796753704, (32, 0, 129, 255)), (0.8362738179251941, (255, 255, 0, 255)), (0.5257586450247, (115, 15, 255, 255)), (1.0, (255, 255, 255, 255))], 'mode': 'rgb'} ),
    ('bipolar', {'ticks': [(0.0, (0, 255, 255, 255)), (1.0, (255, 255, 0, 255)), (0.5, (0, 0, 0, 255)), (0.25, (0, 0, 255, 255)), (0.75, (255, 0, 0, 255))], 'mode': 'rgb'}),
    ('spectrum', {'ticks': [(1.0, (255, 0, 255, 255)), (0.0, (255, 0, 0, 255))], 'mode': 'hsv'}),
    ('cyclic', {'ticks': [(0.0, (255, 0, 4, 255)), (1.0, (255, 0, 0, 255))], 'mode': 'hsv'}),
    ('greyclip', {'ticks': [(0.0, (0, 0, 0, 255)), (0.99, (255, 255, 255, 255)), (1.0, (255, 0, 0, 255))], 'mode': 'rgb'}),
    ('grey', {'ticks': [(0.0, (0, 0, 0, 255)), (1.0, (255, 255, 255, 255))], 'mode': 'rgb'}),
])





class TickSliderItem(GraphicsWidget):
    ## public class
    """**Bases:** :class:`GraphicsWidget <pyqtgraph.GraphicsWidget>`
    
    A rectangular item with tick marks along its length that can (optionally) be moved by the user."""
        
    def __init__(self, orientation='bottom', allowAdd=True, **kargs):
        """
        ============= =================================================================================
        **Arguments**
        orientation   Set the orientation of the gradient. Options are: 'left', 'right'
                      'top', and 'bottom'.
        allowAdd      Specifies whether ticks can be added to the item by the user.
        tickPen       Default is white. Specifies the color of the outline of the ticks.
                      Can be any of the valid arguments for :func:`mkPen <pyqtgraph.mkPen>`
        ============= =================================================================================        
        """
        ## public
        GraphicsWidget.__init__(self)
        self.orientation = orientation
        self.length = 100
        self.tickSize = 15
        self.ticks = {}
        self.maxDim = 20
        self.allowAdd = allowAdd
        if 'tickPen' in kargs:
            self.tickPen = fn.mkPen(kargs['tickPen'])
        else:
            self.tickPen = fn.mkPen('w')
            
        self.orientations = {
            'left': (90, 1, 1), 
            'right': (90, 1, 1), 
            'top': (0, 1, -1), 
            'bottom': (0, 1, 1)
        }
        
        self.setOrientation(orientation)
        #self.setFrameStyle(QtGui.QFrame.NoFrame | QtGui.QFrame.Plain)
        #self.setBackgroundRole(QtGui.QPalette.NoRole)
        #self.setMouseTracking(True)
        
    #def boundingRect(self):
        #return self.mapRectFromParent(self.geometry()).normalized()
        
    #def shape(self):  ## No idea why this is necessary, but rotated items do not receive clicks otherwise.
        #p = QtGui.QPainterPath()
        #p.addRect(self.boundingRect())
        #return p
        
    def paint(self, p, opt, widget):
        #p.setPen(fn.mkPen('g', width=3))
        #p.drawRect(self.boundingRect())
        return
        
    def keyPressEvent(self, ev):
        ev.ignore()

    def setMaxDim(self, mx=None):
        if mx is None:
            mx = self.maxDim
        else:
            self.maxDim = mx
            
        if self.orientation in ['bottom', 'top']:
            self.setFixedHeight(mx)
            self.setMaximumWidth(16777215)
        else:
            self.setFixedWidth(mx)
            self.setMaximumHeight(16777215)
            
    
    def setOrientation(self, orientation):
        ## public
        """Set the orientation of the TickSliderItem.
        
        ============= ===================================================================
        **Arguments**
        orientation   Options are: 'left', 'right', 'top', 'bottom'
                      The orientation option specifies which side of the slider the
                      ticks are on, as well as whether the slider is vertical ('right'
                      and 'left') or horizontal ('top' and 'bottom').
        ============= ===================================================================
        """
        self.orientation = orientation
        self.setMaxDim()
        self.resetTransform()
        ort = orientation
        if ort == 'top':
            self.scale(1, -1)
            self.translate(0, -self.height())
        elif ort == 'left':
            self.rotate(270)
            self.scale(1, -1)
            self.translate(-self.height(), -self.maxDim)
        elif ort == 'right':
            self.rotate(270)
            self.translate(-self.height(), 0)
            #self.setPos(0, -self.height())
        elif ort != 'bottom':
            raise Exception("%s is not a valid orientation. Options are 'left', 'right', 'top', and 'bottom'" %str(ort))
        
        self.translate(self.tickSize/2., 0)
    
    def addTick(self, x, color=None, movable=True):
        ## public
        """
        Add a tick to the item.
        
        ============= ==================================================================
        **Arguments**
        x             Position where tick should be added.
        color         Color of added tick. If color is not specified, the color will be
                      white.
        movable       Specifies whether the tick is movable with the mouse.
        ============= ==================================================================
        """        
        
        if color is None:
            color = QtGui.QColor(255,255,255)
        tick = Tick(self, [x*self.length, 0], color, movable, self.tickSize, pen=self.tickPen)
        self.ticks[tick] = x
        tick.setParentItem(self)
        return tick
    
    def removeTick(self, tick):
        ## public
        """
        Removes the specified tick.
        """
        del self.ticks[tick]
        tick.setParentItem(None)
        if self.scene() is not None:
            self.scene().removeItem(tick)
    
    def tickMoved(self, tick, pos):
        #print "tick changed"
        ## Correct position of tick if it has left bounds.
        newX = min(max(0, pos.x()), self.length)
        pos.setX(newX)
        tick.setPos(pos)
        self.ticks[tick] = float(newX) / self.length
    
    def tickMoveFinished(self, tick):
        pass
    
    def tickClicked(self, tick, ev):
        if ev.button() == QtCore.Qt.RightButton:
            self.removeTick(tick)
    
    def widgetLength(self):
        if self.orientation in ['bottom', 'top']:
            return self.width()
        else:
            return self.height()
    
    def resizeEvent(self, ev):
        wlen = max(40, self.widgetLength())
        self.setLength(wlen-self.tickSize-2)
        self.setOrientation(self.orientation)
        #bounds = self.scene().itemsBoundingRect()
        #bounds.setLeft(min(-self.tickSize*0.5, bounds.left()))
        #bounds.setRight(max(self.length + self.tickSize, bounds.right()))
        #self.setSceneRect(bounds)
        #self.fitInView(bounds, QtCore.Qt.KeepAspectRatio)
        
    def setLength(self, newLen):
        #private
        for t, x in list(self.ticks.items()):
            t.setPos(x * newLen + 1, t.pos().y())
        self.length = float(newLen)
        
    #def mousePressEvent(self, ev):
        #QtGui.QGraphicsView.mousePressEvent(self, ev)
        #self.ignoreRelease = False
        #for i in self.items(ev.pos()):
            #if isinstance(i, Tick):
                #self.ignoreRelease = True
                #break
        ##if len(self.items(ev.pos())) > 0:  ## Let items handle their own clicks
            ##self.ignoreRelease = True
        
    #def mouseReleaseEvent(self, ev):
        #QtGui.QGraphicsView.mouseReleaseEvent(self, ev)
        #if self.ignoreRelease:
            #return
            
        #pos = self.mapToScene(ev.pos())
            
        #if ev.button() == QtCore.Qt.LeftButton and self.allowAdd:
            #if pos.x() < 0 or pos.x() > self.length:
                #return
            #if pos.y() < 0 or pos.y() > self.tickSize:
                #return
            #pos.setX(min(max(pos.x(), 0), self.length))
            #self.addTick(pos.x()/self.length)
        #elif ev.button() == QtCore.Qt.RightButton:
            #self.showMenu(ev)
            
    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton and self.allowAdd:
            pos = ev.pos()
            if pos.x() < 0 or pos.x() > self.length:
                return
            if pos.y() < 0 or pos.y() > self.tickSize:
                return
            pos.setX(min(max(pos.x(), 0), self.length))
            self.addTick(pos.x()/self.length)
        elif ev.button() == QtCore.Qt.RightButton:
            self.showMenu(ev)
        
        #if  ev.button() == QtCore.Qt.RightButton:
            #if self.moving:
                #ev.accept()
                #self.setPos(self.startPosition)
                #self.moving = False
                #self.sigMoving.emit(self)
                #self.sigMoved.emit(self)
            #else:
                #pass
                #self.view().tickClicked(self, ev)
                ###remove

    def hoverEvent(self, ev):
        if (not ev.isExit()) and ev.acceptClicks(QtCore.Qt.LeftButton):
            ev.acceptClicks(QtCore.Qt.RightButton)
            ## show ghost tick
            #self.currentPen = fn.mkPen(255, 0,0)
        #else:
            #self.currentPen = self.pen
        #self.update()
        
    def showMenu(self, ev):
        pass

    def setTickColor(self, tick, color):
        """Set the color of the specified tick.
        
        ============= ==================================================================
        **Arguments** 
        tick          Can be either an integer corresponding to the index of the tick 
                      or a Tick object. Ex: if you had a slider with 3 ticks and you 
                      wanted to change the middle tick, the index would be 1.
        color         The color to make the tick. Can be any argument that is valid for 
                      :func:`mkBrush <pyqtgraph.mkBrush>`
        ============= ==================================================================
        """
        tick = self.getTick(tick)
        tick.color = color
        tick.update()
        #tick.setBrush(QtGui.QBrush(QtGui.QColor(tick.color)))

    def setTickValue(self, tick, val):
        ## public
        """
        Set the position (along the slider) of the tick.
        
        ============= ==================================================================
        **Arguments** 
        tick          Can be either an integer corresponding to the index of the tick 
                      or a Tick object. Ex: if you had a slider with 3 ticks and you 
                      wanted to change the middle tick, the index would be 1.
        val           The desired position of the tick. If val is < 0, position will be 
                      set to 0. If val is > 1, position will be set to 1.
        ============= ==================================================================        
        """
        tick = self.getTick(tick)
        val = min(max(0.0, val), 1.0)
        x = val * self.length
        pos = tick.pos()
        pos.setX(x)
        tick.setPos(pos)
        self.ticks[tick] = val
        
    def tickValue(self, tick):
        ## public
        """Return the value (from 0.0 to 1.0) of the specified tick.
        
        ============= ==================================================================
        **Arguments** 
        tick          Can be either an integer corresponding to the index of the tick 
                      or a Tick object. Ex: if you had a slider with 3 ticks and you 
                      wanted the value of the middle tick, the index would be 1.
        ============= ==================================================================        
        """
        tick = self.getTick(tick)
        return self.ticks[tick]
        
    def getTick(self, tick):
        ## public
        """Return the Tick object at the specified index.
        
        ============= ==================================================================
        **Arguments**       
        tick          An integer corresponding to the index of the desired tick. If the 
                      argument is not an integer it will be returned unchanged.  
        ============= ==================================================================
        """
        if type(tick) is int:
            tick = self.listTicks()[tick][0]
        return tick

    #def mouseMoveEvent(self, ev):
        #QtGui.QGraphicsView.mouseMoveEvent(self, ev)

    def listTicks(self):
        """Return a sorted list of all the Tick objects on the slider."""
        ## public
        ticks = list(self.ticks.items())
        sortList(ticks, lambda a,b: cmp(a[1], b[1]))  ## see pyqtgraph.python2_3.sortList
        return ticks


class GradientEditorItem(TickSliderItem):
    """
    **Bases:** :class:`TickSliderItem <pyqtgraph.TickSliderItem>`
    
    An item that can be used to define a color gradient. Implements common pre-defined gradients that are 
    customizable by the user. :class: `GradientWidget <pyqtgraph.GradientWidget>` provides a widget
    with a GradientEditorItem that can be added to a GUI. 
    
    ================================ ===========================================================
    **Signals**
    sigGradientChanged(self)         Signal is emitted anytime the gradient changes. The signal 
                                     is emitted in real time while ticks are being dragged or 
                                     colors are being changed.
    sigGradientChangeFinished(self)  Signal is emitted when the gradient is finished changing.
    ================================ ===========================================================    
 
    """
    
    sigGradientChanged = QtCore.Signal(object)
    sigGradientChangeFinished = QtCore.Signal(object)
    
    def __init__(self, *args, **kargs):
        """
        Create a new GradientEditorItem. 
        All arguments are passed to :func:`TickSliderItem.__init__ <pyqtgraph.TickSliderItem.__init__>`
        
        ============= =================================================================================
        **Arguments**
        orientation   Set the orientation of the gradient. Options are: 'left', 'right'
                      'top', and 'bottom'.
        allowAdd      Default is True. Specifies whether ticks can be added to the item.
        tickPen       Default is white. Specifies the color of the outline of the ticks.
                      Can be any of the valid arguments for :func:`mkPen <pyqtgraph.mkPen>`
        ============= =================================================================================
        """
        self.currentTick = None
        self.currentTickColor = None
        self.rectSize = 15
        self.gradRect = QtGui.QGraphicsRectItem(QtCore.QRectF(0, self.rectSize, 100, self.rectSize))
        self.backgroundRect = QtGui.QGraphicsRectItem(QtCore.QRectF(0, -self.rectSize, 100, self.rectSize))
        self.backgroundRect.setBrush(QtGui.QBrush(QtCore.Qt.DiagCrossPattern))
        self.colorMode = 'rgb'
        
        TickSliderItem.__init__(self, *args, **kargs)
        
        self.colorDialog = QtGui.QColorDialog()
        self.colorDialog.setOption(QtGui.QColorDialog.ShowAlphaChannel, True)
        self.colorDialog.setOption(QtGui.QColorDialog.DontUseNativeDialog, True)
        
        self.colorDialog.currentColorChanged.connect(self.currentColorChanged)
        self.colorDialog.rejected.connect(self.currentColorRejected)
        self.colorDialog.accepted.connect(self.currentColorAccepted)
        
        self.backgroundRect.setParentItem(self)
        self.gradRect.setParentItem(self)
        
        self.setMaxDim(self.rectSize + self.tickSize)
        
        self.rgbAction = QtGui.QAction('RGB', self)
        self.rgbAction.setCheckable(True)
        self.rgbAction.triggered.connect(lambda: self.setColorMode('rgb'))
        self.hsvAction = QtGui.QAction('HSV', self)
        self.hsvAction.setCheckable(True)
        self.hsvAction.triggered.connect(lambda: self.setColorMode('hsv'))
            
        self.menu = QtGui.QMenu()
        
        ## build context menu of gradients
        l = self.length
        self.length = 100
        global Gradients
        for g in Gradients:
            px = QtGui.QPixmap(100, 15)
            p = QtGui.QPainter(px)
            self.restoreState(Gradients[g])
            grad = self.getGradient()
            brush = QtGui.QBrush(grad)
            p.fillRect(QtCore.QRect(0, 0, 100, 15), brush)
            p.end()
            label = QtGui.QLabel()
            label.setPixmap(px)
            label.setContentsMargins(1, 1, 1, 1)
            act = QtGui.QWidgetAction(self)
            act.setDefaultWidget(label)
            act.triggered.connect(self.contextMenuClicked)
            act.name = g
            self.menu.addAction(act)
        self.length = l
        self.menu.addSeparator()
        self.menu.addAction(self.rgbAction)
        self.menu.addAction(self.hsvAction)
        
        
        for t in list(self.ticks.keys()):
            self.removeTick(t)
        self.addTick(0, QtGui.QColor(0,0,0), True)
        self.addTick(1, QtGui.QColor(255,0,0), True)
        self.setColorMode('rgb')
        self.updateGradient()
    
    def setOrientation(self, orientation):
        ## public
        """
        Set the orientation of the GradientEditorItem. 
        
        ============= ===================================================================
        **Arguments**
        orientation   Options are: 'left', 'right', 'top', 'bottom'
                      The orientation option specifies which side of the gradient the
                      ticks are on, as well as whether the gradient is vertical ('right'
                      and 'left') or horizontal ('top' and 'bottom').
        ============= ===================================================================
        """
        TickSliderItem.setOrientation(self, orientation)
        self.translate(0, self.rectSize)
    
    def showMenu(self, ev):
        #private
        self.menu.popup(ev.screenPos().toQPoint())
    
    def contextMenuClicked(self, b=None):
        #private
        #global Gradients
        act = self.sender()
        self.loadPreset(act.name)
        
    def loadPreset(self, name):
        """
        Load a predefined gradient. 
    
        """ ## TODO: provide image with names of defined gradients
        #global Gradients
        self.restoreState(Gradients[name])
    
    def setColorMode(self, cm):
        """
        Set the color mode for the gradient. Options are: 'hsv', 'rgb'
        
        """
        
        ## public
        if cm not in ['rgb', 'hsv']:
            raise Exception("Unknown color mode %s. Options are 'rgb' and 'hsv'." % str(cm))
        
        try:
            self.rgbAction.blockSignals(True)
            self.hsvAction.blockSignals(True)
            self.rgbAction.setChecked(cm == 'rgb')
            self.hsvAction.setChecked(cm == 'hsv')
        finally:
            self.rgbAction.blockSignals(False)
            self.hsvAction.blockSignals(False)
        self.colorMode = cm
        self.updateGradient()
        
    def colorMap(self):
        """Return a ColorMap object representing the current state of the editor."""
        if self.colorMode == 'hsv':
            raise NotImplementedError('hsv colormaps not yet supported')
        pos = []
        color = []
        for t,x in self.listTicks():
            pos.append(x)
            c = t.color
            color.append([c.red(), c.green(), c.blue(), c.alpha()])
        return ColorMap(np.array(pos), np.array(color, dtype=np.ubyte))
        
    def updateGradient(self):
        #private
        self.gradient = self.getGradient()
        self.gradRect.setBrush(QtGui.QBrush(self.gradient))
        self.sigGradientChanged.emit(self)
        
    def setLength(self, newLen):
        #private (but maybe public)
        TickSliderItem.setLength(self, newLen)
        self.backgroundRect.setRect(1, -self.rectSize, newLen, self.rectSize)
        self.gradRect.setRect(1, -self.rectSize, newLen, self.rectSize)
        self.updateGradient()
        
    def currentColorChanged(self, color):
        #private
        if color.isValid() and self.currentTick is not None:
            self.setTickColor(self.currentTick, color)
            self.updateGradient()
            
    def currentColorRejected(self):
        #private
        self.setTickColor(self.currentTick, self.currentTickColor)
        self.updateGradient()
        
    def currentColorAccepted(self):
        self.sigGradientChangeFinished.emit(self)
        
    def tickClicked(self, tick, ev):
        #private
        if ev.button() == QtCore.Qt.LeftButton:
            if not tick.colorChangeAllowed:
                return
            self.currentTick = tick
            self.currentTickColor = tick.color
            self.colorDialog.setCurrentColor(tick.color)
            self.colorDialog.open()
            #color = QtGui.QColorDialog.getColor(tick.color, self, "Select Color", QtGui.QColorDialog.ShowAlphaChannel)
            #if color.isValid():
                #self.setTickColor(tick, color)
                #self.updateGradient()
        elif ev.button() == QtCore.Qt.RightButton:
            if not tick.removeAllowed:
                return
            if len(self.ticks) > 2:
                self.removeTick(tick)
                self.updateGradient()
                
    def tickMoved(self, tick, pos):
        #private
        TickSliderItem.tickMoved(self, tick, pos)
        self.updateGradient()

    def tickMoveFinished(self, tick):
        self.sigGradientChangeFinished.emit(self)
    

    def getGradient(self):
        """Return a QLinearGradient object."""
        g = QtGui.QLinearGradient(QtCore.QPointF(0,0), QtCore.QPointF(self.length,0))
        if self.colorMode == 'rgb':
            ticks = self.listTicks()
            g.setStops([(x, QtGui.QColor(t.color)) for t,x in ticks])
        elif self.colorMode == 'hsv':  ## HSV mode is approximated for display by interpolating 10 points between each stop
            ticks = self.listTicks()
            stops = []
            stops.append((ticks[0][1], ticks[0][0].color))
            for i in range(1,len(ticks)):
                x1 = ticks[i-1][1]
                x2 = ticks[i][1]
                dx = (x2-x1) / 10.
                for j in range(1,10):
                    x = x1 + dx*j
                    stops.append((x, self.getColor(x)))
                stops.append((x2, self.getColor(x2)))
            g.setStops(stops)
        return g
        
    def getColor(self, x, toQColor=True):
        """
        Return a color for a given value.
        
        ============= ==================================================================
        **Arguments** 
        x             Value (position on gradient) of requested color.
        toQColor      If true, returns a QColor object, else returns a (r,g,b,a) tuple.
        ============= ==================================================================
        """
        ticks = self.listTicks()
        if x <= ticks[0][1]:
            c = ticks[0][0].color
            if toQColor:
                return QtGui.QColor(c)  # always copy colors before handing them out
            else:
                return (c.red(), c.green(), c.blue(), c.alpha())
        if x >= ticks[-1][1]:
            c = ticks[-1][0].color
            if toQColor:
                return QtGui.QColor(c)  # always copy colors before handing them out
            else:
                return (c.red(), c.green(), c.blue(), c.alpha())
            
        x2 = ticks[0][1]
        for i in range(1,len(ticks)):
            x1 = x2
            x2 = ticks[i][1]
            if x1 <= x and x2 >= x:
                break
                
        dx = (x2-x1)
        if dx == 0:
            f = 0.
        else:
            f = (x-x1) / dx
        c1 = ticks[i-1][0].color
        c2 = ticks[i][0].color
        if self.colorMode == 'rgb':
            r = c1.red() * (1.-f) + c2.red() * f
            g = c1.green() * (1.-f) + c2.green() * f
            b = c1.blue() * (1.-f) + c2.blue() * f
            a = c1.alpha() * (1.-f) + c2.alpha() * f
            if toQColor:
                return QtGui.QColor(int(r), int(g), int(b), int(a))
            else:
                return (r,g,b,a)
        elif self.colorMode == 'hsv':
            h1,s1,v1,_ = c1.getHsv()
            h2,s2,v2,_ = c2.getHsv()
            h = h1 * (1.-f) + h2 * f
            s = s1 * (1.-f) + s2 * f
            v = v1 * (1.-f) + v2 * f
            c = QtGui.QColor()
            c.setHsv(h,s,v)
            if toQColor:
                return c
            else:
                return (c.red(), c.green(), c.blue(), c.alpha())
                    
    def getLookupTable(self, nPts, alpha=None):
        """
        Return an RGB(A) lookup table (ndarray). 
        
        ============= ============================================================================
        **Arguments**
        nPts           The number of points in the returned lookup table.
        alpha          True, False, or None - Specifies whether or not alpha values are included 
                       in the table.If alpha is None, alpha will be automatically determined.
        ============= ============================================================================
        """
        if alpha is None:
            alpha = self.usesAlpha()
        if alpha:
            table = np.empty((nPts,4), dtype=np.ubyte)
        else:
            table = np.empty((nPts,3), dtype=np.ubyte)
            
        for i in range(nPts):
            x = float(i)/(nPts-1)
            color = self.getColor(x, toQColor=False)
            table[i] = color[:table.shape[1]]
            
        return table
    
    def usesAlpha(self):
        """Return True if any ticks have an alpha < 255"""
        
        ticks = self.listTicks()
        for t in ticks:
            if t[0].color.alpha() < 255:
                return True
            
        return False
            
    def isLookupTrivial(self):
        """Return True if the gradient has exactly two stops in it: black at 0.0 and white at 1.0"""
        ticks = self.listTicks()
        if len(ticks) != 2:
            return False
        if ticks[0][1] != 0.0 or ticks[1][1] != 1.0:
            return False
        c1 = fn.colorTuple(ticks[0][0].color)
        c2 = fn.colorTuple(ticks[1][0].color)
        if c1 != (0,0,0,255) or c2 != (255,255,255,255):
            return False
        return True


    def mouseReleaseEvent(self, ev):
        #private
        TickSliderItem.mouseReleaseEvent(self, ev)
        self.updateGradient()
        
    def addTick(self, x, color=None, movable=True, finish=True):
        """
        Add a tick to the gradient. Return the tick.
        
        ============= ==================================================================
        **Arguments**
        x             Position where tick should be added.
        color         Color of added tick. If color is not specified, the color will be
                      the color of the gradient at the specified position.
        movable       Specifies whether the tick is movable with the mouse.
        ============= ==================================================================
        """
        
        
        if color is None:
            color = self.getColor(x)
        t = TickSliderItem.addTick(self, x, color=color, movable=movable)
        t.colorChangeAllowed = True
        t.removeAllowed = True
        
        if finish:
            self.sigGradientChangeFinished.emit(self)
        return t


    def removeTick(self, tick, finish=True):
        TickSliderItem.removeTick(self, tick)
        if finish:
            self.sigGradientChangeFinished.emit(self)
        
        
    def saveState(self):
        """
        Return a dictionary with parameters for rebuilding the gradient. Keys will include:
        
           - 'mode': hsv or rgb
           - 'ticks': a list of tuples (pos, (r,g,b,a))
        """
        ## public
        ticks = []
        for t in self.ticks:
            c = t.color
            ticks.append((self.ticks[t], (c.red(), c.green(), c.blue(), c.alpha())))
        state = {'mode': self.colorMode, 'ticks': ticks}
        return state
        
    def restoreState(self, state):
        """
        Restore the gradient specified in state.
        
        ============= ====================================================================
        **Arguments**
        state         A dictionary with same structure as those returned by 
                      :func:`saveState <pyqtgraph.GradientEditorItem.saveState>`
                      
                      Keys must include:
                      
                         - 'mode': hsv or rgb
                         - 'ticks': a list of tuples (pos, (r,g,b,a))
        ============= ====================================================================
        """
        ## public
        self.setColorMode(state['mode'])
        for t in list(self.ticks.keys()):
            self.removeTick(t, finish=False)
        for t in state['ticks']:
            c = QtGui.QColor(*t[1])
            self.addTick(t[0], c, finish=False)
        self.updateGradient()
        self.sigGradientChangeFinished.emit(self)
        
    def setColorMap(self, cm):
        self.setColorMode('rgb')
        for t in list(self.ticks.keys()):
            self.removeTick(t, finish=False)
        colors = cm.getColors(mode='qcolor')
        for i in range(len(cm.pos)):
            x = cm.pos[i]
            c = colors[i]
            self.addTick(x, c, finish=False)
        self.updateGradient()
        self.sigGradientChangeFinished.emit(self)

        
class Tick(QtGui.QGraphicsObject):  ## NOTE: Making this a subclass of GraphicsObject instead results in 
                                    ## activating this bug: https://bugreports.qt-project.org/browse/PYSIDE-86
    ## private class
    
    sigMoving = QtCore.Signal(object)
    sigMoved = QtCore.Signal(object)
    
    def __init__(self, view, pos, color, movable=True, scale=10, pen='w'):
        self.movable = movable
        self.moving = False
        self.view = weakref.ref(view)
        self.scale = scale
        self.color = color
        self.pen = fn.mkPen(pen)
        self.hoverPen = fn.mkPen(255,255,0)
        self.currentPen = self.pen
        self.pg = QtGui.QPainterPath(QtCore.QPointF(0,0))
        self.pg.lineTo(QtCore.QPointF(-scale/3**0.5, scale))
        self.pg.lineTo(QtCore.QPointF(scale/3**0.5, scale))
        self.pg.closeSubpath()
        
        QtGui.QGraphicsObject.__init__(self)
        self.setPos(pos[0], pos[1])
        if self.movable:
            self.setZValue(1)
        else:
            self.setZValue(0)

    def boundingRect(self):
        return self.pg.boundingRect()
    
    def shape(self):
        return self.pg

    def paint(self, p, *args):
        p.setRenderHints(QtGui.QPainter.Antialiasing)
        p.fillPath(self.pg, fn.mkBrush(self.color))
        
        p.setPen(self.currentPen)
        p.drawPath(self.pg)


    def mouseDragEvent(self, ev):
        if self.movable and ev.button() == QtCore.Qt.LeftButton:
            if ev.isStart():
                self.moving = True
                self.cursorOffset = self.pos() - self.mapToParent(ev.buttonDownPos())
                self.startPosition = self.pos()
            ev.accept()
            
            if not self.moving:
                return
                
            newPos = self.cursorOffset + self.mapToParent(ev.pos())
            newPos.setY(self.pos().y())
            
            self.setPos(newPos)
            self.view().tickMoved(self, newPos)
            self.sigMoving.emit(self)
            if ev.isFinish():
                self.moving = False
                self.sigMoved.emit(self)
                self.view().tickMoveFinished(self)

    def mouseClickEvent(self, ev):
        if  ev.button() == QtCore.Qt.RightButton and self.moving:
            ev.accept()
            self.setPos(self.startPosition)
            self.view().tickMoved(self, self.startPosition)
            self.moving = False
            self.sigMoving.emit(self)
            self.sigMoved.emit(self)
        else:
            self.view().tickClicked(self, ev)
            ##remove

    def hoverEvent(self, ev):
        if (not ev.isExit()) and ev.acceptDrags(QtCore.Qt.LeftButton):
            ev.acceptClicks(QtCore.Qt.LeftButton)
            ev.acceptClicks(QtCore.Qt.RightButton)
            self.currentPen = self.hoverPen
        else:
            self.currentPen = self.pen
        self.update()
        
    #def mouseMoveEvent(self, ev):
        ##print self, "move", ev.scenePos()
        #if not self.movable:
            #return
        #if not ev.buttons() & QtCore.Qt.LeftButton:
            #return
            
            
        #newPos = ev.scenePos() + self.mouseOffset
        #newPos.setY(self.pos().y())
        ##newPos.setX(min(max(newPos.x(), 0), 100))
        #self.setPos(newPos)
        #self.view().tickMoved(self, newPos)
        #self.movedSincePress = True
        ##self.emit(QtCore.SIGNAL('tickChanged'), self)
        #ev.accept()

    #def mousePressEvent(self, ev):
        #self.movedSincePress = False
        #if ev.button() == QtCore.Qt.LeftButton:
            #ev.accept()
            #self.mouseOffset = self.pos() - ev.scenePos()
            #self.pressPos = ev.scenePos()
        #elif ev.button() == QtCore.Qt.RightButton:
            #ev.accept()
            ##if self.endTick:
                ##return
            ##self.view.tickChanged(self, delete=True)
            
    #def mouseReleaseEvent(self, ev):
        ##print self, "release", ev.scenePos()
        #if not self.movedSincePress:
            #self.view().tickClicked(self, ev)
        
        ##if ev.button() == QtCore.Qt.LeftButton and ev.scenePos() == self.pressPos:
            ##color = QtGui.QColorDialog.getColor(self.color, None, "Select Color", QtGui.QColorDialog.ShowAlphaChannel)
            ##if color.isValid():
                ##self.color = color
                ##self.setBrush(QtGui.QBrush(QtGui.QColor(self.color)))
                ###self.emit(QtCore.SIGNAL('tickChanged'), self)
                ##self.view.tickChanged(self)
