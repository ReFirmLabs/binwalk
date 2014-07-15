# -*- coding: utf-8 -*-
"""
This example demonstrates writing a custom Node subclass for use with flowcharts.

We implement a couple of simple image processing nodes.
"""
import initExample ## Add path to library (just for examples; you do not need this)

from pyqtgraph.flowchart import Flowchart, Node
import pyqtgraph.flowchart.library as fclib
from pyqtgraph.flowchart.library.common import CtrlNode
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
import scipy.ndimage

app = QtGui.QApplication([])

## Create main window with a grid layout inside
win = QtGui.QMainWindow()
win.setWindowTitle('pyqtgraph example: FlowchartCustomNode')
cw = QtGui.QWidget()
win.setCentralWidget(cw)
layout = QtGui.QGridLayout()
cw.setLayout(layout)

## Create an empty flowchart with a single input and output
fc = Flowchart(terminals={
    'dataIn': {'io': 'in'},
    'dataOut': {'io': 'out'}    
})
w = fc.widget()

layout.addWidget(fc.widget(), 0, 0, 2, 1)

## Create two ImageView widgets to display the raw and processed data with contrast
## and color control.
v1 = pg.ImageView()
v2 = pg.ImageView()
layout.addWidget(v1, 0, 1)
layout.addWidget(v2, 1, 1)

win.show()

## generate random input data
data = np.random.normal(size=(100,100))
data = 25 * scipy.ndimage.gaussian_filter(data, (5,5))
data += np.random.normal(size=(100,100))
data[40:60, 40:60] += 15.0
data[30:50, 30:50] += 15.0
#data += np.sin(np.linspace(0, 100, 1000))
#data = metaarray.MetaArray(data, info=[{'name': 'Time', 'values': np.linspace(0, 1.0, len(data))}, {}])

## Set the raw data as the input value to the flowchart
fc.setInput(dataIn=data)


## At this point, we need some custom Node classes since those provided in the library
## are not sufficient. Each node will define a set of input/output terminals, a 
## processing function, and optionally a control widget (to be displayed in the 
## flowchart control panel)

class ImageViewNode(Node):
    """Node that displays image data in an ImageView widget"""
    nodeName = 'ImageView'
    
    def __init__(self, name):
        self.view = None
        ## Initialize node with only a single input terminal
        Node.__init__(self, name, terminals={'data': {'io':'in'}})
        
    def setView(self, view):  ## setView must be called by the program
        self.view = view
        
    def process(self, data, display=True):
        ## if process is called with display=False, then the flowchart is being operated
        ## in batch processing mode, so we should skip displaying to improve performance.
        
        if display and self.view is not None:
            ## the 'data' argument is the value given to the 'data' terminal
            if data is None:
                self.view.setImage(np.zeros((1,1))) # give a blank array to clear the view
            else:
                self.view.setImage(data)

## register the class so it will appear in the menu of node types.
## It will appear in the 'display' sub-menu.
fclib.registerNodeType(ImageViewNode, [('Display',)])
        
## We will define an unsharp masking filter node as a subclass of CtrlNode.
## CtrlNode is just a convenience class that automatically creates its
## control widget based on a simple data structure.
class UnsharpMaskNode(CtrlNode):
    """Return the input data passed through scipy.ndimage.gaussian_filter."""
    nodeName = "UnsharpMask"
    uiTemplate = [
        ('sigma',  'spin', {'value': 1.0, 'step': 1.0, 'range': [0.0, None]}),
        ('strength', 'spin', {'value': 1.0, 'dec': True, 'step': 0.5, 'minStep': 0.01, 'range': [0.0, None]}),
    ]
    def __init__(self, name):
        ## Define the input / output terminals available on this node
        terminals = {
            'dataIn': dict(io='in'),    # each terminal needs at least a name and
            'dataOut': dict(io='out'),  # to specify whether it is input or output
        }                              # other more advanced options are available
                                       # as well..
        
        CtrlNode.__init__(self, name, terminals=terminals)
        
    def process(self, dataIn, display=True):
        # CtrlNode has created self.ctrls, which is a dict containing {ctrlName: widget}
        sigma = self.ctrls['sigma'].value()
        strength = self.ctrls['strength'].value()
        output = dataIn - (strength * scipy.ndimage.gaussian_filter(dataIn, (sigma,sigma)))
        return {'dataOut': output}
        
## register the class so it will appear in the menu of node types.
## It will appear in a new 'image' sub-menu.
fclib.registerNodeType(UnsharpMaskNode, [('Image',)])
    
    

## Now we will programmatically add nodes to define the function of the flowchart.
## Normally, the user will do this manually or by loading a pre-generated
## flowchart file.

v1Node = fc.createNode('ImageView', pos=(0, -150))
v1Node.setView(v1)

v2Node = fc.createNode('ImageView', pos=(150, -150))
v2Node.setView(v2)

fNode = fc.createNode('UnsharpMask', pos=(0, 0))
fc.connectTerminals(fc['dataIn'], fNode['dataIn'])
fc.connectTerminals(fc['dataIn'], v1Node['data'])
fc.connectTerminals(fNode['dataOut'], v2Node['data'])
fc.connectTerminals(fNode['dataOut'], fc['dataOut'])



## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
