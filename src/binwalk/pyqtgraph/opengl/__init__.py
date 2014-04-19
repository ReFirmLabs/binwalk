from .GLViewWidget import GLViewWidget

from pyqtgraph import importAll
#import os
#def importAll(path):
    #d = os.path.join(os.path.split(__file__)[0], path)
    #files = []
    #for f in os.listdir(d):
        #if os.path.isdir(os.path.join(d, f)) and f != '__pycache__':
            #files.append(f)
        #elif f[-3:] == '.py' and f != '__init__.py':
            #files.append(f[:-3])
        
    #for modName in files:
        #mod = __import__(path+"."+modName, globals(), locals(), fromlist=['*'])
        #if hasattr(mod, '__all__'):
            #names = mod.__all__
        #else:
            #names = [n for n in dir(mod) if n[0] != '_']
        #for k in names:
            #if hasattr(mod, k):
                #globals()[k] = getattr(mod, k)

importAll('items', globals(), locals())
\
from .MeshData import MeshData
## for backward compatibility:
#MeshData.MeshData = MeshData  ## breaks autodoc.

from . import shaders
