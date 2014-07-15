import numpy as np
from PyQt4 import QtGui
import os, pickle, sys

path = os.path.abspath(os.path.split(__file__)[0])
pixmaps = {}
for f in os.listdir(path):
    if not f.endswith('.png'):
        continue
    print(f)
    img = QtGui.QImage(os.path.join(path, f))
    ptr = img.bits()
    ptr.setsize(img.byteCount())
    arr = np.asarray(ptr).reshape(img.height(), img.width(), 4).transpose(1,0,2)
    pixmaps[f] = pickle.dumps(arr)
ver = sys.version_info[0]
fh = open(os.path.join(path, 'pixmapData_%d.py' %ver), 'w')
fh.write("import numpy as np; pixmapData=%s" % repr(pixmaps))
    
