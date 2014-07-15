from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph.parametertree as ptree
import numpy as np
from pyqtgraph.pgcollections import OrderedDict
import pyqtgraph.functions as fn

__all__ = ['ColorMapWidget']

class ColorMapWidget(ptree.ParameterTree):
    """
    This class provides a widget allowing the user to customize color mapping
    for multi-column data. Given a list of field names, the user may specify
    multiple criteria for assigning colors to each record in a numpy record array.
    Multiple criteria are evaluated and combined into a single color for each
    record by user-defined compositing methods.
    
    For simpler color mapping using a single gradient editor, see 
    :class:`GradientWidget <pyqtgraph.GradientWidget>`
    """
    sigColorMapChanged = QtCore.Signal(object)
    
    def __init__(self):
        ptree.ParameterTree.__init__(self, showHeader=False)
        
        self.params = ColorMapParameter()
        self.setParameters(self.params)
        self.params.sigTreeStateChanged.connect(self.mapChanged)
        
        ## wrap a couple methods 
        self.setFields = self.params.setFields
        self.map = self.params.map

    def mapChanged(self):
        self.sigColorMapChanged.emit(self)
        

class ColorMapParameter(ptree.types.GroupParameter):
    sigColorMapChanged = QtCore.Signal(object)
    
    def __init__(self):
        self.fields = {}
        ptree.types.GroupParameter.__init__(self, name='Color Map', addText='Add Mapping..', addList=[])
        self.sigTreeStateChanged.connect(self.mapChanged)
        
    def mapChanged(self):
        self.sigColorMapChanged.emit(self)
        
    def addNew(self, name):
        mode = self.fields[name].get('mode', 'range')
        if mode == 'range':
            self.addChild(RangeColorMapItem(name, self.fields[name]))
        elif mode == 'enum':
            self.addChild(EnumColorMapItem(name, self.fields[name]))
        
    def fieldNames(self):
        return self.fields.keys()
    
    def setFields(self, fields):
        """
        Set the list of fields to be used by the mapper. 
        
        The format of *fields* is::
        
            [ (fieldName, {options}), ... ]
        
        ============== ============================================================
        Field Options:
        mode           Either 'range' or 'enum' (default is range). For 'range', 
                       The user may specify a gradient of colors to be applied 
                       linearly across a specific range of values. For 'enum', 
                       the user specifies a single color for each unique value
                       (see *values* option).
        units          String indicating the units of the data for this field.
        values         List of unique values for which the user may assign a 
                       color when mode=='enum'. Optionally may specify a dict 
                       instead {value: name}.
        ============== ============================================================
        """
        self.fields = OrderedDict(fields)
        #self.fields = fields
        #self.fields.sort()
        names = self.fieldNames()
        self.setAddList(names)
        
    def map(self, data, mode='byte'):
        """
        Return an array of colors corresponding to *data*. 
        
        ========= =================================================================
        Arguments
        data      A numpy record array where the fields in data.dtype match those
                  defined by a prior call to setFields().
        mode      Either 'byte' or 'float'. For 'byte', the method returns an array
                  of dtype ubyte with values scaled 0-255. For 'float', colors are
                  returned as 0.0-1.0 float values.
        ========= =================================================================
        """
        colors = np.zeros((len(data),4))
        for item in self.children():
            if not item['Enabled']:
                continue
            chans = item.param('Channels..')
            mask = np.empty((len(data), 4), dtype=bool)
            for i,f in enumerate(['Red', 'Green', 'Blue', 'Alpha']):
                mask[:,i] = chans[f]
            
            colors2 = item.map(data)
            
            op = item['Operation']
            if op == 'Add':
                colors[mask] = colors[mask] + colors2[mask]
            elif op == 'Multiply':
                colors[mask] *= colors2[mask]
            elif op == 'Overlay':
                a = colors2[:,3:4]
                c3 = colors * (1-a) + colors2 * a
                c3[:,3:4] = colors[:,3:4] + (1-colors[:,3:4]) * a
                colors = c3
            elif op == 'Set':
                colors[mask] = colors2[mask]
            
                
        colors = np.clip(colors, 0, 1)
        if mode == 'byte':
            colors = (colors * 255).astype(np.ubyte)
        
        return colors
            
    
class RangeColorMapItem(ptree.types.SimpleParameter):
    def __init__(self, name, opts):
        self.fieldName = name
        units = opts.get('units', '')
        ptree.types.SimpleParameter.__init__(self, 
            name=name, autoIncrementName=True, type='colormap', removable=True, renamable=True, 
            children=[
                #dict(name="Field", type='list', value=name, values=fields),
                dict(name='Min', type='float', value=0.0, suffix=units, siPrefix=True),
                dict(name='Max', type='float', value=1.0, suffix=units, siPrefix=True),
                dict(name='Operation', type='list', value='Overlay', values=['Overlay', 'Add', 'Multiply', 'Set']),
                dict(name='Channels..', type='group', expanded=False, children=[
                    dict(name='Red', type='bool', value=True),
                    dict(name='Green', type='bool', value=True),
                    dict(name='Blue', type='bool', value=True),
                    dict(name='Alpha', type='bool', value=True),
                    ]),
                dict(name='Enabled', type='bool', value=True),
                dict(name='NaN', type='color'),
            ])
    
    def map(self, data):
        data = data[self.fieldName]
        
        
        
        scaled = np.clip((data-self['Min']) / (self['Max']-self['Min']), 0, 1)
        cmap = self.value()
        colors = cmap.map(scaled, mode='float')
        
        mask = np.isnan(data) | np.isinf(data)
        nanColor = self['NaN']
        nanColor = (nanColor.red()/255., nanColor.green()/255., nanColor.blue()/255., nanColor.alpha()/255.)
        colors[mask] = nanColor
        
        return colors


class EnumColorMapItem(ptree.types.GroupParameter):
    def __init__(self, name, opts):
        self.fieldName = name
        vals = opts.get('values', [])
        if isinstance(vals, list):
            vals = OrderedDict([(v,str(v)) for v in vals])
        childs = [{'name': v, 'type': 'color'} for v in vals]
        
        childs = []
        for val,vname in vals.items():
            ch = ptree.Parameter.create(name=vname, type='color')
            ch.maskValue = val
            childs.append(ch)
        
        ptree.types.GroupParameter.__init__(self, 
            name=name, autoIncrementName=True, removable=True, renamable=True, 
            children=[
                dict(name='Values', type='group', children=childs),
                dict(name='Operation', type='list', value='Overlay', values=['Overlay', 'Add', 'Multiply', 'Set']),
                dict(name='Channels..', type='group', expanded=False, children=[
                    dict(name='Red', type='bool', value=True),
                    dict(name='Green', type='bool', value=True),
                    dict(name='Blue', type='bool', value=True),
                    dict(name='Alpha', type='bool', value=True),
                    ]),
                dict(name='Enabled', type='bool', value=True),
                dict(name='Default', type='color'),
            ])
    
    def map(self, data):
        data = data[self.fieldName]
        colors = np.empty((len(data), 4))
        default = np.array(fn.colorTuple(self['Default'])) / 255.
        colors[:] = default
        
        for v in self.param('Values'):
            mask = data == v.maskValue
            c = np.array(fn.colorTuple(v.value())) / 255.
            colors[mask] = c
        #scaled = np.clip((data-self['Min']) / (self['Max']-self['Min']), 0, 1)
        #cmap = self.value()
        #colors = cmap.map(scaled, mode='float')
        
        #mask = np.isnan(data) | np.isinf(data)
        #nanColor = self['NaN']
        #nanColor = (nanColor.red()/255., nanColor.green()/255., nanColor.blue()/255., nanColor.alpha()/255.)
        #colors[mask] = nanColor
        
        return colors


