# -*- coding: utf-8 -*-
"""
ROI.py -  Interactive graphics items for GraphicsView (ROI widgets)
Copyright 2010  Luke Campagnola
Distributed under MIT/X11 license. See license.txt for more infomation.

Implements a series of graphics items which display movable/scalable/rotatable shapes
for use as region-of-interest markers. ROI class automatically handles extraction 
of array data from ImageItems.

The ROI class is meant to serve as the base for more specific types; see several examples
of how to build an ROI at the bottom of the file.
"""

from pyqtgraph.Qt import QtCore, QtGui
#if not hasattr(QtCore, 'Signal'):
    #QtCore.Signal = QtCore.pyqtSignal
import numpy as np
from numpy.linalg import norm
import scipy.ndimage as ndimage
from pyqtgraph.Point import *
from pyqtgraph.SRTTransform import SRTTransform
from math import cos, sin
import pyqtgraph.functions as fn
from .GraphicsObject import GraphicsObject
from .UIGraphicsItem import UIGraphicsItem

__all__ = [
    'ROI', 
    'TestROI', 'RectROI', 'EllipseROI', 'CircleROI', 'PolygonROI', 
    'LineROI', 'MultiLineROI', 'MultiRectROI', 'LineSegmentROI', 'PolyLineROI', 'SpiralROI',
]


def rectStr(r):
    return "[%f, %f] + [%f, %f]" % (r.x(), r.y(), r.width(), r.height())

class ROI(GraphicsObject):
    """Generic region-of-interest widget. 
    Can be used for implementing many types of selection box with rotate/translate/scale handles.
    
    Signals
    ----------------------- ----------------------------------------------------
    sigRegionChangeFinished Emitted when the user stops dragging the ROI (or
                            one of its handles) or if the ROI is changed
                            programatically.
    sigRegionChangeStarted  Emitted when the user starts dragging the ROI (or
                            one of its handles).
    sigRegionChanged        Emitted any time the position of the ROI changes,
                            including while it is being dragged by the user.
    sigHoverEvent           Emitted when the mouse hovers over the ROI.
    sigClicked              Emitted when the user clicks on the ROI.
                            Note that clicking is disabled by default to prevent
                            stealing clicks from objects behind the ROI. To 
                            enable clicking, call 
                            roi.setAcceptedMouseButtons(QtCore.Qt.LeftButton). 
                            See QtGui.QGraphicsItem documentation for more 
                            details.
    sigRemoveRequested      Emitted when the user selects 'remove' from the 
                            ROI's context menu (if available).
    ----------------------- ----------------------------------------------------
    """
    
    sigRegionChangeFinished = QtCore.Signal(object)
    sigRegionChangeStarted = QtCore.Signal(object)
    sigRegionChanged = QtCore.Signal(object)
    sigHoverEvent = QtCore.Signal(object)
    sigClicked = QtCore.Signal(object, object)
    sigRemoveRequested = QtCore.Signal(object)
    
    def __init__(self, pos, size=Point(1, 1), angle=0.0, invertible=False, maxBounds=None, snapSize=1.0, scaleSnap=False, translateSnap=False, rotateSnap=False, parent=None, pen=None, movable=True, removable=False):
        #QObjectWorkaround.__init__(self)
        GraphicsObject.__init__(self, parent)
        self.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        pos = Point(pos)
        size = Point(size)
        self.aspectLocked = False
        self.translatable = movable
        self.rotateAllowed = True
        self.removable = removable
        self.menu = None
        
        self.freeHandleMoved = False ## keep track of whether free handles have moved since last change signal was emitted.
        self.mouseHovering = False
        if pen is None:
            pen = (255, 255, 255)
        self.setPen(pen)
        
        self.handlePen = QtGui.QPen(QtGui.QColor(150, 255, 255))
        self.handles = []
        self.state = {'pos': Point(0,0), 'size': Point(1,1), 'angle': 0}  ## angle is in degrees for ease of Qt integration
        self.lastState = None
        self.setPos(pos)
        self.setAngle(angle)
        self.setSize(size)
        self.setZValue(10)
        self.isMoving = False
        
        self.handleSize = 5
        self.invertible = invertible
        self.maxBounds = maxBounds
        
        self.snapSize = snapSize
        self.translateSnap = translateSnap
        self.rotateSnap = rotateSnap
        self.scaleSnap = scaleSnap
        #self.setFlag(self.ItemIsSelectable, True)
    
    def getState(self):
        return self.stateCopy()

    def stateCopy(self):
        sc = {}
        sc['pos'] = Point(self.state['pos'])
        sc['size'] = Point(self.state['size'])
        sc['angle'] = self.state['angle']
        return sc
        
    def saveState(self):
        """Return the state of the widget in a format suitable for storing to disk. (Points are converted to tuple)"""
        state = {}
        state['pos'] = tuple(self.state['pos'])
        state['size'] = tuple(self.state['size'])
        state['angle'] = self.state['angle']
        return state
    
    def setState(self, state, update=True):
        self.setPos(state['pos'], update=False)
        self.setSize(state['size'], update=False)
        self.setAngle(state['angle'], update=update)
    
    def setZValue(self, z):
        QtGui.QGraphicsItem.setZValue(self, z)
        for h in self.handles:
            h['item'].setZValue(z+1)
        
    def parentBounds(self):
        return self.mapToParent(self.boundingRect()).boundingRect()

    def setPen(self, pen):
        self.pen = fn.mkPen(pen)
        self.currentPen = self.pen
        self.update()
        
    def size(self):
        return self.getState()['size']
        
    def pos(self):
        return self.getState()['pos']
        
    def angle(self):
        return self.getState()['angle']
        
    def setPos(self, pos, update=True, finish=True):
        """Set the position of the ROI (in the parent's coordinate system).
        By default, this will cause both sigRegionChanged and sigRegionChangeFinished to be emitted.
        
        If finish is False, then sigRegionChangeFinished will not be emitted. You can then use 
        stateChangeFinished() to cause the signal to be emitted after a series of state changes.
        
        If update is False, the state change will be remembered but not processed and no signals 
        will be emitted. You can then use stateChanged() to complete the state change. This allows
        multiple change functions to be called sequentially while minimizing processing overhead
        and repeated signals. Setting update=False also forces finish=False.
        """
        
        pos = Point(pos)
        self.state['pos'] = pos
        QtGui.QGraphicsItem.setPos(self, pos)
        if update:
            self.stateChanged(finish=finish)
        
    def setSize(self, size, update=True, finish=True):
        """Set the size of the ROI. May be specified as a QPoint, Point, or list of two values.
        See setPos() for an explanation of the update and finish arguments.
        """
        size = Point(size)
        self.prepareGeometryChange()
        self.state['size'] = size
        if update:
            self.stateChanged(finish=finish)
        
    def setAngle(self, angle, update=True, finish=True):
        """Set the angle of rotation (in degrees) for this ROI.
        See setPos() for an explanation of the update and finish arguments.
        """
        self.state['angle'] = angle
        tr = QtGui.QTransform()
        #tr.rotate(-angle * 180 / np.pi)
        tr.rotate(angle)
        self.setTransform(tr)
        if update:
            self.stateChanged(finish=finish)
        
    def scale(self, s, center=[0,0], update=True, finish=True):
        """
        Resize the ROI by scaling relative to *center*.
        See setPos() for an explanation of the *update* and *finish* arguments.
        """
        c = self.mapToParent(Point(center) * self.state['size'])
        self.prepareGeometryChange()
        newSize = self.state['size'] * s
        c1 = self.mapToParent(Point(center) * newSize)
        newPos = self.state['pos'] + c - c1
        
        self.setSize(newSize, update=False)
        self.setPos(newPos, update=update, finish=finish)
        
   
    def translate(self, *args, **kargs):
        """
        Move the ROI to a new position.
        Accepts either (x, y, snap) or ([x,y], snap) as arguments
        If the ROI is bounded and the move would exceed boundaries, then the ROI
        is moved to the nearest acceptable position instead.
        
        snap can be:
           None (default): use self.translateSnap and self.snapSize to determine whether/how to snap
           False:          do not snap
           Point(w,h)      snap to rectangular grid with spacing (w,h)
           True:           snap using self.snapSize (and ignoring self.translateSnap)
           
        Also accepts *update* and *finish* arguments (see setPos() for a description of these).
        """

        if len(args) == 1:
            pt = args[0]
        else:
            pt = args
            
        newState = self.stateCopy()
        newState['pos'] = newState['pos'] + pt
        
        ## snap position
        #snap = kargs.get('snap', None)
        #if (snap is not False)   and   not (snap is None and self.translateSnap is False):
        
        snap = kargs.get('snap', None)
        if snap is None:
            snap = self.translateSnap
        if snap is not False:
            newState['pos'] = self.getSnapPosition(newState['pos'], snap=snap)
        
        #d = ev.scenePos() - self.mapToScene(self.pressPos)
        if self.maxBounds is not None:
            r = self.stateRect(newState)
            #r0 = self.sceneTransform().mapRect(self.boundingRect())
            d = Point(0,0)
            if self.maxBounds.left() > r.left():
                d[0] = self.maxBounds.left() - r.left()
            elif self.maxBounds.right() < r.right():
                d[0] = self.maxBounds.right() - r.right()
            if self.maxBounds.top() > r.top():
                d[1] = self.maxBounds.top() - r.top()
            elif self.maxBounds.bottom() < r.bottom():
                d[1] = self.maxBounds.bottom() - r.bottom()
            newState['pos'] += d
        
        #self.state['pos'] = newState['pos']
        update = kargs.get('update', True)
        finish = kargs.get('finish', True)
        self.setPos(newState['pos'], update=update, finish=finish)
        #if 'update' not in kargs or kargs['update'] is True:
        #self.stateChanged()

    def rotate(self, angle, update=True, finish=True):
        self.setAngle(self.angle()+angle, update=update, finish=finish)

    def handleMoveStarted(self):
        self.preMoveState = self.getState()
    
    def addTranslateHandle(self, pos, axes=None, item=None, name=None, index=None):
        pos = Point(pos)
        return self.addHandle({'name': name, 'type': 't', 'pos': pos, 'item': item}, index=index)
    
    def addFreeHandle(self, pos=None, axes=None, item=None, name=None, index=None):
        if pos is not None:
            pos = Point(pos)
        return self.addHandle({'name': name, 'type': 'f', 'pos': pos, 'item': item}, index=index)
    
    def addScaleHandle(self, pos, center, axes=None, item=None, name=None, lockAspect=False, index=None):
        pos = Point(pos)
        center = Point(center)
        info = {'name': name, 'type': 's', 'center': center, 'pos': pos, 'item': item, 'lockAspect': lockAspect}
        if pos.x() == center.x():
            info['xoff'] = True
        if pos.y() == center.y():
            info['yoff'] = True
        return self.addHandle(info, index=index)
    
    def addRotateHandle(self, pos, center, item=None, name=None, index=None):
        pos = Point(pos)
        center = Point(center)
        return self.addHandle({'name': name, 'type': 'r', 'center': center, 'pos': pos, 'item': item}, index=index)
    
    def addScaleRotateHandle(self, pos, center, item=None, name=None, index=None):
        pos = Point(pos)
        center = Point(center)
        if pos[0] != center[0] and pos[1] != center[1]:
            raise Exception("Scale/rotate handles must have either the same x or y coordinate as their center point.")
        return self.addHandle({'name': name, 'type': 'sr', 'center': center, 'pos': pos, 'item': item}, index=index)
    
    def addRotateFreeHandle(self, pos, center, axes=None, item=None, name=None, index=None):
        pos = Point(pos)
        center = Point(center)
        return self.addHandle({'name': name, 'type': 'rf', 'center': center, 'pos': pos, 'item': item}, index=index)
    
    def addHandle(self, info, index=None):
        ## If a Handle was not supplied, create it now
        if 'item' not in info or info['item'] is None:
            h = Handle(self.handleSize, typ=info['type'], pen=self.handlePen, parent=self)
            h.setPos(info['pos'] * self.state['size'])
            info['item'] = h
        else:
            h = info['item']
            if info['pos'] is None:
                info['pos'] = h.pos()
            
        ## connect the handle to this ROI
        #iid = len(self.handles)
        h.connectROI(self)
        if index is None:
            self.handles.append(info)
        else:
            self.handles.insert(index, info)
        
        h.setZValue(self.zValue()+1)
        self.stateChanged()
        return h
    
    def indexOfHandle(self, handle):
        if isinstance(handle, Handle):
            index = [i for i, info in enumerate(self.handles) if info['item'] is handle]    
            if len(index) == 0:
                raise Exception("Cannot remove handle; it is not attached to this ROI")
            return index[0]
        else:
            return handle
        
    def removeHandle(self, handle):
        """Remove a handle from this ROI. Argument may be either a Handle instance or the integer index of the handle."""
        index = self.indexOfHandle(handle)
            
        handle = self.handles[index]['item']
        self.handles.pop(index)
        handle.disconnectROI(self)
        if len(handle.rois) == 0:
            self.scene().removeItem(handle)
        self.stateChanged()
    
    def replaceHandle(self, oldHandle, newHandle):
        """Replace one handle in the ROI for another. This is useful when connecting multiple ROIs together.
        *oldHandle* may be a Handle instance or the index of a handle."""
        #print "========================="
        #print "replace", oldHandle, newHandle
        #print self
        #print self.handles
        #print "-----------------"
        index = self.indexOfHandle(oldHandle)
        info = self.handles[index]
        self.removeHandle(index)
        info['item'] = newHandle
        info['pos'] = newHandle.pos()
        self.addHandle(info, index=index)
        #print self.handles
        
    def checkRemoveHandle(self, handle):
        ## This is used when displaying a Handle's context menu to determine
        ## whether removing is allowed. 
        ## Subclasses may wish to override this to disable the menu entry.
        ## Note: by default, handles are not user-removable even if this method returns True.
        return True
        
        
    def getLocalHandlePositions(self, index=None):
        """Returns the position of a handle in ROI coordinates"""
        if index == None:
            positions = []
            for h in self.handles:
                positions.append((h['name'], h['pos']))
            return positions
        else:
            return (self.handles[index]['name'], self.handles[index]['pos'])
            
    def getSceneHandlePositions(self, index=None):
        if index == None:
            positions = []
            for h in self.handles:
                positions.append((h['name'], h['item'].scenePos()))
            return positions
        else:
            return (self.handles[index]['name'], self.handles[index]['item'].scenePos())
        
    def getHandles(self):
        return [h['item'] for h in self.handles]
    
    def mapSceneToParent(self, pt):
        return self.mapToParent(self.mapFromScene(pt))

    def setSelected(self, s):
        QtGui.QGraphicsItem.setSelected(self, s)
        #print "select", self, s
        if s:
            for h in self.handles:
                h['item'].show()
        else:
            for h in self.handles:
                h['item'].hide()


    def hoverEvent(self, ev):
        hover = False
        if not ev.isExit():
            if self.translatable and ev.acceptDrags(QtCore.Qt.LeftButton):
                hover=True
                
            for btn in [QtCore.Qt.LeftButton, QtCore.Qt.RightButton, QtCore.Qt.MidButton]:
                if int(self.acceptedMouseButtons() & btn) > 0 and ev.acceptClicks(btn):
                    hover=True
            if self.contextMenuEnabled():
                ev.acceptClicks(QtCore.Qt.RightButton)
                
        if hover:
            self.setMouseHover(True)
            self.sigHoverEvent.emit(self)
            ev.acceptClicks(QtCore.Qt.LeftButton)  ## If the ROI is hilighted, we should accept all clicks to avoid confusion.
            ev.acceptClicks(QtCore.Qt.RightButton)
            ev.acceptClicks(QtCore.Qt.MidButton)
        else:
            self.setMouseHover(False)

    def setMouseHover(self, hover):
        ## Inform the ROI that the mouse is(not) hovering over it
        if self.mouseHovering == hover:
            return
        self.mouseHovering = hover
        if hover:
            self.currentPen = fn.mkPen(255, 255, 0)
        else:
            self.currentPen = self.pen
        self.update()

    def contextMenuEnabled(self):
        return self.removable
    
    def raiseContextMenu(self, ev):
        if not self.contextMenuEnabled():
            return
        menu = self.getMenu()
        menu = self.scene().addParentContextMenus(self, menu, ev)
        pos = ev.screenPos()
        menu.popup(QtCore.QPoint(pos.x(), pos.y()))

    def getMenu(self):
        if self.menu is None:
            self.menu = QtGui.QMenu()
            self.menu.setTitle("ROI")
            remAct = QtGui.QAction("Remove ROI", self.menu)
            remAct.triggered.connect(self.removeClicked)
            self.menu.addAction(remAct)
            self.menu.remAct = remAct
        return self.menu

    def removeClicked(self):
        ## Send remove event only after we have exited the menu event handler
        self.removeTimer = QtCore.QTimer()
        self.removeTimer.timeout.connect(lambda: self.sigRemoveRequested.emit(self))
        self.removeTimer.start(0)
        

    
    def mouseDragEvent(self, ev):
        if ev.isStart():
            #p = ev.pos()
            #if not self.isMoving and not self.shape().contains(p):
                #ev.ignore()
                #return        
            if ev.button() == QtCore.Qt.LeftButton:
                self.setSelected(True)
                if self.translatable:
                    self.isMoving = True
                    self.preMoveState = self.getState()
                    self.cursorOffset = self.pos() - self.mapToParent(ev.buttonDownPos())
                    self.sigRegionChangeStarted.emit(self)
                    ev.accept()
                else:
                    ev.ignore()

        elif ev.isFinish():
            if self.translatable:
                if self.isMoving:
                    self.stateChangeFinished()
                self.isMoving = False
            return

        if self.translatable and self.isMoving and ev.buttons() == QtCore.Qt.LeftButton:
            snap = True if (ev.modifiers() & QtCore.Qt.ControlModifier) else None
            newPos = self.mapToParent(ev.pos()) + self.cursorOffset
            self.translate(newPos - self.pos(), snap=snap, finish=False)
        
    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton and self.isMoving:
            ev.accept()
            self.cancelMove()
        if ev.button() == QtCore.Qt.RightButton and self.contextMenuEnabled():
            self.raiseContextMenu(ev)
            ev.accept()
        elif int(ev.button() & self.acceptedMouseButtons()) > 0:
            ev.accept()
            self.sigClicked.emit(self, ev)
        else:
            ev.ignore()
            
        
            

    def cancelMove(self):
        self.isMoving = False
        self.setState(self.preMoveState)


    #def pointDragEvent(self, pt, ev):
        ### just for handling drag start/stop.
        ### drag moves are handled through movePoint()
        
        #if ev.isStart():
            #self.isMoving = True
            #self.preMoveState = self.getState()
            
            #self.sigRegionChangeStarted.emit(self)
        #elif ev.isFinish():
            #self.isMoving = False
            #self.sigRegionChangeFinished.emit(self)
            #return
        
        
    #def pointPressEvent(self, pt, ev):
        ##print "press"
        #self.isMoving = True
        #self.preMoveState = self.getState()
        
        ##self.emit(QtCore.SIGNAL('regionChangeStarted'), self)
        #self.sigRegionChangeStarted.emit(self)
        ##self.pressPos = self.mapFromScene(ev.scenePos())
        ##self.pressHandlePos = self.handles[pt]['item'].pos()
    
    #def pointReleaseEvent(self, pt, ev):
        ##print "release"
        #self.isMoving = False
        ##self.emit(QtCore.SIGNAL('regionChangeFinished'), self)
        #self.sigRegionChangeFinished.emit(self)
    
    #def pointMoveEvent(self, pt, ev):
        #self.movePoint(pt, ev.scenePos(), ev.modifiers())
        
    
    def checkPointMove(self, handle, pos, modifiers):
        """When handles move, they must ask the ROI if the move is acceptable.
        By default, this always returns True. Subclasses may wish override.
        """
        return True
    

    def movePoint(self, handle, pos, modifiers=QtCore.Qt.KeyboardModifier(), finish=True, coords='parent'):
        ## called by Handles when they are moved. 
        ## pos is the new position of the handle in scene coords, as requested by the handle.
        
        newState = self.stateCopy()
        index = self.indexOfHandle(handle)
        h = self.handles[index]
        p0 = self.mapToParent(h['pos'] * self.state['size'])
        p1 = Point(pos)
        
        if coords == 'parent':
            pass
        elif coords == 'scene':
            p1 = self.mapSceneToParent(p1)
        else:
            raise Exception("New point location must be given in either 'parent' or 'scene' coordinates.")

        
        ## transform p0 and p1 into parent's coordinates (same as scene coords if there is no parent). I forget why.
        #p0 = self.mapSceneToParent(p0)
        #p1 = self.mapSceneToParent(p1)

        ## Handles with a 'center' need to know their local position relative to the center point (lp0, lp1)
        if 'center' in h:
            c = h['center']
            cs = c * self.state['size']
            lp0 = self.mapFromParent(p0) - cs
            lp1 = self.mapFromParent(p1) - cs
        
        if h['type'] == 't':
            snap = True if (modifiers & QtCore.Qt.ControlModifier) else None
            #if self.translateSnap or ():
                #snap = Point(self.snapSize, self.snapSize)
            self.translate(p1-p0, snap=snap, update=False)
        
        elif h['type'] == 'f':
            newPos = self.mapFromParent(p1)
            h['item'].setPos(newPos)
            h['pos'] = newPos
            self.freeHandleMoved = True
            #self.sigRegionChanged.emit(self)  ## should be taken care of by call to stateChanged()
            
        elif h['type'] == 's':
            ## If a handle and its center have the same x or y value, we can't scale across that axis.
            if h['center'][0] == h['pos'][0]:
                lp1[0] = 0
            if h['center'][1] == h['pos'][1]:
                lp1[1] = 0
            
            ## snap 
            if self.scaleSnap or (modifiers & QtCore.Qt.ControlModifier):
                lp1[0] = round(lp1[0] / self.snapSize) * self.snapSize
                lp1[1] = round(lp1[1] / self.snapSize) * self.snapSize
                
            ## preserve aspect ratio (this can override snapping)
            if h['lockAspect'] or (modifiers & QtCore.Qt.AltModifier):
                #arv = Point(self.preMoveState['size']) - 
                lp1 = lp1.proj(lp0)
            
            ## determine scale factors and new size of ROI
            hs = h['pos'] - c
            if hs[0] == 0:
                hs[0] = 1
            if hs[1] == 0:
                hs[1] = 1
            newSize = lp1 / hs
            
            ## Perform some corrections and limit checks
            if newSize[0] == 0:
                newSize[0] = newState['size'][0]
            if newSize[1] == 0:
                newSize[1] = newState['size'][1]
            if not self.invertible:
                if newSize[0] < 0:
                    newSize[0] = newState['size'][0]
                if newSize[1] < 0:
                    newSize[1] = newState['size'][1]
            if self.aspectLocked:
                newSize[0] = newSize[1]
            
            ## Move ROI so the center point occupies the same scene location after the scale
            s0 = c * self.state['size']
            s1 = c * newSize
            cc = self.mapToParent(s0 - s1) - self.mapToParent(Point(0, 0))
            
            ## update state, do more boundary checks
            newState['size'] = newSize
            newState['pos'] = newState['pos'] + cc
            if self.maxBounds is not None:
                r = self.stateRect(newState)
                if not self.maxBounds.contains(r):
                    return
            
            self.setPos(newState['pos'], update=False)
            self.setSize(newState['size'], update=False)
        
        elif h['type'] in ['r', 'rf']:
            if h['type'] == 'rf':
                self.freeHandleMoved = True
            
            if not self.rotateAllowed:
                return
            ## If the handle is directly over its center point, we can't compute an angle.
            if lp1.length() == 0 or lp0.length() == 0:
                return
            
            ## determine new rotation angle, constrained if necessary
            ang = newState['angle'] - lp0.angle(lp1)
            if ang is None:  ## this should never happen..
                return
            if self.rotateSnap or (modifiers & QtCore.Qt.ControlModifier):
                ang = round(ang / 15.) * 15.  ## 180/12 = 15
            
            ## create rotation transform
            tr = QtGui.QTransform()
            tr.rotate(ang)
            
            ## move ROI so that center point remains stationary after rotate
            cc = self.mapToParent(cs) - (tr.map(cs) + self.state['pos'])
            newState['angle'] = ang
            newState['pos'] = newState['pos'] + cc
            
            ## check boundaries, update
            if self.maxBounds is not None:
                r = self.stateRect(newState)
                if not self.maxBounds.contains(r):
                    return
            #self.setTransform(tr)
            self.setPos(newState['pos'], update=False)
            self.setAngle(ang, update=False)
            #self.state = newState
            
            ## If this is a free-rotate handle, its distance from the center may change.
            
            if h['type'] == 'rf':
                h['item'].setPos(self.mapFromScene(p1))  ## changes ROI coordinates of handle
                
        elif h['type'] == 'sr':
            if h['center'][0] == h['pos'][0]:
                scaleAxis = 1
            else:
                scaleAxis = 0
            
            if lp1.length() == 0 or lp0.length() == 0:
                return
            
            ang = newState['angle'] - lp0.angle(lp1)
            if ang is None:
                return
            if self.rotateSnap or (modifiers & QtCore.Qt.ControlModifier):
                #ang = round(ang / (np.pi/12.)) * (np.pi/12.)
                ang = round(ang / 15.) * 15.
            
            hs = abs(h['pos'][scaleAxis] - c[scaleAxis])
            newState['size'][scaleAxis] = lp1.length() / hs
            #if self.scaleSnap or (modifiers & QtCore.Qt.ControlModifier):
            if self.scaleSnap:  ## use CTRL only for angular snap here.
                newState['size'][scaleAxis] = round(newState['size'][scaleAxis] / self.snapSize) * self.snapSize
            if newState['size'][scaleAxis] == 0:
                newState['size'][scaleAxis] = 1
                
            c1 = c * newState['size']
            tr = QtGui.QTransform()
            tr.rotate(ang)
            
            cc = self.mapToParent(cs) - (tr.map(c1) + self.state['pos'])
            newState['angle'] = ang
            newState['pos'] = newState['pos'] + cc
            if self.maxBounds is not None:
                r = self.stateRect(newState)
                if not self.maxBounds.contains(r):
                    return
            #self.setTransform(tr)
            #self.setPos(newState['pos'], update=False)
            #self.prepareGeometryChange()
            #self.state = newState
            self.setState(newState, update=False)
        
        self.stateChanged(finish=finish)
    
    def stateChanged(self, finish=True):
        """Process changes to the state of the ROI.
        If there are any changes, then the positions of handles are updated accordingly
        and sigRegionChanged is emitted. If finish is True, then 
        sigRegionChangeFinished will also be emitted."""
        
        changed = False
        if self.lastState is None:
            changed = True
        else:
            for k in list(self.state.keys()):
                if self.state[k] != self.lastState[k]:
                    changed = True
        
        self.prepareGeometryChange()
        if changed:
            ## Move all handles to match the current configuration of the ROI
            for h in self.handles:
                if h['item'] in self.childItems():
                    p = h['pos']
                    h['item'].setPos(h['pos'] * self.state['size'])
                #else:
                #    trans = self.state['pos']-self.lastState['pos']
                #    h['item'].setPos(h['pos'] + h['item'].parentItem().mapFromParent(trans))
                    
            self.update()
            self.sigRegionChanged.emit(self)
        elif self.freeHandleMoved:
            self.sigRegionChanged.emit(self)
            
        self.freeHandleMoved = False
        self.lastState = self.stateCopy()
            
        if finish:
            self.stateChangeFinished()
    
    def stateChangeFinished(self):
        self.sigRegionChangeFinished.emit(self)
    
    def stateRect(self, state):
        r = QtCore.QRectF(0, 0, state['size'][0], state['size'][1])
        tr = QtGui.QTransform()
        #tr.rotate(-state['angle'] * 180 / np.pi)
        tr.rotate(-state['angle'])
        r = tr.mapRect(r)
        return r.adjusted(state['pos'][0], state['pos'][1], state['pos'][0], state['pos'][1])
    
    
    def getSnapPosition(self, pos, snap=None):
        ## Given that pos has been requested, return the nearest snap-to position
        ## optionally, snap may be passed in to specify a rectangular snap grid.
        ## override this function for more interesting snap functionality..
        
        if snap is None or snap is True:
            if self.snapSize is None:
                return pos
            snap = Point(self.snapSize, self.snapSize)
        
        return Point(
            round(pos[0] / snap[0]) * snap[0],
            round(pos[1] / snap[1]) * snap[1]
        )
    
    
    def boundingRect(self):
        return QtCore.QRectF(0, 0, self.state['size'][0], self.state['size'][1]).normalized()

    def paint(self, p, opt, widget):
        p.save()
        r = self.boundingRect()
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(self.currentPen)
        p.translate(r.left(), r.top())
        p.scale(r.width(), r.height())
        p.drawRect(0, 0, 1, 1)
        p.restore()

    def getArraySlice(self, data, img, axes=(0,1), returnSlice=True):
        """Return a tuple of slice objects that can be used to slice the region from data covered by this ROI.
        Also returns the transform which maps the ROI into data coordinates.
        
        If returnSlice is set to False, the function returns a pair of tuples with the values that would have 
        been used to generate the slice objects. ((ax0Start, ax0Stop), (ax1Start, ax1Stop))
        
        If the slice can not be computed (usually because the scene/transforms are not properly
        constructed yet), then the method returns None.
        """
        #print "getArraySlice"
        
        ## Determine shape of array along ROI axes
        dShape = (data.shape[axes[0]], data.shape[axes[1]])
        #print "  dshape", dShape
        
        ## Determine transform that maps ROI bounding box to image coordinates
        try:
            tr = self.sceneTransform() * fn.invertQTransform(img.sceneTransform())
        except np.linalg.linalg.LinAlgError:
            return None
            
        ## Modify transform to scale from image coords to data coords
        #m = QtGui.QTransform()
        tr.scale(float(dShape[0]) / img.width(), float(dShape[1]) / img.height())
        #tr = tr * m
        
        ## Transform ROI bounds into data bounds
        dataBounds = tr.mapRect(self.boundingRect())
        #print "  boundingRect:", self.boundingRect()
        #print "  dataBounds:", dataBounds
        
        ## Intersect transformed ROI bounds with data bounds
        intBounds = dataBounds.intersect(QtCore.QRectF(0, 0, dShape[0], dShape[1]))
        #print "  intBounds:", intBounds
        
        ## Determine index values to use when referencing the array. 
        bounds = (
            (int(min(intBounds.left(), intBounds.right())), int(1+max(intBounds.left(), intBounds.right()))),
            (int(min(intBounds.bottom(), intBounds.top())), int(1+max(intBounds.bottom(), intBounds.top())))
        )
        #print "  bounds:", bounds
        
        if returnSlice:
            ## Create slice objects
            sl = [slice(None)] * data.ndim
            sl[axes[0]] = slice(*bounds[0])
            sl[axes[1]] = slice(*bounds[1])
            return tuple(sl), tr
        else:
            return bounds, tr

    def getArrayRegion(self, data, img, axes=(0,1), returnMappedCoords=False, **kwds):
        """Use the position and orientation of this ROI relative to an imageItem to pull a slice from an array.
        
        This method uses :func:`affineSlice <pyqtgraph.affineSlice>` to generate
        the slice from *data* and uses :func:`getAffineSliceParams <pyqtgraph.ROI.getAffineSliceParams>` to determine the parameters to 
        pass to :func:`affineSlice <pyqtgraph.affineSlice>`.
        
        If *returnMappedCoords* is True, then the method returns a tuple (result, coords) 
        such that coords is the set of coordinates used to interpolate values from the original
        data, mapped into the parent coordinate system of the image. This is useful, when slicing
        data from images that have been transformed, for determining the location of each value
        in the sliced data.
        
        All extra keyword arguments are passed to :func:`affineSlice <pyqtgraph.affineSlice>`.
        """
        
        shape, vectors, origin = self.getAffineSliceParams(data, img, axes)
        if not returnMappedCoords:
            return fn.affineSlice(data, shape=shape, vectors=vectors, origin=origin, axes=axes, **kwds)
        else:
            kwds['returnCoords'] = True
            result, coords = fn.affineSlice(data, shape=shape, vectors=vectors, origin=origin, axes=axes, **kwds)
            #tr = fn.transformToArray(img.transform())[:2]  ## remove perspective transform values
            
            ### separate translation from scale/rotate
            #translate = tr[:,2]
            #tr = tr[:,:2]
            #tr = tr.reshape((2,2) + (1,)*(coords.ndim-1))
            #coords = coords[np.newaxis, ...]
            
            ### map coordinates and return
            #mapped = (tr*coords).sum(axis=0)  ## apply scale/rotate
            #mapped += translate.reshape((2,1,1))
            mapped = fn.transformCoordinates(img.transform(), coords)
            return result, mapped
            
            
        ### transpose data so x and y are the first 2 axes
        #trAx = range(0, data.ndim)
        #trAx.remove(axes[0])
        #trAx.remove(axes[1])
        #tr1 = tuple(axes) + tuple(trAx)
        #arr = data.transpose(tr1)
        
        ### Determine the minimal area of the data we will need
        #(dataBounds, roiDataTransform) = self.getArraySlice(data, img, returnSlice=False, axes=axes)

        ### Pad data boundaries by 1px if possible
        #dataBounds = (
            #(max(dataBounds[0][0]-1, 0), min(dataBounds[0][1]+1, arr.shape[0])),
            #(max(dataBounds[1][0]-1, 0), min(dataBounds[1][1]+1, arr.shape[1]))
        #)

        ### Extract minimal data from array
        #arr1 = arr[dataBounds[0][0]:dataBounds[0][1], dataBounds[1][0]:dataBounds[1][1]]
        
        ### Update roiDataTransform to reflect this extraction
        #roiDataTransform *= QtGui.QTransform().translate(-dataBounds[0][0], -dataBounds[1][0]) 
        #### (roiDataTransform now maps from ROI coords to extracted data coords)
        
        
        ### Rotate array
        #if abs(self.state['angle']) > 1e-5:
            #arr2 = ndimage.rotate(arr1, self.state['angle'] * 180 / np.pi, order=1)
            
            ### update data transforms to reflect this rotation
            #rot = QtGui.QTransform().rotate(self.state['angle'] * 180 / np.pi)
            #roiDataTransform *= rot
            
            ### The rotation also causes a shift which must be accounted for:
            #dataBound = QtCore.QRectF(0, 0, arr1.shape[0], arr1.shape[1])
            #rotBound = rot.mapRect(dataBound)
            #roiDataTransform *= QtGui.QTransform().translate(-rotBound.left(), -rotBound.top())
            
        #else:
            #arr2 = arr1
        
        
        
        #### Shift off partial pixels
        ## 1. map ROI into current data space
        #roiBounds = roiDataTransform.mapRect(self.boundingRect())
        
        ## 2. Determine amount to shift data
        #shift = (int(roiBounds.left()) - roiBounds.left(), int(roiBounds.bottom()) - roiBounds.bottom())
        #if abs(shift[0]) > 1e-6 or abs(shift[1]) > 1e-6:
            ## 3. pad array with 0s before shifting
            #arr2a = np.zeros((arr2.shape[0]+2, arr2.shape[1]+2) + arr2.shape[2:], dtype=arr2.dtype)
            #arr2a[1:-1, 1:-1] = arr2
            
            ## 4. shift array and udpate transforms
            #arr3 = ndimage.shift(arr2a, shift + (0,)*(arr2.ndim-2), order=1)
            #roiDataTransform *= QtGui.QTransform().translate(1+shift[0], 1+shift[1]) 
        #else:
            #arr3 = arr2
        
        
        #### Extract needed region from rotated/shifted array
        ## 1. map ROI into current data space (round these values off--they should be exact integer values at this point)
        #roiBounds = roiDataTransform.mapRect(self.boundingRect())
        ##print self, roiBounds.height()
        ##import traceback
        ##traceback.print_stack()
        
        #roiBounds = QtCore.QRect(round(roiBounds.left()), round(roiBounds.top()), round(roiBounds.width()), round(roiBounds.height()))
        
        ##2. intersect ROI with data bounds
        #dataBounds = roiBounds.intersect(QtCore.QRect(0, 0, arr3.shape[0], arr3.shape[1]))
        
        ##3. Extract data from array
        #db = dataBounds
        #bounds = (
            #(db.left(), db.right()+1),
            #(db.top(), db.bottom()+1)
        #)
        #arr4 = arr3[bounds[0][0]:bounds[0][1], bounds[1][0]:bounds[1][1]]

        #### Create zero array in size of ROI
        #arr5 = np.zeros((roiBounds.width(), roiBounds.height()) + arr4.shape[2:], dtype=arr4.dtype)
        
        ### Fill array with ROI data
        #orig = Point(dataBounds.topLeft() - roiBounds.topLeft())
        #subArr = arr5[orig[0]:orig[0]+arr4.shape[0], orig[1]:orig[1]+arr4.shape[1]]
        #subArr[:] = arr4[:subArr.shape[0], :subArr.shape[1]]
        
        
        ### figure out the reverse transpose order
        #tr2 = np.array(tr1)
        #for i in range(0, len(tr2)):
            #tr2[tr1[i]] = i
        #tr2 = tuple(tr2)
        
        ### Untranspose array before returning
        #return arr5.transpose(tr2)

    def getAffineSliceParams(self, data, img, axes=(0,1)):
        """
        Returns the parameters needed to use :func:`affineSlice <pyqtgraph.affineSlice>` to 
        extract a subset of *data* using this ROI and *img* to specify the subset.
        
        See :func:`getArrayRegion <pyqtgraph.ROI.getArrayRegion>` for more information.
        """
        if self.scene() is not img.scene():
            raise Exception("ROI and target item must be members of the same scene.")
        
        shape = self.state['size']
        
        origin = self.mapToItem(img, QtCore.QPointF(0, 0))
        
        ## vx and vy point in the directions of the slice axes, but must be scaled properly
        vx = self.mapToItem(img, QtCore.QPointF(1, 0)) - origin
        vy = self.mapToItem(img, QtCore.QPointF(0, 1)) - origin
        
        lvx = np.sqrt(vx.x()**2 + vx.y()**2)
        lvy = np.sqrt(vy.x()**2 + vy.y()**2)
        pxLen = img.width() / float(data.shape[axes[0]])
        #img.width is number of pixels or width of item?
        #need pxWidth and pxHeight instead of pxLen ?
        sx =  pxLen / lvx
        sy =  pxLen / lvy
        
        vectors = ((vx.x()*sx, vx.y()*sx), (vy.x()*sy, vy.y()*sy))
        shape = self.state['size']
        shape = [abs(shape[0]/sx), abs(shape[1]/sy)]
        
        origin = (origin.x(), origin.y())
        return shape, vectors, origin
        
    def getGlobalTransform(self, relativeTo=None):
        """Return global transformation (rotation angle+translation) required to move 
        from relative state to current state. If relative state isn't specified,
        then we use the state of the ROI when mouse is pressed."""
        if relativeTo == None:
            relativeTo = self.preMoveState
        st = self.getState()
        
        ## this is only allowed because we will be comparing the two 
        relativeTo['scale'] = relativeTo['size']
        st['scale'] = st['size']
        
        
        
        t1 = SRTTransform(relativeTo)
        t2 = SRTTransform(st)
        return t2/t1
        
        
        #st = self.getState()
        
        ### rotation
        #ang = (st['angle']-relativeTo['angle']) * 180. / 3.14159265358
        #rot = QtGui.QTransform()
        #rot.rotate(-ang)

        ### We need to come up with a universal transformation--one that can be applied to other objects 
        ### such that all maintain alignment. 
        ### More specifically, we need to turn the ROI's position and angle into
        ### a rotation _around the origin_ and a translation.
        
        #p0 = Point(relativeTo['pos'])

        ### base position, rotated
        #p1 = rot.map(p0)
        
        #trans = Point(st['pos']) - p1
        #return trans, ang

    def applyGlobalTransform(self, tr):
        st = self.getState()
        
        st['scale'] = st['size']
        st = SRTTransform(st)
        st = (st * tr).saveState()
        st['size'] = st['scale']
        self.setState(st)


class Handle(UIGraphicsItem):
    
    types = {   ## defines number of sides, start angle for each handle type
        't': (4, np.pi/4),
        'f': (4, np.pi/4), 
        's': (4, 0),
        'r': (12, 0),
        'sr': (12, 0),
        'rf': (12, 0),
    }

    sigClicked = QtCore.Signal(object, object)   # self, event
    sigRemoveRequested = QtCore.Signal(object)   # self
    
    def __init__(self, radius, typ=None, pen=(200, 200, 220), parent=None, deletable=False):
        #print "   create item with parent", parent
        #self.bounds = QtCore.QRectF(-1e-10, -1e-10, 2e-10, 2e-10)
        #self.setFlags(self.ItemIgnoresTransformations | self.ItemSendsScenePositionChanges)
        self.rois = []
        self.radius = radius
        self.typ = typ
        self.pen = fn.mkPen(pen)
        self.currentPen = self.pen
        self.pen.setWidth(0)
        self.pen.setCosmetic(True)
        self.isMoving = False
        self.sides, self.startAng = self.types[typ]
        self.buildPath()
        self._shape = None
        self.menu = self.buildMenu()
        
        UIGraphicsItem.__init__(self, parent=parent)
        self.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        self.deletable = deletable
        if deletable:
            self.setAcceptedMouseButtons(QtCore.Qt.RightButton)        
        #self.updateShape()
        self.setZValue(11)
            
    def connectROI(self, roi):
        ### roi is the "parent" roi, i is the index of the handle in roi.handles
        self.rois.append(roi)
        
    def disconnectROI(self, roi):
        self.rois.remove(roi)
        #for i, r in enumerate(self.roi):
            #if r[0] == roi:
                #self.roi.pop(i)
                
    #def close(self):
        #for r in self.roi:
            #r.removeHandle(self)
            
    def setDeletable(self, b):
        self.deletable = b
        if b:
            self.setAcceptedMouseButtons(self.acceptedMouseButtons() | QtCore.Qt.RightButton)
        else:
            self.setAcceptedMouseButtons(self.acceptedMouseButtons() & ~QtCore.Qt.RightButton)
            
    def removeClicked(self):
        self.sigRemoveRequested.emit(self)

    def hoverEvent(self, ev):
        hover = False
        if not ev.isExit():
            if ev.acceptDrags(QtCore.Qt.LeftButton):
                hover=True
            for btn in [QtCore.Qt.LeftButton, QtCore.Qt.RightButton, QtCore.Qt.MidButton]:
                if int(self.acceptedMouseButtons() & btn) > 0 and ev.acceptClicks(btn):
                    hover=True
                    
        if hover:
            self.currentPen = fn.mkPen(255, 255,0)
        else:
            self.currentPen = self.pen
        self.update()
        #if (not ev.isExit()) and ev.acceptDrags(QtCore.Qt.LeftButton):
            #self.currentPen = fn.mkPen(255, 255,0)
        #else:
            #self.currentPen = self.pen
        #self.update()
            


    def mouseClickEvent(self, ev):
        ## right-click cancels drag
        if ev.button() == QtCore.Qt.RightButton and self.isMoving:
            self.isMoving = False  ## prevents any further motion
            self.movePoint(self.startPos, finish=True)
            #for r in self.roi:
                #r[0].cancelMove()
            ev.accept()
        elif int(ev.button() & self.acceptedMouseButtons()) > 0:
            ev.accept()
            if ev.button() == QtCore.Qt.RightButton and self.deletable:
                self.raiseContextMenu(ev)
            self.sigClicked.emit(self, ev)
        else:
            ev.ignore()        
            
            #elif self.deletable:
                #ev.accept()
                #self.raiseContextMenu(ev)
            #else:
                #ev.ignore()
                
    def buildMenu(self):
        menu = QtGui.QMenu()
        menu.setTitle("Handle")
        self.removeAction = menu.addAction("Remove handle", self.removeClicked) 
        return menu
        
    def getMenu(self):
        return self.menu
                
            
    def getContextMenus(self, event):
        return [self.menu]
    
    def raiseContextMenu(self, ev):
        menu = self.scene().addParentContextMenus(self, self.getMenu(), ev)
        
        ## Make sure it is still ok to remove this handle
        removeAllowed = all([r.checkRemoveHandle(self) for r in self.rois])
        self.removeAction.setEnabled(removeAllowed)
        pos = ev.screenPos()
        menu.popup(QtCore.QPoint(pos.x(), pos.y()))    

    def mouseDragEvent(self, ev):
        if ev.button() != QtCore.Qt.LeftButton:
            return
        ev.accept()
        
        ## Inform ROIs that a drag is happening 
        ##  note: the ROI is informed that the handle has moved using ROI.movePoint
        ##  this is for other (more nefarious) purposes.
        #for r in self.roi:
            #r[0].pointDragEvent(r[1], ev)
            
        if ev.isFinish():
            if self.isMoving:
                for r in self.rois:
                    r.stateChangeFinished()
            self.isMoving = False
        elif ev.isStart():
            for r in self.rois:
                r.handleMoveStarted()
            self.isMoving = True
            self.startPos = self.scenePos()
            self.cursorOffset = self.scenePos() - ev.buttonDownScenePos()
            
        if self.isMoving:  ## note: isMoving may become False in mid-drag due to right-click.
            pos = ev.scenePos() + self.cursorOffset
            self.movePoint(pos, ev.modifiers(), finish=False)

    def movePoint(self, pos, modifiers=QtCore.Qt.KeyboardModifier(), finish=True):
        for r in self.rois:
            if not r.checkPointMove(self, pos, modifiers):
                return
        #print "point moved; inform %d ROIs" % len(self.roi)
        # A handle can be used by multiple ROIs; tell each to update its handle position
        for r in self.rois:
            r.movePoint(self, pos, modifiers, finish=finish, coords='scene')
        
    def buildPath(self):
        size = self.radius
        self.path = QtGui.QPainterPath()
        ang = self.startAng
        dt = 2*np.pi / self.sides
        for i in range(0, self.sides+1):
            x = size * cos(ang)
            y = size * sin(ang)
            ang += dt
            if i == 0:
                self.path.moveTo(x, y)
            else:
                self.path.lineTo(x, y)            
            
    def paint(self, p, opt, widget):
        ### determine rotation of transform
        #m = self.sceneTransform()
        ##mi = m.inverted()[0]
        #v = m.map(QtCore.QPointF(1, 0)) - m.map(QtCore.QPointF(0, 0))
        #va = np.arctan2(v.y(), v.x())
        
        ### Determine length of unit vector in painter's coords
        ##size = mi.map(Point(self.radius, self.radius)) - mi.map(Point(0, 0))
        ##size = (size.x()*size.x() + size.y() * size.y()) ** 0.5
        #size = self.radius
        
        #bounds = QtCore.QRectF(-size, -size, size*2, size*2)
        #if bounds != self.bounds:
            #self.bounds = bounds
            #self.prepareGeometryChange()
        p.setRenderHints(p.Antialiasing, True)
        p.setPen(self.currentPen)
        
        #p.rotate(va * 180. / 3.1415926)
        #p.drawPath(self.path)        
        p.drawPath(self.shape())
        #ang = self.startAng + va
        #dt = 2*np.pi / self.sides
        #for i in range(0, self.sides):
            #x1 = size * cos(ang)
            #y1 = size * sin(ang)
            #x2 = size * cos(ang+dt)
            #y2 = size * sin(ang+dt)
            #ang += dt
            #p.drawLine(Point(x1, y1), Point(x2, y2))
            
    def shape(self):
        if self._shape is None:
            s = self.generateShape()
            if s is None:
                return self.path
            self._shape = s
            self.prepareGeometryChange()  ## beware--this can cause the view to adjust, which would immediately invalidate the shape.
        return self._shape
    
    def boundingRect(self):
        #print 'roi:', self.roi
        s1 = self.shape()
        #print "   s1:", s1
        #s2 = self.shape()
        #print "   s2:", s2
        
        return self.shape().boundingRect()
            
    def generateShape(self):
        ## determine rotation of transform
        #m = self.sceneTransform()  ## Qt bug: do not access sceneTransform() until we know this object has a scene.
        #mi = m.inverted()[0]
        dt = self.deviceTransform()
        
        if dt is None:
            self._shape = self.path
            return None
        
        v = dt.map(QtCore.QPointF(1, 0)) - dt.map(QtCore.QPointF(0, 0))
        va = np.arctan2(v.y(), v.x())
        
        dti = fn.invertQTransform(dt)
        devPos = dt.map(QtCore.QPointF(0,0))
        tr = QtGui.QTransform()
        tr.translate(devPos.x(), devPos.y())
        tr.rotate(va * 180. / 3.1415926)
        
        return dti.map(tr.map(self.path))
        
        
    def viewTransformChanged(self):
        GraphicsObject.viewTransformChanged(self)
        self._shape = None  ## invalidate shape, recompute later if requested.
        self.update()
        
    #def itemChange(self, change, value):
        #if change == self.ItemScenePositionHasChanged:
            #self.updateShape()


class TestROI(ROI):
    def __init__(self, pos, size, **args):
        #QtGui.QGraphicsRectItem.__init__(self, pos[0], pos[1], size[0], size[1])
        ROI.__init__(self, pos, size, **args)
        #self.addTranslateHandle([0, 0])
        self.addTranslateHandle([0.5, 0.5])
        self.addScaleHandle([1, 1], [0, 0])
        self.addScaleHandle([0, 0], [1, 1])
        self.addScaleRotateHandle([1, 0.5], [0.5, 0.5])
        self.addScaleHandle([0.5, 1], [0.5, 0.5])
        self.addRotateHandle([1, 0], [0, 0])
        self.addRotateHandle([0, 1], [1, 1])



class RectROI(ROI):
    def __init__(self, pos, size, centered=False, sideScalers=False, **args):
        #QtGui.QGraphicsRectItem.__init__(self, 0, 0, size[0], size[1])
        ROI.__init__(self, pos, size, **args)
        if centered:
            center = [0.5, 0.5]
        else:
            center = [0, 0]
            
        #self.addTranslateHandle(center)
        self.addScaleHandle([1, 1], center)
        if sideScalers:
            self.addScaleHandle([1, 0.5], [center[0], 0.5])
            self.addScaleHandle([0.5, 1], [0.5, center[1]])

class LineROI(ROI):
    def __init__(self, pos1, pos2, width, **args):
        pos1 = Point(pos1)
        pos2 = Point(pos2)
        d = pos2-pos1
        l = d.length()
        ang = Point(1, 0).angle(d)
        ra = ang * np.pi / 180.
        c = Point(-width/2. * sin(ra), -width/2. * cos(ra))
        pos1 = pos1 + c
        
        ROI.__init__(self, pos1, size=Point(l, width), angle=ang, **args)
        self.addScaleRotateHandle([0, 0.5], [1, 0.5])
        self.addScaleRotateHandle([1, 0.5], [0, 0.5])
        self.addScaleHandle([0.5, 1], [0.5, 0.5])
        

        
class MultiRectROI(QtGui.QGraphicsObject):
    """
    Chain of rectangular ROIs connected by handles. 
    
    This is generally used to mark a curved path through 
    an image similarly to PolyLineROI. It differs in that each segment
    of the chain is rectangular instead of linear and thus has width.
    """
    sigRegionChangeFinished = QtCore.Signal(object)
    sigRegionChangeStarted = QtCore.Signal(object)
    sigRegionChanged = QtCore.Signal(object)
    
    def __init__(self, points, width, pen=None, **args):
        QtGui.QGraphicsObject.__init__(self)
        self.pen = pen
        self.roiArgs = args
        self.lines = []
        if len(points) < 2:
            raise Exception("Must start with at least 2 points")
        
        ## create first segment
        self.addSegment(points[1], connectTo=points[0], scaleHandle=True)
        
        ## create remaining segments
        for p in points[2:]:
            self.addSegment(p)
        
        
    def paint(self, *args):
        pass
    
    def boundingRect(self):
        return QtCore.QRectF()
        
    def roiChangedEvent(self):
        w = self.lines[0].state['size'][1]
        for l in self.lines[1:]:
            w0 = l.state['size'][1]
            if w == w0:
                continue
            l.scale([1.0, w/w0], center=[0.5,0.5])
        self.sigRegionChanged.emit(self)
            
    def roiChangeStartedEvent(self):
        self.sigRegionChangeStarted.emit(self)
        
    def roiChangeFinishedEvent(self):
        self.sigRegionChangeFinished.emit(self)
        
    def getHandlePositions(self):
        """Return the positions of all handles in local coordinates."""
        pos = [self.mapFromScene(self.lines[0].getHandles()[0].scenePos())]
        for l in self.lines:
            pos.append(self.mapFromScene(l.getHandles()[1].scenePos()))
        return pos
        
    def getArrayRegion(self, arr, img=None, axes=(0,1)):
        rgns = []
        for l in self.lines:
            rgn = l.getArrayRegion(arr, img, axes=axes)
            if rgn is None:
                continue
                #return None
            rgns.append(rgn)
            #print l.state['size']
            
        ## make sure orthogonal axis is the same size
        ## (sometimes fp errors cause differences)
        ms = min([r.shape[axes[1]] for r in rgns])
        sl = [slice(None)] * rgns[0].ndim
        sl[axes[1]] = slice(0,ms)
        rgns = [r[sl] for r in rgns]
        #print [r.shape for r in rgns], axes
        
        return np.concatenate(rgns, axis=axes[0])
        
    def addSegment(self, pos=(0,0), scaleHandle=False, connectTo=None):
        """
        Add a new segment to the ROI connecting from the previous endpoint to *pos*.
        (pos is specified in the parent coordinate system of the MultiRectROI)
        """
        
        ## by default, connect to the previous endpoint
        if connectTo is None:
            connectTo = self.lines[-1].getHandles()[1]
            
        ## create new ROI
        newRoi = ROI((0,0), [1, 5], parent=self, pen=self.pen, **self.roiArgs)
        self.lines.append(newRoi)
        
        ## Add first SR handle
        if isinstance(connectTo, Handle):
            self.lines[-1].addScaleRotateHandle([0, 0.5], [1, 0.5], item=connectTo)
            newRoi.movePoint(connectTo, connectTo.scenePos(), coords='scene')
        else:
            h = self.lines[-1].addScaleRotateHandle([0, 0.5], [1, 0.5])
            newRoi.movePoint(h, connectTo, coords='scene')
            
        ## add second SR handle
        h = self.lines[-1].addScaleRotateHandle([1, 0.5], [0, 0.5]) 
        newRoi.movePoint(h, pos)
        
        ## optionally add scale handle (this MUST come after the two SR handles)
        if scaleHandle:
            newRoi.addScaleHandle([0.5, 1], [0.5, 0.5])
            
        newRoi.translatable = False 
        newRoi.sigRegionChanged.connect(self.roiChangedEvent) 
        newRoi.sigRegionChangeStarted.connect(self.roiChangeStartedEvent) 
        newRoi.sigRegionChangeFinished.connect(self.roiChangeFinishedEvent)
        self.sigRegionChanged.emit(self) 
    

    def removeSegment(self, index=-1): 
        """Remove a segment from the ROI."""
        roi = self.lines[index]
        self.lines.pop(index)
        self.scene().removeItem(roi)
        roi.sigRegionChanged.disconnect(self.roiChangedEvent) 
        roi.sigRegionChangeStarted.disconnect(self.roiChangeStartedEvent) 
        roi.sigRegionChangeFinished.disconnect(self.roiChangeFinishedEvent)
        
        self.sigRegionChanged.emit(self)
        
        
class MultiLineROI(MultiRectROI):
    def __init__(self, *args, **kwds):
        MultiRectROI.__init__(self, *args, **kwds)
        print("Warning: MultiLineROI has been renamed to MultiRectROI. (and MultiLineROI may be redefined in the future)")
        
class EllipseROI(ROI):
    def __init__(self, pos, size, **args):
        #QtGui.QGraphicsRectItem.__init__(self, 0, 0, size[0], size[1])
        ROI.__init__(self, pos, size, **args)
        self.addRotateHandle([1.0, 0.5], [0.5, 0.5])
        self.addScaleHandle([0.5*2.**-0.5 + 0.5, 0.5*2.**-0.5 + 0.5], [0.5, 0.5])
            
    def paint(self, p, opt, widget):
        r = self.boundingRect()
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(self.currentPen)
        
        p.scale(r.width(), r.height())## workaround for GL bug
        r = QtCore.QRectF(r.x()/r.width(), r.y()/r.height(), 1,1)
        
        p.drawEllipse(r)
        
    def getArrayRegion(self, arr, img=None):
        arr = ROI.getArrayRegion(self, arr, img)
        if arr is None or arr.shape[0] == 0 or arr.shape[1] == 0:
            return None
        w = arr.shape[0]
        h = arr.shape[1]
        ## generate an ellipsoidal mask
        mask = np.fromfunction(lambda x,y: (((x+0.5)/(w/2.)-1)**2+ ((y+0.5)/(h/2.)-1)**2)**0.5 < 1, (w, h))
    
        return arr * mask
    
    def shape(self):
        self.path = QtGui.QPainterPath()
        self.path.addEllipse(self.boundingRect())
        return self.path
        
        
class CircleROI(EllipseROI):
    def __init__(self, pos, size, **args):
        ROI.__init__(self, pos, size, **args)
        self.aspectLocked = True
        #self.addTranslateHandle([0.5, 0.5])
        self.addScaleHandle([0.5*2.**-0.5 + 0.5, 0.5*2.**-0.5 + 0.5], [0.5, 0.5])
        
class PolygonROI(ROI):
    ## deprecated. Use PloyLineROI instead.
    
    def __init__(self, positions, pos=None, **args):
        if pos is None:
            pos = [0,0]
        ROI.__init__(self, pos, [1,1], **args)
        #ROI.__init__(self, positions[0])
        for p in positions:
            self.addFreeHandle(p)
        self.setZValue(1000)
        print("Warning: PolygonROI is deprecated. Use PolyLineROI instead.")
        
            
    def listPoints(self):
        return [p['item'].pos() for p in self.handles]
            
    #def movePoint(self, *args, **kargs):
        #ROI.movePoint(self, *args, **kargs)
        #self.prepareGeometryChange()
        #for h in self.handles:
            #h['pos'] = h['item'].pos()
            
    def paint(self, p, *args):
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(self.currentPen)
        for i in range(len(self.handles)):
            h1 = self.handles[i]['item'].pos()
            h2 = self.handles[i-1]['item'].pos()
            p.drawLine(h1, h2)
        
    def boundingRect(self):
        r = QtCore.QRectF()
        for h in self.handles:
            r |= self.mapFromItem(h['item'], h['item'].boundingRect()).boundingRect()   ## |= gives the union of the two QRectFs
        return r
    
    def shape(self):
        p = QtGui.QPainterPath()
        p.moveTo(self.handles[0]['item'].pos())
        for i in range(len(self.handles)):
            p.lineTo(self.handles[i]['item'].pos())
        return p
    
    def stateCopy(self):
        sc = {}
        sc['pos'] = Point(self.state['pos'])
        sc['size'] = Point(self.state['size'])
        sc['angle'] = self.state['angle']
        #sc['handles'] = self.handles
        return sc

class PolyLineROI(ROI):
    """Container class for multiple connected LineSegmentROIs. Responsible for adding new 
    line segments, and for translation/(rotation?) of multiple lines together."""
    def __init__(self, positions, closed=False, pos=None, **args):
        
        if pos is None:
            pos = [0,0]
            
        ROI.__init__(self, pos, size=[1,1], **args)
        self.closed = closed
        self.segments = []
        
        for p in positions:
            self.addFreeHandle(p)
         
        start = -1 if self.closed else 0
        for i in range(start, len(self.handles)-1):
            self.addSegment(self.handles[i]['item'], self.handles[i+1]['item'])

    def addSegment(self, h1, h2, index=None):
        seg = LineSegmentROI(handles=(h1, h2), pen=self.pen, parent=self, movable=False)
        if index is None:
            self.segments.append(seg)
        else:
            self.segments.insert(index, seg)
        seg.sigClicked.connect(self.segmentClicked)
        seg.setAcceptedMouseButtons(QtCore.Qt.LeftButton)
        seg.setZValue(self.zValue()+1)
        for h in seg.handles:
            h['item'].setDeletable(True)
            h['item'].setAcceptedMouseButtons(h['item'].acceptedMouseButtons() | QtCore.Qt.LeftButton) ## have these handles take left clicks too, so that handles cannot be added on top of other handles
        
    def setMouseHover(self, hover):
        ## Inform all the ROI's segments that the mouse is(not) hovering over it
        ROI.setMouseHover(self, hover)
        for s in self.segments:
            s.setMouseHover(hover)
          
    def addHandle(self, info, index=None):
        h = ROI.addHandle(self, info, index=index)
        h.sigRemoveRequested.connect(self.removeHandle)
        return h
        
    def segmentClicked(self, segment, ev=None, pos=None): ## pos should be in this item's coordinate system
        if ev != None:
            pos = segment.mapToParent(ev.pos())
        elif pos != None:
            pos = pos
        else:
            raise Exception("Either an event or a position must be given.")
        h1 = segment.handles[0]['item']
        h2 = segment.handles[1]['item']
        
        i = self.segments.index(segment)
        h3 = self.addFreeHandle(pos, index=self.indexOfHandle(h2))
        self.addSegment(h3, h2, index=i+1)
        segment.replaceHandle(h2, h3)
        
    def removeHandle(self, handle, updateSegments=True):
        ROI.removeHandle(self, handle)
        handle.sigRemoveRequested.disconnect(self.removeHandle)
        
        if not updateSegments:
            return
        segments = handle.rois[:]
        
        if len(segments) == 1:
            self.removeSegment(segments[0])
        else:
            handles = [h['item'] for h in segments[1].handles]
            handles.remove(handle)
            segments[0].replaceHandle(handle, handles[0])
            self.removeSegment(segments[1])
        
    def removeSegment(self, seg):
        for handle in seg.handles[:]:
            seg.removeHandle(handle['item'])
        self.segments.remove(seg)
        seg.sigClicked.disconnect(self.segmentClicked)
        self.scene().removeItem(seg)
        
    def checkRemoveHandle(self, h):
        ## called when a handle is about to display its context menu
        if self.closed:
            return len(self.handles) > 3
        else:
            return len(self.handles) > 2
        
    def paint(self, p, *args):
        #for s in self.segments:
            #s.update()
        #p.setPen(self.currentPen)
        #p.setPen(fn.mkPen('w'))
        #p.drawRect(self.boundingRect())
        #p.drawPath(self.shape())
        pass
    
    def boundingRect(self):
        return self.shape().boundingRect()
        #r = QtCore.QRectF()
        #for h in self.handles:
            #r |= self.mapFromItem(h['item'], h['item'].boundingRect()).boundingRect()   ## |= gives the union of the two QRectFs
        #return r 

    def shape(self):
        p = QtGui.QPainterPath()
        if len(self.handles) == 0:
            return p
        p.moveTo(self.handles[0]['item'].pos())
        for i in range(len(self.handles)):
            p.lineTo(self.handles[i]['item'].pos())
        p.lineTo(self.handles[0]['item'].pos())
        return p        

    def getArrayRegion(self, data, img, axes=(0,1), returnMappedCoords=False, **kwds):
        sl = self.getArraySlice(data, img, axes=(0,1))
        if sl is None:
            return None
        sliced = data[sl[0]]
        im = QtGui.QImage(sliced.shape[axes[0]], sliced.shape[axes[1]], QtGui.QImage.Format_ARGB32)
        im.fill(0x0)
        p = QtGui.QPainter(im)
        p.setPen(fn.mkPen(None))
        p.setBrush(fn.mkBrush('w'))
        p.setTransform(self.itemTransform(img)[0])
        bounds = self.mapRectToItem(img, self.boundingRect())
        p.translate(-bounds.left(), -bounds.top()) 
        p.drawPath(self.shape())
        p.end()
        mask = fn.imageToArray(im)[:,:,0].astype(float) / 255.
        shape = [1] * data.ndim
        shape[axes[0]] = sliced.shape[axes[0]]
        shape[axes[1]] = sliced.shape[axes[1]]
        return sliced * mask.reshape(shape)


class LineSegmentROI(ROI):
    """
    ROI subclass with two freely-moving handles defining a line.
    """
    
    def __init__(self, positions=(None, None), pos=None, handles=(None,None), **args):
        if pos is None:
            pos = [0,0]
            
        ROI.__init__(self, pos, [1,1], **args)
        #ROI.__init__(self, positions[0])
        if len(positions) > 2:
            raise Exception("LineSegmentROI must be defined by exactly 2 positions. For more points, use PolyLineROI.")
        
        for i, p in enumerate(positions):
            self.addFreeHandle(p, item=handles[i])
                
        
    def listPoints(self):
        return [p['item'].pos() for p in self.handles]
            
    def paint(self, p, *args):
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(self.currentPen)
        h1 = self.handles[0]['item'].pos()
        h2 = self.handles[1]['item'].pos()
        p.drawLine(h1, h2)
        
    def boundingRect(self):
        return self.shape().boundingRect()
    
    def shape(self):
        p = QtGui.QPainterPath()
    
        h1 = self.handles[0]['item'].pos()
        h2 = self.handles[1]['item'].pos()
        dh = h2-h1
        if dh.length() == 0:
            return p
        pxv = self.pixelVectors(dh)[1]
        if pxv is None:
            return p
            
        pxv *= 4
        
        p.moveTo(h1+pxv)
        p.lineTo(h2+pxv)
        p.lineTo(h2-pxv)
        p.lineTo(h1-pxv)
        p.lineTo(h1+pxv)
      
        return p
    
    def getArrayRegion(self, data, img, axes=(0,1)):
        """
        Use the position of this ROI relative to an imageItem to pull a slice from an array.
        Since this pulls 1D data from a 2D coordinate system, the return value will have ndim = data.ndim-1
        """
        
        imgPts = [self.mapToItem(img, h['item'].pos()) for h in self.handles]
        rgns = []
        for i in range(len(imgPts)-1):
            d = Point(imgPts[i+1] - imgPts[i])
            o = Point(imgPts[i])
            r = fn.affineSlice(data, shape=(int(d.length()),), vectors=[Point(d.norm())], origin=o, axes=axes, order=1)
            rgns.append(r)
            
        return np.concatenate(rgns, axis=axes[0])
        

class SpiralROI(ROI):
    def __init__(self, pos=None, size=None, **args):
        if size == None:
            size = [100e-6,100e-6]
        if pos == None:
            pos = [0,0]
        ROI.__init__(self, pos, size, **args)
        self.translateSnap = False
        self.addFreeHandle([0.25,0], name='a')
        self.addRotateFreeHandle([1,0], [0,0], name='r')
        #self.getRadius()
        #QtCore.connect(self, QtCore.SIGNAL('regionChanged'), self.
        
        
    def getRadius(self):
        radius = Point(self.handles[1]['item'].pos()).length()
        #r2 = radius[1]
        #r3 = r2[0]
        return radius
    
    def boundingRect(self):
        r = self.getRadius()
        return QtCore.QRectF(-r*1.1, -r*1.1, 2.2*r, 2.2*r)
        #return self.bounds
    
    #def movePoint(self, *args, **kargs):
        #ROI.movePoint(self, *args, **kargs)
        #self.prepareGeometryChange()
        #for h in self.handles:
            #h['pos'] = h['item'].pos()/self.state['size'][0]
            
    def stateChanged(self, finish=True):
        ROI.stateChanged(self, finish=finish)
        if len(self.handles) > 1:
            self.path = QtGui.QPainterPath()
            h0 = Point(self.handles[0]['item'].pos()).length()
            a = h0/(2.0*np.pi)
            theta = 30.0*(2.0*np.pi)/360.0
            self.path.moveTo(QtCore.QPointF(a*theta*cos(theta), a*theta*sin(theta)))
            x0 = a*theta*cos(theta)
            y0 = a*theta*sin(theta)
            radius = self.getRadius()
            theta += 20.0*(2.0*np.pi)/360.0
            i = 0
            while Point(x0, y0).length() < radius and i < 1000:
                x1 = a*theta*cos(theta)
                y1 = a*theta*sin(theta)
                self.path.lineTo(QtCore.QPointF(x1,y1))
                theta += 20.0*(2.0*np.pi)/360.0
                x0 = x1
                y0 = y1
                i += 1
           
                
            return self.path
    
        
    def shape(self):
        p = QtGui.QPainterPath()
        p.addEllipse(self.boundingRect())
        return p
    
    def paint(self, p, *args):
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        #path = self.shape()
        p.setPen(self.currentPen)
        p.drawPath(self.path)
        p.setPen(QtGui.QPen(QtGui.QColor(255,0,0)))
        p.drawPath(self.shape())
        p.setPen(QtGui.QPen(QtGui.QColor(0,0,255)))
        p.drawRect(self.boundingRect())
        
    

            

