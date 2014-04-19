from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph.parametertree as ptree
import numpy as np
from pyqtgraph.pgcollections import OrderedDict
import pyqtgraph as pg

__all__ = ['DataFilterWidget']

class DataFilterWidget(ptree.ParameterTree):
    """
    This class allows the user to filter multi-column data sets by specifying
    multiple criteria
    """
    
    sigFilterChanged = QtCore.Signal(object)
    
    def __init__(self):
        ptree.ParameterTree.__init__(self, showHeader=False)
        self.params = DataFilterParameter()
        
        self.setParameters(self.params)
        self.params.sigTreeStateChanged.connect(self.filterChanged)
        
        self.setFields = self.params.setFields
        self.filterData = self.params.filterData
        self.describe = self.params.describe
        
    def filterChanged(self):
        self.sigFilterChanged.emit(self)
        
    def parameters(self):
        return self.params
        
        
class DataFilterParameter(ptree.types.GroupParameter):
    
    sigFilterChanged = QtCore.Signal(object)
    
    def __init__(self):
        self.fields = {}
        ptree.types.GroupParameter.__init__(self, name='Data Filter', addText='Add filter..', addList=[])
        self.sigTreeStateChanged.connect(self.filterChanged)
    
    def filterChanged(self):
        self.sigFilterChanged.emit(self)
        
    def addNew(self, name):
        mode = self.fields[name].get('mode', 'range')
        if mode == 'range':
            self.addChild(RangeFilterItem(name, self.fields[name]))
        elif mode == 'enum':
            self.addChild(EnumFilterItem(name, self.fields[name]))
            
            
    def fieldNames(self):
        return self.fields.keys()
    
    def setFields(self, fields):
        self.fields = OrderedDict(fields)
        names = self.fieldNames()
        self.setAddList(names)
    
    def filterData(self, data):
        if len(data) == 0:
            return data
        return data[self.generateMask(data)]
    
    def generateMask(self, data):
        mask = np.ones(len(data), dtype=bool)
        if len(data) == 0:
            return mask
        for fp in self:
            if fp.value() is False:
                continue
            mask &= fp.generateMask(data, mask.copy())
            #key, mn, mx = fp.fieldName, fp['Min'], fp['Max']
            
            #vals = data[key]
            #mask &= (vals >= mn)
            #mask &= (vals < mx)  ## Use inclusive minimum and non-inclusive maximum. This makes it easier to create non-overlapping selections
        return mask
    
    def describe(self):
        """Return a list of strings describing the currently enabled filters."""
        desc = []
        for fp in self:
            if fp.value() is False:
                continue
            desc.append(fp.describe())
        return desc

class RangeFilterItem(ptree.types.SimpleParameter):
    def __init__(self, name, opts):
        self.fieldName = name
        units = opts.get('units', '')
        self.units = units
        ptree.types.SimpleParameter.__init__(self, 
            name=name, autoIncrementName=True, type='bool', value=True, removable=True, renamable=True, 
            children=[
                #dict(name="Field", type='list', value=name, values=fields),
                dict(name='Min', type='float', value=0.0, suffix=units, siPrefix=True),
                dict(name='Max', type='float', value=1.0, suffix=units, siPrefix=True),
            ])
            
    def generateMask(self, data, mask):
        vals = data[self.fieldName][mask]
        mask[mask] = (vals >= self['Min']) & (vals < self['Max'])  ## Use inclusive minimum and non-inclusive maximum. This makes it easier to create non-overlapping selections
        return mask
    
    def describe(self):
        return "%s < %s < %s" % (pg.siFormat(self['Min'], suffix=self.units), self.fieldName, pg.siFormat(self['Max'], suffix=self.units))
    
class EnumFilterItem(ptree.types.SimpleParameter):
    def __init__(self, name, opts):
        self.fieldName = name
        vals = opts.get('values', [])
        childs = []
        if isinstance(vals, list):
            vals = OrderedDict([(v,str(v)) for v in vals])
        for val,vname in vals.items():
            ch = ptree.Parameter.create(name=vname, type='bool', value=True)
            ch.maskValue = val
            childs.append(ch)
        ch = ptree.Parameter.create(name='(other)', type='bool', value=True)
        ch.maskValue = '__other__'
        childs.append(ch)
            
        ptree.types.SimpleParameter.__init__(self, 
            name=name, autoIncrementName=True, type='bool', value=True, removable=True, renamable=True, 
            children=childs)
    
    def generateMask(self, data, startMask):
        vals = data[self.fieldName][startMask]
        mask = np.ones(len(vals), dtype=bool)
        otherMask = np.ones(len(vals), dtype=bool)
        for c in self:
            key = c.maskValue
            if key == '__other__':
                m = ~otherMask
            else:
                m = vals != key
                otherMask &= m
            if c.value() is False:
                mask &= m
        startMask[startMask] = mask
        return startMask

    def describe(self):
        vals = [ch.name() for ch in self if ch.value() is True]
        return "%s: %s" % (self.fieldName, ', '.join(vals))