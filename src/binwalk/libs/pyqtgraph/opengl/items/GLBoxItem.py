from OpenGL.GL import *
from .. GLGraphicsItem import GLGraphicsItem
from pyqtgraph.Qt import QtGui
import pyqtgraph as pg

__all__ = ['GLBoxItem']

class GLBoxItem(GLGraphicsItem):
    """
    **Bases:** :class:`GLGraphicsItem <pyqtgraph.opengl.GLGraphicsItem>`
    
    Displays a wire-frame box.
    """
    def __init__(self, size=None, color=None, glOptions='translucent'):
        GLGraphicsItem.__init__(self)
        if size is None:
            size = QtGui.QVector3D(1,1,1)
        self.setSize(size=size)
        if color is None:
            color = (255,255,255,80)
        self.setColor(color)
        self.setGLOptions(glOptions)
    
    def setSize(self, x=None, y=None, z=None, size=None):
        """
        Set the size of the box (in its local coordinate system; this does not affect the transform)
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
    
    def setColor(self, *args):
        """Set the color of the box. Arguments are the same as those accepted by functions.mkColor()"""
        self.__color = pg.Color(*args)
        
    def color(self):
        return self.__color
    
    def paint(self):
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        #glEnable( GL_BLEND )
        #glEnable( GL_ALPHA_TEST )
        ##glAlphaFunc( GL_ALWAYS,0.5 )
        #glEnable( GL_POINT_SMOOTH )
        #glDisable( GL_DEPTH_TEST )
        self.setupGLState()
        
        glBegin( GL_LINES )
        
        glColor4f(*self.color().glColor())
        x,y,z = self.size()
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, z)
        glVertex3f(x, 0, 0)
        glVertex3f(x, 0, z)
        glVertex3f(0, y, 0)
        glVertex3f(0, y, z)
        glVertex3f(x, y, 0)
        glVertex3f(x, y, z)

        glVertex3f(0, 0, 0)
        glVertex3f(0, y, 0)
        glVertex3f(x, 0, 0)
        glVertex3f(x, y, 0)
        glVertex3f(0, 0, z)
        glVertex3f(0, y, z)
        glVertex3f(x, 0, z)
        glVertex3f(x, y, z)
        
        glVertex3f(0, 0, 0)
        glVertex3f(x, 0, 0)
        glVertex3f(0, y, 0)
        glVertex3f(x, y, 0)
        glVertex3f(0, 0, z)
        glVertex3f(x, 0, z)
        glVertex3f(0, y, z)
        glVertex3f(x, y, z)
        
        glEnd()
        
        