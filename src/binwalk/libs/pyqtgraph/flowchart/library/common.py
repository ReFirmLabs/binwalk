# -*- coding: utf-8 -*-
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.widgets.SpinBox import SpinBox
#from pyqtgraph.SignalProxy import SignalProxy
from pyqtgraph.WidgetGroup import WidgetGroup
#from ColorMapper import ColorMapper
from ..Node import Node
import numpy as np
from pyqtgraph.widgets.ColorButton import ColorButton
try:
    import metaarray
    HAVE_METAARRAY = True
except:
    HAVE_METAARRAY = False


def generateUi(opts):
    """Convenience function for generating common UI types"""
    widget = QtGui.QWidget()
    l = QtGui.QFormLayout()
    l.setSpacing(0)
    widget.setLayout(l)
    ctrls = {}
    row = 0
    for opt in opts:
        if len(opt) == 2:
            k, t = opt
            o = {}
        elif len(opt) == 3:
            k, t, o = opt
        else:
            raise Exception("Widget specification must be (name, type) or (name, type, {opts})")
        if t == 'intSpin':
            w = QtGui.QSpinBox()
            if 'max' in o:
                w.setMaximum(o['max'])
            if 'min' in o:
                w.setMinimum(o['min'])
            if 'value' in o:
                w.setValue(o['value'])
        elif t == 'doubleSpin':
            w = QtGui.QDoubleSpinBox()
            if 'max' in o:
                w.setMaximum(o['max'])
            if 'min' in o:
                w.setMinimum(o['min'])                
            if 'value' in o:
                w.setValue(o['value'])
        elif t == 'spin':
            w = SpinBox()
            w.setOpts(**o)
        elif t == 'check':
            w = QtGui.QCheckBox()
            if 'checked' in o:
                w.setChecked(o['checked'])
        elif t == 'combo':
            w = QtGui.QComboBox()
            for i in o['values']:
                w.addItem(i)
        #elif t == 'colormap':
            #w = ColorMapper()
        elif t == 'color':
            w = ColorButton()
        else:
            raise Exception("Unknown widget type '%s'" % str(t))
        if 'tip' in o:
            w.setToolTip(o['tip'])
        w.setObjectName(k)
        l.addRow(k, w)
        if o.get('hidden', False):
            w.hide()
            label = l.labelForField(w)
            label.hide()
            
        ctrls[k] = w
        w.rowNum = row
        row += 1
    group = WidgetGroup(widget)
    return widget, group, ctrls


class CtrlNode(Node):
    """Abstract class for nodes with auto-generated control UI"""
    
    sigStateChanged = QtCore.Signal(object)
    
    def __init__(self, name, ui=None, terminals=None):
        if ui is None:
            if hasattr(self, 'uiTemplate'):
                ui = self.uiTemplate
            else:
                ui = []
        if terminals is None:
            terminals = {'In': {'io': 'in'}, 'Out': {'io': 'out', 'bypass': 'In'}}
        Node.__init__(self, name=name, terminals=terminals)
        
        self.ui, self.stateGroup, self.ctrls = generateUi(ui)
        self.stateGroup.sigChanged.connect(self.changed)
       
    def ctrlWidget(self):
        return self.ui
       
    def changed(self):
        self.update()
        self.sigStateChanged.emit(self)

    def process(self, In, display=True):
        out = self.processData(In)
        return {'Out': out}
    
    def saveState(self):
        state = Node.saveState(self)
        state['ctrl'] = self.stateGroup.state()
        return state
    
    def restoreState(self, state):
        Node.restoreState(self, state)
        if self.stateGroup is not None:
            self.stateGroup.setState(state.get('ctrl', {}))
            
    def hideRow(self, name):
        w = self.ctrls[name]
        l = self.ui.layout().labelForField(w)
        w.hide()
        l.hide()
        
    def showRow(self, name):
        w = self.ctrls[name]
        l = self.ui.layout().labelForField(w)
        w.show()
        l.show()



def metaArrayWrapper(fn):
    def newFn(self, data, *args, **kargs):
        if HAVE_METAARRAY and (hasattr(data, 'implements') and data.implements('MetaArray')):
            d1 = fn(self, data.view(np.ndarray), *args, **kargs)
            info = data.infoCopy()
            if d1.shape != data.shape:
                for i in range(data.ndim):
                    if 'values' in info[i]:
                        info[i]['values'] = info[i]['values'][:d1.shape[i]]
            return metaarray.MetaArray(d1, info=info)
        else:
            return fn(self, data, *args, **kargs)
    return newFn

