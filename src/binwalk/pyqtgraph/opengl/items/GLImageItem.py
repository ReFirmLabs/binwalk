from OpenGL.GL import *
from .. GLGraphicsItem import GLGraphicsItem
from pyqtgraph.Qt import QtGui
import numpy as np

__all__ = ['GLImageItem']

class GLImageItem(GLGraphicsItem):
    """
    **Bases:** :class:`GLGraphicsItem <pyqtgraph.opengl.GLGraphicsItem>`
    
    Displays image data as a textured quad.
    """
    
    
    def __init__(self, data, smooth=False, glOptions='translucent'):
        """
        
        ==============  =======================================================================================
        **Arguments:**
        data            Volume data to be rendered. *Must* be 3D numpy array (x, y, RGBA) with dtype=ubyte.
                        (See functions.makeRGBA)
        smooth          (bool) If True, the volume slices are rendered with linear interpolation 
        ==============  =======================================================================================
        """
        
        self.smooth = smooth
        self.data = data
        GLGraphicsItem.__init__(self)
        self.setGLOptions(glOptions)
        
    def initializeGL(self):
        glEnable(GL_TEXTURE_2D)
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        if self.smooth:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        else:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
        #glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_BORDER)
        shape = self.data.shape
        
        ## Test texture dimensions first
        glTexImage2D(GL_PROXY_TEXTURE_2D, 0, GL_RGBA, shape[0], shape[1], 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        if glGetTexLevelParameteriv(GL_PROXY_TEXTURE_2D, 0, GL_TEXTURE_WIDTH) == 0:
            raise Exception("OpenGL failed to create 2D texture (%dx%d); too large for this hardware." % shape[:2])
        
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, shape[0], shape[1], 0, GL_RGBA, GL_UNSIGNED_BYTE, self.data.transpose((1,0,2)))
        glDisable(GL_TEXTURE_2D)
        
        #self.lists = {}
        #for ax in [0,1,2]:
            #for d in [-1, 1]:
                #l = glGenLists(1)
                #self.lists[(ax,d)] = l
                #glNewList(l, GL_COMPILE)
                #self.drawVolume(ax, d)
                #glEndList()

                
    def paint(self):
        
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        
        self.setupGLState()
        
        #glEnable(GL_DEPTH_TEST)
        ##glDisable(GL_CULL_FACE)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        #glEnable( GL_BLEND )
        #glEnable( GL_ALPHA_TEST )
        glColor4f(1,1,1,1)

        glBegin(GL_QUADS)
        glTexCoord2f(0,0)
        glVertex3f(0,0,0)
        glTexCoord2f(1,0)
        glVertex3f(self.data.shape[0], 0, 0)
        glTexCoord2f(1,1)
        glVertex3f(self.data.shape[0], self.data.shape[1], 0)
        glTexCoord2f(0,1)
        glVertex3f(0, self.data.shape[1], 0)
        glEnd()
        glDisable(GL_TEXTURE_3D)
                
