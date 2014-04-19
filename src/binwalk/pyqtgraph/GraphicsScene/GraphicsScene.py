from pyqtgraph.Qt import QtCore, QtGui

from pyqtgraph.python2_3 import sortList
#try:
    #from PyQt4 import QtOpenGL
    #HAVE_OPENGL = True
#except ImportError:
    #HAVE_OPENGL = False

import weakref
from pyqtgraph.Point import Point
import pyqtgraph.functions as fn
import pyqtgraph.ptime as ptime
from .mouseEvents import *
import pyqtgraph.debug as debug
from . import exportDialog

if hasattr(QtCore, 'PYQT_VERSION'):
    try:
        import sip
        HAVE_SIP = True
    except ImportError:
        HAVE_SIP = False
else:
    HAVE_SIP = False


__all__ = ['GraphicsScene']

class GraphicsScene(QtGui.QGraphicsScene):
    """
    Extension of QGraphicsScene that implements a complete, parallel mouse event system.
    (It would have been preferred to just alter the way QGraphicsScene creates and delivers 
    events, but this turned out to be impossible because the constructor for QGraphicsMouseEvent
    is private)
    
    *  Generates MouseClicked events in addition to the usual press/move/release events. 
       (This works around a problem where it is impossible to have one item respond to a 
       drag if another is watching for a click.)
    *  Adjustable radius around click that will catch objects so you don't have to click *exactly* over small/thin objects
    *  Global context menu--if an item implements a context menu, then its parent(s) may also add items to the menu.
    *  Allows items to decide _before_ a mouse click which item will be the recipient of mouse events.
       This lets us indicate unambiguously to the user which item they are about to click/drag on
    *  Eats mouseMove events that occur too soon after a mouse press.
    *  Reimplements items() and itemAt() to circumvent PyQt bug
    
    Mouse interaction is as follows:
    
    1) Every time the mouse moves, the scene delivers both the standard hoverEnter/Move/LeaveEvents 
       as well as custom HoverEvents. 
    2) Items are sent HoverEvents in Z-order and each item may optionally call event.acceptClicks(button), 
       acceptDrags(button) or both. If this method call returns True, this informs the item that _if_ 
       the user clicks/drags the specified mouse button, the item is guaranteed to be the 
       recipient of click/drag events (the item may wish to change its appearance to indicate this).
       If the call to acceptClicks/Drags returns False, then the item is guaranteed to *not* receive
       the requested event (because another item has already accepted it). 
    3) If the mouse is clicked, a mousePressEvent is generated as usual. If any items accept this press event, then
       No click/drag events will be generated and mouse interaction proceeds as defined by Qt. This allows
       items to function properly if they are expecting the usual press/move/release sequence of events.
       (It is recommended that items do NOT accept press events, and instead use click/drag events)
       Note: The default implementation of QGraphicsItem.mousePressEvent will *accept* the event if the 
       item is has its Selectable or Movable flags enabled. You may need to override this behavior.
    4) If no item accepts the mousePressEvent, then the scene will begin delivering mouseDrag and/or mouseClick events.
       If the mouse is moved a sufficient distance (or moved slowly enough) before the button is released, 
       then a mouseDragEvent is generated.
       If no drag events are generated before the button is released, then a mouseClickEvent is generated. 
    5) Click/drag events are delivered to the item that called acceptClicks/acceptDrags on the HoverEvent
       in step 1. If no such items exist, then the scene attempts to deliver the events to items near the event. 
       ClickEvents may be delivered in this way even if no
       item originally claimed it could accept the click. DragEvents may only be delivered this way if it is the initial
       move in a drag.
    """
    
    sigMouseHover = QtCore.Signal(object)   ## emits a list of objects hovered over
    sigMouseMoved = QtCore.Signal(object)   ## emits position of mouse on every move
    sigMouseClicked = QtCore.Signal(object)   ## emitted when mouse is clicked. Check for event.isAccepted() to see whether the event has already been acted on.
    
    sigPrepareForPaint = QtCore.Signal()  ## emitted immediately before the scene is about to be rendered
    
    _addressCache = weakref.WeakValueDictionary()
    
    ExportDirectory = None
    
    @classmethod
    def registerObject(cls, obj):
        """
        Workaround for PyQt bug in qgraphicsscene.items()
        All subclasses of QGraphicsObject must register themselves with this function.
        (otherwise, mouse interaction with those objects will likely fail)
        """
        if HAVE_SIP and isinstance(obj, sip.wrapper):
            cls._addressCache[sip.unwrapinstance(sip.cast(obj, QtGui.QGraphicsItem))] = obj
            
            
    def __init__(self, clickRadius=2, moveDistance=5):
        QtGui.QGraphicsScene.__init__(self)
        self.setClickRadius(clickRadius)
        self.setMoveDistance(moveDistance)
        self.exportDirectory = None
        
        self.clickEvents = []
        self.dragButtons = []
        self.prepItems = weakref.WeakKeyDictionary()  ## set of items with prepareForPaintMethods
        self.mouseGrabber = None
        self.dragItem = None
        self.lastDrag = None
        self.hoverItems = weakref.WeakKeyDictionary()
        self.lastHoverEvent = None
        #self.searchRect = QtGui.QGraphicsRectItem()
        #self.searchRect.setPen(fn.mkPen(200,0,0))
        #self.addItem(self.searchRect)
        
        self.contextMenu = [QtGui.QAction("Export...", self)]
        self.contextMenu[0].triggered.connect(self.showExportDialog)
        
        self.exportDialog = None
        
    def render(self, *args):
        self.prepareForPaint()
        return QtGui.QGraphicsScene.render(self, *args)

    def prepareForPaint(self):
        """Called before every render. This method will inform items that the scene is about to
        be rendered by emitting sigPrepareForPaint.
        
        This allows items to delay expensive processing until they know a paint will be required."""
        self.sigPrepareForPaint.emit()
    

    def setClickRadius(self, r):
        """
        Set the distance away from mouse clicks to search for interacting items.
        When clicking, the scene searches first for items that directly intersect the click position
        followed by any other items that are within a rectangle that extends r pixels away from the 
        click position. 
        """
        self._clickRadius = r
        
    def setMoveDistance(self, d):
        """
        Set the distance the mouse must move after a press before mouseMoveEvents will be delivered.
        This ensures that clicks with a small amount of movement are recognized as clicks instead of
        drags.
        """
        self._moveDistance = d

    def mousePressEvent(self, ev):
        #print 'scenePress'
        QtGui.QGraphicsScene.mousePressEvent(self, ev)
        #print "mouseGrabberItem: ", self.mouseGrabberItem()
        if self.mouseGrabberItem() is None:  ## nobody claimed press; we are free to generate drag/click events
            self.clickEvents.append(MouseClickEvent(ev))
            
            ## set focus on the topmost focusable item under this click
            items = self.items(ev.scenePos())
            for i in items:
                if i.isEnabled() and i.isVisible() and int(i.flags() & i.ItemIsFocusable) > 0:
                    i.setFocus(QtCore.Qt.MouseFocusReason)
                    break
        #else:
            #addr = sip.unwrapinstance(sip.cast(self.mouseGrabberItem(), QtGui.QGraphicsItem))
            #item = GraphicsScene._addressCache.get(addr, self.mouseGrabberItem())            
            #print "click grabbed by:", item
        
    def mouseMoveEvent(self, ev):
        self.sigMouseMoved.emit(ev.scenePos())
        
        ## First allow QGraphicsScene to deliver hoverEnter/Move/ExitEvents
        QtGui.QGraphicsScene.mouseMoveEvent(self, ev)
        
        ## Next deliver our own HoverEvents
        self.sendHoverEvents(ev)
        
        if int(ev.buttons()) != 0:  ## button is pressed; send mouseMoveEvents and mouseDragEvents
            QtGui.QGraphicsScene.mouseMoveEvent(self, ev)
            if self.mouseGrabberItem() is None:
                now = ptime.time()
                init = False
                ## keep track of which buttons are involved in dragging
                for btn in [QtCore.Qt.LeftButton, QtCore.Qt.MidButton, QtCore.Qt.RightButton]:
                    if int(ev.buttons() & btn) == 0:
                        continue
                    if int(btn) not in self.dragButtons:  ## see if we've dragged far enough yet
                        cev = [e for e in self.clickEvents if int(e.button()) == int(btn)][0]
                        dist = Point(ev.screenPos() - cev.screenPos())
                        if dist.length() < self._moveDistance and now - cev.time() < 0.5:
                            continue
                        init = init or (len(self.dragButtons) == 0)  ## If this is the first button to be dragged, then init=True
                        self.dragButtons.append(int(btn))
                        
                ## If we have dragged buttons, deliver a drag event
                if len(self.dragButtons) > 0:
                    if self.sendDragEvent(ev, init=init):
                        ev.accept()
                
    def leaveEvent(self, ev):  ## inform items that mouse is gone
        if len(self.dragButtons) == 0:
            self.sendHoverEvents(ev, exitOnly=True)
        
                
    def mouseReleaseEvent(self, ev):
        #print 'sceneRelease'
        if self.mouseGrabberItem() is None:
            #print "sending click/drag event"
            if ev.button() in self.dragButtons:
                if self.sendDragEvent(ev, final=True):
                    #print "sent drag event"
                    ev.accept()
                self.dragButtons.remove(ev.button())
            else:
                cev = [e for e in self.clickEvents if int(e.button()) == int(ev.button())]
                if self.sendClickEvent(cev[0]):
                    #print "sent click event"
                    ev.accept()
                self.clickEvents.remove(cev[0])
                
        if int(ev.buttons()) == 0:
            self.dragItem = None
            self.dragButtons = []
            self.clickEvents = []
            self.lastDrag = None
        QtGui.QGraphicsScene.mouseReleaseEvent(self, ev)
        
        self.sendHoverEvents(ev)  ## let items prepare for next click/drag

    def mouseDoubleClickEvent(self, ev):
        QtGui.QGraphicsScene.mouseDoubleClickEvent(self, ev)
        if self.mouseGrabberItem() is None:  ## nobody claimed press; we are free to generate drag/click events
            self.clickEvents.append(MouseClickEvent(ev, double=True))
        
    def sendHoverEvents(self, ev, exitOnly=False):
        ## if exitOnly, then just inform all previously hovered items that the mouse has left.
        
        if exitOnly:
            acceptable=False
            items = []
            event = HoverEvent(None, acceptable)
        else:
            acceptable = int(ev.buttons()) == 0  ## if we are in mid-drag, do not allow items to accept the hover event.
            event = HoverEvent(ev, acceptable)
            items = self.itemsNearEvent(event, hoverable=True)
            self.sigMouseHover.emit(items)
            
        prevItems = list(self.hoverItems.keys())
            
        for item in items:
            if hasattr(item, 'hoverEvent'):
                event.currentItem = item
                if item not in self.hoverItems:
                    self.hoverItems[item] = None
                    event.enter = True
                else:
                    prevItems.remove(item)
                    event.enter = False
                    
                try:
                    item.hoverEvent(event)
                except:
                    debug.printExc("Error sending hover event:")
                    
        event.enter = False
        event.exit = True
        for item in prevItems:
            event.currentItem = item
            try:
                item.hoverEvent(event)
            except:
                debug.printExc("Error sending hover exit event:")
            finally:
                del self.hoverItems[item]
        
        if hasattr(ev, 'buttons') and int(ev.buttons()) == 0:
            self.lastHoverEvent = event  ## save this so we can ask about accepted events later.
            

    def sendDragEvent(self, ev, init=False, final=False):
        ## Send a MouseDragEvent to the current dragItem or to 
        ## items near the beginning of the drag
        event = MouseDragEvent(ev, self.clickEvents[0], self.lastDrag, start=init, finish=final)
        #print "dragEvent: init=", init, 'final=', final, 'self.dragItem=', self.dragItem
        if init and self.dragItem is None:
            if self.lastHoverEvent is not None:
                acceptedItem = self.lastHoverEvent.dragItems().get(event.button(), None)
            else:
                acceptedItem = None
                
            if acceptedItem is not None:
                #print "Drag -> pre-selected item:", acceptedItem
                self.dragItem = acceptedItem
                event.currentItem = self.dragItem
                try:
                    self.dragItem.mouseDragEvent(event)
                except:
                    debug.printExc("Error sending drag event:")
                    
            else:
                #print "drag -> new item"
                for item in self.itemsNearEvent(event):
                    #print "check item:", item
                    if not item.isVisible() or not item.isEnabled():
                        continue
                    if hasattr(item, 'mouseDragEvent'):
                        event.currentItem = item
                        try:
                            item.mouseDragEvent(event)
                        except:
                            debug.printExc("Error sending drag event:")
                        if event.isAccepted():
                            #print "   --> accepted"
                            self.dragItem = item
                            if int(item.flags() & item.ItemIsFocusable) > 0:
                                item.setFocus(QtCore.Qt.MouseFocusReason)
                            break
        elif self.dragItem is not None:
            event.currentItem = self.dragItem
            try:
                self.dragItem.mouseDragEvent(event)
            except:
                debug.printExc("Error sending hover exit event:")
            
        self.lastDrag = event
        
        return event.isAccepted()
            
        
    def sendClickEvent(self, ev):
        ## if we are in mid-drag, click events may only go to the dragged item.
        if self.dragItem is not None and hasattr(self.dragItem, 'mouseClickEvent'):
            ev.currentItem = self.dragItem
            self.dragItem.mouseClickEvent(ev)
            
        ## otherwise, search near the cursor
        else:
            if self.lastHoverEvent is not None:
                acceptedItem = self.lastHoverEvent.clickItems().get(ev.button(), None)
            else:
                acceptedItem = None
                
            if acceptedItem is not None:
                ev.currentItem = acceptedItem
                try:
                    acceptedItem.mouseClickEvent(ev)
                except:
                    debug.printExc("Error sending click event:")
            else:
                for item in self.itemsNearEvent(ev):
                    if not item.isVisible() or not item.isEnabled():
                        continue
                    if hasattr(item, 'mouseClickEvent'):
                        ev.currentItem = item
                        try:
                            item.mouseClickEvent(ev)
                        except:
                            debug.printExc("Error sending click event:")
                            
                        if ev.isAccepted():
                            if int(item.flags() & item.ItemIsFocusable) > 0:
                                item.setFocus(QtCore.Qt.MouseFocusReason)
                            break
                #if not ev.isAccepted() and ev.button() is QtCore.Qt.RightButton:
                    #print "GraphicsScene emitting sigSceneContextMenu"
                    #self.sigMouseClicked.emit(ev)
                    #ev.accept()
        self.sigMouseClicked.emit(ev)
        return ev.isAccepted()
        
    #def claimEvent(self, item, button, eventType):
        #key = (button, eventType)
        #if key in self.claimedEvents:
            #return False
        #self.claimedEvents[key] = item
        #print "event", key, "claimed by", item
        #return True
        
        
    def items(self, *args):
        #print 'args:', args
        items = QtGui.QGraphicsScene.items(self, *args)
        ## PyQt bug: items() returns a list of QGraphicsItem instances. If the item is subclassed from QGraphicsObject,
        ## then the object returned will be different than the actual item that was originally added to the scene
        items2 = list(map(self.translateGraphicsItem, items))
        #if HAVE_SIP and isinstance(self, sip.wrapper):
            #items2 = []
            #for i in items:
                #addr = sip.unwrapinstance(sip.cast(i, QtGui.QGraphicsItem))
                #i2 = GraphicsScene._addressCache.get(addr, i)
                ##print i, "==>", i2
                #items2.append(i2)
        #print 'items:', items
        return items2
    
    def selectedItems(self, *args):
        items = QtGui.QGraphicsScene.selectedItems(self, *args)
        ## PyQt bug: items() returns a list of QGraphicsItem instances. If the item is subclassed from QGraphicsObject,
        ## then the object returned will be different than the actual item that was originally added to the scene
        #if HAVE_SIP and isinstance(self, sip.wrapper):
            #items2 = []
            #for i in items:
                #addr = sip.unwrapinstance(sip.cast(i, QtGui.QGraphicsItem))
                #i2 = GraphicsScene._addressCache.get(addr, i)
                ##print i, "==>", i2
                #items2.append(i2)
        items2 = list(map(self.translateGraphicsItem, items))

        #print 'items:', items
        return items2

    def itemAt(self, *args):
        item = QtGui.QGraphicsScene.itemAt(self, *args)
        
        ## PyQt bug: items() returns a list of QGraphicsItem instances. If the item is subclassed from QGraphicsObject,
        ## then the object returned will be different than the actual item that was originally added to the scene
        #if HAVE_SIP and isinstance(self, sip.wrapper):
            #addr = sip.unwrapinstance(sip.cast(item, QtGui.QGraphicsItem))
            #item = GraphicsScene._addressCache.get(addr, item)
        #return item
        return self.translateGraphicsItem(item)

    def itemsNearEvent(self, event, selMode=QtCore.Qt.IntersectsItemShape, sortOrder=QtCore.Qt.DescendingOrder, hoverable=False):
        """
        Return an iterator that iterates first through the items that directly intersect point (in Z order)
        followed by any other items that are within the scene's click radius.
        """
        #tr = self.getViewWidget(event.widget()).transform()
        view = self.views()[0]
        tr = view.viewportTransform()
        r = self._clickRadius
        rect = view.mapToScene(QtCore.QRect(0, 0, 2*r, 2*r)).boundingRect()
        
        seen = set()
        if hasattr(event, 'buttonDownScenePos'):
            point = event.buttonDownScenePos()
        else:
            point = event.scenePos()
        w = rect.width()
        h = rect.height()
        rgn = QtCore.QRectF(point.x()-w, point.y()-h, 2*w, 2*h)
        #self.searchRect.setRect(rgn)


        items = self.items(point, selMode, sortOrder, tr)
        
        ## remove items whose shape does not contain point (scene.items() apparently sucks at this)
        items2 = []
        for item in items:
            if hoverable and not hasattr(item, 'hoverEvent'):
                continue
            shape = item.shape()
            if shape is None:
                continue
            if item.mapToScene(shape).contains(point):
                items2.append(item)
        
        ## Sort by descending Z-order (don't trust scene.itms() to do this either)
        ## use 'absolute' z value, which is the sum of all item/parent ZValues
        def absZValue(item):
            if item is None:
                return 0
            return item.zValue() + absZValue(item.parentItem())
        
        sortList(items2, lambda a,b: cmp(absZValue(b), absZValue(a)))
        
        return items2
        
        #for item in items:
            ##seen.add(item)

            #shape = item.mapToScene(item.shape())
            #if not shape.contains(point):
                #continue
            #yield item
        #for item in self.items(rgn, selMode, sortOrder, tr):
            ##if item not in seen:
            #yield item
        
    def getViewWidget(self):
        return self.views()[0]
    
    #def getViewWidget(self, widget):
        ### same pyqt bug -- mouseEvent.widget() doesn't give us the original python object.
        ### [[doesn't seem to work correctly]]
        #if HAVE_SIP and isinstance(self, sip.wrapper):
            #addr = sip.unwrapinstance(sip.cast(widget, QtGui.QWidget))
            ##print "convert", widget, addr
            #for v in self.views():
                #addr2 = sip.unwrapinstance(sip.cast(v, QtGui.QWidget))
                ##print "   check:", v, addr2
                #if addr2 == addr:
                    #return v
        #else:
            #return widget
        
    def addParentContextMenus(self, item, menu, event):
        """
        Can be called by any item in the scene to expand its context menu to include parent context menus.
        Parents may implement getContextMenus to add new menus / actions to the existing menu.
        getContextMenus must accept 1 argument (the event that generated the original menu) and
        return a single QMenu or a list of QMenus.
        
        The final menu will look like:
        
            |    Original Item 1
            |    Original Item 2
            |    ...
            |    Original Item N
            |    ------------------
            |    Parent Item 1
            |    Parent Item 2
            |    ...
            |    Grandparent Item 1
            |    ...
            
        
        ==============  ==================================================
        **Arguments:**
        item            The item that initially created the context menu 
                        (This is probably the item making the call to this function)
        menu            The context menu being shown by the item
        event           The original event that triggered the menu to appear.
        ==============  ==================================================
        """
        
        #items = self.itemsNearEvent(ev)
        menusToAdd = []
        while item is not self:
            item = item.parentItem()
            
            if item is None:
                item = self
                
            if not hasattr(item, "getContextMenus"):
                continue
            
            subMenus = item.getContextMenus(event)
            if subMenus is None:
                continue
            if type(subMenus) is not list: ## so that some items (like FlowchartViewBox) can return multiple menus
                subMenus = [subMenus]
            
            for sm in subMenus:
                menusToAdd.append(sm)
        
        if len(menusToAdd) > 0:
            menu.addSeparator()
            
        for m in menusToAdd:
            if isinstance(m, QtGui.QMenu):
                menu.addMenu(m)
            elif isinstance(m, QtGui.QAction):
                menu.addAction(m)
            else:
                raise Exception("Cannot add object %s (type=%s) to QMenu." % (str(m), str(type(m))))
            
        return menu

    def getContextMenus(self, event):
        self.contextMenuItem = event.acceptedItem
        return self.contextMenu

    def showExportDialog(self):
        if self.exportDialog is None:
            self.exportDialog = exportDialog.ExportDialog(self)
        self.exportDialog.show(self.contextMenuItem)

    @staticmethod
    def translateGraphicsItem(item):
        ## for fixing pyqt bugs where the wrong item is returned
        if HAVE_SIP and isinstance(item, sip.wrapper):
            addr = sip.unwrapinstance(sip.cast(item, QtGui.QGraphicsItem))
            item = GraphicsScene._addressCache.get(addr, item)
        return item

    @staticmethod
    def translateGraphicsItems(items):
        return list(map(GraphicsScene.translateGraphicsItem, items))



