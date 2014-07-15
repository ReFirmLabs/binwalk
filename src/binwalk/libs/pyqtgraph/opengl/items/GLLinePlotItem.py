from OpenGL.GL import *
from OpenGL.arrays import vbo
from .. GLGraphicsItem import GLGraphicsItem
from .. import shaders
from pyqtgraph import QtGui
import numpy as np

__all__ = ['GLLinePlotItem']

class GLLinePlotItem(GLGraphicsItem):
    """Draws line plots in 3D."""
    
    def __init__(self, **kwds):
        """All keyword arguments are passed to setData()"""
        GLGraphicsItem.__init__(self)
        glopts = kwds.pop('glOptions', 'additive')
        self.setGLOptions(glopts)
        self.pos = None
        self.width = 1.
        self.color = (1.0,1.0,1.0,1.0)
        self.setData(**kwds)
    
    def setData(self, **kwds):
        """
        Update the data displayed by this item. All arguments are optional; 
        for example it is allowed to update vertex positions while leaving 
        colors unchanged, etc.
        
        ====================  ==================================================
        Arguments:
        ------------------------------------------------------------------------
        pos                   (N,3) array of floats specifying point locations.
        color                 (N,4) array of floats (0.0-1.0) or
                              tuple of floats specifying
                              a single color for the entire item.
        width                 float specifying line width
        antialias             enables smooth line drawing
        ====================  ==================================================
        """
        args = ['pos', 'color', 'width', 'connected', 'antialias']
        for k in kwds.keys():
            if k not in args:
                raise Exception('Invalid keyword argument: %s (allowed arguments are %s)' % (k, str(args)))
        self.antialias = False
        for arg in args:
            if arg in kwds:
                setattr(self, arg, kwds[arg])
                #self.vbo.pop(arg, None)
        self.update()

    def initializeGL(self):
        pass
        
    #def setupGLState(self):
        #"""Prepare OpenGL state for drawing. This function is called immediately before painting."""
        ##glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)  ## requires z-sorting to render properly.
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        #glEnable( GL_BLEND )
        #glEnable( GL_ALPHA_TEST )
        #glDisable( GL_DEPTH_TEST )
        
        ##glEnable( GL_POINT_SMOOTH )

        ##glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)
        ##glPointParameterfv(GL_POINT_DISTANCE_ATTENUATION, (0, 0, -1e-3))
        ##glPointParameterfv(GL_POINT_SIZE_MAX, (65500,))
        ##glPointParameterfv(GL_POINT_SIZE_MIN, (0,))
        
    def paint(self):
        if self.pos is None:
            return
        self.setupGLState()
        
        glEnableClientState(GL_VERTEX_ARRAY)

        try:
            glVertexPointerf(self.pos)
            
            if isinstance(self.color, np.ndarray):
                glEnableClientState(GL_COLOR_ARRAY)
                glColorPointerf(self.color)
            else:
                if isinstance(self.color, QtGui.QColor):
                    glColor4f(*fn.glColor(self.color))
                else:
                    glColor4f(*self.color)
            glLineWidth(self.width)
            #glPointSize(self.width)
            
            if self.antialias:
                glEnable(GL_LINE_SMOOTH)
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                glHint(GL_LINE_SMOOTH_HINT, GL_NICEST);
                
            glDrawArrays(GL_LINE_STRIP, 0, int(self.pos.size / self.pos.shape[-1]))
        finally:
            glDisableClientState(GL_COLOR_ARRAY)
            glDisableClientState(GL_VERTEX_ARRAY)
    
        
