# -*- coding: utf-8 -*-
import initExample ## Add path to library (just for examples; you do not need this)
import numpy as np
import pyqtgraph.multiprocess as mp
import pyqtgraph as pg
import time




print("\n=================\nStart Process")
proc = mp.Process()
import os
print("parent:", os.getpid(), "child:", proc.proc.pid)
print("started")
rnp = proc._import('numpy')
arr = rnp.array([1,2,3,4])
print(repr(arr))
print(str(arr))
print("return value:", repr(arr.mean(_returnType='value')))
print( "return proxy:", repr(arr.mean(_returnType='proxy')))
print( "return auto: ", repr(arr.mean(_returnType='auto')))
proc.join()
print( "process finished")



print( "\n=================\nStart ForkedProcess")
proc = mp.ForkedProcess()
rnp = proc._import('numpy')
arr = rnp.array([1,2,3,4])
print( repr(arr))
print( str(arr))
print( repr(arr.mean()))
proc.join()
print( "process finished")




import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
app = pg.QtGui.QApplication([])

print( "\n=================\nStart QtProcess")
import sys
if (sys.flags.interactive != 1):
    print( "   (not interactive; remote process will exit immediately.)")
proc = mp.QtProcess()
d1 = proc.transfer(np.random.normal(size=1000))
d2 = proc.transfer(np.random.normal(size=1000))
rpg = proc._import('pyqtgraph')
plt = rpg.plot(d1+d2)


## Start Qt event loop unless running in interactive mode or using pyside.
#import sys
#if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    #QtGui.QApplication.instance().exec_()
