from pyqtgraph.Qt import QtGui, QtCore  
from pyqtgraph.GraphicsScene import GraphicsScene
from pyqtgraph.Point import Point
import pyqtgraph.functions as fn
import weakref
from pyqtgraph.pgcollections import OrderedDict
import operator, sys

class FiniteCache(OrderedDict):
    """Caches a finite number of objects, removing
    least-frequently used items."""
    def __init__(self, length):
        self._length = length
        OrderedDict.__init__(self)
        
    def __setitem__(self, item, val):
        self.pop(item, None) # make sure item is added to end
        OrderedDict.__setitem__(self, item, val) 
        while len(self) > self._length:
            del self[list(self.keys())[0]]
        
    def __getitem__(self, item):
        val = OrderedDict.__getitem__(self, item)
        del self[item]
        self[item] = val  ## promote this key        
        return val
        
        

class GraphicsItem(object):
    """
    **Bases:** :class:`object`

    Abstract class providing useful methods to GraphicsObject and GraphicsWidget.
    (This is required because we cannot have multiple inheritance with QObject subclasses.)

    A note about Qt's GraphicsView framework:

    The GraphicsView system places a lot of emphasis on the notion that the graphics within the scene should be device independent--you should be able to take the same graphics and display them on screens of different resolutions, printers, export to SVG, etc. This is nice in principle, but causes me a lot of headache in practice. It means that I have to circumvent all the device-independent expectations any time I want to operate in pixel coordinates rather than arbitrary scene coordinates. A lot of the code in GraphicsItem is devoted to this task--keeping track of view widgets and device transforms, computing the size and shape of a pixel in local item coordinates, etc. Note that in item coordinates, a pixel does not have to be square or even rectangular, so just asking how to increase a bounding rect by 2px can be a rather complex task.
    """
    _pixelVectorGlobalCache = FiniteCache(100)
    
    def __init__(self, register=True):
        if not hasattr(self, '_qtBaseClass'):
            for b in self.__class__.__bases__:
                if issubclass(b, QtGui.QGraphicsItem):
                    self.__class__._qtBaseClass = b
                    break
        if not hasattr(self, '_qtBaseClass'):
            raise Exception('Could not determine Qt base class for GraphicsItem: %s' % str(self))
        
        self._pixelVectorCache = [None, None]
        self._viewWidget = None
        self._viewBox = None
        self._connectedView = None
        self._exportOpts = False   ## If False, not currently exporting. Otherwise, contains dict of export options.
        if register:
            GraphicsScene.registerObject(self)  ## workaround for pyqt bug in graphicsscene.items()
                    

                    
                    
    def getViewWidget(self):
        """
        Return the view widget for this item. If the scene has multiple views, only the first view is returned.
        The return value is cached; clear the cached value with forgetViewWidget()
        """
        if self._viewWidget is None:
            scene = self.scene()
            if scene is None:
                return None
            views = scene.views()
            if len(views) < 1:
                return None
            self._viewWidget = weakref.ref(self.scene().views()[0])
        return self._viewWidget()
    
    def forgetViewWidget(self):
        self._viewWidget = None
    
    def getViewBox(self):
        """
        Return the first ViewBox or GraphicsView which bounds this item's visible space.
        If this item is not contained within a ViewBox, then the GraphicsView is returned.
        If the item is contained inside nested ViewBoxes, then the inner-most ViewBox is returned.
        The result is cached; clear the cache with forgetViewBox()
        """
        if self._viewBox is None:
            p = self
            while True:
                try:
                    p = p.parentItem()
                except RuntimeError:  ## sometimes happens as items are being removed from a scene and collected.
                    return None
                if p is None:
                    vb = self.getViewWidget()
                    if vb is None:
                        return None
                    else:
                        self._viewBox = weakref.ref(vb)
                        break
                if hasattr(p, 'implements') and p.implements('ViewBox'):
                    self._viewBox = weakref.ref(p)
                    break
        return self._viewBox()  ## If we made it this far, _viewBox is definitely not None

    def forgetViewBox(self):
        self._viewBox = None
        
        
    def deviceTransform(self, viewportTransform=None):
        """
        Return the transform that converts local item coordinates to device coordinates (usually pixels).
        Extends deviceTransform to automatically determine the viewportTransform.
        """
        if self._exportOpts is not False and 'painter' in self._exportOpts: ## currently exporting; device transform may be different.
            return self._exportOpts['painter'].deviceTransform()
            
        if viewportTransform is None:
            view = self.getViewWidget()
            if view is None:
                return None
            viewportTransform = view.viewportTransform()
        dt = self._qtBaseClass.deviceTransform(self, viewportTransform)
        
        #xmag = abs(dt.m11())+abs(dt.m12())
        #ymag = abs(dt.m21())+abs(dt.m22())
        #if xmag * ymag == 0: 
        if dt.determinant() == 0:  ## occurs when deviceTransform is invalid because widget has not been displayed
            return None
        else:
            return dt
        
    def viewTransform(self):
        """Return the transform that maps from local coordinates to the item's ViewBox coordinates
        If there is no ViewBox, return the scene transform.
        Returns None if the item does not have a view."""
        view = self.getViewBox()
        if view is None:
            return None
        if hasattr(view, 'implements') and view.implements('ViewBox'):
            tr = self.itemTransform(view.innerSceneItem())
            if isinstance(tr, tuple):
                tr = tr[0]   ## difference between pyside and pyqt
            return tr
        else:
            return self.sceneTransform()
            #return self.deviceTransform(view.viewportTransform())



    def getBoundingParents(self):
        """Return a list of parents to this item that have child clipping enabled."""
        p = self
        parents = []
        while True:
            p = p.parentItem()
            if p is None:
                break
            if p.flags() & self.ItemClipsChildrenToShape:
                parents.append(p)
        return parents
    
    def viewRect(self):
        """Return the bounds (in item coordinates) of this item's ViewBox or GraphicsWidget"""
        view = self.getViewBox()
        if view is None:
            return None
        bounds = self.mapRectFromView(view.viewRect())
        if bounds is None:
            return None

        bounds = bounds.normalized()
        
        ## nah.
        #for p in self.getBoundingParents():
            #bounds &= self.mapRectFromScene(p.sceneBoundingRect())
            
        return bounds
        
        
        
    def pixelVectors(self, direction=None):
        """Return vectors in local coordinates representing the width and height of a view pixel.
        If direction is specified, then return vectors parallel and orthogonal to it.
        
        Return (None, None) if pixel size is not yet defined (usually because the item has not yet been displayed)
        or if pixel size is below floating-point precision limit.
        """
        
        ## This is an expensive function that gets called very frequently.
        ## We have two levels of cache to try speeding things up.
        
        dt = self.deviceTransform()
        if dt is None:
            return None, None
            
        ## Ignore translation. If the translation is much larger than the scale
        ## (such as when looking at unix timestamps), we can get floating-point errors.
        dt.setMatrix(dt.m11(), dt.m12(), 0, dt.m21(), dt.m22(), 0, 0, 0, 1)
        
        ## check local cache
        if direction is None and dt == self._pixelVectorCache[0]:
            return tuple(map(Point, self._pixelVectorCache[1]))  ## return a *copy*
        
        ## check global cache
        #key = (dt.m11(), dt.m21(), dt.m31(), dt.m12(), dt.m22(), dt.m32(), dt.m31(), dt.m32())
        key = (dt.m11(), dt.m21(), dt.m12(), dt.m22())
        pv = self._pixelVectorGlobalCache.get(key, None)
        if direction is None and pv is not None:
            self._pixelVectorCache = [dt, pv]
            return tuple(map(Point,pv))  ## return a *copy*
        
        
        if direction is None:
            direction = QtCore.QPointF(1, 0)  
        if direction.manhattanLength() == 0:
            raise Exception("Cannot compute pixel length for 0-length vector.")
            
        ## attempt to re-scale direction vector to fit within the precision of the coordinate system
        ## Here's the problem: we need to map the vector 'direction' from the item to the device, via transform 'dt'.
        ## In some extreme cases, this mapping can fail unless the length of 'direction' is cleverly chosen.
        ## Example:
        ##   dt = [ 1, 0,    2 
        ##          0, 2, 1e20
        ##          0, 0,    1 ]
        ## Then we map the origin (0,0) and direction (0,1) and get:
        ##    o' = 2,1e20
        ##    d' = 2,1e20  <-- should be 1e20+2, but this can't be represented with a 32-bit float
        ##    
        ##    |o' - d'|  == 0    <-- this is the problem.
        
        ## Perhaps the easiest solution is to exclude the transformation column from dt. Does this cause any other problems?
        
        #if direction.x() == 0:
            #r = abs(dt.m32())/(abs(dt.m12()) + abs(dt.m22()))
            ##r = 1.0/(abs(dt.m12()) + abs(dt.m22()))
        #elif direction.y() == 0:
            #r = abs(dt.m31())/(abs(dt.m11()) + abs(dt.m21()))
            ##r = 1.0/(abs(dt.m11()) + abs(dt.m21()))
        #else:
            #r = ((abs(dt.m32())/(abs(dt.m12()) + abs(dt.m22()))) * (abs(dt.m31())/(abs(dt.m11()) + abs(dt.m21()))))**0.5
        #if r == 0:
            #r = 1.  ## shouldn't need to do this; probably means the math above is wrong?
        #directionr = direction * r
        directionr = direction
        
        ## map direction vector onto device
        #viewDir = Point(dt.map(directionr) - dt.map(Point(0,0)))
        #mdirection = dt.map(directionr)
        dirLine = QtCore.QLineF(QtCore.QPointF(0,0), directionr)
        viewDir = dt.map(dirLine)
        if viewDir.length() == 0:
            return None, None   ##  pixel size cannot be represented on this scale
           
        ## get unit vector and orthogonal vector (length of pixel)
        #orthoDir = Point(viewDir[1], -viewDir[0])  ## orthogonal to line in pixel-space
        try:  
            normView = viewDir.unitVector()
            #normView = viewDir.norm()  ## direction of one pixel orthogonal to line
            normOrtho = normView.normalVector()
            #normOrtho = orthoDir.norm()
        except:
            raise Exception("Invalid direction %s" %directionr)
            
        ## map back to item 
        dti = fn.invertQTransform(dt)
        #pv = Point(dti.map(normView)-dti.map(Point(0,0))), Point(dti.map(normOrtho)-dti.map(Point(0,0)))
        pv = Point(dti.map(normView).p2()), Point(dti.map(normOrtho).p2())
        self._pixelVectorCache[1] = pv
        self._pixelVectorCache[0] = dt
        self._pixelVectorGlobalCache[key] = pv
        return self._pixelVectorCache[1]
    
        
    def pixelLength(self, direction, ortho=False):
        """Return the length of one pixel in the direction indicated (in local coordinates)
        If ortho=True, then return the length of one pixel orthogonal to the direction indicated.
        
        Return None if pixel size is not yet defined (usually because the item has not yet been displayed).
        """
        normV, orthoV = self.pixelVectors(direction)
        if normV == None or orthoV == None:
            return None
        if ortho:
            return orthoV.length()
        return normV.length()
        

    def pixelSize(self):
        ## deprecated
        v = self.pixelVectors()
        if v == (None, None):
            return None, None
        return (v[0].x()**2+v[0].y()**2)**0.5, (v[1].x()**2+v[1].y()**2)**0.5

    def pixelWidth(self):
        ## deprecated
        vt = self.deviceTransform()
        if vt is None:
            return 0
        vt = fn.invertQTransform(vt)
        return vt.map(QtCore.QLineF(0, 0, 1, 0)).length()
        
    def pixelHeight(self):
        ## deprecated
        vt = self.deviceTransform()
        if vt is None:
            return 0
        vt = fn.invertQTransform(vt)
        return vt.map(QtCore.QLineF(0, 0, 0, 1)).length()
        #return Point(vt.map(QtCore.QPointF(0, 1))-vt.map(QtCore.QPointF(0, 0))).length()
        
        
    def mapToDevice(self, obj):
        """
        Return *obj* mapped from local coordinates to device coordinates (pixels).
        If there is no device mapping available, return None.
        """
        vt = self.deviceTransform()
        if vt is None:
            return None
        return vt.map(obj)
        
    def mapFromDevice(self, obj):
        """
        Return *obj* mapped from device coordinates (pixels) to local coordinates.
        If there is no device mapping available, return None.
        """
        vt = self.deviceTransform()
        if vt is None:
            return None
        vt = fn.invertQTransform(vt)
        return vt.map(obj)

    def mapRectToDevice(self, rect):
        """
        Return *rect* mapped from local coordinates to device coordinates (pixels).
        If there is no device mapping available, return None.
        """
        vt = self.deviceTransform()
        if vt is None:
            return None
        return vt.mapRect(rect)

    def mapRectFromDevice(self, rect):
        """
        Return *rect* mapped from device coordinates (pixels) to local coordinates.
        If there is no device mapping available, return None.
        """
        vt = self.deviceTransform()
        if vt is None:
            return None
        vt = fn.invertQTransform(vt)
        return vt.mapRect(rect)
    
    def mapToView(self, obj):
        vt = self.viewTransform()
        if vt is None:
            return None
        return vt.map(obj)
        
    def mapRectToView(self, obj):
        vt = self.viewTransform()
        if vt is None:
            return None
        return vt.mapRect(obj)
        
    def mapFromView(self, obj):
        vt = self.viewTransform()
        if vt is None:
            return None
        vt = fn.invertQTransform(vt)
        return vt.map(obj)

    def mapRectFromView(self, obj):
        vt = self.viewTransform()
        if vt is None:
            return None
        vt = fn.invertQTransform(vt)
        return vt.mapRect(obj)

    def pos(self):
        return Point(self._qtBaseClass.pos(self))
    
    def viewPos(self):
        return self.mapToView(self.mapFromParent(self.pos()))
    
    def parentItem(self):
        ## PyQt bug -- some items are returned incorrectly.
        return GraphicsScene.translateGraphicsItem(self._qtBaseClass.parentItem(self))
        
    def setParentItem(self, parent):
        ## Workaround for Qt bug: https://bugreports.qt-project.org/browse/QTBUG-18616
        if parent is not None:
            pscene = parent.scene()
            if pscene is not None and self.scene() is not pscene:
                pscene.addItem(self)
        return self._qtBaseClass.setParentItem(self, parent)
    
    def childItems(self):
        ## PyQt bug -- some child items are returned incorrectly.
        return list(map(GraphicsScene.translateGraphicsItem, self._qtBaseClass.childItems(self)))


    def sceneTransform(self):
        ## Qt bug: do no allow access to sceneTransform() until 
        ## the item has a scene.
        
        if self.scene() is None:
            return self.transform()
        else:
            return self._qtBaseClass.sceneTransform(self)


    def transformAngle(self, relativeItem=None):
        """Return the rotation produced by this item's transform (this assumes there is no shear in the transform)
        If relativeItem is given, then the angle is determined relative to that item.
        """
        if relativeItem is None:
            relativeItem = self.parentItem()
            

        tr = self.itemTransform(relativeItem)
        if isinstance(tr, tuple):  ## difference between pyside and pyqt
            tr = tr[0]
        #vec = tr.map(Point(1,0)) - tr.map(Point(0,0))
        vec = tr.map(QtCore.QLineF(0,0,1,0))
        #return Point(vec).angle(Point(1,0))
        return vec.angleTo(QtCore.QLineF(vec.p1(), vec.p1()+QtCore.QPointF(1,0)))
        
    #def itemChange(self, change, value):
        #ret = self._qtBaseClass.itemChange(self, change, value)
        #if change == self.ItemParentHasChanged or change == self.ItemSceneHasChanged:
            #print "Item scene changed:", self
            #self.setChildScene(self)  ## This is bizarre.
        #return ret

    #def setChildScene(self, ch):
        #scene = self.scene()
        #for ch2 in ch.childItems():
            #if ch2.scene() is not scene:
                #print "item", ch2, "has different scene:", ch2.scene(), scene
                #scene.addItem(ch2)
                #QtGui.QApplication.processEvents()
                #print "   --> ", ch2.scene()
            #self.setChildScene(ch2)

    def parentChanged(self):
        """Called when the item's parent has changed. 
        This method handles connecting / disconnecting from ViewBox signals
        to make sure viewRangeChanged works properly. It should generally be 
        extended, not overridden."""
        self._updateView()
        

    def _updateView(self):
        ## called to see whether this item has a new view to connect to
        ## NOTE: This is called from GraphicsObject.itemChange or GraphicsWidget.itemChange.

        ## It is possible this item has moved to a different ViewBox or widget;
        ## clear out previously determined references to these.
        self.forgetViewBox()
        self.forgetViewWidget()
        
        ## check for this item's current viewbox or view widget
        view = self.getViewBox()
        #if view is None:
            ##print "  no view"
            #return

        oldView = None
        if self._connectedView is not None:
            oldView = self._connectedView()
            
        if view is oldView:
            #print "  already have view", view
            return

        ## disconnect from previous view
        if oldView is not None:
            #print "disconnect:", self, oldView
            try:
                oldView.sigRangeChanged.disconnect(self.viewRangeChanged)
            except TypeError:
                pass
            
            try:
                oldView.sigTransformChanged.disconnect(self.viewTransformChanged)
            except TypeError:
                pass
            
            self._connectedView = None

        ## connect to new view
        if view is not None:
            #print "connect:", self, view
            view.sigRangeChanged.connect(self.viewRangeChanged)
            view.sigTransformChanged.connect(self.viewTransformChanged)
            self._connectedView = weakref.ref(view)
            self.viewRangeChanged()
            self.viewTransformChanged()
        
        ## inform children that their view might have changed
        self._replaceView(oldView)
        
        self.viewChanged(view, oldView)
        
    def viewChanged(self, view, oldView):
        """Called when this item's view has changed
        (ie, the item has been added to or removed from a ViewBox)"""
        pass
        
    def _replaceView(self, oldView, item=None):
        if item is None:
            item = self
        for child in item.childItems():
            if isinstance(child, GraphicsItem):
                if child.getViewBox() is oldView:
                    child._updateView()
                        #self._replaceView(oldView, child)
            else:
                self._replaceView(oldView, child)
        
        

    def viewRangeChanged(self):
        """
        Called whenever the view coordinates of the ViewBox containing this item have changed.
        """
        pass
    
    def viewTransformChanged(self):
        """
        Called whenever the transformation matrix of the view has changed.
        (eg, the view range has changed or the view was resized)
        """
        pass
    
    #def prepareGeometryChange(self):
        #self._qtBaseClass.prepareGeometryChange(self)
        #self.informViewBoundsChanged()
        
    def informViewBoundsChanged(self):
        """
        Inform this item's container ViewBox that the bounds of this item have changed.
        This is used by ViewBox to react if auto-range is enabled.
        """
        view = self.getViewBox()
        if view is not None and hasattr(view, 'implements') and view.implements('ViewBox'):
            view.itemBoundsChanged(self)  ## inform view so it can update its range if it wants
    
    def childrenShape(self):
        """Return the union of the shapes of all descendants of this item in local coordinates."""
        childs = self.allChildItems()
        shapes = [self.mapFromItem(c, c.shape()) for c in self.allChildItems()]
        return reduce(operator.add, shapes)
    
    def allChildItems(self, root=None):
        """Return list of the entire item tree descending from this item."""
        if root is None:
            root = self
        tree = []
        for ch in root.childItems():
            tree.append(ch)
            tree.extend(self.allChildItems(ch))
        return tree
    
    
    def setExportMode(self, export, opts=None):
        """
        This method is called by exporters to inform items that they are being drawn for export
        with a specific set of options. Items access these via self._exportOptions.
        When exporting is complete, _exportOptions is set to False.
        """
        if opts is None:
            opts = {}
        if export:
            self._exportOpts = opts
            #if 'antialias' not in opts:
                #self._exportOpts['antialias'] = True
        else:
            self._exportOpts = False
    
    #def update(self):
        #self._qtBaseClass.update(self)
        #print "Update:", self
