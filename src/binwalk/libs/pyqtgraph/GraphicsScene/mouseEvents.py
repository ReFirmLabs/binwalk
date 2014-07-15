from pyqtgraph.Point import Point
from pyqtgraph.Qt import QtCore, QtGui
import weakref
import pyqtgraph.ptime as ptime

class MouseDragEvent(object):
    """
    Instances of this class are delivered to items in a :class:`GraphicsScene <pyqtgraph.GraphicsScene>` via their mouseDragEvent() method when the item is being mouse-dragged. 
    
    """
    
    
    
    def __init__(self, moveEvent, pressEvent, lastEvent, start=False, finish=False):
        self.start = start
        self.finish = finish
        self.accepted = False
        self.currentItem = None
        self._buttonDownScenePos = {}
        self._buttonDownScreenPos = {}
        for btn in [QtCore.Qt.LeftButton, QtCore.Qt.MidButton, QtCore.Qt.RightButton]:
            self._buttonDownScenePos[int(btn)] = moveEvent.buttonDownScenePos(btn)
            self._buttonDownScreenPos[int(btn)] = moveEvent.buttonDownScreenPos(btn)
        self._scenePos = moveEvent.scenePos()
        self._screenPos = moveEvent.screenPos()
        if lastEvent is None:
            self._lastScenePos = pressEvent.scenePos()
            self._lastScreenPos = pressEvent.screenPos()
        else:
            self._lastScenePos = lastEvent.scenePos()
            self._lastScreenPos = lastEvent.screenPos()
        self._buttons = moveEvent.buttons()
        self._button = pressEvent.button()
        self._modifiers = moveEvent.modifiers()
        self.acceptedItem = None
        
    def accept(self):
        """An item should call this method if it can handle the event. This will prevent the event being delivered to any other items."""
        self.accepted = True
        self.acceptedItem = self.currentItem
        
    def ignore(self):
        """An item should call this method if it cannot handle the event. This will allow the event to be delivered to other items."""
        self.accepted = False
    
    def isAccepted(self):
        return self.accepted
    
    def scenePos(self):
        """Return the current scene position of the mouse."""
        return Point(self._scenePos)
    
    def screenPos(self):
        """Return the current screen position (pixels relative to widget) of the mouse."""
        return Point(self._screenPos)
    
    def buttonDownScenePos(self, btn=None):
        """
        Return the scene position of the mouse at the time *btn* was pressed.
        If *btn* is omitted, then the button that initiated the drag is assumed.
        """
        if btn is None:
            btn = self.button()
        return Point(self._buttonDownScenePos[int(btn)])
    
    def buttonDownScreenPos(self, btn=None):
        """
        Return the screen position (pixels relative to widget) of the mouse at the time *btn* was pressed.
        If *btn* is omitted, then the button that initiated the drag is assumed.
        """
        if btn is None:
            btn = self.button()
        return Point(self._buttonDownScreenPos[int(btn)])
    
    def lastScenePos(self):
        """
        Return the scene position of the mouse immediately prior to this event.
        """
        return Point(self._lastScenePos)
    
    def lastScreenPos(self):
        """
        Return the screen position of the mouse immediately prior to this event.
        """
        return Point(self._lastScreenPos)
    
    def buttons(self):
        """
        Return the buttons currently pressed on the mouse.
        (see QGraphicsSceneMouseEvent::buttons in the Qt documentation)
        """
        return self._buttons
        
    def button(self):
        """Return the button that initiated the drag (may be different from the buttons currently pressed)
        (see QGraphicsSceneMouseEvent::button in the Qt documentation)
        
        """
        return self._button
        
    def pos(self):
        """
        Return the current position of the mouse in the coordinate system of the item
        that the event was delivered to.
        """
        return Point(self.currentItem.mapFromScene(self._scenePos))
    
    def lastPos(self):
        """
        Return the previous position of the mouse in the coordinate system of the item
        that the event was delivered to.
        """
        return Point(self.currentItem.mapFromScene(self._lastScenePos))
        
    def buttonDownPos(self, btn=None):
        """
        Return the position of the mouse at the time the drag was initiated
        in the coordinate system of the item that the event was delivered to.
        """
        if btn is None:
            btn = self.button()
        return Point(self.currentItem.mapFromScene(self._buttonDownScenePos[int(btn)]))
    
    def isStart(self):
        """Returns True if this event is the first since a drag was initiated."""
        return self.start
        
    def isFinish(self):
        """Returns False if this is the last event in a drag. Note that this
        event will have the same position as the previous one."""
        return self.finish

    def __repr__(self):
        lp = self.lastPos()
        p = self.pos()
        return "<MouseDragEvent (%g,%g)->(%g,%g) buttons=%d start=%s finish=%s>" % (lp.x(), lp.y(), p.x(), p.y(), int(self.buttons()), str(self.isStart()), str(self.isFinish()))
        
    def modifiers(self):
        """Return any keyboard modifiers currently pressed.
        (see QGraphicsSceneMouseEvent::modifiers in the Qt documentation)
        
        """
        return self._modifiers



class MouseClickEvent(object):
    """
    Instances of this class are delivered to items in a :class:`GraphicsScene <pyqtgraph.GraphicsScene>` via their mouseClickEvent() method when the item is clicked. 
    
    
    """
    
    def __init__(self, pressEvent, double=False):
        self.accepted = False
        self.currentItem = None
        self._double = double
        self._scenePos = pressEvent.scenePos()
        self._screenPos = pressEvent.screenPos()
        self._button = pressEvent.button()
        self._buttons = pressEvent.buttons()
        self._modifiers = pressEvent.modifiers()
        self._time = ptime.time()
        self.acceptedItem = None
        
    def accept(self):
        """An item should call this method if it can handle the event. This will prevent the event being delivered to any other items."""
        self.accepted = True
        self.acceptedItem = self.currentItem
        
    def ignore(self):
        """An item should call this method if it cannot handle the event. This will allow the event to be delivered to other items."""
        self.accepted = False
    
    def isAccepted(self):
        return self.accepted
    
    def scenePos(self):
        """Return the current scene position of the mouse."""
        return Point(self._scenePos)
    
    def screenPos(self):
        """Return the current screen position (pixels relative to widget) of the mouse."""
        return Point(self._screenPos)
    
    def buttons(self):
        """
        Return the buttons currently pressed on the mouse.
        (see QGraphicsSceneMouseEvent::buttons in the Qt documentation)
        """
        return self._buttons
    
    def button(self):
        """Return the mouse button that generated the click event.
        (see QGraphicsSceneMouseEvent::button in the Qt documentation)
        """
        return self._button
    
    def double(self):
        """Return True if this is a double-click."""
        return self._double

    def pos(self):
        """
        Return the current position of the mouse in the coordinate system of the item
        that the event was delivered to.
        """
        return Point(self.currentItem.mapFromScene(self._scenePos))
    
    def lastPos(self):
        """
        Return the previous position of the mouse in the coordinate system of the item
        that the event was delivered to.
        """
        return Point(self.currentItem.mapFromScene(self._lastScenePos))
        
    def modifiers(self):
        """Return any keyboard modifiers currently pressed.
        (see QGraphicsSceneMouseEvent::modifiers in the Qt documentation)        
        """
        return self._modifiers

    def __repr__(self):
        p = self.pos()
        return "<MouseClickEvent (%g,%g) button=%d>" % (p.x(), p.y(), int(self.button()))
        
    def time(self):
        return self._time



class HoverEvent(object):
    """
    Instances of this class are delivered to items in a :class:`GraphicsScene <pyqtgraph.GraphicsScene>` via their hoverEvent() method when the mouse is hovering over the item.
    This event class both informs items that the mouse cursor is nearby and allows items to 
    communicate with one another about whether each item will accept *potential* mouse events. 
    
    It is common for multiple overlapping items to receive hover events and respond by changing 
    their appearance. This can be misleading to the user since, in general, only one item will
    respond to mouse events. To avoid this, items make calls to event.acceptClicks(button) 
    and/or acceptDrags(button).
    
    Each item may make multiple calls to acceptClicks/Drags, each time for a different button. 
    If the method returns True, then the item is guaranteed to be
    the recipient of the claimed event IF the user presses the specified mouse button before
    moving. If claimEvent returns False, then this item is guaranteed NOT to get the specified
    event (because another has already claimed it) and the item should change its appearance 
    accordingly.
    
    event.isEnter() returns True if the mouse has just entered the item's shape;
    event.isExit() returns True if the mouse has just left.
    """
    def __init__(self, moveEvent, acceptable):
        self.enter = False
        self.acceptable = acceptable
        self.exit = False
        self.__clickItems = weakref.WeakValueDictionary()
        self.__dragItems = weakref.WeakValueDictionary()
        self.currentItem = None
        if moveEvent is not None:
            self._scenePos = moveEvent.scenePos()
            self._screenPos = moveEvent.screenPos()
            self._lastScenePos = moveEvent.lastScenePos()
            self._lastScreenPos = moveEvent.lastScreenPos()
            self._buttons = moveEvent.buttons()
            self._modifiers = moveEvent.modifiers()
        else:
            self.exit = True
            
        
        
    def isEnter(self):
        """Returns True if the mouse has just entered the item's shape"""
        return self.enter
        
    def isExit(self):
        """Returns True if the mouse has just exited the item's shape"""
        return self.exit
        
    def acceptClicks(self, button):
        """Inform the scene that the item (that the event was delivered to)
        would accept a mouse click event if the user were to click before
        moving the mouse again.
        
        Returns True if the request is successful, otherwise returns False (indicating
        that some other item would receive an incoming click).
        """
        if not self.acceptable:
            return False
        if button not in self.__clickItems:
            self.__clickItems[button] = self.currentItem
            return True
        return False
        
    def acceptDrags(self, button):
        """Inform the scene that the item (that the event was delivered to)
        would accept a mouse drag event if the user were to drag before
        the next hover event.
        
        Returns True if the request is successful, otherwise returns False (indicating
        that some other item would receive an incoming drag event).
        """
        if not self.acceptable:
            return False
        if button not in self.__dragItems:
            self.__dragItems[button] = self.currentItem
            return True
        return False
        
    def scenePos(self):
        """Return the current scene position of the mouse."""
        return Point(self._scenePos)
    
    def screenPos(self):
        """Return the current screen position of the mouse."""
        return Point(self._screenPos)
    
    def lastScenePos(self):
        """Return the previous scene position of the mouse."""
        return Point(self._lastScenePos)
    
    def lastScreenPos(self):
        """Return the previous screen position of the mouse."""
        return Point(self._lastScreenPos)
    
    def buttons(self):
        """
        Return the buttons currently pressed on the mouse.
        (see QGraphicsSceneMouseEvent::buttons in the Qt documentation)
        """
        return self._buttons
        
    def pos(self):
        """
        Return the current position of the mouse in the coordinate system of the item
        that the event was delivered to.
        """
        return Point(self.currentItem.mapFromScene(self._scenePos))
    
    def lastPos(self):
        """
        Return the previous position of the mouse in the coordinate system of the item
        that the event was delivered to.
        """
        return Point(self.currentItem.mapFromScene(self._lastScenePos))

    def __repr__(self):
        lp = self.lastPos()
        p = self.pos()
        return "<HoverEvent (%g,%g)->(%g,%g) buttons=%d enter=%s exit=%s>" % (lp.x(), lp.y(), p.x(), p.y(), int(self.buttons()), str(self.isEnter()), str(self.isExit()))
        
    def modifiers(self):
        """Return any keyboard modifiers currently pressed.
        (see QGraphicsSceneMouseEvent::modifiers in the Qt documentation)        
        """
        return self._modifiers
    
    def clickItems(self):
        return self.__clickItems
        
    def dragItems(self):
        return self.__dragItems
        
    
    