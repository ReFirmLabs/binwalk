from OpenGL.GL import *
from .. GLGraphicsItem import GLGraphicsItem
from pyqtgraph.Qt import QtGui
import numpy as np

__all__ = ['GLVolumeItem']

class GLVolumeItem(GLGraphicsItem):
    """
    **Bases:** :class:`GLGraphicsItem <pyqtgraph.opengl.GLGraphicsItem>`
    
    Displays volumetric data. 
    """
    
    
    def __init__(self, data, sliceDensity=1, smooth=True, glOptions='translucent'):
        """
        ==============  =======================================================================================
        **Arguments:**
        data            Volume data to be rendered. *Must* be 4D numpy array (x, y, z, RGBA) with dtype=ubyte.
        sliceDensity    Density of slices to render through the volume. A value of 1 means one slice per voxel.
        smooth          (bool) If True, the volume slices are rendered with linear interpolation 
        ==============  =======================================================================================
        """
        
        self.sliceDensity = sliceDensity
        self.smooth = smooth
        self.data = data
        GLGraphicsItem.__init__(self)
        self.setGLOptions(glOptions)
        
    def initializeGL(self):
        glEnable(GL_TEXTURE_3D)
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_3D, self.texture)
        if self.smooth:
            glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        else:
            glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_BORDER)
        shape = self.data.shape
        
        ## Test texture dimensions first
        glTexImage3D(GL_PROXY_TEXTURE_3D, 0, GL_RGBA, shape[0], shape[1], shape[2], 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        if glGetTexLevelParameteriv(GL_PROXY_TEXTURE_3D, 0, GL_TEXTURE_WIDTH) == 0:
            raise Exception("OpenGL failed to create 3D texture (%dx%dx%d); too large for this hardware." % shape[:3])
        
        glTexImage3D(GL_TEXTURE_3D, 0, GL_RGBA, shape[0], shape[1], shape[2], 0, GL_RGBA, GL_UNSIGNED_BYTE, self.data.transpose((2,1,0,3)))
        glDisable(GL_TEXTURE_3D)
        
        self.lists = {}
        for ax in [0,1,2]:
            for d in [-1, 1]:
                l = glGenLists(1)
                self.lists[(ax,d)] = l
                glNewList(l, GL_COMPILE)
                self.drawVolume(ax, d)
                glEndList()

                
    def paint(self):
        self.setupGLState()
        
        glEnable(GL_TEXTURE_3D)
        glBindTexture(GL_TEXTURE_3D, self.texture)
        
        #glEnable(GL_DEPTH_TEST)
        #glDisable(GL_CULL_FACE)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        #glEnable( GL_BLEND )
        #glEnable( GL_ALPHA_TEST )
        glColor4f(1,1,1,1)

        view = self.view()
        center = QtGui.QVector3D(*[x/2. for x in self.data.shape[:3]])
        cam = self.mapFromParent(view.cameraPosition()) - center
        #print "center", center, "cam", view.cameraPosition(), self.mapFromParent(view.cameraPosition()), "diff", cam
        cam = np.array([cam.x(), cam.y(), cam.z()])
        ax = np.argmax(abs(cam))
        d = 1 if cam[ax] > 0 else -1
        glCallList(self.lists[(ax,d)])  ## draw axes
        glDisable(GL_TEXTURE_3D)
                
    def drawVolume(self, ax, d):
        N = 5
        
        imax = [0,1,2]
        imax.remove(ax)
        
        tp = [[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
        vp = [[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
        nudge = [0.5/x for x in self.data.shape]
        tp[0][imax[0]] = 0+nudge[imax[0]]
        tp[0][imax[1]] = 0+nudge[imax[1]]
        tp[1][imax[0]] = 1-nudge[imax[0]]
        tp[1][imax[1]] = 0+nudge[imax[1]]
        tp[2][imax[0]] = 1-nudge[imax[0]]
        tp[2][imax[1]] = 1-nudge[imax[1]]
        tp[3][imax[0]] = 0+nudge[imax[0]]
        tp[3][imax[1]] = 1-nudge[imax[1]]
        
        vp[0][imax[0]] = 0
        vp[0][imax[1]] = 0
        vp[1][imax[0]] = self.data.shape[imax[0]]
        vp[1][imax[1]] = 0
        vp[2][imax[0]] = self.data.shape[imax[0]]
        vp[2][imax[1]] = self.data.shape[imax[1]]
        vp[3][imax[0]] = 0
        vp[3][imax[1]] = self.data.shape[imax[1]]
        slices = self.data.shape[ax] * self.sliceDensity
        r = list(range(slices))
        if d == -1:
            r = r[::-1]
            
        glBegin(GL_QUADS)
        tzVals = np.linspace(nudge[ax], 1.0-nudge[ax], slices)
        vzVals = np.linspace(0, self.data.shape[ax], slices)
        for i in r:
            z = tzVals[i]
            w = vzVals[i]
            
            tp[0][ax] = z
            tp[1][ax] = z
            tp[2][ax] = z
            tp[3][ax] = z
            
            vp[0][ax] = w
            vp[1][ax] = w
            vp[2][ax] = w
            vp[3][ax] = w
            
            
            glTexCoord3f(*tp[0])
            glVertex3f(*vp[0])
            glTexCoord3f(*tp[1])
            glVertex3f(*vp[1])
            glTexCoord3f(*tp[2])
            glVertex3f(*vp[2])
            glTexCoord3f(*tp[3])
            glVertex3f(*vp[3])
        glEnd()
        
        
        
        
        
        
        
        
        
        ## Interesting idea:
        ## remove projection/modelview matrixes, recreate in texture coords. 
        ## it _sorta_ works, but needs tweaking.
        #mvm = glGetDoublev(GL_MODELVIEW_MATRIX)
        #pm = glGetDoublev(GL_PROJECTION_MATRIX)
        #m = QtGui.QMatrix4x4(mvm.flatten()).inverted()[0]
        #p = QtGui.QMatrix4x4(pm.flatten()).inverted()[0]
        
        #glMatrixMode(GL_PROJECTION)
        #glPushMatrix()
        #glLoadIdentity()
        #N=1
        #glOrtho(-N,N,-N,N,-100,100)
        
        #glMatrixMode(GL_MODELVIEW)
        #glLoadIdentity()
        
        
        #glMatrixMode(GL_TEXTURE)
        #glLoadIdentity()
        #glMultMatrixf(m.copyDataTo())
        
        #view = self.view()
        #w = view.width()
        #h = view.height()
        #dist = view.opts['distance']
        #fov = view.opts['fov']
        #nearClip = dist * .1
        #farClip = dist * 5.
        #r = nearClip * np.tan(fov)
        #t = r * h / w
        
        #p = QtGui.QMatrix4x4()
        #p.frustum( -r, r, -t, t, nearClip, farClip)
        #glMultMatrixf(p.inverted()[0].copyDataTo())
        
        
        #glBegin(GL_QUADS)
        
        #M=1
        #for i in range(500):
            #z = i/500.
            #w = -i/500.
            #glTexCoord3f(-M, -M, z)
            #glVertex3f(-N, -N, w)
            #glTexCoord3f(M, -M, z)
            #glVertex3f(N, -N, w)
            #glTexCoord3f(M, M, z)
            #glVertex3f(N, N, w)
            #glTexCoord3f(-M, M, z)
            #glVertex3f(-N, N, w)
        #glEnd()
        #glDisable(GL_TEXTURE_3D)

        #glMatrixMode(GL_PROJECTION)
        #glPopMatrix()
        
        

