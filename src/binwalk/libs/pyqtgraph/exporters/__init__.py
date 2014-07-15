Exporters = []
from pyqtgraph import importModules
#from .. import frozenSupport
import os
d = os.path.split(__file__)[0]
#files = []
#for f in frozenSupport.listdir(d):
    #if frozenSupport.isdir(os.path.join(d, f)) and f != '__pycache__':
        #files.append(f)
    #elif f[-3:] == '.py' and f not in ['__init__.py', 'Exporter.py']:
        #files.append(f[:-3])
    
#for modName in files:
    #mod = __import__(modName, globals(), locals(), fromlist=['*'])
for mod in importModules('', globals(), locals(), excludes=['Exporter']).values():
    if hasattr(mod, '__all__'):
        names = mod.__all__
    else:
        names = [n for n in dir(mod) if n[0] != '_']
    for k in names:
        if hasattr(mod, k):
            Exporters.append(getattr(mod, k))


def listExporters():
    return Exporters[:]

