from ..Qt import QtGui, QtCore
from ..Point import Point


class GraphicsWidgetAnchor(object):
    """
    Class used to allow GraphicsWidgets to anchor to a specific position on their
    parent. The item will be automatically repositioned if the parent is resized. 
    This is used, for example, to anchor a LegendItem to a corner of its parent 
    PlotItem.

    """

    def __init__(self):
        self.__parent = None
        self.__parentAnchor = None
        self.__itemAnchor = None
        self.__offset = (0,0)
        if hasattr(self, 'geometryChanged'):
            self.geometryChanged.connect(self.__geometryChanged)

    def anchor(self, itemPos, parentPos, offset=(0,0)):
        """
        Anchors the item at its local itemPos to the item's parent at parentPos.
        Both positions are expressed in values relative to the size of the item or parent;
        a value of 0 indicates left or top edge, while 1 indicates right or bottom edge.
        
        Optionally, offset may be specified to introduce an absolute offset. 
        
        Example: anchor a box such that its upper-right corner is fixed 10px left
        and 10px down from its parent's upper-right corner::
        
            box.anchor(itemPos=(1,0), parentPos=(1,0), offset=(-10,10))
        """
        parent = self.parentItem()
        if parent is None:
            raise Exception("Cannot anchor; parent is not set.")
        
        if self.__parent is not parent:
            if self.__parent is not None:
                self.__parent.geometryChanged.disconnect(self.__geometryChanged)
                
            self.__parent = parent
            parent.geometryChanged.connect(self.__geometryChanged)
        
        self.__itemAnchor = itemPos
        self.__parentAnchor = parentPos
        self.__offset = offset
        self.__geometryChanged()
    

    def autoAnchor(self, pos, relative=True):
        """
        Set the position of this item relative to its parent by automatically 
        choosing appropriate anchor settings.
        
        If relative is True, one corner of the item will be anchored to 
        the appropriate location on the parent with no offset. The anchored
        corner will be whichever is closest to the parent's boundary.
        
        If relative is False, one corner of the item will be anchored to the same
        corner of the parent, with an absolute offset to achieve the correct
        position. 
        """
        pos = Point(pos)
        br = self.mapRectToParent(self.boundingRect()).translated(pos - self.pos())
        pbr = self.parentItem().boundingRect()
        anchorPos = [0,0]
        parentPos = Point()
        itemPos = Point()
        if abs(br.left() - pbr.left()) < abs(br.right() - pbr.right()):
            anchorPos[0] = 0
            parentPos[0] = pbr.left()
            itemPos[0] = br.left()
        else:
            anchorPos[0] = 1
            parentPos[0] = pbr.right()
            itemPos[0] = br.right()

        if abs(br.top() - pbr.top()) < abs(br.bottom() - pbr.bottom()):
            anchorPos[1] = 0
            parentPos[1] = pbr.top()
            itemPos[1] = br.top()
        else:
            anchorPos[1] = 1
            parentPos[1] = pbr.bottom()
            itemPos[1] = br.bottom()
        
        if relative:
            relPos = [(itemPos[0]-pbr.left()) / pbr.width(), (itemPos[1]-pbr.top()) / pbr.height()]
            self.anchor(anchorPos, relPos)
        else:
            offset = itemPos - parentPos
            self.anchor(anchorPos, anchorPos, offset)
    
    def __geometryChanged(self):
        if self.__parent is None:
            return
        if self.__itemAnchor is None:
            return
            
        o = self.mapToParent(Point(0,0))
        a = self.boundingRect().bottomRight() * Point(self.__itemAnchor)
        a = self.mapToParent(a)
        p = self.__parent.boundingRect().bottomRight() * Point(self.__parentAnchor)
        off = Point(self.__offset)
        pos = p + (o-a) + off
        self.setPos(pos)
        
        