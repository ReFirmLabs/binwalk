from pyqtgraph.Qt import QtGui
import pyqtgraph.functions as fn
import numpy as np

class MeshData(object):
    """
    Class for storing and operating on 3D mesh data. May contain:
    
    - list of vertex locations
    - list of edges
    - list of triangles
    - colors per vertex, edge, or tri
    - normals per vertex or tri
    
    This class handles conversion between the standard [list of vertexes, list of faces]
    format (suitable for use with glDrawElements) and 'indexed' [list of vertexes] format
    (suitable for use with glDrawArrays). It will automatically compute face normal
    vectors as well as averaged vertex normal vectors. 
    
    The class attempts to be as efficient as possible in caching conversion results and
    avoiding unnecessary conversions.
    """

    def __init__(self, vertexes=None, faces=None, edges=None, vertexColors=None, faceColors=None):
        """
        ============= =====================================================
        Arguments
        vertexes      (Nv, 3) array of vertex coordinates. 
                      If faces is not specified, then this will instead be
                      interpreted as (Nf, 3, 3) array of coordinates.
        faces         (Nf, 3) array of indexes into the vertex array.
        edges         [not available yet]
        vertexColors  (Nv, 4) array of vertex colors. 
                      If faces is not specified, then this will instead be
                      interpreted as (Nf, 3, 4) array of colors.
        faceColors    (Nf, 4) array of face colors.
        ============= =====================================================
        
        All arguments are optional.
        """
        self._vertexes = None  # (Nv,3) array of vertex coordinates
        self._vertexesIndexedByFaces = None   #  (Nf, 3, 3) array of vertex coordinates
        self._vertexesIndexedByEdges = None   #  (Ne, 2, 3) array of vertex coordinates
        
        ## mappings between vertexes, faces, and edges
        self._faces = None   # Nx3 array of indexes into self._vertexes specifying three vertexes for each face
        self._edges = None   # Nx2 array of indexes into self._vertexes specifying two vertexes per edge
        self._vertexFaces = None  ## maps vertex ID to a list of face IDs (inverse mapping of _faces)
        self._vertexEdges = None  ## maps vertex ID to a list of edge IDs (inverse mapping of _edges)
        
        ## Per-vertex data
        self._vertexNormals = None                # (Nv, 3) array of normals, one per vertex
        self._vertexNormalsIndexedByFaces = None  # (Nf, 3, 3) array of normals
        self._vertexColors = None                 # (Nv, 3) array of colors
        self._vertexColorsIndexedByFaces = None   # (Nf, 3, 4) array of colors
        self._vertexColorsIndexedByEdges = None   # (Nf, 2, 4) array of colors
        
        ## Per-face data
        self._faceNormals = None                # (Nf, 3) array of face normals
        self._faceNormalsIndexedByFaces = None  # (Nf, 3, 3) array of face normals
        self._faceColors = None                 # (Nf, 4) array of face colors
        self._faceColorsIndexedByFaces = None   # (Nf, 3, 4) array of face colors
        self._faceColorsIndexedByEdges = None   # (Ne, 2, 4) array of face colors
        
        ## Per-edge data
        self._edgeColors = None                # (Ne, 4) array of edge colors
        self._edgeColorsIndexedByEdges = None  # (Ne, 2, 4) array of edge colors
        #self._meshColor = (1, 1, 1, 0.1)  # default color to use if no face/edge/vertex colors are given
        
        
        
        if vertexes is not None:
            if faces is None:
                self.setVertexes(vertexes, indexed='faces')
                if vertexColors is not None:
                    self.setVertexColors(vertexColors, indexed='faces')
                if faceColors is not None:
                    self.setFaceColors(faceColors, indexed='faces')
            else:
                self.setVertexes(vertexes)
                self.setFaces(faces)
                if vertexColors is not None:
                    self.setVertexColors(vertexColors)
                if faceColors is not None:
                    self.setFaceColors(faceColors)
            
            #self.setFaces(vertexes=vertexes, faces=faces, vertexColors=vertexColors, faceColors=faceColors)
            
        
    #def setFaces(self, vertexes=None, faces=None, vertexColors=None, faceColors=None):
        #"""
        #Set the faces in this data set.
        #Data may be provided either as an Nx3x3 array of floats (9 float coordinate values per face)::
        
            #faces = [ [(x, y, z), (x, y, z), (x, y, z)], ... ] 
            
        #or as an Nx3 array of ints (vertex integers) AND an Mx3 array of floats (3 float coordinate values per vertex)::
        
            #faces = [ (p1, p2, p3), ... ]
            #vertexes = [ (x, y, z), ... ]
            
        #"""
        #if not isinstance(vertexes, np.ndarray):
            #vertexes = np.array(vertexes)
        #if vertexes.dtype != np.float:
            #vertexes = vertexes.astype(float)
        #if faces is None:
            #self._setIndexedFaces(vertexes, vertexColors, faceColors)
        #else:
            #self._setUnindexedFaces(faces, vertexes, vertexColors, faceColors)
        ##print self.vertexes().shape
        ##print self.faces().shape
        
    
    #def setMeshColor(self, color):
        #"""Set the color of the entire mesh. This removes any per-face or per-vertex colors."""
        #color = fn.Color(color)
        #self._meshColor = color.glColor()
        #self._vertexColors = None
        #self._faceColors = None
    
        
    #def __iter__(self):
        #"""Iterate over all faces, yielding a list of three tuples [(position, normal, color), ...] for each face."""
        #vnorms = self.vertexNormals()
        #vcolors = self.vertexColors()
        #for i in range(self._faces.shape[0]):
            #face = []
            #for j in [0,1,2]:
                #vind = self._faces[i,j]
                #pos = self._vertexes[vind]
                #norm = vnorms[vind]
                #if vcolors is None:
                    #color = self._meshColor
                #else:
                    #color = vcolors[vind]
                #face.append((pos, norm, color))
            #yield face
    
    #def __len__(self):
        #return len(self._faces)
    
    def faces(self):
        """Return an array (Nf, 3) of vertex indexes, three per triangular face in the mesh."""
        return self._faces
    
    def edges(self):
        """Return an array (Nf, 3) of vertex indexes, two per edge in the mesh."""
        if self._edges is None:
            self._computeEdges()
        return self._edges
        
    def setFaces(self, faces):
        """Set the (Nf, 3) array of faces. Each rown in the array contains
        three indexes into the vertex array, specifying the three corners 
        of a triangular face."""
        self._faces = faces
        self._edges = None
        self._vertexFaces = None
        self._vertexesIndexedByFaces = None
        self.resetNormals()
        self._vertexColorsIndexedByFaces = None
        self._faceColorsIndexedByFaces = None
        
        
    
    def vertexes(self, indexed=None):
        """Return an array (N,3) of the positions of vertexes in the mesh. 
        By default, each unique vertex appears only once in the array.
        If indexed is 'faces', then the array will instead contain three vertexes
        per face in the mesh (and a single vertex may appear more than once in the array)."""
        if indexed is None:
            if self._vertexes is None and self._vertexesIndexedByFaces is not None:
                self._computeUnindexedVertexes()
            return self._vertexes
        elif indexed == 'faces':
            if self._vertexesIndexedByFaces is None and self._vertexes is not None:
                self._vertexesIndexedByFaces = self._vertexes[self.faces()]
            return self._vertexesIndexedByFaces
        else:
            raise Exception("Invalid indexing mode. Accepts: None, 'faces'")
        
    def setVertexes(self, verts=None, indexed=None, resetNormals=True):
        """
        Set the array (Nv, 3) of vertex coordinates.
        If indexed=='faces', then the data must have shape (Nf, 3, 3) and is
        assumed to be already indexed as a list of faces.
        This will cause any pre-existing normal vectors to be cleared
        unless resetNormals=False.
        """
        if indexed is None:
            if verts is not None:
                self._vertexes = verts
            self._vertexesIndexedByFaces = None
        elif indexed=='faces':
            self._vertexes = None
            if verts is not None:
                self._vertexesIndexedByFaces = verts
        else:
            raise Exception("Invalid indexing mode. Accepts: None, 'faces'")
        
        if resetNormals:
            self.resetNormals()
    
    def resetNormals(self):
        self._vertexNormals = None
        self._vertexNormalsIndexedByFaces = None
        self._faceNormals = None
        self._faceNormalsIndexedByFaces = None
            
        
    def hasFaceIndexedData(self):
        """Return True if this object already has vertex positions indexed by face"""
        return self._vertexesIndexedByFaces is not None
    
    def hasEdgeIndexedData(self):
        return self._vertexesIndexedByEdges is not None
    
    def hasVertexColor(self):
        """Return True if this data set has vertex color information"""
        for v in (self._vertexColors, self._vertexColorsIndexedByFaces, self._vertexColorsIndexedByEdges):
            if v is not None:
                return True
        return False
        
    def hasFaceColor(self):
        """Return True if this data set has face color information"""
        for v in (self._faceColors, self._faceColorsIndexedByFaces, self._faceColorsIndexedByEdges):
            if v is not None:
                return True
        return False
        
    
    def faceNormals(self, indexed=None):
        """
        Return an array (Nf, 3) of normal vectors for each face.
        If indexed='faces', then instead return an indexed array
        (Nf, 3, 3)  (this is just the same array with each vector
        copied three times).
        """
        if self._faceNormals is None:
            v = self.vertexes(indexed='faces')
            self._faceNormals = np.cross(v[:,1]-v[:,0], v[:,2]-v[:,0])
        
        
        if indexed is None:
            return self._faceNormals
        elif indexed == 'faces':
            if self._faceNormalsIndexedByFaces is None:
                norms = np.empty((self._faceNormals.shape[0], 3, 3))
                norms[:] = self._faceNormals[:,np.newaxis,:]
                self._faceNormalsIndexedByFaces = norms
            return self._faceNormalsIndexedByFaces
        else:
            raise Exception("Invalid indexing mode. Accepts: None, 'faces'")
        
    def vertexNormals(self, indexed=None):
        """
        Return an array of normal vectors.
        By default, the array will be (N, 3) with one entry per unique vertex in the mesh.
        If indexed is 'faces', then the array will contain three normal vectors per face
        (and some vertexes may be repeated).
        """
        if self._vertexNormals is None:
            faceNorms = self.faceNormals()
            vertFaces = self.vertexFaces()
            self._vertexNormals = np.empty(self._vertexes.shape, dtype=float)
            for vindex in xrange(self._vertexes.shape[0]):
                norms = faceNorms[vertFaces[vindex]]  ## get all face normals
                norm = norms.sum(axis=0)       ## sum normals
                norm /= (norm**2).sum()**0.5  ## and re-normalize
                self._vertexNormals[vindex] = norm
                
        if indexed is None:
            return self._vertexNormals
        elif indexed == 'faces':
            return self._vertexNormals[self.faces()]
        else:
            raise Exception("Invalid indexing mode. Accepts: None, 'faces'")
        
    def vertexColors(self, indexed=None):
        """
        Return an array (Nv, 4) of vertex colors.
        If indexed=='faces', then instead return an indexed array
        (Nf, 3, 4). 
        """
        if indexed is None:
            return self._vertexColors
        elif indexed == 'faces':
            if self._vertexColorsIndexedByFaces is None:
                self._vertexColorsIndexedByFaces = self._vertexColors[self.faces()]
            return self._vertexColorsIndexedByFaces
        else:
            raise Exception("Invalid indexing mode. Accepts: None, 'faces'")
        
    def setVertexColors(self, colors, indexed=None):
        """
        Set the vertex color array (Nv, 4).
        If indexed=='faces', then the array will be interpreted
        as indexed and should have shape (Nf, 3, 4)
        """
        if indexed is None:
            self._vertexColors = colors
            self._vertexColorsIndexedByFaces = None
        elif indexed == 'faces':
            self._vertexColors = None
            self._vertexColorsIndexedByFaces = colors
        else:
            raise Exception("Invalid indexing mode. Accepts: None, 'faces'")
        
    def faceColors(self, indexed=None):
        """
        Return an array (Nf, 4) of face colors.
        If indexed=='faces', then instead return an indexed array
        (Nf, 3, 4)  (note this is just the same array with each color
        repeated three times). 
        """
        if indexed is None:
            return self._faceColors
        elif indexed == 'faces':
            if self._faceColorsIndexedByFaces is None and self._faceColors is not None:
                Nf = self._faceColors.shape[0]
                self._faceColorsIndexedByFaces = np.empty((Nf, 3, 4), dtype=self._faceColors.dtype)
                self._faceColorsIndexedByFaces[:] = self._faceColors.reshape(Nf, 1, 4)
            return self._faceColorsIndexedByFaces
        else:
            raise Exception("Invalid indexing mode. Accepts: None, 'faces'")
        
    def setFaceColors(self, colors, indexed=None):
        """
        Set the face color array (Nf, 4).
        If indexed=='faces', then the array will be interpreted
        as indexed and should have shape (Nf, 3, 4)
        """
        if indexed is None:
            self._faceColors = colors
            self._faceColorsIndexedByFaces = None
        elif indexed == 'faces':
            self._faceColors = None
            self._faceColorsIndexedByFaces = colors
        else:
            raise Exception("Invalid indexing mode. Accepts: None, 'faces'")
        
    def faceCount(self):
        """
        Return the number of faces in the mesh.
        """
        if self._faces is not None:
            return self._faces.shape[0]
        elif self._vertexesIndexedByFaces is not None:
            return self._vertexesIndexedByFaces.shape[0]
        
    def edgeColors(self):
        return self._edgeColors
        
    #def _setIndexedFaces(self, faces, vertexColors=None, faceColors=None):
        #self._vertexesIndexedByFaces = faces
        #self._vertexColorsIndexedByFaces = vertexColors
        #self._faceColorsIndexedByFaces = faceColors
        
    def _computeUnindexedVertexes(self):
        ## Given (Nv, 3, 3) array of vertexes-indexed-by-face, convert backward to unindexed vertexes
        ## This is done by collapsing into a list of 'unique' vertexes (difference < 1e-14) 
        
        ## I think generally this should be discouraged..
        
        faces = self._vertexesIndexedByFaces
        verts = {}  ## used to remember the index of each vertex position
        self._faces = np.empty(faces.shape[:2], dtype=np.uint)
        self._vertexes = []
        self._vertexFaces = []
        self._faceNormals = None
        self._vertexNormals = None
        for i in xrange(faces.shape[0]):
            face = faces[i]
            inds = []
            for j in range(face.shape[0]):
                pt = face[j]
                pt2 = tuple([round(x*1e14) for x in pt])  ## quantize to be sure that nearly-identical points will be merged
                index = verts.get(pt2, None)
                if index is None:
                    #self._vertexes.append(QtGui.QVector3D(*pt))
                    self._vertexes.append(pt)
                    self._vertexFaces.append([])
                    index = len(self._vertexes)-1
                    verts[pt2] = index
                self._vertexFaces[index].append(i)  # keep track of which vertexes belong to which faces
                self._faces[i,j] = index
        self._vertexes = np.array(self._vertexes, dtype=float)
    
    #def _setUnindexedFaces(self, faces, vertexes, vertexColors=None, faceColors=None):
        #self._vertexes = vertexes #[QtGui.QVector3D(*v) for v in vertexes]
        #self._faces = faces.astype(np.uint)
        #self._edges = None
        #self._vertexFaces = None
        #self._faceNormals = None
        #self._vertexNormals = None
        #self._vertexColors = vertexColors
        #self._faceColors = faceColors

    def vertexFaces(self):
        """
        Return list mapping each vertex index to a list of face indexes that use the vertex.
        """
        if self._vertexFaces is None:
            self._vertexFaces = [None] * len(self.vertexes())
            for i in xrange(self._faces.shape[0]):
                face = self._faces[i]
                for ind in face:
                    if self._vertexFaces[ind] is None:
                        self._vertexFaces[ind] = []  ## need a unique/empty list to fill
                    self._vertexFaces[ind].append(i)
        return self._vertexFaces
        
    #def reverseNormals(self):
        #"""
        #Reverses the direction of all normal vectors.
        #"""
        #pass
        
    #def generateEdgesFromFaces(self):
        #"""
        #Generate a set of edges by listing all the edges of faces and removing any duplicates.
        #Useful for displaying wireframe meshes.
        #"""
        #pass
        
    def _computeEdges(self):
        ## generate self._edges from self._faces
        #print self._faces
        nf = len(self._faces)
        edges = np.empty(nf*3, dtype=[('i', np.uint, 2)])
        edges['i'][0:nf] = self._faces[:,:2]
        edges['i'][nf:2*nf] = self._faces[:,1:3]
        edges['i'][-nf:,0] = self._faces[:,2]
        edges['i'][-nf:,1] = self._faces[:,0]
        
        # sort per-edge
        mask = edges['i'][:,0] > edges['i'][:,1]
        edges['i'][mask] = edges['i'][mask][:,::-1]
        
        # remove duplicate entries
        self._edges = np.unique(edges)['i']
        #print self._edges
        
        
    def save(self):
        """Serialize this mesh to a string appropriate for disk storage"""
        import pickle
        if self._faces is not None:
            names = ['_vertexes', '_faces']
        else:
            names = ['_vertexesIndexedByFaces']
            
        if self._vertexColors is not None:
            names.append('_vertexColors')
        elif self._vertexColorsIndexedByFaces is not None:
            names.append('_vertexColorsIndexedByFaces')
            
        if self._faceColors is not None:
            names.append('_faceColors')
        elif self._faceColorsIndexedByFaces is not None:
            names.append('_faceColorsIndexedByFaces')
            
        state = dict([(n,getattr(self, n)) for n in names])
        return pickle.dumps(state)
        
    def restore(self, state):
        """Restore the state of a mesh previously saved using save()"""
        import pickle
        state = pickle.loads(state)
        for k in state:
            if isinstance(state[k], list):
                if isinstance(state[k][0], QtGui.QVector3D):
                    state[k] = [[v.x(), v.y(), v.z()] for v in state[k]]
                state[k] = np.array(state[k])
            setattr(self, k, state[k])



    @staticmethod
    def sphere(rows, cols, radius=1.0, offset=True):
        """
        Return a MeshData instance with vertexes and faces computed
        for a spherical surface.
        """
        verts = np.empty((rows+1, cols, 3), dtype=float)
        
        ## compute vertexes
        phi = (np.arange(rows+1) * np.pi / rows).reshape(rows+1, 1)
        s = radius * np.sin(phi)
        verts[...,2] = radius * np.cos(phi)
        th = ((np.arange(cols) * 2 * np.pi / cols).reshape(1, cols)) 
        if offset:
            th = th + ((np.pi / cols) * np.arange(rows+1).reshape(rows+1,1))  ## rotate each row by 1/2 column
        verts[...,0] = s * np.cos(th)
        verts[...,1] = s * np.sin(th)
        verts = verts.reshape((rows+1)*cols, 3)[cols-1:-(cols-1)]  ## remove redundant vertexes from top and bottom
        
        ## compute faces
        faces = np.empty((rows*cols*2, 3), dtype=np.uint)
        rowtemplate1 = ((np.arange(cols).reshape(cols, 1) + np.array([[0, 1, 0]])) % cols) + np.array([[0, 0, cols]])
        rowtemplate2 = ((np.arange(cols).reshape(cols, 1) + np.array([[0, 1, 1]])) % cols) + np.array([[cols, 0, cols]])
        for row in range(rows):
            start = row * cols * 2 
            faces[start:start+cols] = rowtemplate1 + row * cols
            faces[start+cols:start+(cols*2)] = rowtemplate2 + row * cols
        faces = faces[cols:-cols]  ## cut off zero-area triangles at top and bottom
        
        ## adjust for redundant vertexes that were removed from top and bottom
        vmin = cols-1
        faces[faces<vmin] = vmin
        faces -= vmin  
        vmax = verts.shape[0]-1
        faces[faces>vmax] = vmax
        
        return MeshData(vertexes=verts, faces=faces)
        
        