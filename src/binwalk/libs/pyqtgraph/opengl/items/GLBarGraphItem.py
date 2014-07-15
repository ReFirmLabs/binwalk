from .GLMeshItem import GLMeshItem
from ..MeshData import MeshData
import numpy as np

class GLBarGraphItem(GLMeshItem):
    def __init__(self, pos, size):
        """
        pos is (...,3) array of the bar positions (the corner of each bar)
        size is (...,3) array of the sizes of each bar
        """
        nCubes = reduce(lambda a,b: a*b, pos.shape[:-1])
        cubeVerts = np.mgrid[0:2,0:2,0:2].reshape(3,8).transpose().reshape(1,8,3)
        cubeFaces = np.array([
            [0,1,2], [3,2,1],
            [4,5,6], [7,6,5],
            [0,1,4], [5,4,1],
            [2,3,6], [7,6,3],
            [0,2,4], [6,4,2],
            [1,3,5], [7,5,3]]).reshape(1,12,3)
        size = size.reshape((nCubes, 1, 3))
        pos = pos.reshape((nCubes, 1, 3))
        verts = cubeVerts * size + pos
        faces = cubeFaces + (np.arange(nCubes) * 8).reshape(nCubes,1,1)
        md = MeshData(verts.reshape(nCubes*8,3), faces.reshape(nCubes*12,3))
        
        GLMeshItem.__init__(self, meshdata=md, shader='shaded', smooth=False)

        
        