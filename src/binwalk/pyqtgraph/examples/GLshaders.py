# -*- coding: utf-8 -*-
"""
Demonstration of some of the shader programs included with pyqtgraph that can be 
used to affect the appearance of a surface.
"""



## Add path to library (just for examples; you do not need this)
import initExample

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.opengl as gl

app = QtGui.QApplication([])
w = gl.GLViewWidget()
w.show()
w.setWindowTitle('pyqtgraph example: GL Shaders')
w.setCameraPosition(distance=15, azimuth=-90)

g = gl.GLGridItem()
g.scale(2,2,1)
w.addItem(g)

import numpy as np


md = gl.MeshData.sphere(rows=10, cols=20)
x = np.linspace(-8, 8, 6)

m1 = gl.GLMeshItem(meshdata=md, smooth=True, color=(1, 0, 0, 0.2), shader='balloon', glOptions='additive')
m1.translate(x[0], 0, 0)
m1.scale(1, 1, 2)
w.addItem(m1)

m2 = gl.GLMeshItem(meshdata=md, smooth=True, shader='normalColor', glOptions='opaque')
m2.translate(x[1], 0, 0)
m2.scale(1, 1, 2)
w.addItem(m2)

m3 = gl.GLMeshItem(meshdata=md, smooth=True, shader='viewNormalColor', glOptions='opaque')
m3.translate(x[2], 0, 0)
m3.scale(1, 1, 2)
w.addItem(m3)

m4 = gl.GLMeshItem(meshdata=md, smooth=True, shader='shaded', glOptions='opaque')
m4.translate(x[3], 0, 0)
m4.scale(1, 1, 2)
w.addItem(m4)

m5 = gl.GLMeshItem(meshdata=md, smooth=True, color=(1, 0, 0, 1), shader='edgeHilight', glOptions='opaque')
m5.translate(x[4], 0, 0)
m5.scale(1, 1, 2)
w.addItem(m5)

m6 = gl.GLMeshItem(meshdata=md, smooth=True, color=(1, 0, 0, 1), shader='heightColor', glOptions='opaque')
m6.translate(x[5], 0, 0)
m6.scale(1, 1, 2)
w.addItem(m6)




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
