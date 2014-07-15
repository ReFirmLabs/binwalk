from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph import Transform3D
from OpenGL.GL import *
from OpenGL import GL

GLOptions = {
    'opaque': {
        GL_DEPTH_TEST: True,
        GL_BLEND: False,
        GL_ALPHA_TEST: False,
        GL_CULL_FACE: False,
    },
    'translucent': {
        GL_DEPTH_TEST: True,
        GL_BLEND: True,
        GL_ALPHA_TEST: False,
        GL_CULL_FACE: False,
        'glBlendFunc': (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA),
    },
    'additive': {
        GL_DEPTH_TEST: False,
        GL_BLEND: True,
        GL_ALPHA_TEST: False,
        GL_CULL_FACE: False,
        'glBlendFunc': (GL_SRC_ALPHA, GL_ONE),
    },
}    


class GLGraphicsItem(QtCore.QObject):
    def __init__(self, parentItem=None):
        QtCore.QObject.__init__(self)
        self.__parent = None
        self.__view = None
        self.__children = set()
        self.__transform = Transform3D()
        self.__visible = True
        self.setParentItem(parentItem)
        self.setDepthValue(0)
        self.__glOpts = {}
        
    def setParentItem(self, item):
        """Set this item's parent in the scenegraph hierarchy."""
        if self.__parent is not None:
            self.__parent.__children.remove(self)
        if item is not None:
            item.__children.add(self)
        self.__parent = item
        
        if self.__parent is not None and self.view() is not self.__parent.view():
            if self.view() is not None:
                self.view().removeItem(self)
            self.__parent.view().addItem(self)
    
    def setGLOptions(self, opts):
        """
        Set the OpenGL state options to use immediately before drawing this item.
        (Note that subclasses must call setupGLState before painting for this to work)
        
        The simplest way to invoke this method is to pass in the name of
        a predefined set of options (see the GLOptions variable):
        
        ============= ======================================================
        opaque        Enables depth testing and disables blending
        translucent   Enables depth testing and blending
                      Elements must be drawn sorted back-to-front for
                      translucency to work correctly.
        additive      Disables depth testing, enables blending.
                      Colors are added together, so sorting is not required.
        ============= ======================================================
        
        It is also possible to specify any arbitrary settings as a dictionary. 
        This may consist of {'functionName': (args...)} pairs where functionName must 
        be a callable attribute of OpenGL.GL, or {GL_STATE_VAR: bool} pairs 
        which will be interpreted as calls to glEnable or glDisable(GL_STATE_VAR).
        
        For example::
            
            {
                GL_ALPHA_TEST: True,
                GL_CULL_FACE: False,
                'glBlendFunc': (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA),
            }
            
        
        """
        if isinstance(opts, basestring):
            opts = GLOptions[opts]
        self.__glOpts = opts.copy()
        self.update()
        
    def updateGLOptions(self, opts):
        """
        Modify the OpenGL state options to use immediately before drawing this item.
        *opts* must be a dictionary as specified by setGLOptions.
        Values may also be None, in which case the key will be ignored.
        """
        self.__glOpts.update(opts)
        
    
    def parentItem(self):
        """Return a this item's parent in the scenegraph hierarchy."""
        return self.__parent
        
    def childItems(self):
        """Return a list of this item's children in the scenegraph hierarchy."""
        return list(self.__children)
        
    def _setView(self, v):
        self.__view = v
        
    def view(self):
        return self.__view
        
    def setDepthValue(self, value):
        """
        Sets the depth value of this item. Default is 0.
        This controls the order in which items are drawn--those with a greater depth value will be drawn later.
        Items with negative depth values are drawn before their parent.
        (This is analogous to QGraphicsItem.zValue)
        The depthValue does NOT affect the position of the item or the values it imparts to the GL depth buffer.
        """
        self.__depthValue = value
        
    def depthValue(self):
        """Return the depth value of this item. See setDepthValue for more information."""
        return self.__depthValue
        
    def setTransform(self, tr):
        """Set the local transform for this object.
        Must be a :class:`Transform3D <pyqtgraph.Transform3D>` instance. This transform
        determines how the local coordinate system of the item is mapped to the coordinate
        system of its parent."""
        self.__transform = Transform3D(tr)
        self.update()
        
    def resetTransform(self):
        """Reset this item's transform to an identity transformation."""
        self.__transform.setToIdentity()
        self.update()
        
    def applyTransform(self, tr, local):
        """
        Multiply this object's transform by *tr*. 
        If local is True, then *tr* is multiplied on the right of the current transform::
        
            newTransform = transform * tr
            
        If local is False, then *tr* is instead multiplied on the left::
        
            newTransform = tr * transform
        """
        if local:
            self.setTransform(self.transform() * tr)
        else:
            self.setTransform(tr * self.transform())
        
    def transform(self):
        """Return this item's transform object."""
        return self.__transform
        
    def viewTransform(self):
        """Return the transform mapping this item's local coordinate system to the 
        view coordinate system."""
        tr = self.__transform
        p = self
        while True:
            p = p.parentItem()
            if p is None:
                break
            tr = p.transform() * tr
        return Transform3D(tr)
        
    def translate(self, dx, dy, dz, local=False):
        """
        Translate the object by (*dx*, *dy*, *dz*) in its parent's coordinate system.
        If *local* is True, then translation takes place in local coordinates.
        """
        tr = Transform3D()
        tr.translate(dx, dy, dz)
        self.applyTransform(tr, local=local)
        
    def rotate(self, angle, x, y, z, local=False):
        """
        Rotate the object around the axis specified by (x,y,z).
        *angle* is in degrees.
        
        """
        tr = Transform3D()
        tr.rotate(angle, x, y, z)
        self.applyTransform(tr, local=local)
    
    def scale(self, x, y, z, local=True):
        """
        Scale the object by (*dx*, *dy*, *dz*) in its local coordinate system.
        If *local* is False, then scale takes place in the parent's coordinates.
        """
        tr = Transform3D()
        tr.scale(x, y, z)
        self.applyTransform(tr, local=local)
    
    
    def hide(self):
        """Hide this item. 
        This is equivalent to setVisible(False)."""
        self.setVisible(False)
        
    def show(self):
        """Make this item visible if it was previously hidden.
        This is equivalent to setVisible(True)."""
        self.setVisible(True)
    
    def setVisible(self, vis):
        """Set the visibility of this item."""
        self.__visible = vis
        self.update()
        
    def visible(self):
        """Return True if the item is currently set to be visible.
        Note that this does not guarantee that the item actually appears in the
        view, as it may be obscured or outside of the current view area."""
        return self.__visible
    
    
    def initializeGL(self):
        """
        Called after an item is added to a GLViewWidget. 
        The widget's GL context is made current before this method is called.
        (So this would be an appropriate time to generate lists, upload textures, etc.)
        """
        pass
    
    def setupGLState(self):
        """
        This method is responsible for preparing the GL state options needed to render 
        this item (blending, depth testing, etc). The method is called immediately before painting the item.
        """
        for k,v in self.__glOpts.items():
            if v is None:
                continue
            if isinstance(k, basestring):
                func = getattr(GL, k)
                func(*v)
            else:
                if v is True:
                    glEnable(k)
                else:
                    glDisable(k)
    
    def paint(self):
        """
        Called by the GLViewWidget to draw this item.
        It is the responsibility of the item to set up its own modelview matrix,
        but the caller will take care of pushing/popping.
        """
        self.setupGLState()
        
    def update(self):
        """
        Indicates that this item needs to be redrawn, and schedules an update 
        with the view it is displayed in.
        """
        v = self.view()
        if v is None:
            return
        v.update()
        
    def mapToParent(self, point):
        tr = self.transform()
        if tr is None:
            return point
        return tr.map(point)
        
    def mapFromParent(self, point):
        tr = self.transform()
        if tr is None:
            return point
        return tr.inverted()[0].map(point)
        
    def mapToView(self, point):
        tr = self.viewTransform()
        if tr is None:
            return point
        return tr.map(point)
        
    def mapFromView(self, point):
        tr = self.viewTransform()
        if tr is None:
            return point
        return tr.inverted()[0].map(point)
        
        
        