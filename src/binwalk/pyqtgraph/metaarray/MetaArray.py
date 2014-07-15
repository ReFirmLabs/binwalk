# -*- coding: utf-8 -*-
"""
MetaArray.py -  Class encapsulating ndarray with meta data
Copyright 2010  Luke Campagnola
Distributed under MIT/X11 license. See license.txt for more infomation.

MetaArray is an array class based on numpy.ndarray that allows storage of per-axis meta data
such as axis values, names, units, column names, etc. It also enables several
new methods for slicing and indexing the array based on this meta data. 
More info at http://www.scipy.org/Cookbook/MetaArray
"""

import numpy as np
import types, copy, threading, os, re
import pickle
from functools import reduce
#import traceback

## By default, the library will use HDF5 when writing files.
## This can be overridden by setting USE_HDF5 = False
USE_HDF5 = True
try:
    import h5py
    HAVE_HDF5 = True
except:
    USE_HDF5 = False
    HAVE_HDF5 = False


def axis(name=None, cols=None, values=None, units=None):
    """Convenience function for generating axis descriptions when defining MetaArrays"""
    ax = {}
    cNameOrder = ['name', 'units', 'title']
    if name is not None:
        ax['name'] = name
    if values is not None:
        ax['values'] = values
    if units is not None:
        ax['units'] = units
    if cols is not None:
        ax['cols'] = []
        for c in cols:
            if type(c) != list and type(c) != tuple:
                c = [c]
            col = {}
            for i in range(0,len(c)):
                col[cNameOrder[i]] = c[i]
            ax['cols'].append(col)
    return ax

class sliceGenerator(object):
    """Just a compact way to generate tuples of slice objects."""
    def __getitem__(self, arg):
        return arg
    def __getslice__(self, arg):
        return arg
SLICER = sliceGenerator()
    

class MetaArray(object):
    """N-dimensional array with meta data such as axis titles, units, and column names.
  
    May be initialized with a file name, a tuple representing the dimensions of the array,
    or any arguments that could be passed on to numpy.array()
  
    The info argument sets the metadata for the entire array. It is composed of a list
    of axis descriptions where each axis may have a name, title, units, and a list of column 
    descriptions. An additional dict at the end of the axis list may specify parameters
    that apply to values in the entire array.
  
    For example:
        A 2D array of altitude values for a topographical map might look like
            info=[
        {'name': 'lat', 'title': 'Lattitude'}, 
        {'name': 'lon', 'title': 'Longitude'}, 
        {'title': 'Altitude', 'units': 'm'}
      ]
        In this case, every value in the array represents the altitude in feet at the lat, lon
        position represented by the array index. All of the following return the 
        value at lat=10, lon=5:
            array[10, 5]
            array['lon':5, 'lat':10]
            array['lat':10][5]
        Now suppose we want to combine this data with another array of equal dimensions that
        represents the average rainfall for each location. We could easily store these as two 
        separate arrays or combine them into a 3D array with this description:
            info=[
        {'name': 'vals', 'cols': [
          {'name': 'altitude', 'units': 'm'}, 
          {'name': 'rainfall', 'units': 'cm/year'}
        ]},
        {'name': 'lat', 'title': 'Lattitude'}, 
        {'name': 'lon', 'title': 'Longitude'}
      ]
        We can now access the altitude values with array[0] or array['altitude'], and the
        rainfall values with array[1] or array['rainfall']. All of the following return
        the rainfall value at lat=10, lon=5:
            array[1, 10, 5]
            array['lon':5, 'lat':10, 'val': 'rainfall']
            array['rainfall', 'lon':5, 'lat':10]
        Notice that in the second example, there is no need for an extra (4th) axis description
        since the actual values are described (name and units) in the column info for the first axis.
    """
  
    version = '2'
    
    ## Types allowed as axis or column names
    nameTypes = [basestring, tuple]
    @staticmethod
    def isNameType(var):
        return any([isinstance(var, t) for t in MetaArray.nameTypes])
        
        
    ## methods to wrap from embedded ndarray / HDF5 
    wrapMethods = set(['__eq__', '__ne__', '__le__', '__lt__', '__ge__', '__gt__'])
  
    def __init__(self, data=None, info=None, dtype=None, file=None, copy=False, **kwargs):
        object.__init__(self)
        #self._infoOwned = False
        self._isHDF = False
        
        if file is not None:
            self._data = None
            self.readFile(file, **kwargs)
            if self._data is None:
                raise Exception("File read failed: %s" % file)
        else:
            self._info = info
            if (hasattr(data, 'implements') and data.implements('MetaArray')):
                self._info = data._info
                self._data = data.asarray()
            elif isinstance(data, tuple):  ## create empty array with specified shape
                self._data = np.empty(data, dtype=dtype)
            else:
                self._data = np.array(data, dtype=dtype, copy=copy)

        ## run sanity checks on info structure
        self.checkInfo()
    
    def checkInfo(self):
        info = self._info
        if info is None:
            if self._data is None:
                return
            else:
                self._info = [{} for i in range(self.ndim)]
                return
        else:
            try:
                info = list(info)
            except:
                raise Exception("Info must be a list of axis specifications")
            if len(info) < self.ndim+1:
                info.extend([{}]*(self.ndim+1-len(info)))
            elif len(info) > self.ndim+1:
                raise Exception("Info parameter must be list of length ndim+1 or less.")
            for i in range(len(info)):
                if not isinstance(info[i], dict):
                    if info[i] is None:
                        info[i] = {}
                    else:
                        raise Exception("Axis specification must be Dict or None")
                if i < self.ndim and 'values' in info[i]:
                    if type(info[i]['values']) is list:
                        info[i]['values'] = np.array(info[i]['values'])
                    elif type(info[i]['values']) is not np.ndarray:
                        raise Exception("Axis values must be specified as list or ndarray")
                    if info[i]['values'].ndim != 1 or info[i]['values'].shape[0] != self.shape[i]:
                        raise Exception("Values array for axis %d has incorrect shape. (given %s, but should be %s)" % (i, str(info[i]['values'].shape), str((self.shape[i],))))
                if i < self.ndim and 'cols' in info[i]:
                    if not isinstance(info[i]['cols'], list):
                        info[i]['cols'] = list(info[i]['cols'])
                    if len(info[i]['cols']) != self.shape[i]:
                        raise Exception('Length of column list for axis %d does not match data. (given %d, but should be %d)' % (i, len(info[i]['cols']), self.shape[i]))
   
    def implements(self, name=None):
        ## Rather than isinstance(obj, MetaArray) use object.implements('MetaArray')
        if name is None:
            return ['MetaArray']
        else:
            return name == 'MetaArray'
    
    #def __array_finalize__(self,obj):
        ### array_finalize is called every time a MetaArray is created 
        ### (whereas __new__ is not necessarily called every time)
        
        ### obj is the object from which this array was generated (for example, when slicing or view()ing)
        
        ## We use the getattr method to set a default if 'obj' doesn't have the 'info' attribute
        ##print "Create new MA from object", str(type(obj))
        ##import traceback
        ##traceback.print_stack()
        ##print "finalize", type(self), type(obj)
        #if not hasattr(self, '_info'):
            ##if isinstance(obj, MetaArray):
                ##print "  copy info:", obj._info
            #self._info = getattr(obj, '_info', [{}]*(obj.ndim+1))
            #self._infoOwned = False  ## Do not make changes to _info until it is copied at least once
        ##print "  self info:", self._info
      
        ## We could have checked first whether self._info was already defined:
        ##if not hasattr(self, 'info'):
        ##    self._info = getattr(obj, 'info', {})
    
  
    def __getitem__(self, ind):
        #print "getitem:", ind
        
        ## should catch scalar requests as early as possible to speed things up (?)
        
        nInd = self._interpretIndexes(ind)
        
        #a = np.ndarray.__getitem__(self, nInd)
        a = self._data[nInd]
        if len(nInd) == self.ndim:
            if np.all([not isinstance(ind, slice) for ind in nInd]):  ## no slices; we have requested a single value from the array
                return a
        #if type(a) != type(self._data) and not isinstance(a, np.ndarray):  ## indexing returned single value
            #return a
        
        ## indexing returned a sub-array; generate new info array to go with it
        #print "   new MA:", type(a), a.shape
        info = []
        extraInfo = self._info[-1].copy()
        for i in range(0, len(nInd)):   ## iterate over all axes
            #print "   axis", i
            if type(nInd[i]) in [slice, list] or isinstance(nInd[i], np.ndarray):  ## If the axis is sliced, keep the info but chop if necessary
                #print "      slice axis", i, nInd[i]
                #a._info[i] = self._axisSlice(i, nInd[i])
                #print "         info:", a._info[i]
                info.append(self._axisSlice(i, nInd[i]))
            else: ## If the axis is indexed, then move the information from that single index to the last info dictionary
                #print "indexed:", i, nInd[i], type(nInd[i])
                newInfo = self._axisSlice(i, nInd[i])
                name = None
                colName = None
                for k in newInfo:
                    if k == 'cols':
                        if 'cols' not in extraInfo:
                            extraInfo['cols'] = []
                        extraInfo['cols'].append(newInfo[k])
                        if 'units' in newInfo[k]:
                            extraInfo['units'] = newInfo[k]['units']
                        if 'name' in newInfo[k]:
                            colName = newInfo[k]['name']
                    elif k == 'name':
                        name = newInfo[k]
                    else:
                        if k not in extraInfo:
                            extraInfo[k] = newInfo[k]
                        extraInfo[k] = newInfo[k]
                if 'name' not in extraInfo:
                    if name is None:
                        if colName is not None:
                            extraInfo['name'] = colName
                    else:
                        if colName is not None:
                            extraInfo['name'] = str(name) + ': ' + str(colName)
                        else:
                            extraInfo['name'] = name
                        
                        
                #print "Lost info:", newInfo
                #a._info[i] = None
                #if 'name' in newInfo:
                    #a._info[-1][newInfo['name']] = newInfo
        info.append(extraInfo)
        
        #self._infoOwned = False
        #while None in a._info:
            #a._info.remove(None)
        return MetaArray(a, info=info)
  
    @property
    def ndim(self):
        return len(self.shape)  ## hdf5 objects do not have ndim property.
            
    @property
    def shape(self):
        return self._data.shape
        
    @property
    def dtype(self):
        return self._data.dtype
        
    def __len__(self):
        return len(self._data)
        
    def __getslice__(self, *args):
        return self.__getitem__(slice(*args))
  
    def __setitem__(self, ind, val):
        nInd = self._interpretIndexes(ind)
        try:
            self._data[nInd] = val
        except:
            print(self, nInd, val)
            raise
        
    def __getattr__(self, attr):
        if attr in self.wrapMethods:
            return getattr(self._data, attr)
        else:
            raise AttributeError(attr)
            #return lambda *args, **kwargs: MetaArray(getattr(a.view(ndarray), attr)(*args, **kwargs)
        
    def __eq__(self, b):
        return self._binop('__eq__', b)
        
    def __ne__(self, b):
        return self._binop('__ne__', b)
        #if isinstance(b, MetaArray):
            #b = b.asarray()
        #return self.asarray() != b
        
    def __sub__(self, b):
        return self._binop('__sub__', b)
        #if isinstance(b, MetaArray):
            #b = b.asarray()
        #return MetaArray(self.asarray() - b, info=self.infoCopy())

    def __add__(self, b):
        return self._binop('__add__', b)

    def __mul__(self, b):
        return self._binop('__mul__', b)
        
    def __div__(self, b):
        return self._binop('__div__', b)
        
    def __truediv__(self, b):
        return self._binop('__truediv__', b)
        
    def _binop(self, op, b):
        if isinstance(b, MetaArray):
            b = b.asarray()
        a = self.asarray()
        c = getattr(a, op)(b)
        if c.shape != a.shape:
            raise Exception("Binary operators with MetaArray must return an array of the same shape (this shape is %s, result shape was %s)" % (a.shape, c.shape))
        return MetaArray(c, info=self.infoCopy())
        
    def asarray(self):
        if isinstance(self._data, np.ndarray):
            return self._data
        else:
            return np.array(self._data)
            
    def __array__(self):
        ## supports np.array(metaarray_instance) 
        return self.asarray()
            
    def view(self, typ):
        ## deprecated; kept for backward compatibility
        if typ is np.ndarray:
            return self.asarray()
        else:
            raise Exception('invalid view type: %s' % str(typ))
  
    def axisValues(self, axis):
        """Return the list of values for an axis"""
        ax = self._interpretAxis(axis)
        if 'values' in self._info[ax]:
            return self._info[ax]['values']
        else:
            raise Exception('Array axis %s (%d) has no associated values.' % (str(axis), ax))
  
    def xvals(self, axis):
        """Synonym for axisValues()"""
        return self.axisValues(axis)
        
    def axisHasValues(self, axis):
        ax = self._interpretAxis(axis)
        return 'values' in self._info[ax]
        
    def axisHasColumns(self, axis):
        ax = self._interpretAxis(axis)
        return 'cols' in self._info[ax]
  
    def axisUnits(self, axis):
        """Return the units for axis"""
        ax = self._info[self._interpretAxis(axis)]
        if 'units' in ax:
            return ax['units']
        
    def hasColumn(self, axis, col):
        ax = self._info[self._interpretAxis(axis)]
        if 'cols' in ax:
            for c in ax['cols']:
                if c['name'] == col:
                    return True
        return False
        
    def listColumns(self, axis=None):
        """Return a list of column names for axis. If axis is not specified, then return a dict of {axisName: (column names), ...}."""
        if axis is None:
            ret = {}
            for i in range(self.ndim):
                if 'cols' in self._info[i]:
                    cols = [c['name'] for c in self._info[i]['cols']]
                else:
                    cols = []
                ret[self.axisName(i)] = cols
            return ret
        else:
            axis = self._interpretAxis(axis)
            return [c['name'] for c in self._info[axis]['cols']]
        
    def columnName(self, axis, col):
        ax = self._info[self._interpretAxis(axis)]
        return ax['cols'][col]['name']
        
    def axisName(self, n):
        return self._info[n].get('name', n)
        
    def columnUnits(self, axis, column):
        """Return the units for column in axis"""
        ax = self._info[self._interpretAxis(axis)]
        if 'cols' in ax:
            for c in ax['cols']:
                if c['name'] == column:
                    return c['units']
            raise Exception("Axis %s has no column named %s" % (str(axis), str(column)))
        else:
            raise Exception("Axis %s has no column definitions" % str(axis))
  
    def rowsort(self, axis, key=0):
        """Return this object with all records sorted along axis using key as the index to the values to compare. Does not yet modify meta info."""
        ## make sure _info is copied locally before modifying it!
    
        keyList = self[key]
        order = keyList.argsort()
        if type(axis) == int:
            ind = [slice(None)]*axis
            ind.append(order)
        elif isinstance(axis, basestring):
            ind = (slice(axis, order),)
        return self[tuple(ind)]
  
    def append(self, val, axis):
        """Return this object with val appended along axis. Does not yet combine meta info."""
        ## make sure _info is copied locally before modifying it!
    
        s = list(self.shape)
        axis = self._interpretAxis(axis)
        s[axis] += 1
        n = MetaArray(tuple(s), info=self._info, dtype=self.dtype)
        ind = [slice(None)]*self.ndim
        ind[axis] = slice(None,-1)
        n[tuple(ind)] = self
        ind[axis] = -1
        n[tuple(ind)] = val
        return n
  
    def extend(self, val, axis):
        """Return the concatenation along axis of this object and val. Does not yet combine meta info."""
        ## make sure _info is copied locally before modifying it!
    
        axis = self._interpretAxis(axis)
        return MetaArray(np.concatenate(self, val, axis), info=self._info)
  
    def infoCopy(self, axis=None):
        """Return a deep copy of the axis meta info for this object"""
        if axis is None:
            return copy.deepcopy(self._info)
        else:
            return copy.deepcopy(self._info[self._interpretAxis(axis)])
  
    def copy(self):
        return MetaArray(self._data.copy(), info=self.infoCopy())
  
  
    def _interpretIndexes(self, ind):
        #print "interpret", ind
        if not isinstance(ind, tuple):
            ## a list of slices should be interpreted as a tuple of slices.
            if isinstance(ind, list) and len(ind) > 0 and isinstance(ind[0], slice):
                ind = tuple(ind)
            ## everything else can just be converted to a length-1 tuple
            else:
                ind = (ind,)
                
        nInd = [slice(None)]*self.ndim
        numOk = True  ## Named indices not started yet; numbered sill ok
        for i in range(0,len(ind)):
            (axis, index, isNamed) = self._interpretIndex(ind[i], i, numOk)
            #try:
            nInd[axis] = index
            #except:
                #print "ndim:", self.ndim
                #print "axis:", axis
                #print "index spec:", ind[i]
                #print "index num:", index
                #raise
            if isNamed:
                numOk = False
        return tuple(nInd)
      
    def _interpretAxis(self, axis):
        if isinstance(axis, basestring) or isinstance(axis, tuple):
            return self._getAxis(axis)
        else:
            return axis
  
    def _interpretIndex(self, ind, pos, numOk):
        #print "Interpreting index", ind, pos, numOk
        
        ## should probably check for int first to speed things up..
        if type(ind) is int:
            if not numOk:
                raise Exception("string and integer indexes may not follow named indexes")
            #print "  normal numerical index"
            return (pos, ind, False)
        if MetaArray.isNameType(ind):
            if not numOk:
                raise Exception("string and integer indexes may not follow named indexes")
            #print "  String index, column is ", self._getIndex(pos, ind)
            return (pos, self._getIndex(pos, ind), False)
        elif type(ind) is slice:
            #print "  Slice index"
            if MetaArray.isNameType(ind.start) or MetaArray.isNameType(ind.stop):  ## Not an actual slice!
                #print "    ..not a real slice"
                axis = self._interpretAxis(ind.start)
                #print "    axis is", axis
                
                ## x[Axis:Column]
                if MetaArray.isNameType(ind.stop):
                    #print "    column name, column is ", self._getIndex(axis, ind.stop)
                    index = self._getIndex(axis, ind.stop)
                    
                ## x[Axis:min:max]
                elif (isinstance(ind.stop, float) or isinstance(ind.step, float)) and ('values' in self._info[axis]):
                    #print "    axis value range"
                    if ind.stop is None:
                        mask = self.xvals(axis) < ind.step
                    elif ind.step is None:
                        mask = self.xvals(axis) >= ind.stop
                    else:
                        mask = (self.xvals(axis) >= ind.stop) * (self.xvals(axis) < ind.step)
                    ##print "mask:", mask
                    index = mask
                    
                ## x[Axis:columnIndex]
                elif isinstance(ind.stop, int) or isinstance(ind.step, int):
                    #print "    normal slice after named axis"
                    if ind.step is None:
                        index = ind.stop
                    else:
                        index = slice(ind.stop, ind.step)
                    
                ## x[Axis: [list]]
                elif type(ind.stop) is list:
                    #print "    list of indexes from named axis"
                    index = []
                    for i in ind.stop:
                        if type(i) is int:
                            index.append(i)
                        elif MetaArray.isNameType(i):
                            index.append(self._getIndex(axis, i))
                        else:
                            ## unrecognized type, try just passing on to array
                            index = ind.stop
                            break
                
                else:
                    #print "    other type.. forward on to array for handling", type(ind.stop)
                    index = ind.stop
                #print "Axis %s (%s) : %s" % (ind.start, str(axis), str(type(index)))
                #if type(index) is np.ndarray:
                    #print "    ", index.shape
                return (axis, index, True)
            else:
                #print "  Looks like a real slice, passing on to array"
                return (pos, ind, False)
        elif type(ind) is list:
            #print "  List index., interpreting each element individually"
            indList = [self._interpretIndex(i, pos, numOk)[1] for i in ind]
            return (pos, indList, False)
        else:
            if not numOk:
                raise Exception("string and integer indexes may not follow named indexes")
            #print "  normal numerical index"
            return (pos, ind, False)
  
    def _getAxis(self, name):
        for i in range(0, len(self._info)):
            axis = self._info[i]
            if 'name' in axis and axis['name'] == name:
                return i
        raise Exception("No axis named %s.\n  info=%s" % (name, self._info))
  
    def _getIndex(self, axis, name):
        ax = self._info[axis]
        if ax is not None and 'cols' in ax:
            for i in range(0, len(ax['cols'])):
                if 'name' in ax['cols'][i] and ax['cols'][i]['name'] == name:
                    return i
        raise Exception("Axis %d has no column named %s.\n  info=%s" % (axis, name, self._info))
  
    def _axisCopy(self, i):
        return copy.deepcopy(self._info[i])
  
    def _axisSlice(self, i, cols):
        #print "axisSlice", i, cols
        if 'cols' in self._info[i] or 'values' in self._info[i]:
            ax = self._axisCopy(i)
            if 'cols' in ax:
                #print "  slicing columns..", array(ax['cols']), cols
                sl = np.array(ax['cols'])[cols]
                if isinstance(sl, np.ndarray):
                    sl = list(sl)
                ax['cols'] = sl
                #print "  result:", ax['cols']
            if 'values' in ax:
                ax['values'] = np.array(ax['values'])[cols]
        else:
            ax = self._info[i]
        #print "     ", ax
        return ax
  
    def prettyInfo(self):
        s = ''
        titles = []
        maxl = 0
        for i in range(len(self._info)-1):
            ax = self._info[i]
            axs = ''
            if 'name' in ax:
                axs += '"%s"' % str(ax['name'])
            else:
                axs += "%d" % i
            if 'units' in ax:
                axs += " (%s)" % str(ax['units'])
            titles.append(axs)
            if len(axs) > maxl:
                maxl = len(axs)
        
        for i in range(min(self.ndim, len(self._info)-1)):
            ax = self._info[i]
            axs = titles[i]
            axs += '%s[%d] :' % (' ' * (maxl + 2 - len(axs)), self.shape[i])
            if 'values' in ax:
                v0 = ax['values'][0]
                v1 = ax['values'][-1]
                axs += " values: [%g ... %g] (step %g)" % (v0, v1, (v1-v0)/(self.shape[i]-1))
            if 'cols' in ax:
                axs += " columns: "
                colstrs = []
                for c in range(len(ax['cols'])):
                    col = ax['cols'][c]
                    cs = str(col.get('name', c))
                    if 'units' in col:
                        cs += " (%s)" % col['units']
                    colstrs.append(cs)
                axs += '[' + ', '.join(colstrs) + ']'
            s += axs + "\n"
        s += str(self._info[-1])
        return s
  
    def __repr__(self):
        return "%s\n-----------------------------------------------\n%s" % (self.view(np.ndarray).__repr__(), self.prettyInfo())

    def __str__(self):
        return self.__repr__()


    def axisCollapsingFn(self, fn, axis=None, *args, **kargs):
        #arr = self.view(np.ndarray)
        fn = getattr(self._data, fn)
        if axis is None:
            return fn(axis, *args, **kargs)
        else:
            info = self.infoCopy()
            axis = self._interpretAxis(axis)
            info.pop(axis)
            return MetaArray(fn(axis, *args, **kargs), info=info)

    def mean(self, axis=None, *args, **kargs):
        return self.axisCollapsingFn('mean', axis, *args, **kargs)
            

    def min(self, axis=None, *args, **kargs):
        return self.axisCollapsingFn('min', axis, *args, **kargs)

    def max(self, axis=None, *args, **kargs):
        return self.axisCollapsingFn('max', axis, *args, **kargs)

    def transpose(self, *args):
        if len(args) == 1 and hasattr(args[0], '__iter__'):
            order = args[0]
        else:
            order = args
        
        order = [self._interpretAxis(ax) for ax in order]
        infoOrder = order  + list(range(len(order), len(self._info)))
        info = [self._info[i] for i in infoOrder]
        order = order + list(range(len(order), self.ndim))
        
        try:
            if self._isHDF:
                return MetaArray(np.array(self._data).transpose(order), info=info)
            else:
                return MetaArray(self._data.transpose(order), info=info)
        except:
            print(order)
            raise

    #### File I/O Routines
    def readFile(self, filename, **kwargs):
        """Load the data and meta info stored in *filename*
        Different arguments are allowed depending on the type of file.
        For HDF5 files:
        
            *writable* (bool) if True, then any modifications to data in the array will be stored to disk.
            *readAllData* (bool) if True, then all data in the array is immediately read from disk
                          and the file is closed (this is the default for files < 500MB). Otherwise, the file will
                          be left open and data will be read only as requested (this is 
                          the default for files >= 500MB).
        
        
        """
        ## decide which read function to use
        fd = open(filename, 'rb')
        magic = fd.read(8)
        if magic == '\x89HDF\r\n\x1a\n':
            fd.close()
            self._readHDF5(filename, **kwargs)
            self._isHDF = True
        else:
            fd.seek(0)
            meta = MetaArray._readMeta(fd)
            if 'version' in meta:
                ver = meta['version']
            else:
                ver = 1
            rFuncName = '_readData%s' % str(ver)
            if not hasattr(MetaArray, rFuncName):
                raise Exception("This MetaArray library does not support array version '%s'" % ver)
            rFunc = getattr(self, rFuncName)
            rFunc(fd, meta, **kwargs)
            self._isHDF = False

    @staticmethod
    def _readMeta(fd):
        """Read meta array from the top of a file. Read lines until a blank line is reached.
        This function should ideally work for ALL versions of MetaArray.
        """
        meta = ''
        ## Read meta information until the first blank line
        while True:
            line = fd.readline().strip()
            if line == '':
                break
            meta += line
        ret = eval(meta)
        #print ret
        return ret

    def _readData1(self, fd, meta, mmap=False):
        ## Read array data from the file descriptor for MetaArray v1 files
        ## read in axis values for any axis that specifies a length
        frameSize = 1
        for ax in meta['info']:
            if 'values_len' in ax:
                ax['values'] = np.fromstring(fd.read(ax['values_len']), dtype=ax['values_type'])
                frameSize *= ax['values_len']
                del ax['values_len']
                del ax['values_type']
        ## the remaining data is the actual array
        if mmap:
            subarr = np.memmap(fd, dtype=meta['type'], mode='r', shape=meta['shape'])
        else:
            subarr = np.fromstring(fd.read(), dtype=meta['type'])
            subarr.shape = meta['shape']
        self._info = meta['info']
        self._data = subarr
            
    def _readData2(self, fd, meta, mmap=False, subset=None):
        ## read in axis values
        dynAxis = None
        frameSize = 1
        ## read in axis values for any axis that specifies a length
        for i in range(len(meta['info'])):
            ax = meta['info'][i]
            if 'values_len' in ax:
                if ax['values_len'] == 'dynamic':
                    if dynAxis is not None:
                        raise Exception("MetaArray has more than one dynamic axis! (this is not allowed)")
                    dynAxis = i
                else:
                    ax['values'] = np.fromstring(fd.read(ax['values_len']), dtype=ax['values_type'])
                    frameSize *= ax['values_len']
                    del ax['values_len']
                    del ax['values_type']
                    
        ## No axes are dynamic, just read the entire array in at once
        if dynAxis is None:
            #if rewriteDynamic is not None:
                #raise Exception("")
            if meta['type'] == 'object':
                if mmap:
                    raise Exception('memmap not supported for arrays with dtype=object')
                subarr = pickle.loads(fd.read())
            else:
                if mmap:
                    subarr = np.memmap(fd, dtype=meta['type'], mode='r', shape=meta['shape'])
                else:
                    subarr = np.fromstring(fd.read(), dtype=meta['type'])
            #subarr = subarr.view(subtype)
            subarr.shape = meta['shape']
            #subarr._info = meta['info']
        ## One axis is dynamic, read in a frame at a time
        else:
            if mmap:
                raise Exception('memmap not supported for non-contiguous arrays. Use rewriteContiguous() to convert.')
            ax = meta['info'][dynAxis]
            xVals = []
            frames = []
            frameShape = list(meta['shape'])
            frameShape[dynAxis] = 1
            frameSize = reduce(lambda a,b: a*b, frameShape)
            n = 0
            while True:
                ## Extract one non-blank line
                while True:
                    line = fd.readline()
                    if line != '\n':
                        break
                if line == '':
                    break
                    
                ## evaluate line
                inf = eval(line)
                
                ## read data block
                #print "read %d bytes as %s" % (inf['len'], meta['type'])
                if meta['type'] == 'object':
                    data = pickle.loads(fd.read(inf['len']))
                else:
                    data = np.fromstring(fd.read(inf['len']), dtype=meta['type'])
                
                if data.size != frameSize * inf['numFrames']:
                    #print data.size, frameSize, inf['numFrames']
                    raise Exception("Wrong frame size in MetaArray file! (frame %d)" % n)
                    
                ## read in data block
                shape = list(frameShape)
                shape[dynAxis] = inf['numFrames']
                data.shape = shape
                if subset is not None:
                    dSlice = subset[dynAxis]
                    if dSlice.start is None:
                        dStart = 0
                    else:
                        dStart = max(0, dSlice.start - n)
                    if dSlice.stop is None:
                        dStop = data.shape[dynAxis]
                    else:
                        dStop = min(data.shape[dynAxis], dSlice.stop - n)
                    newSubset = list(subset[:])
                    newSubset[dynAxis] = slice(dStart, dStop)
                    if dStop > dStart:
                        #print n, data.shape, " => ", newSubset, data[tuple(newSubset)].shape
                        frames.append(data[tuple(newSubset)].copy())
                else:
                    #data = data[subset].copy()  ## what's this for??
                    frames.append(data)
                
                n += inf['numFrames']
                if 'xVals' in inf:
                    xVals.extend(inf['xVals'])
            subarr = np.concatenate(frames, axis=dynAxis)
            if len(xVals)> 0:
                ax['values'] = np.array(xVals, dtype=ax['values_type'])
            del ax['values_len']
            del ax['values_type']
        #subarr = subarr.view(subtype)
        #subarr._info = meta['info']
        self._info = meta['info']
        self._data = subarr
        #raise Exception()  ## stress-testing
        #return subarr

    def _readHDF5(self, fileName, readAllData=None, writable=False, **kargs):
        if 'close' in kargs and readAllData is None: ## for backward compatibility
            readAllData = kargs['close']
       
        if readAllData is True and writable is True:
            raise Exception("Incompatible arguments: readAllData=True and writable=True")
        
        if not HAVE_HDF5:
            try:
                assert writable==False
                assert readAllData != False
                self._readHDF5Remote(fileName)
                return
            except:
                raise Exception("The file '%s' is HDF5-formatted, but the HDF5 library (h5py) was not found." % fileName)
        
        ## by default, readAllData=True for files < 500MB
        if readAllData is None:
            size = os.stat(fileName).st_size
            readAllData = (size < 500e6)
        
        if writable is True:
            mode = 'r+'
        else:
            mode = 'r'
        f = h5py.File(fileName, mode)
        
        ver = f.attrs['MetaArray']
        if ver > MetaArray.version:
            print("Warning: This file was written with MetaArray version %s, but you are using version %s. (Will attempt to read anyway)" % (str(ver), str(MetaArray.version)))
        meta = MetaArray.readHDF5Meta(f['info'])
        self._info = meta
        
        if writable or not readAllData:  ## read all data, convert to ndarray, close file
            self._data = f['data']
            self._openFile = f
        else:
            self._data = f['data'][:]
            f.close()
            
    def _readHDF5Remote(self, fileName):
        ## Used to read HDF5 files via remote process.
        ## This is needed in the case that HDF5 is not importable due to the use of python-dbg.
        proc = getattr(MetaArray, '_hdf5Process', None)
        
        if proc == False:
            raise Exception('remote read failed')
        if proc == None:
            import pyqtgraph.multiprocess as mp
            #print "new process"
            proc = mp.Process(executable='/usr/bin/python')
            proc.setProxyOptions(deferGetattr=True)
            MetaArray._hdf5Process = proc
            MetaArray._h5py_metaarray = proc._import('pyqtgraph.metaarray')
        ma = MetaArray._h5py_metaarray.MetaArray(file=fileName)
        self._data = ma.asarray()._getValue()
        self._info = ma._info._getValue()
        #print MetaArray._hdf5Process
        #import inspect
        #print MetaArray, id(MetaArray), inspect.getmodule(MetaArray)
        
        

    @staticmethod
    def mapHDF5Array(data, writable=False):
        off = data.id.get_offset()
        if writable:
            mode = 'r+'
        else:
            mode = 'r'
        if off is None:
            raise Exception("This dataset uses chunked storage; it can not be memory-mapped. (store using mappable=True)")
        return np.memmap(filename=data.file.filename, offset=off, dtype=data.dtype, shape=data.shape, mode=mode)
        



    @staticmethod
    def readHDF5Meta(root, mmap=False):
        data = {}
        
        ## Pull list of values from attributes and child objects
        for k in root.attrs:
            val = root.attrs[k]
            if isinstance(val, basestring):  ## strings need to be re-evaluated to their original types
                try:
                    val = eval(val)
                except:
                    raise Exception('Can not evaluate string: "%s"' % val)
            data[k] = val
        for k in root:
            obj = root[k]
            if isinstance(obj, h5py.highlevel.Group):
                val = MetaArray.readHDF5Meta(obj)
            elif isinstance(obj, h5py.highlevel.Dataset):
                if mmap:
                    val = MetaArray.mapHDF5Array(obj)
                else:
                    val = obj[:]
            else:
                raise Exception("Don't know what to do with type '%s'" % str(type(obj)))
            data[k] = val
        
        typ = root.attrs['_metaType_']
        del data['_metaType_']
        
        if typ == 'dict':
            return data
        elif typ == 'list' or typ == 'tuple':
            d2 = [None]*len(data)
            for k in data:
                d2[int(k)] = data[k]
            if typ == 'tuple':
                d2 = tuple(d2)
            return d2
        else:
            raise Exception("Don't understand metaType '%s'" % typ)
        

    def write(self, fileName, **opts):
        """Write this object to a file. The object can be restored by calling MetaArray(file=fileName)
        opts:
            appendAxis: the name (or index) of the appendable axis. Allows the array to grow.
            compression: None, 'gzip' (good compression), 'lzf' (fast compression), etc.
            chunks: bool or tuple specifying chunk shape
        """
        
        if USE_HDF5 and HAVE_HDF5:
            return self.writeHDF5(fileName, **opts)
        else:
            return self.writeMa(fileName, **opts)

    def writeMeta(self, fileName):
        """Used to re-write meta info to the given file.
        This feature is only available for HDF5 files."""
        f = h5py.File(fileName, 'r+')
        if f.attrs['MetaArray'] != MetaArray.version:
            raise Exception("The file %s was created with a different version of MetaArray. Will not modify." % fileName)
        del f['info']
        
        self.writeHDF5Meta(f, 'info', self._info)
        f.close()


    def writeHDF5(self, fileName, **opts):
        ## default options for writing datasets
        dsOpts = {  
            'compression': 'lzf',
            'chunks': True,
        }
        
        ## if there is an appendable axis, then we can guess the desired chunk shape (optimized for appending)
        appAxis = opts.get('appendAxis', None)
        if appAxis is not None:
            appAxis = self._interpretAxis(appAxis)
            cs = [min(100000, x) for x in self.shape]
            cs[appAxis] = 1
            dsOpts['chunks'] = tuple(cs)
            
        ## if there are columns, then we can guess a different chunk shape
        ## (read one column at a time)
        else:
            cs = [min(100000, x) for x in self.shape]
            for i in range(self.ndim):
                if 'cols' in self._info[i]:
                    cs[i] = 1
            dsOpts['chunks'] = tuple(cs)
        
        ## update options if they were passed in
        for k in dsOpts:
            if k in opts:
                dsOpts[k] = opts[k]
        
        
        ## If mappable is in options, it disables chunking/compression
        if opts.get('mappable', False):
            dsOpts = {
                'chunks': None,
                'compression': None
            }
        
            
        ## set maximum shape to allow expansion along appendAxis
        append = False
        if appAxis is not None:
            maxShape = list(self.shape)
            ax = self._interpretAxis(appAxis)
            maxShape[ax] = None
            if os.path.exists(fileName):
                append = True
            dsOpts['maxshape'] = tuple(maxShape)
        else:
            dsOpts['maxshape'] = None
            
        if append:
            f = h5py.File(fileName, 'r+')
            if f.attrs['MetaArray'] != MetaArray.version:
                raise Exception("The file %s was created with a different version of MetaArray. Will not modify." % fileName)
            
            ## resize data and write in new values
            data = f['data']
            shape = list(data.shape)
            shape[ax] += self.shape[ax]
            data.resize(tuple(shape))
            sl = [slice(None)] * len(data.shape)
            sl[ax] = slice(-self.shape[ax], None)
            data[tuple(sl)] = self.view(np.ndarray)
            
            ## add axis values if they are present.
            axInfo = f['info'][str(ax)]
            if 'values' in axInfo:
                v = axInfo['values']
                v2 = self._info[ax]['values']
                shape = list(v.shape)
                shape[0] += v2.shape[0]
                v.resize(shape)
                v[-v2.shape[0]:] = v2
            f.close()
        else:
            f = h5py.File(fileName, 'w')
            f.attrs['MetaArray'] = MetaArray.version
            #print dsOpts
            f.create_dataset('data', data=self.view(np.ndarray), **dsOpts)
            
            ## dsOpts is used when storing meta data whenever an array is encountered
            ## however, 'chunks' will no longer be valid for these arrays if it specifies a chunk shape.
            ## 'maxshape' is right-out.
            if isinstance(dsOpts['chunks'], tuple):
                dsOpts['chunks'] = True
                if 'maxshape' in dsOpts:
                    del dsOpts['maxshape']
            self.writeHDF5Meta(f, 'info', self._info, **dsOpts)
            f.close()

    def writeHDF5Meta(self, root, name, data, **dsOpts):
        if isinstance(data, np.ndarray):
            dsOpts['maxshape'] = (None,) + data.shape[1:]
            root.create_dataset(name, data=data, **dsOpts)
        elif isinstance(data, list) or isinstance(data, tuple):
            gr = root.create_group(name)
            if isinstance(data, list):
                gr.attrs['_metaType_'] = 'list'
            else:
                gr.attrs['_metaType_'] = 'tuple'
            #n = int(np.log10(len(data))) + 1
            for i in range(len(data)):
                self.writeHDF5Meta(gr, str(i), data[i], **dsOpts)
        elif isinstance(data, dict):
            gr = root.create_group(name)
            gr.attrs['_metaType_'] = 'dict'
            for k, v in data.items():
                self.writeHDF5Meta(gr, k, v, **dsOpts)
        elif isinstance(data, int) or isinstance(data, float) or isinstance(data, np.integer) or isinstance(data, np.floating):
            root.attrs[name] = data
        else:
            try:   ## strings, bools, None are stored as repr() strings
                root.attrs[name] = repr(data)
            except:
                print("Can not store meta data of type '%s' in HDF5. (key is '%s')" % (str(type(data)), str(name)))
                raise 

        
    def writeMa(self, fileName, appendAxis=None, newFile=False):
        """Write an old-style .ma file"""
        meta = {'shape':self.shape, 'type':str(self.dtype), 'info':self.infoCopy(), 'version':MetaArray.version}
        axstrs = []
        
        ## copy out axis values for dynamic axis if requested
        if appendAxis is not None:
            if MetaArray.isNameType(appendAxis):
                appendAxis = self._interpretAxis(appendAxis)
            
            
            ax = meta['info'][appendAxis]
            ax['values_len'] = 'dynamic'
            if 'values' in ax:
                ax['values_type'] = str(ax['values'].dtype)
                dynXVals = ax['values']
                del ax['values']
            else:
                dynXVals = None
                
        ## Generate axis data string, modify axis info so we know how to read it back in later
        for ax in meta['info']:
            if 'values' in ax:
                axstrs.append(ax['values'].tostring())
                ax['values_len'] = len(axstrs[-1])
                ax['values_type'] = str(ax['values'].dtype)
                del ax['values']
                
        ## Decide whether to output the meta block for a new file
        if not newFile:
            ## If the file does not exist or its size is 0, then we must write the header
            newFile = (not os.path.exists(fileName))  or  (os.stat(fileName).st_size == 0)
        
        ## write data to file
        if appendAxis is None or newFile:
            fd = open(fileName, 'wb')
            fd.write(str(meta) + '\n\n')
            for ax in axstrs:
                fd.write(ax)
        else:
            fd = open(fileName, 'ab')
        
        if self.dtype != object:
            dataStr = self.view(np.ndarray).tostring()
        else:
            dataStr = pickle.dumps(self.view(np.ndarray))
        #print self.size, len(dataStr), self.dtype
        if appendAxis is not None:
            frameInfo = {'len':len(dataStr), 'numFrames':self.shape[appendAxis]}
            if dynXVals is not None:
                frameInfo['xVals'] = list(dynXVals)
            fd.write('\n'+str(frameInfo)+'\n')
        fd.write(dataStr)
        fd.close()
        
    def writeCsv(self, fileName=None):
        """Write 2D array to CSV file or return the string if no filename is given"""
        if self.ndim > 2:
            raise Exception("CSV Export is only for 2D arrays")
        if fileName is not None:
            file = open(fileName, 'w')
        ret = ''
        if 'cols' in self._info[0]:
            s = ','.join([x['name'] for x in self._info[0]['cols']]) + '\n'
            if fileName is not None:
                file.write(s)
            else:
                ret += s
        for row in range(0, self.shape[1]):
            s = ','.join(["%g" % x for x in self[:, row]]) + '\n'
            if fileName is not None:
                file.write(s)
            else:
                ret += s
        if fileName is not None:
            file.close()
        else:
            return ret
        


#class H5MetaList():
    

#def rewriteContiguous(fileName, newName):
    #"""Rewrite a dynamic array file as contiguous"""
    #def _readData2(fd, meta, subtype, mmap):
        ### read in axis values
        #dynAxis = None
        #frameSize = 1
        ### read in axis values for any axis that specifies a length
        #for i in range(len(meta['info'])):
            #ax = meta['info'][i]
            #if ax.has_key('values_len'):
                #if ax['values_len'] == 'dynamic':
                    #if dynAxis is not None:
                        #raise Exception("MetaArray has more than one dynamic axis! (this is not allowed)")
                    #dynAxis = i
                #else:
                    #ax['values'] = fromstring(fd.read(ax['values_len']), dtype=ax['values_type'])
                    #frameSize *= ax['values_len']
                    #del ax['values_len']
                    #del ax['values_type']
                    
        ### No axes are dynamic, just read the entire array in at once
        #if dynAxis is None:
            #raise Exception('Array has no dynamic axes.')
        ### One axis is dynamic, read in a frame at a time
        #else:
            #if mmap:
                #raise Exception('memmap not supported for non-contiguous arrays. Use rewriteContiguous() to convert.')
            #ax = meta['info'][dynAxis]
            #xVals = []
            #frames = []
            #frameShape = list(meta['shape'])
            #frameShape[dynAxis] = 1
            #frameSize = reduce(lambda a,b: a*b, frameShape)
            #n = 0
            #while True:
                ### Extract one non-blank line
                #while True:
                    #line = fd.readline()
                    #if line != '\n':
                        #break
                #if line == '':
                    #break
                    
                ### evaluate line
                #inf = eval(line)
                
                ### read data block
                ##print "read %d bytes as %s" % (inf['len'], meta['type'])
                #if meta['type'] == 'object':
                    #data = pickle.loads(fd.read(inf['len']))
                #else:
                    #data = fromstring(fd.read(inf['len']), dtype=meta['type'])
                
                #if data.size != frameSize * inf['numFrames']:
                    ##print data.size, frameSize, inf['numFrames']
                    #raise Exception("Wrong frame size in MetaArray file! (frame %d)" % n)
                    
                ### read in data block
                #shape = list(frameShape)
                #shape[dynAxis] = inf['numFrames']
                #data.shape = shape
                #frames.append(data)
                
                #n += inf['numFrames']
                #if 'xVals' in inf:
                    #xVals.extend(inf['xVals'])
            #subarr = np.concatenate(frames, axis=dynAxis)
            #if len(xVals)> 0:
                #ax['values'] = array(xVals, dtype=ax['values_type'])
            #del ax['values_len']
            #del ax['values_type']
        #subarr = subarr.view(subtype)
        #subarr._info = meta['info']
        #return subarr
    


  
  
if __name__ == '__main__':
    ## Create an array with every option possible
    
    arr = np.zeros((2, 5, 3, 5), dtype=int)
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            for k in range(arr.shape[2]):
                for l in range(arr.shape[3]):
                    arr[i,j,k,l] = (i+1)*1000 + (j+1)*100 + (k+1)*10 + (l+1)
        
    info = [
        axis('Axis1'), 
        axis('Axis2', values=[1,2,3,4,5]), 
        axis('Axis3', cols=[
            ('Ax3Col1'),
            ('Ax3Col2', 'mV', 'Axis3 Column2'),
            (('Ax3','Col3'), 'A', 'Axis3 Column3')]),
        {'name': 'Axis4', 'values': np.array([1.1, 1.2, 1.3, 1.4, 1.5]), 'units': 's'},
        {'extra': 'info'}
    ]
    
    ma = MetaArray(arr, info=info)
    
    print("====  Original Array =======")
    print(ma)
    print("\n\n")
    
    #### Tests follow:
    
    
    #### Index/slice tests: check that all values and meta info are correct after slice
    print("\n -- normal integer indexing\n")
    
    print("\n  ma[1]")
    print(ma[1])
    
    print("\n  ma[1, 2:4]")
    print(ma[1, 2:4])
    
    print("\n  ma[1, 1:5:2]")
    print(ma[1, 1:5:2])
    
    print("\n -- named axis indexing\n")
    
    print("\n  ma['Axis2':3]")
    print(ma['Axis2':3])
    
    print("\n  ma['Axis2':3:5]")
    print(ma['Axis2':3:5])
    
    print("\n  ma[1, 'Axis2':3]")
    print(ma[1, 'Axis2':3])
    
    print("\n  ma[:, 'Axis2':3]")
    print(ma[:, 'Axis2':3])
    
    print("\n  ma['Axis2':3, 'Axis4':0:2]")
    print(ma['Axis2':3, 'Axis4':0:2])
    
    
    print("\n -- column name indexing\n")
    
    print("\n  ma['Axis3':'Ax3Col1']")
    print(ma['Axis3':'Ax3Col1'])
    
    print("\n  ma['Axis3':('Ax3','Col3')]")
    print(ma['Axis3':('Ax3','Col3')])
    
    print("\n  ma[:, :, 'Ax3Col2']")
    print(ma[:, :, 'Ax3Col2'])
    
    print("\n  ma[:, :, ('Ax3','Col3')]")
    print(ma[:, :, ('Ax3','Col3')])
    
    
    print("\n -- axis value range indexing\n")
    
    print("\n  ma['Axis2':1.5:4.5]")
    print(ma['Axis2':1.5:4.5])
    
    print("\n  ma['Axis4':1.15:1.45]")
    print(ma['Axis4':1.15:1.45])
    
    print("\n  ma['Axis4':1.15:1.25]")
    print(ma['Axis4':1.15:1.25])
    
    
    
    print("\n -- list indexing\n")
    
    print("\n  ma[:, [0,2,4]]")
    print(ma[:, [0,2,4]])
    
    print("\n  ma['Axis4':[0,2,4]]")
    print(ma['Axis4':[0,2,4]])
    
    print("\n  ma['Axis3':[0, ('Ax3','Col3')]]")
    print(ma['Axis3':[0, ('Ax3','Col3')]])
    
    
    
    print("\n -- boolean indexing\n")
    
    print("\n  ma[:, array([True, True, False, True, False])]")
    print(ma[:, np.array([True, True, False, True, False])])
    
    print("\n  ma['Axis4':array([True, False, False, False])]")
    print(ma['Axis4':np.array([True, False, False, False])])
    
    
    
    
    
    #### Array operations 
    #  - Concatenate
    #  - Append
    #  - Extend
    #  - Rowsort
    
    
    
    
    #### File I/O tests
    
    print("\n================  File I/O Tests  ===================\n")
    import tempfile
    tf = tempfile.mktemp()
    tf = 'test.ma'
    # write whole array
    
    print("\n  -- write/read test")
    ma.write(tf)
    ma2 = MetaArray(file=tf)
    
    #print ma2
    print("\nArrays are equivalent:", (ma == ma2).all())
    #print "Meta info is equivalent:", ma.infoCopy() == ma2.infoCopy()
    os.remove(tf)
    
    # CSV write
    
    # append mode
    
    
    print("\n================append test (%s)===============" % tf)
    ma['Axis2':0:2].write(tf, appendAxis='Axis2')
    for i in range(2,ma.shape[1]):
        ma['Axis2':[i]].write(tf, appendAxis='Axis2')
    
    ma2 = MetaArray(file=tf)
    
    #print ma2
    print("\nArrays are equivalent:", (ma == ma2).all())
    #print "Meta info is equivalent:", ma.infoCopy() == ma2.infoCopy()
    
    os.remove(tf)    
    
    
    
    ## memmap test
    print("\n==========Memmap test============")
    ma.write(tf, mappable=True)
    ma2 = MetaArray(file=tf, mmap=True)
    print("\nArrays are equivalent:", (ma == ma2).all())
    os.remove(tf)    
    