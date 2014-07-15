from OpenGL.GL import *
from .. GLGraphicsItem import GLGraphicsItem
from .. MeshData import MeshData
from pyqtgraph.Qt import QtGui
import pyqtgraph as pg
from .. import shaders
import numpy as np



__all__ = ['GLMeshItem']

class GLMeshItem(GLGraphicsItem):
    """
    **Bases:** :class:`GLGraphicsItem <pyqtgraph.opengl.GLGraphicsItem>`
    
    Displays a 3D triangle mesh. 
    """
    def __init__(self, **kwds):
        """
        ============== =====================================================
        Arguments
        meshdata       MeshData object from which to determine geometry for 
                       this item.
        color          Default face color used if no vertex or face colors 
                       are specified.
        edgeColor      Default edge color to use if no edge colors are
                       specified in the mesh data.
        drawEdges      If True, a wireframe mesh will be drawn. 
                       (default=False)
        drawFaces      If True, mesh faces are drawn. (default=True)
        shader         Name of shader program to use when drawing faces.
                       (None for no shader)
        smooth         If True, normal vectors are computed for each vertex
                       and interpolated within each face.
        computeNormals If False, then computation of normal vectors is 
                       disabled. This can provide a performance boost for 
                       meshes that do not make use of normals.
        ============== =====================================================
        """
        self.opts = {
            'meshdata': None,
            'color': (1., 1., 1., 1.),
            'drawEdges': False,
            'drawFaces': True,
            'edgeColor': (0.5, 0.5, 0.5, 1.0),
            'shader': None,
            'smooth': True,
            'computeNormals': True,
        }
        
        GLGraphicsItem.__init__(self)
        glopts = kwds.pop('glOptions', 'opaque')
        self.setGLOptions(glopts)
        shader = kwds.pop('shader', None)
        self.setShader(shader)
        
        self.setMeshData(**kwds)
        
        ## storage for data compiled from MeshData object
        self.vertexes = None
        self.normals = None
        self.colors = None
        self.faces = None
        
    def setShader(self, shader):
        """Set the shader used when rendering faces in the mesh. (see the GL shaders example)"""
        self.opts['shader'] = shader
        self.update()
        
    def shader(self):
        shader = self.opts['shader']
        if isinstance(shader, shaders.ShaderProgram):
            return shader
        else:
            return shaders.getShaderProgram(shader)
        
    def setColor(self, c):
        """Set the default color to use when no vertex or face colors are specified."""
        self.opts['color'] = c
        self.update()
        
    def setMeshData(self, **kwds):
        """
        Set mesh data for this item. This can be invoked two ways:
        
        1. Specify *meshdata* argument with a new MeshData object
        2. Specify keyword arguments to be passed to MeshData(..) to create a new instance.
        """
        md = kwds.get('meshdata', None)
        if md is None:
            opts = {}
            for k in ['vertexes', 'faces', 'edges', 'vertexColors', 'faceColors']:
                try:
                    opts[k] = kwds.pop(k)
                except KeyError:
                    pass
            md = MeshData(**opts)
        
        self.opts['meshdata'] = md
        self.opts.update(kwds)
        self.meshDataChanged()
        self.update()
        
    
    def meshDataChanged(self):
        """
        This method must be called to inform the item that the MeshData object
        has been altered.
        """
        
        self.vertexes = None
        self.faces = None
        self.normals = None
        self.colors = None
        self.edges = None
        self.edgeColors = None
        self.update()
    
    def parseMeshData(self):
        ## interpret vertex / normal data before drawing
        ## This can:
        ##   - automatically generate normals if they were not specified
        ##   - pull vertexes/noormals/faces from MeshData if that was specified
        
        if self.vertexes is not None and self.normals is not None:
            return
        #if self.opts['normals'] is None:
            #if self.opts['meshdata'] is None:
                #self.opts['meshdata'] = MeshData(vertexes=self.opts['vertexes'], faces=self.opts['faces'])
        if self.opts['meshdata'] is not None:
            md = self.opts['meshdata']
            if self.opts['smooth'] and not md.hasFaceIndexedData():
                self.vertexes = md.vertexes()
                if self.opts['computeNormals']:
                    self.normals = md.vertexNormals()
                self.faces = md.faces()
                if md.hasVertexColor():
                    self.colors = md.vertexColors()
                if md.hasFaceColor():
                    self.colors = md.faceColors()
            else:
                self.vertexes = md.vertexes(indexed='faces')
                if self.opts['computeNormals']:
                    if self.opts['smooth']:
                        self.normals = md.vertexNormals(indexed='faces')
                    else:
                        self.normals = md.faceNormals(indexed='faces')
                self.faces = None
                if md.hasVertexColor():
                    self.colors = md.vertexColors(indexed='faces')
                elif md.hasFaceColor():
                    self.colors = md.faceColors(indexed='faces')
                    
            if self.opts['drawEdges']:
                self.edges = md.edges()
                self.edgeVerts = md.vertexes()
            return
    
    def paint(self):
        self.setupGLState()
        
        self.parseMeshData()        
        
        if self.opts['drawFaces']:
            with self.shader():
                verts = self.vertexes
                norms = self.normals
                color = self.colors
                faces = self.faces
                if verts is None:
                    return
                glEnableClientState(GL_VERTEX_ARRAY)
                try:
                    glVertexPointerf(verts)
                    
                    if self.colors is None:
                        color = self.opts['color']
                        if isinstance(color, QtGui.QColor):
                            glColor4f(*pg.glColor(color))
                        else:
                            glColor4f(*color)
                    else:
                        glEnableClientState(GL_COLOR_ARRAY)
                        glColorPointerf(color)
                    
                    
                    if norms is not None:
                        glEnableClientState(GL_NORMAL_ARRAY)
                        glNormalPointerf(norms)
                    
                    if faces is None:
                        glDrawArrays(GL_TRIANGLES, 0, np.product(verts.shape[:-1]))
                    else:
                        faces = faces.astype(np.uint).flatten()
                        glDrawElements(GL_TRIANGLES, faces.shape[0], GL_UNSIGNED_INT, faces)
                finally:
                    glDisableClientState(GL_NORMAL_ARRAY)
                    glDisableClientState(GL_VERTEX_ARRAY)
                    glDisableClientState(GL_COLOR_ARRAY)
            
        if self.opts['drawEdges']:
            verts = self.edgeVerts
            edges = self.edges
            glEnableClientState(GL_VERTEX_ARRAY)
            try:
                glVertexPointerf(verts)
                
                if self.edgeColors is None:
                    color = self.opts['edgeColor']
                    if isinstance(color, QtGui.QColor):
                        glColor4f(*pg.glColor(color))
                    else:
                        glColor4f(*color)
                else:
                    glEnableClientState(GL_COLOR_ARRAY)
                    glColorPointerf(color)
                edges = edges.flatten()
                glDrawElements(GL_LINES, edges.shape[0], GL_UNSIGNED_INT, edges)
            finally:
                glDisableClientState(GL_VERTEX_ARRAY)
                glDisableClientState(GL_COLOR_ARRAY)
            
