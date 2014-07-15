from OpenGL.GL import *
from .. GLGraphicsItem import GLGraphicsItem
from pyqtgraph import QtGui

__all__ = ['GLGridItem']

class GLGridItem(GLGraphicsItem):
    """
    **Bases:** :class:`GLGraphicsItem <pyqtgraph.opengl.GLGraphicsItem>`
    
    Displays a wire-grame grid. 
    """
    
    def __init__(self, size=None, color=None, antialias=True, glOptions='translucent'):
        GLGraphicsItem.__init__(self)
        self.setGLOptions(glOptions)
        self.antialias = antialias
        if size is None:
            size = QtGui.QVector3D(1,1,1)
        self.setSize(size=size)
    
    def setSize(self, x=None, y=None, z=None, size=None):
        """
        Set the size of the axes (in its local coordinate system; this does not affect the transform)
        Arguments can be x,y,z or size=QVector3D().
        """
        if size is not None:
            x = size.x()
            y = size.y()
            z = size.z()
        self.__size = [x,y,z]
        self.update()
        
    def size(self):
        return self.__size[:]
    
    
    def paint(self):
        self.setupGLState()
        
        if self.antialias:
            glEnable(GL_LINE_SMOOTH)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glHint(GL_LINE_SMOOTH_HINT, GL_NICEST);
            
        glBegin( GL_LINES )
        
        x,y,z = self.size()
        glColor4f(1, 1, 1, .3)
        for x in range(-10, 11):
            glVertex3f(x, -10, 0)
            glVertex3f(x,  10, 0)
        for y in range(-10, 11):
            glVertex3f(-10, y, 0)
            glVertex3f( 10, y, 0)
        
        glEnd()
