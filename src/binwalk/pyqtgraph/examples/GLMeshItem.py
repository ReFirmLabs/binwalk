# -*- coding: utf-8 -*-
"""
Simple examples demonstrating the use of GLMeshItem.

"""

## Add path to library (just for examples; you do not need this)
import initExample

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.opengl as gl

app = QtGui.QApplication([])
w = gl.GLViewWidget()
w.show()
w.setWindowTitle('pyqtgraph example: GLMeshItem')
w.setCameraPosition(distance=40)

g = gl.GLGridItem()
g.scale(2,2,1)
w.addItem(g)

import numpy as np


## Example 1:
## Array of vertex positions and array of vertex indexes defining faces
## Colors are specified per-face

verts = np.array([
    [0, 0, 0],
    [2, 0, 0],
    [1, 2, 0],
    [1, 1, 1],
])
faces = np.array([
    [0, 1, 2],
    [0, 1, 3],
    [0, 2, 3],
    [1, 2, 3]
])
colors = np.array([
    [1, 0, 0, 0.3],
    [0, 1, 0, 0.3],
    [0, 0, 1, 0.3],
    [1, 1, 0, 0.3]
])

## Mesh item will automatically compute face normals.
m1 = gl.GLMeshItem(vertexes=verts, faces=faces, faceColors=colors, smooth=False)
m1.translate(5, 5, 0)
m1.setGLOptions('additive')
w.addItem(m1)

## Example 2:
## Array of vertex positions, three per face
## Colors are specified per-vertex

verts = verts[faces]  ## Same mesh geometry as example 2, but now we are passing in 12 vertexes
colors = np.random.random(size=(verts.shape[0], 3, 4))
#colors[...,3] = 1.0

m2 = gl.GLMeshItem(vertexes=verts, vertexColors=colors, smooth=False, shader='balloon')
m2.translate(-5, 5, 0)
w.addItem(m2)


## Example 3:
## icosahedron

md = gl.MeshData.sphere(rows=10, cols=20)
#colors = np.random.random(size=(md.faceCount(), 4))
#colors[:,3] = 0.3
#colors[100:] = 0.0
colors = np.ones((md.faceCount(), 4), dtype=float)
colors[::2,0] = 0
colors[:,1] = np.linspace(0, 1, colors.shape[0])
md.setFaceColors(colors)
m3 = gl.GLMeshItem(meshdata=md, smooth=False)#, shader='balloon')

#m3.translate(-5, -5, 0)
w.addItem(m3)


# Example 4:
# wireframe

md = gl.MeshData.sphere(rows=4, cols=8)
m4 = gl.GLMeshItem(meshdata=md, smooth=False, drawFaces=False, drawEdges=True, edgeColor=(1,1,1,1))
m4.translate(0,10,0)
w.addItem(m4)






#def psi(i, j, k, offset=(25, 25, 50)):
    #x = i-offset[0]
    #y = j-offset[1]
    #z = k-offset[2]
    #th = np.arctan2(z, (x**2+y**2)**0.5)
    #phi = np.arctan2(y, x)
    #r = (x**2 + y**2 + z **2)**0.5
    #a0 = 1
    ##ps = (1./81.) * (2./np.pi)**0.5 * (1./a0)**(3/2) * (6 - r/a0) * (r/a0) * np.exp(-r/(3*a0)) * np.cos(th)
    #ps = (1./81.) * 1./(6.*np.pi)**0.5 * (1./a0)**(3/2) * (r/a0)**2 * np.exp(-r/(3*a0)) * (3 * np.cos(th)**2 - 1)
    
    #return ps
    
    ##return ((1./81.) * (1./np.pi)**0.5 * (1./a0)**(3/2) * (r/a0)**2 * (r/a0) * np.exp(-r/(3*a0)) * np.sin(th) * np.cos(th) * np.exp(2 * 1j * phi))**2 


#print("Generating scalar field..")
#data = np.abs(np.fromfunction(psi, (50,50,100)))


##data = np.fromfunction(lambda i,j,k: np.sin(0.2*((i-25)**2+(j-15)**2+k**2)**0.5), (50,50,50)); 
#print("Generating isosurface..")
#verts = pg.isosurface(data, data.max()/4.)

#md = gl.MeshData.MeshData(vertexes=verts)

#colors = np.ones((md.vertexes(indexed='faces').shape[0], 4), dtype=float)
#colors[:,3] = 0.3
#colors[:,2] = np.linspace(0, 1, colors.shape[0])
#m1 = gl.GLMeshItem(meshdata=md, color=colors, smooth=False)

#w.addItem(m1)
#m1.translate(-25, -25, -20)

#m2 = gl.GLMeshItem(vertexes=verts, color=colors, smooth=True)

#w.addItem(m2)
#m2.translate(-25, -25, -50)
    


## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
