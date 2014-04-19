from pyqtgraph.Qt import QtCore, QtGui, QtOpenGL
from OpenGL.GL import *
app = QtGui.QApplication([])

class GLTest(QtOpenGL.QGLWidget):
    def __init__(self):
        QtOpenGL.QGLWidget.__init__(self)
        self.makeCurrent()
        print("GL version:" + glGetString(GL_VERSION))
        print("MAX_TEXTURE_SIZE: %d" % glGetIntegerv(GL_MAX_TEXTURE_SIZE))
        print("MAX_3D_TEXTURE_SIZE: %d" % glGetIntegerv(GL_MAX_3D_TEXTURE_SIZE))
        print("Extensions: " + glGetString(GL_EXTENSIONS))

GLTest()


