from pyqtgraph.Qt import QtGui, QtCore
from .UIGraphicsItem import UIGraphicsItem
from .InfiniteLine import InfiniteLine
import pyqtgraph.functions as fn
import pyqtgraph.debug as debug

__all__ = ['LinearRegionItem']

class LinearRegionItem(UIGraphicsItem):
    """
    **Bases:** :class:`UIGraphicsItem <pyqtgraph.UIGraphicsItem>`
    
    Used for marking a horizontal or vertical region in plots.
    The region can be dragged and is bounded by lines which can be dragged individually.
    
    ===============================  =============================================================================
    **Signals:**
    sigRegionChangeFinished(self)    Emitted when the user has finished dragging the region (or one of its lines)
                                     and when the region is changed programatically.
    sigRegionChanged(self)           Emitted while the user is dragging the region (or one of its lines)
                                     and when the region is changed programatically.
    ===============================  =============================================================================
    """
    
    sigRegionChangeFinished = QtCore.Signal(object)
    sigRegionChanged = QtCore.Signal(object)
    Vertical = 0
    Horizontal = 1
    
    def __init__(self, values=[0,1], orientation=None, brush=None, movable=True, bounds=None):
        """Create a new LinearRegionItem.
        
        ============= =====================================================================
        **Arguments**
        values        A list of the positions of the lines in the region. These are not 
                      limits; limits can be set by specifying bounds.
        orientation   Options are LinearRegionItem.Vertical or LinearRegionItem.Horizontal.
                      If not specified it will be vertical.
        brush         Defines the brush that fills the region. Can be any arguments that 
                      are valid for :func:`mkBrush <pyqtgraph.mkBrush>`. Default is 
                      transparent blue.
        movable       If True, the region and individual lines are movable by the user; if 
                      False, they are static.
        bounds        Optional [min, max] bounding values for the region
        ============= =====================================================================
        """
        
        UIGraphicsItem.__init__(self)
        if orientation is None:
            orientation = LinearRegionItem.Vertical
        self.orientation = orientation
        self.bounds = QtCore.QRectF()
        self.blockLineSignal = False
        self.moving = False
        self.mouseHovering = False
        
        if orientation == LinearRegionItem.Horizontal:
            self.lines = [
                InfiniteLine(QtCore.QPointF(0, values[0]), 0, movable=movable, bounds=bounds), 
                InfiniteLine(QtCore.QPointF(0, values[1]), 0, movable=movable, bounds=bounds)]
        elif orientation == LinearRegionItem.Vertical:
            self.lines = [
                InfiniteLine(QtCore.QPointF(values[1], 0), 90, movable=movable, bounds=bounds), 
                InfiniteLine(QtCore.QPointF(values[0], 0), 90, movable=movable, bounds=bounds)]
        else:
            raise Exception('Orientation must be one of LinearRegionItem.Vertical or LinearRegionItem.Horizontal')
        
        
        for l in self.lines:
            l.setParentItem(self)
            l.sigPositionChangeFinished.connect(self.lineMoveFinished)
            l.sigPositionChanged.connect(self.lineMoved)
            
        if brush is None:
            brush = QtGui.QBrush(QtGui.QColor(0, 0, 255, 50))
        self.setBrush(brush)
        
        self.setMovable(movable)
        
    def getRegion(self):
        """Return the values at the edges of the region."""
        #if self.orientation[0] == 'h':
            #r = (self.bounds.top(), self.bounds.bottom())
        #else:
            #r = (self.bounds.left(), self.bounds.right())
        r = [self.lines[0].value(), self.lines[1].value()]
        return (min(r), max(r))

    def setRegion(self, rgn):
        """Set the values for the edges of the region.
        
        ============= ==============================================
        **Arguments** 
        rgn           A list or tuple of the lower and upper values.
        ============= ==============================================
        """
        if self.lines[0].value() == rgn[0] and self.lines[1].value() == rgn[1]:
            return
        self.blockLineSignal = True
        self.lines[0].setValue(rgn[0])
        self.blockLineSignal = False
        self.lines[1].setValue(rgn[1])
        #self.blockLineSignal = False
        self.lineMoved()
        self.lineMoveFinished()

    def setBrush(self, *br, **kargs):
        """Set the brush that fills the region. Can have any arguments that are valid
        for :func:`mkBrush <pyqtgraph.mkBrush>`.
        """
        self.brush = fn.mkBrush(*br, **kargs)
        self.currentBrush = self.brush

    def setBounds(self, bounds):
        """Optional [min, max] bounding values for the region. To have no bounds on the
        region use [None, None].
        Does not affect the current position of the region unless it is outside the new bounds. 
        See :func:`setRegion <pyqtgraph.LinearRegionItem.setRegion>` to set the position 
        of the region."""
        for l in self.lines:
            l.setBounds(bounds)
        
    def setMovable(self, m):
        """Set lines to be movable by the user, or not. If lines are movable, they will 
        also accept HoverEvents."""
        for l in self.lines:
            l.setMovable(m)
        self.movable = m
        self.setAcceptHoverEvents(m)

    def boundingRect(self):
        br = UIGraphicsItem.boundingRect(self)
        rng = self.getRegion()
        if self.orientation == LinearRegionItem.Vertical:
            br.setLeft(rng[0])
            br.setRight(rng[1])
        else:
            br.setTop(rng[0])
            br.setBottom(rng[1])
        return br.normalized()
        
    def paint(self, p, *args):
        #prof = debug.Profiler('LinearRegionItem.paint')
        UIGraphicsItem.paint(self, p, *args)
        p.setBrush(self.currentBrush)
        p.setPen(fn.mkPen(None))
        p.drawRect(self.boundingRect())
        #prof.finish()

    def dataBounds(self, axis, frac=1.0, orthoRange=None):
        if axis == self.orientation:
            return self.getRegion()
        else:
            return None

    def lineMoved(self):
        if self.blockLineSignal:
            return
        self.prepareGeometryChange()
        #self.emit(QtCore.SIGNAL('regionChanged'), self)
        self.sigRegionChanged.emit(self)
            
    def lineMoveFinished(self):
        #self.emit(QtCore.SIGNAL('regionChangeFinished'), self)
        self.sigRegionChangeFinished.emit(self)
        
            
    #def updateBounds(self):
        #vb = self.view().viewRect()
        #vals = [self.lines[0].value(), self.lines[1].value()]
        #if self.orientation[0] == 'h':
            #vb.setTop(min(vals))
            #vb.setBottom(max(vals))
        #else:
            #vb.setLeft(min(vals))
            #vb.setRight(max(vals))
        #if vb != self.bounds:
            #self.bounds = vb
            #self.rect.setRect(vb)
        
    #def mousePressEvent(self, ev):
        #if not self.movable:
            #ev.ignore()
            #return
        #for l in self.lines:
            #l.mousePressEvent(ev)  ## pass event to both lines so they move together
        ##if self.movable and ev.button() == QtCore.Qt.LeftButton:
            ##ev.accept()
            ##self.pressDelta = self.mapToParent(ev.pos()) - QtCore.QPointF(*self.p)
        ##else:
            ##ev.ignore()
            
    #def mouseReleaseEvent(self, ev):
        #for l in self.lines:
            #l.mouseReleaseEvent(ev)
            
    #def mouseMoveEvent(self, ev):
        ##print "move", ev.pos()
        #if not self.movable:
            #return
        #self.lines[0].blockSignals(True)  # only want to update once
        #for l in self.lines:
            #l.mouseMoveEvent(ev)
        #self.lines[0].blockSignals(False)
        ##self.setPos(self.mapToParent(ev.pos()) - self.pressDelta)
        ##self.emit(QtCore.SIGNAL('dragged'), self)

    def mouseDragEvent(self, ev):
        if not self.movable or int(ev.button() & QtCore.Qt.LeftButton) == 0:
            return
        ev.accept()
        
        if ev.isStart():
            bdp = ev.buttonDownPos()
            self.cursorOffsets = [l.pos() - bdp for l in self.lines]
            self.startPositions = [l.pos() for l in self.lines]
            self.moving = True
            
        if not self.moving:
            return
            
        #delta = ev.pos() - ev.lastPos()
        self.lines[0].blockSignals(True)  # only want to update once
        for i, l in enumerate(self.lines):
            l.setPos(self.cursorOffsets[i] + ev.pos())
            #l.setPos(l.pos()+delta)
            #l.mouseDragEvent(ev)
        self.lines[0].blockSignals(False)
        self.prepareGeometryChange()
        
        if ev.isFinish():
            self.moving = False
            self.sigRegionChangeFinished.emit(self)
        else:
            self.sigRegionChanged.emit(self)
            
    def mouseClickEvent(self, ev):
        if self.moving and ev.button() == QtCore.Qt.RightButton:
            ev.accept()
            for i, l in enumerate(self.lines):
                l.setPos(self.startPositions[i])
            self.moving = False
            self.sigRegionChanged.emit(self)
            self.sigRegionChangeFinished.emit(self)


    def hoverEvent(self, ev):
        if self.movable and (not ev.isExit()) and ev.acceptDrags(QtCore.Qt.LeftButton):
            self.setMouseHover(True)
        else:
            self.setMouseHover(False)
            
    def setMouseHover(self, hover):
        ## Inform the item that the mouse is(not) hovering over it
        if self.mouseHovering == hover:
            return
        self.mouseHovering = hover
        if hover:
            c = self.brush.color()
            c.setAlpha(c.alpha() * 2)
            self.currentBrush = fn.mkBrush(c)
        else:
            self.currentBrush = self.brush
        self.update()

    #def hoverEnterEvent(self, ev):
        #print "rgn hover enter"
        #ev.ignore()
        #self.updateHoverBrush()

    #def hoverMoveEvent(self, ev):
        #print "rgn hover move"
        #ev.ignore()
        #self.updateHoverBrush()

    #def hoverLeaveEvent(self, ev):
        #print "rgn hover leave"
        #ev.ignore()
        #self.updateHoverBrush(False)
        
    #def updateHoverBrush(self, hover=None):
        #if hover is None:
            #scene = self.scene()
            #hover = scene.claimEvent(self, QtCore.Qt.LeftButton, scene.Drag)
        
        #if hover:
            #self.currentBrush = fn.mkBrush(255, 0,0,100)
        #else:
            #self.currentBrush = self.brush
        #self.update()

