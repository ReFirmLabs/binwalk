"""
Allows easy loading of pixmaps used in UI elements. 
Provides support for frozen environments as well.
"""

import os, sys, pickle
from ..functions import makeQImage
from ..Qt import QtGui
if sys.version_info[0] == 2:
    from . import pixmapData_2 as pixmapData
else:
    from . import pixmapData_3 as pixmapData


def getPixmap(name):
    """
    Return a QPixmap corresponding to the image file with the given name.
    (eg. getPixmap('auto') loads pyqtgraph/pixmaps/auto.png)
    """
    key = name+'.png'
    data = pixmapData.pixmapData[key]
    if isinstance(data, basestring) or isinstance(data, bytes):
        pixmapData.pixmapData[key] = pickle.loads(data)
    arr = pixmapData.pixmapData[key]
    return QtGui.QPixmap(makeQImage(arr, alpha=True))
    
