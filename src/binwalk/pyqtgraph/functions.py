# -*- coding: utf-8 -*-
"""
functions.py -  Miscellaneous functions with no other home
Copyright 2010  Luke Campagnola
Distributed under MIT/X11 license. See license.txt for more infomation.
"""

from __future__ import division
from .python2_3 import asUnicode
Colors = {
    'b': (0,0,255,255),
    'g': (0,255,0,255),
    'r': (255,0,0,255),
    'c': (0,255,255,255),
    'm': (255,0,255,255),
    'y': (255,255,0,255),
    'k': (0,0,0,255),
    'w': (255,255,255,255),
}  

SI_PREFIXES = asUnicode('yzafpnµm kMGTPEZY')
SI_PREFIXES_ASCII = 'yzafpnum kMGTPEZY'



from .Qt import QtGui, QtCore, USE_PYSIDE
import pyqtgraph as pg
import numpy as np
import decimal, re
import ctypes
import sys, struct

try:
    import scipy.ndimage
    HAVE_SCIPY = True
    if pg.getConfigOption('useWeave'):
        try:
            import scipy.weave
        except ImportError:
            pg.setConfigOptions(useWeave=False)
except ImportError:
    HAVE_SCIPY = False

from . import debug

def siScale(x, minVal=1e-25, allowUnicode=True):
    """
    Return the recommended scale factor and SI prefix string for x.
    
    Example::
    
        siScale(0.0001)   # returns (1e6, 'μ')
        # This indicates that the number 0.0001 is best represented as 0.0001 * 1e6 = 100 μUnits
    """
    
    if isinstance(x, decimal.Decimal):
        x = float(x)
        
    try:
        if np.isnan(x) or np.isinf(x):
            return(1, '')
    except:
        print(x, type(x))
        raise
    if abs(x) < minVal:
        m = 0
        x = 0
    else:
        m = int(np.clip(np.floor(np.log(abs(x))/np.log(1000)), -9.0, 9.0))
    
    if m == 0:
        pref = ''
    elif m < -8 or m > 8:
        pref = 'e%d' % (m*3)
    else:
        if allowUnicode:
            pref = SI_PREFIXES[m+8]
        else:
            pref = SI_PREFIXES_ASCII[m+8]
    p = .001**m
    
    return (p, pref)    

def siFormat(x, precision=3, suffix='', space=True, error=None, minVal=1e-25, allowUnicode=True):
    """
    Return the number x formatted in engineering notation with SI prefix.
    
    Example::
        siFormat(0.0001, suffix='V')  # returns "100 μV"
    """
    
    if space is True:
        space = ' '
    if space is False:
        space = ''
        
    
    (p, pref) = siScale(x, minVal, allowUnicode)
    if not (len(pref) > 0 and pref[0] == 'e'):
        pref = space + pref
    
    if error is None:
        fmt = "%." + str(precision) + "g%s%s"
        return fmt % (x*p, pref, suffix)
    else:
        if allowUnicode:
            plusminus = space + asUnicode("±") + space
        else:
            plusminus = " +/- "
        fmt = "%." + str(precision) + "g%s%s%s%s"
        return fmt % (x*p, pref, suffix, plusminus, siFormat(error, precision=precision, suffix=suffix, space=space, minVal=minVal))
    
def siEval(s):
    """
    Convert a value written in SI notation to its equivalent prefixless value
    
    Example::
    
        siEval("100 μV")  # returns 0.0001
    """
    
    s = asUnicode(s)
    m = re.match(r'(-?((\d+(\.\d*)?)|(\.\d+))([eE]-?\d+)?)\s*([u' + SI_PREFIXES + r']?).*$', s)
    if m is None:
        raise Exception("Can't convert string '%s' to number." % s)
    v = float(m.groups()[0])
    p = m.groups()[6]
    #if p not in SI_PREFIXES:
        #raise Exception("Can't convert string '%s' to number--unknown prefix." % s)
    if p ==  '':
        n = 0
    elif p == 'u':
        n = -2
    else:
        n = SI_PREFIXES.index(p) - 8
    return v * 1000**n
    

class Color(QtGui.QColor):
    def __init__(self, *args):
        QtGui.QColor.__init__(self, mkColor(*args))
        
    def glColor(self):
        """Return (r,g,b,a) normalized for use in opengl"""
        return (self.red()/255., self.green()/255., self.blue()/255., self.alpha()/255.)
        
    def __getitem__(self, ind):
        return (self.red, self.green, self.blue, self.alpha)[ind]()
        
    
def mkColor(*args):
    """
    Convenience function for constructing QColor from a variety of argument types. Accepted arguments are:
    
    ================ ================================================
     'c'             one of: r, g, b, c, m, y, k, w                      
     R, G, B, [A]    integers 0-255
     (R, G, B, [A])  tuple of integers 0-255
     float           greyscale, 0.0-1.0
     int             see :func:`intColor() <pyqtgraph.intColor>`
     (int, hues)     see :func:`intColor() <pyqtgraph.intColor>`
     "RGB"           hexadecimal strings; may begin with '#'
     "RGBA"          
     "RRGGBB"       
     "RRGGBBAA"     
     QColor          QColor instance; makes a copy.
    ================ ================================================
    """
    err = 'Not sure how to make a color from "%s"' % str(args)
    if len(args) == 1:
        if isinstance(args[0], QtGui.QColor):
            return QtGui.QColor(args[0])
        elif isinstance(args[0], float):
            r = g = b = int(args[0] * 255)
            a = 255
        elif isinstance(args[0], basestring):
            c = args[0]
            if c[0] == '#':
                c = c[1:]
            if len(c) == 1:
                (r, g, b, a) = Colors[c]
            if len(c) == 3:
                r = int(c[0]*2, 16)
                g = int(c[1]*2, 16)
                b = int(c[2]*2, 16)
                a = 255
            elif len(c) == 4:
                r = int(c[0]*2, 16)
                g = int(c[1]*2, 16)
                b = int(c[2]*2, 16)
                a = int(c[3]*2, 16)
            elif len(c) == 6:
                r = int(c[0:2], 16)
                g = int(c[2:4], 16)
                b = int(c[4:6], 16)
                a = 255
            elif len(c) == 8:
                r = int(c[0:2], 16)
                g = int(c[2:4], 16)
                b = int(c[4:6], 16)
                a = int(c[6:8], 16)
        elif hasattr(args[0], '__len__'):
            if len(args[0]) == 3:
                (r, g, b) = args[0]
                a = 255
            elif len(args[0]) == 4:
                (r, g, b, a) = args[0]
            elif len(args[0]) == 2:
                return intColor(*args[0])
            else:
                raise Exception(err)
        elif type(args[0]) == int:
            return intColor(args[0])
        else:
            raise Exception(err)
    elif len(args) == 3:
        (r, g, b) = args
        a = 255
    elif len(args) == 4:
        (r, g, b, a) = args
    else:
        raise Exception(err)
    
    args = [r,g,b,a]
    args = [0 if np.isnan(a) or np.isinf(a) else a for a in args]
    args = list(map(int, args))
    return QtGui.QColor(*args)


def mkBrush(*args, **kwds):
    """
    | Convenience function for constructing Brush.
    | This function always constructs a solid brush and accepts the same arguments as :func:`mkColor() <pyqtgraph.mkColor>`
    | Calling mkBrush(None) returns an invisible brush.
    """
    if 'color' in kwds:
        color = kwds['color']
    elif len(args) == 1:
        arg = args[0]
        if arg is None:
            return QtGui.QBrush(QtCore.Qt.NoBrush)
        elif isinstance(arg, QtGui.QBrush):
            return QtGui.QBrush(arg)
        else:
            color = arg
    elif len(args) > 1:
        color = args
    return QtGui.QBrush(mkColor(color))

def mkPen(*args, **kargs):
    """
    Convenience function for constructing QPen. 
    
    Examples::
    
        mkPen(color)
        mkPen(color, width=2)
        mkPen(cosmetic=False, width=4.5, color='r')
        mkPen({'color': "FF0", width: 2})
        mkPen(None)   # (no pen)
    
    In these examples, *color* may be replaced with any arguments accepted by :func:`mkColor() <pyqtgraph.mkColor>`    """
    
    color = kargs.get('color', None)
    width = kargs.get('width', 1)
    style = kargs.get('style', None)
    dash = kargs.get('dash', None)
    cosmetic = kargs.get('cosmetic', True)
    hsv = kargs.get('hsv', None)
    
    if len(args) == 1:
        arg = args[0]
        if isinstance(arg, dict):
            return mkPen(**arg)
        if isinstance(arg, QtGui.QPen):
            return QtGui.QPen(arg)  ## return a copy of this pen
        elif arg is None:
            style = QtCore.Qt.NoPen
        else:
            color = arg
    if len(args) > 1:
        color = args
        
    if color is None:
        color = mkColor(200, 200, 200)
    if hsv is not None:
        color = hsvColor(*hsv)
    else:
        color = mkColor(color)
        
    pen = QtGui.QPen(QtGui.QBrush(color), width)
    pen.setCosmetic(cosmetic)
    if style is not None:
        pen.setStyle(style)
    if dash is not None:
        pen.setDashPattern(dash)
    return pen

def hsvColor(hue, sat=1.0, val=1.0, alpha=1.0):
    """Generate a QColor from HSVa values. (all arguments are float 0.0-1.0)"""
    c = QtGui.QColor()
    c.setHsvF(hue, sat, val, alpha)
    return c

    
def colorTuple(c):
    """Return a tuple (R,G,B,A) from a QColor"""
    return (c.red(), c.green(), c.blue(), c.alpha())

def colorStr(c):
    """Generate a hex string code from a QColor"""
    return ('%02x'*4) % colorTuple(c)

def intColor(index, hues=9, values=1, maxValue=255, minValue=150, maxHue=360, minHue=0, sat=255, alpha=255, **kargs):
    """
    Creates a QColor from a single index. Useful for stepping through a predefined list of colors.
    
    The argument *index* determines which color from the set will be returned. All other arguments determine what the set of predefined colors will be
     
    Colors are chosen by cycling across hues while varying the value (brightness). 
    By default, this selects from a list of 9 hues."""
    hues = int(hues)
    values = int(values)
    ind = int(index) % (hues * values)
    indh = ind % hues
    indv = ind / hues
    if values > 1:
        v = minValue + indv * ((maxValue-minValue) / (values-1))
    else:
        v = maxValue
    h = minHue + (indh * (maxHue-minHue)) / hues
    
    c = QtGui.QColor()
    c.setHsv(h, sat, v)
    c.setAlpha(alpha)
    return c

def glColor(*args, **kargs):
    """
    Convert a color to OpenGL color format (r,g,b,a) floats 0.0-1.0
    Accepts same arguments as :func:`mkColor <pyqtgraph.mkColor>`.
    """
    c = mkColor(*args, **kargs)
    return (c.red()/255., c.green()/255., c.blue()/255., c.alpha()/255.)

    

def makeArrowPath(headLen=20, tipAngle=20, tailLen=20, tailWidth=3, baseAngle=0):
    """
    Construct a path outlining an arrow with the given dimensions.
    The arrow points in the -x direction with tip positioned at 0,0.
    If *tipAngle* is supplied (in degrees), it overrides *headWidth*.
    If *tailLen* is None, no tail will be drawn.
    """
    headWidth = headLen * np.tan(tipAngle * 0.5 * np.pi/180.)
    path = QtGui.QPainterPath()
    path.moveTo(0,0)
    path.lineTo(headLen, -headWidth)
    if tailLen is None:
        innerY = headLen - headWidth * np.tan(baseAngle*np.pi/180.)
        path.lineTo(innerY, 0)
    else:
        tailWidth *= 0.5
        innerY = headLen - (headWidth-tailWidth) * np.tan(baseAngle*np.pi/180.)
        path.lineTo(innerY, -tailWidth)
        path.lineTo(headLen + tailLen, -tailWidth)
        path.lineTo(headLen + tailLen, tailWidth)
        path.lineTo(innerY, tailWidth)
    path.lineTo(headLen, headWidth)
    path.lineTo(0,0)
    return path
    
    
    
def affineSlice(data, shape, origin, vectors, axes, order=1, returnCoords=False, **kargs):
    """
    Take a slice of any orientation through an array. This is useful for extracting sections of multi-dimensional arrays such as MRI images for viewing as 1D or 2D data.
    
    The slicing axes are aribtrary; they do not need to be orthogonal to the original data or even to each other. It is possible to use this function to extract arbitrary linear, rectangular, or parallelepiped shapes from within larger datasets. The original data is interpolated onto a new array of coordinates using scipy.ndimage.map_coordinates (see the scipy documentation for more information about this).
    
    For a graphical interface to this function, see :func:`ROI.getArrayRegion <pyqtgraph.ROI.getArrayRegion>`
    
    ==============  ====================================================================================================
    Arguments:
    *data*          (ndarray) the original dataset
    *shape*         the shape of the slice to take (Note the return value may have more dimensions than len(shape))
    *origin*        the location in the original dataset that will become the origin of the sliced data.
    *vectors*       list of unit vectors which point in the direction of the slice axes. Each vector must have the same 
                    length as *axes*. If the vectors are not unit length, the result will be scaled relative to the 
                    original data. If the vectors are not orthogonal, the result will be sheared relative to the 
                    original data.
    *axes*          The axes in the original dataset which correspond to the slice *vectors*
    *order*         The order of spline interpolation. Default is 1 (linear). See scipy.ndimage.map_coordinates
                    for more information.
    *returnCoords*  If True, return a tuple (result, coords) where coords is the array of coordinates used to select
                    values from the original dataset.
    *All extra keyword arguments are passed to scipy.ndimage.map_coordinates.*
    --------------------------------------------------------------------------------------------------------------------
    ==============  ====================================================================================================
    
    Note the following must be true: 
        
        | len(shape) == len(vectors) 
        | len(origin) == len(axes) == len(vectors[i])
        
    Example: start with a 4D fMRI data set, take a diagonal-planar slice out of the last 3 axes
        
        * data = array with dims (time, x, y, z) = (100, 40, 40, 40)
        * The plane to pull out is perpendicular to the vector (x,y,z) = (1,1,1) 
        * The origin of the slice will be at (x,y,z) = (40, 0, 0)
        * We will slice a 20x20 plane from each timepoint, giving a final shape (100, 20, 20)
        
    The call for this example would look like::
        
        affineSlice(data, shape=(20,20), origin=(40,0,0), vectors=((-1, 1, 0), (-1, 0, 1)), axes=(1,2,3))
    
    """
    if not HAVE_SCIPY:
        raise Exception("This function requires the scipy library, but it does not appear to be importable.")

    # sanity check
    if len(shape) != len(vectors):
        raise Exception("shape and vectors must have same length.")
    if len(origin) != len(axes):
        raise Exception("origin and axes must have same length.")
    for v in vectors:
        if len(v) != len(axes):
            raise Exception("each vector must be same length as axes.")
        
    shape = list(map(np.ceil, shape))

    ## transpose data so slice axes come first
    trAx = list(range(data.ndim))
    for x in axes:
        trAx.remove(x)
    tr1 = tuple(axes) + tuple(trAx)
    data = data.transpose(tr1)
    #print "tr1:", tr1
    ## dims are now [(slice axes), (other axes)]
    

    ## make sure vectors are arrays
    if not isinstance(vectors, np.ndarray):
        vectors = np.array(vectors)
    if not isinstance(origin, np.ndarray):
        origin = np.array(origin)
    origin.shape = (len(axes),) + (1,)*len(shape)
    
    ## Build array of sample locations. 
    grid = np.mgrid[tuple([slice(0,x) for x in shape])]  ## mesh grid of indexes
    #print shape, grid.shape
    x = (grid[np.newaxis,...] * vectors.transpose()[(Ellipsis,) + (np.newaxis,)*len(shape)]).sum(axis=1)  ## magic
    x += origin
    #print "X values:"
    #print x
    ## iterate manually over unused axes since map_coordinates won't do it for us
    extraShape = data.shape[len(axes):]
    output = np.empty(tuple(shape) + extraShape, dtype=data.dtype)
    for inds in np.ndindex(*extraShape):
        ind = (Ellipsis,) + inds
        #print data[ind].shape, x.shape, output[ind].shape, output.shape
        output[ind] = scipy.ndimage.map_coordinates(data[ind], x, order=order, **kargs)
    
    tr = list(range(output.ndim))
    trb = []
    for i in range(min(axes)):
        ind = tr1.index(i) + (len(shape)-len(axes))
        tr.remove(ind)
        trb.append(ind)
    tr2 = tuple(trb+tr)

    ## Untranspose array before returning
    output = output.transpose(tr2)
    if returnCoords:
        return (output, x)
    else:
        return output

def transformToArray(tr):
    """
    Given a QTransform, return a 3x3 numpy array.
    Given a QMatrix4x4, return a 4x4 numpy array.
    
    Example: map an array of x,y coordinates through a transform::
    
        ## coordinates to map are (1,5), (2,6), (3,7), and (4,8)
        coords = np.array([[1,2,3,4], [5,6,7,8], [1,1,1,1]])  # the extra '1' coordinate is needed for translation to work
        
        ## Make an example transform
        tr = QtGui.QTransform()
        tr.translate(3,4)
        tr.scale(2, 0.1)
        
        ## convert to array
        m = pg.transformToArray()[:2]  # ignore the perspective portion of the transformation
        
        ## map coordinates through transform
        mapped = np.dot(m, coords)
    """
    #return np.array([[tr.m11(), tr.m12(), tr.m13()],[tr.m21(), tr.m22(), tr.m23()],[tr.m31(), tr.m32(), tr.m33()]])
    ## The order of elements given by the method names m11..m33 is misleading--
    ## It is most common for x,y translation to occupy the positions 1,3 and 2,3 in
    ## a transformation matrix. However, with QTransform these values appear at m31 and m32.
    ## So the correct interpretation is transposed:
    if isinstance(tr, QtGui.QTransform):
        return np.array([[tr.m11(), tr.m21(), tr.m31()], [tr.m12(), tr.m22(), tr.m32()], [tr.m13(), tr.m23(), tr.m33()]])
    elif isinstance(tr, QtGui.QMatrix4x4):
        return np.array(tr.copyDataTo()).reshape(4,4)
    else:
        raise Exception("Transform argument must be either QTransform or QMatrix4x4.")

def transformCoordinates(tr, coords, transpose=False):
    """
    Map a set of 2D or 3D coordinates through a QTransform or QMatrix4x4.
    The shape of coords must be (2,...) or (3,...)
    The mapping will _ignore_ any perspective transformations.
    
    For coordinate arrays with ndim=2, this is basically equivalent to matrix multiplication.
    Most arrays, however, prefer to put the coordinate axis at the end (eg. shape=(...,3)). To 
    allow this, use transpose=True.
    
    """
    
    if transpose:
        ## move last axis to beginning. This transposition will be reversed before returning the mapped coordinates.
        coords = coords.transpose((coords.ndim-1,) + tuple(range(0,coords.ndim-1)))
    
    nd = coords.shape[0]
    if isinstance(tr, np.ndarray):
        m = tr
    else:
        m = transformToArray(tr)
        m = m[:m.shape[0]-1]  # remove perspective
    
    ## If coords are 3D and tr is 2D, assume no change for Z axis
    if m.shape == (2,3) and nd == 3:
        m2 = np.zeros((3,4))
        m2[:2, :2] = m[:2,:2]
        m2[:2, 3] = m[:2,2]
        m2[2,2] = 1
        m = m2
    
    ## if coords are 2D and tr is 3D, ignore Z axis
    if m.shape == (3,4) and nd == 2:
        m2 = np.empty((2,3))
        m2[:,:2] = m[:2,:2]
        m2[:,2] = m[:2,3]
        m = m2
    
    ## reshape tr and coords to prepare for multiplication
    m = m.reshape(m.shape + (1,)*(coords.ndim-1))
    coords = coords[np.newaxis, ...]
    
    # separate scale/rotate and translation    
    translate = m[:,-1]  
    m = m[:, :-1]
    
    ## map coordinates and return
    mapped = (m*coords).sum(axis=1)  ## apply scale/rotate
    mapped += translate
    
    if transpose:
        ## move first axis to end.
        mapped = mapped.transpose(tuple(range(1,mapped.ndim)) + (0,))
    return mapped
    
    

    
def solve3DTransform(points1, points2):
    """
    Find a 3D transformation matrix that maps points1 onto points2.
    Points must be specified as a list of 4 Vectors.
    """
    if not HAVE_SCIPY:
        raise Exception("This function depends on the scipy library, but it does not appear to be importable.")
    A = np.array([[points1[i].x(), points1[i].y(), points1[i].z(), 1] for i in range(4)])
    B = np.array([[points2[i].x(), points2[i].y(), points2[i].z(), 1] for i in range(4)])
    
    ## solve 3 sets of linear equations to determine transformation matrix elements
    matrix = np.zeros((4,4))
    for i in range(3):
        matrix[i] = scipy.linalg.solve(A, B[:,i])  ## solve Ax = B; x is one row of the desired transformation matrix
    
    return matrix
    
def solveBilinearTransform(points1, points2):
    """
    Find a bilinear transformation matrix (2x4) that maps points1 onto points2.
    Points must be specified as a list of 4 Vector, Point, QPointF, etc.
    
    To use this matrix to map a point [x,y]::
    
        mapped = np.dot(matrix, [x*y, x, y, 1])
    """
    if not HAVE_SCIPY:
        raise Exception("This function depends on the scipy library, but it does not appear to be importable.")
    ## A is 4 rows (points) x 4 columns (xy, x, y, 1)
    ## B is 4 rows (points) x 2 columns (x, y)
    A = np.array([[points1[i].x()*points1[i].y(), points1[i].x(), points1[i].y(), 1] for i in range(4)])
    B = np.array([[points2[i].x(), points2[i].y()] for i in range(4)])
    
    ## solve 2 sets of linear equations to determine transformation matrix elements
    matrix = np.zeros((2,4))
    for i in range(2):
        matrix[i] = scipy.linalg.solve(A, B[:,i])  ## solve Ax = B; x is one row of the desired transformation matrix
    
    return matrix
    
def rescaleData(data, scale, offset, dtype=None):
    """Return data rescaled and optionally cast to a new dtype::
    
        data => (data-offset) * scale
        
    Uses scipy.weave (if available) to improve performance.
    """
    if dtype is None:
        dtype = data.dtype
    else:
        dtype = np.dtype(dtype)
    
    try:
        if not pg.getConfigOption('useWeave'):
            raise Exception('Weave is disabled; falling back to slower version.')
        
        ## require native dtype when using weave
        if not data.dtype.isnative:
            data = data.astype(data.dtype.newbyteorder('='))
        if not dtype.isnative:
            weaveDtype = dtype.newbyteorder('=')
        else:
            weaveDtype = dtype
        
        newData = np.empty((data.size,), dtype=weaveDtype)
        flat = np.ascontiguousarray(data).reshape(data.size)
        size = data.size
        
        code = """
        double sc = (double)scale;
        double off = (double)offset;
        for( int i=0; i<size; i++ ) {
            newData[i] = ((double)flat[i] - off) * sc;
        }
        """
        scipy.weave.inline(code, ['flat', 'newData', 'size', 'offset', 'scale'], compiler='gcc')
        if dtype != weaveDtype:
            newData = newData.astype(dtype)
        data = newData.reshape(data.shape)
    except:
        if pg.getConfigOption('useWeave'):
            if pg.getConfigOption('weaveDebug'):
                debug.printExc("Error; disabling weave.")
            pg.setConfigOption('useWeave', False)
        
        #p = np.poly1d([scale, -offset*scale])
        #data = p(data).astype(dtype)
        d2 = data-offset
        d2 *= scale
        data = d2.astype(dtype)
    return data
    
def applyLookupTable(data, lut):
    """
    Uses values in *data* as indexes to select values from *lut*.
    The returned data has shape data.shape + lut.shape[1:]
    
    Uses scipy.weave to improve performance if it is available.
    Note: color gradient lookup tables can be generated using GradientWidget.
    """
    if data.dtype.kind not in ('i', 'u'):
        data = data.astype(int)
    
    ## using np.take appears to be faster than even the scipy.weave method and takes care of clipping as well.
    return np.take(lut, data, axis=0, mode='clip')  
    
    ### old methods: 
    #data = np.clip(data, 0, lut.shape[0]-1)
    
    #try:
        #if not USE_WEAVE:
            #raise Exception('Weave is disabled; falling back to slower version.')
        
        ### number of values to copy for each LUT lookup
        #if lut.ndim == 1:
            #ncol = 1
        #else:
            #ncol = sum(lut.shape[1:])
        
        ### output array
        #newData = np.empty((data.size, ncol), dtype=lut.dtype)
        
        ### flattened input arrays
        #flatData = data.flatten()
        #flatLut = lut.reshape((lut.shape[0], ncol))
        
        #dataSize = data.size
        
        ### strides for accessing each item 
        #newStride = newData.strides[0] / newData.dtype.itemsize
        #lutStride = flatLut.strides[0] / flatLut.dtype.itemsize
        #dataStride = flatData.strides[0] / flatData.dtype.itemsize
        
        ### strides for accessing individual values within a single LUT lookup
        #newColStride = newData.strides[1] / newData.dtype.itemsize
        #lutColStride = flatLut.strides[1] / flatLut.dtype.itemsize
        
        #code = """
        
        #for( int i=0; i<dataSize; i++ ) {
            #for( int j=0; j<ncol; j++ ) {
                #newData[i*newStride + j*newColStride] = flatLut[flatData[i*dataStride]*lutStride + j*lutColStride];
            #}
        #}
        #"""
        #scipy.weave.inline(code, ['flatData', 'flatLut', 'newData', 'dataSize', 'ncol', 'newStride', 'lutStride', 'dataStride', 'newColStride', 'lutColStride'])
        #newData = newData.reshape(data.shape + lut.shape[1:])
        ##if np.any(newData != lut[data]):
            ##print "mismatch!"
            
        #data = newData
    #except:
        #if USE_WEAVE:
            #debug.printExc("Error; disabling weave.")
            #USE_WEAVE = False
        #data = lut[data]
        
    #return data


def makeRGBA(*args, **kwds):
    """Equivalent to makeARGB(..., useRGBA=True)"""
    kwds['useRGBA'] = True
    return makeARGB(*args, **kwds)

def makeARGB(data, lut=None, levels=None, scale=None, useRGBA=False): 
    """ 
    Convert an array of values into an ARGB array suitable for building QImages, OpenGL textures, etc.
    
    Returns the ARGB array (values 0-255) and a boolean indicating whether there is alpha channel data.
    This is a two stage process:
    
        1) Rescale the data based on the values in the *levels* argument (min, max).
        2) Determine the final output by passing the rescaled values through a lookup table.
   
    Both stages are optional.
    
    ============ ==================================================================================
    Arguments:
    data         numpy array of int/float types. If 
    levels       List [min, max]; optionally rescale data before converting through the
                 lookup table. The data is rescaled such that min->0 and max->*scale*::
                 
                    rescaled = (clip(data, min, max) - min) * (*scale* / (max - min))
                 
                 It is also possible to use a 2D (N,2) array of values for levels. In this case,
                 it is assumed that each pair of min,max values in the levels array should be 
                 applied to a different subset of the input data (for example, the input data may 
                 already have RGB values and the levels are used to independently scale each 
                 channel). The use of this feature requires that levels.shape[0] == data.shape[-1].
    scale        The maximum value to which data will be rescaled before being passed through the 
                 lookup table (or returned if there is no lookup table). By default this will
                 be set to the length of the lookup table, or 256 is no lookup table is provided.
                 For OpenGL color specifications (as in GLColor4f) use scale=1.0
    lut          Optional lookup table (array with dtype=ubyte).
                 Values in data will be converted to color by indexing directly from lut.
                 The output data shape will be input.shape + lut.shape[1:].
                 
                 Note: the output of makeARGB will have the same dtype as the lookup table, so
                 for conversion to QImage, the dtype must be ubyte.
                 
                 Lookup tables can be built using GradientWidget.
    useRGBA      If True, the data is returned in RGBA order (useful for building OpenGL textures). 
                 The default is False, which returns in ARGB order for use with QImage 
                 (Note that 'ARGB' is a term used by the Qt documentation; the _actual_ order 
                 is BGRA).
    ============ ==================================================================================
    """
    prof = debug.Profiler('functions.makeARGB', disabled=True)
    
    if lut is not None and not isinstance(lut, np.ndarray):
        lut = np.array(lut)
    if levels is not None and not isinstance(levels, np.ndarray):
        levels = np.array(levels)
    
    ## sanity checks
    #if data.ndim == 3:
        #if data.shape[2] not in (3,4):
            #raise Exception("data.shape[2] must be 3 or 4")
        ##if lut is not None:
            ##raise Exception("can not use lookup table with 3D data")
    #elif data.ndim != 2:
        #raise Exception("data must be 2D or 3D")
        
    #if lut is not None:
        ##if lut.ndim == 2:
            ##if lut.shape[1] :
                ##raise Exception("lut.shape[1] must be 3 or 4")
        ##elif lut.ndim != 1:
            ##raise Exception("lut must be 1D or 2D")
        #if lut.dtype != np.ubyte:
            #raise Exception('lookup table must have dtype=ubyte (got %s instead)' % str(lut.dtype))
            

    if levels is not None:
        if levels.ndim == 1:
            if len(levels) != 2:
                raise Exception('levels argument must have length 2')
        elif levels.ndim == 2:
            if lut is not None and lut.ndim > 1:
                raise Exception('Cannot make ARGB data when bot levels and lut have ndim > 2')
            if levels.shape != (data.shape[-1], 2):
                raise Exception('levels must have shape (data.shape[-1], 2)')
        else:
            print(levels)
            raise Exception("levels argument must be 1D or 2D.")
        #levels = np.array(levels)
        #if levels.shape == (2,):
            #pass
        #elif levels.shape in [(3,2), (4,2)]:
            #if data.ndim == 3:
                #raise Exception("Can not use 2D levels with 3D data.")
            #if lut is not None:
                #raise Exception('Can not use 2D levels and lookup table together.')
        #else:
            #raise Exception("Levels must have shape (2,) or (3,2) or (4,2)")
        
    prof.mark('1')

    if scale is None:
        if lut is not None:
            scale = lut.shape[0]
        else:
            scale = 255.

    ## Apply levels if given
    if levels is not None:
        
        if isinstance(levels, np.ndarray) and levels.ndim == 2:
            ## we are going to rescale each channel independently
            if levels.shape[0] != data.shape[-1]:
                raise Exception("When rescaling multi-channel data, there must be the same number of levels as channels (data.shape[-1] == levels.shape[0])")
            newData = np.empty(data.shape, dtype=int)
            for i in range(data.shape[-1]):
                minVal, maxVal = levels[i]
                if minVal == maxVal:
                    maxVal += 1e-16
                newData[...,i] = rescaleData(data[...,i], scale/(maxVal-minVal), minVal, dtype=int)
            data = newData
        else:
            minVal, maxVal = levels
            if minVal == maxVal:
                maxVal += 1e-16
            data = rescaleData(data, scale/(maxVal-minVal), minVal, dtype=int)
    prof.mark('2')


    ## apply LUT if given
    if lut is not None:
        data = applyLookupTable(data, lut)
    else:
        if data.dtype is not np.ubyte:
            data = np.clip(data, 0, 255).astype(np.ubyte)
    prof.mark('3')


    ## copy data into ARGB ordered array
    imgData = np.empty(data.shape[:2]+(4,), dtype=np.ubyte)
    if data.ndim == 2:
        data = data[..., np.newaxis]

    prof.mark('4')

    if useRGBA:
        order = [0,1,2,3] ## array comes out RGBA
    else:
        order = [2,1,0,3] ## for some reason, the colors line up as BGR in the final image.
        
    if data.shape[2] == 1:
        for i in range(3):
            imgData[..., order[i]] = data[..., 0]    
    else:
        for i in range(0, data.shape[2]):
            imgData[..., order[i]] = data[..., i]    
        
    prof.mark('5')
        
    if data.shape[2] == 4:
        alpha = True
    else:
        alpha = False
        imgData[..., 3] = 255
        
    prof.mark('6')
        
    prof.finish()
    return imgData, alpha
    

def makeQImage(imgData, alpha=None, copy=True, transpose=True):
    """
    Turn an ARGB array into QImage.
    By default, the data is copied; changes to the array will not
    be reflected in the image. The image will be given a 'data' attribute
    pointing to the array which shares its data to prevent python
    freeing that memory while the image is in use.
    
    =========== ===================================================================
    Arguments:
    imgData     Array of data to convert. Must have shape (width, height, 3 or 4) 
                and dtype=ubyte. The order of values in the 3rd axis must be 
                (b, g, r, a).
    alpha       If True, the QImage returned will have format ARGB32. If False,
                the format will be RGB32. By default, _alpha_ is True if
                array.shape[2] == 4.
    copy        If True, the data is copied before converting to QImage.
                If False, the new QImage points directly to the data in the array.
                Note that the array must be contiguous for this to work
                (see numpy.ascontiguousarray).
    transpose   If True (the default), the array x/y axes are transposed before 
                creating the image. Note that Qt expects the axes to be in 
                (height, width) order whereas pyqtgraph usually prefers the 
                opposite.
    =========== ===================================================================    
    """
    ## create QImage from buffer
    prof = debug.Profiler('functions.makeQImage', disabled=True)
    
    ## If we didn't explicitly specify alpha, check the array shape.
    if alpha is None:
        alpha = (imgData.shape[2] == 4)
        
    copied = False
    if imgData.shape[2] == 3:  ## need to make alpha channel (even if alpha==False; QImage requires 32 bpp)
        if copy is True:
            d2 = np.empty(imgData.shape[:2] + (4,), dtype=imgData.dtype)
            d2[:,:,:3] = imgData
            d2[:,:,3] = 255
            imgData = d2
            copied = True
        else:
            raise Exception('Array has only 3 channels; cannot make QImage without copying.')
    
    if alpha:
        imgFormat = QtGui.QImage.Format_ARGB32
    else:
        imgFormat = QtGui.QImage.Format_RGB32
        
    if transpose:
        imgData = imgData.transpose((1, 0, 2))  ## QImage expects the row/column order to be opposite
    
    if not imgData.flags['C_CONTIGUOUS']:
        if copy is False:
            extra = ' (try setting transpose=False)' if transpose else ''
            raise Exception('Array is not contiguous; cannot make QImage without copying.'+extra)
        imgData = np.ascontiguousarray(imgData)
        copied = True
        
    if copy is True and copied is False:
        imgData = imgData.copy()
        
    if USE_PYSIDE:
        ch = ctypes.c_char.from_buffer(imgData, 0)
        img = QtGui.QImage(ch, imgData.shape[1], imgData.shape[0], imgFormat)
    else:
        #addr = ctypes.addressof(ctypes.c_char.from_buffer(imgData, 0))
        ## PyQt API for QImage changed between 4.9.3 and 4.9.6 (I don't know exactly which version it was)
        ## So we first attempt the 4.9.6 API, then fall back to 4.9.3
        #addr = ctypes.c_char.from_buffer(imgData, 0)
        #try:
            #img = QtGui.QImage(addr, imgData.shape[1], imgData.shape[0], imgFormat)
        #except TypeError:  
            #addr = ctypes.addressof(addr)
            #img = QtGui.QImage(addr, imgData.shape[1], imgData.shape[0], imgFormat)
        try:
            img = QtGui.QImage(imgData.ctypes.data, imgData.shape[1], imgData.shape[0], imgFormat)
        except:
            if copy:
                # does not leak memory, is not mutable
                img = QtGui.QImage(buffer(imgData), imgData.shape[1], imgData.shape[0], imgFormat)
            else:
                # mutable, but leaks memory
                img = QtGui.QImage(memoryview(imgData), imgData.shape[1], imgData.shape[0], imgFormat)
                
    img.data = imgData
    return img
    #try:
        #buf = imgData.data
    #except AttributeError:  ## happens when image data is non-contiguous
        #buf = imgData.data
        
    #prof.mark('1')
    #qimage = QtGui.QImage(buf, imgData.shape[1], imgData.shape[0], imgFormat)
    #prof.mark('2')
    #qimage.data = imgData
    #prof.finish()
    #return qimage

def imageToArray(img, copy=False, transpose=True):
    """
    Convert a QImage into numpy array. The image must have format RGB32, ARGB32, or ARGB32_Premultiplied.
    By default, the image is not copied; changes made to the array will appear in the QImage as well (beware: if 
    the QImage is collected before the array, there may be trouble).
    The array will have shape (width, height, (b,g,r,a)).
    """
    fmt = img.format()
    ptr = img.bits()
    if USE_PYSIDE:
        arr = np.frombuffer(ptr, dtype=np.ubyte)
    else:
        ptr.setsize(img.byteCount())
        arr = np.asarray(ptr)
    
    if fmt == img.Format_RGB32:
        arr = arr.reshape(img.height(), img.width(), 3)
    elif fmt == img.Format_ARGB32 or fmt == img.Format_ARGB32_Premultiplied:
        arr = arr.reshape(img.height(), img.width(), 4)
    
    if copy:
        arr = arr.copy()
        
    if transpose:
        return arr.transpose((1,0,2))
    else:
        return arr
    
def colorToAlpha(data, color):
    """
    Given an RGBA image in *data*, convert *color* to be transparent. 
    *data* must be an array (w, h, 3 or 4) of ubyte values and *color* must be 
    an array (3) of ubyte values.
    This is particularly useful for use with images that have a black or white background.
    
    Algorithm is taken from Gimp's color-to-alpha function in plug-ins/common/colortoalpha.c
    Credit:
        /*
        * Color To Alpha plug-in v1.0 by Seth Burgess, sjburges@gimp.org 1999/05/14
        *  with algorithm by clahey
        */
    
    """
    data = data.astype(float)
    if data.shape[-1] == 3:  ## add alpha channel if needed
        d2 = np.empty(data.shape[:2]+(4,), dtype=data.dtype)
        d2[...,:3] = data
        d2[...,3] = 255
        data = d2
    
    color = color.astype(float)
    alpha = np.zeros(data.shape[:2]+(3,), dtype=float)
    output = data.copy()
    
    for i in [0,1,2]:
        d = data[...,i]
        c = color[i]
        mask = d > c
        alpha[...,i][mask] = (d[mask] - c) / (255. - c)
        imask = d < c
        alpha[...,i][imask] = (c - d[imask]) / c
    
    output[...,3] = alpha.max(axis=2) * 255.
    
    mask = output[...,3] >= 1.0  ## avoid zero division while processing alpha channel
    correction = 255. / output[...,3][mask]  ## increase value to compensate for decreased alpha
    for i in [0,1,2]:
        output[...,i][mask] = ((output[...,i][mask]-color[i]) * correction) + color[i]
        output[...,3][mask] *= data[...,3][mask] / 255.  ## combine computed and previous alpha values
    
    #raise Exception()
    return np.clip(output, 0, 255).astype(np.ubyte)
    


def arrayToQPath(x, y, connect='all'):
    """Convert an array of x,y coordinats to QPainterPath as efficiently as possible.
    The *connect* argument may be 'all', indicating that each point should be
    connected to the next; 'pairs', indicating that each pair of points
    should be connected, or an array of int32 values (0 or 1) indicating
    connections.
    """

    ## Create all vertices in path. The method used below creates a binary format so that all
    ## vertices can be read in at once. This binary format may change in future versions of Qt,
    ## so the original (slower) method is left here for emergencies:
        #path.moveTo(x[0], y[0])
        #if connect == 'all':
            #for i in range(1, y.shape[0]):
                #path.lineTo(x[i], y[i])
        #elif connect == 'pairs':
            #for i in range(1, y.shape[0]):
                #if i%2 == 0:
                    #path.lineTo(x[i], y[i])
                #else:
                    #path.moveTo(x[i], y[i])
        #elif isinstance(connect, np.ndarray):
            #for i in range(1, y.shape[0]):
                #if connect[i] == 1:
                    #path.lineTo(x[i], y[i])
                #else:
                    #path.moveTo(x[i], y[i])
        #else:
            #raise Exception('connect argument must be "all", "pairs", or array')

    ## Speed this up using >> operator
    ## Format is:
    ##    numVerts(i4)   0(i4)
    ##    x(f8)   y(f8)   0(i4)    <-- 0 means this vertex does not connect
    ##    x(f8)   y(f8)   1(i4)    <-- 1 means this vertex connects to the previous vertex
    ##    ...
    ##    0(i4)
    ##
    ## All values are big endian--pack using struct.pack('>d') or struct.pack('>i')

    path = QtGui.QPainterPath()

    #prof = debug.Profiler('PlotCurveItem.generatePath', disabled=True)
    n = x.shape[0]
    # create empty array, pad with extra space on either end
    arr = np.empty(n+2, dtype=[('x', '>f8'), ('y', '>f8'), ('c', '>i4')])
    # write first two integers
    #prof.mark('allocate empty')
    byteview = arr.view(dtype=np.ubyte)
    byteview[:12] = 0
    byteview.data[12:20] = struct.pack('>ii', n, 0)
    #prof.mark('pack header')
    # Fill array with vertex values
    arr[1:-1]['x'] = x
    arr[1:-1]['y'] = y

    # decide which points are connected by lines
    if connect == 'pairs':
        connect = np.empty((n/2,2), dtype=np.int32)
        connect[:,0] = 1
        connect[:,1] = 0
        connect = connect.flatten()
    if connect == 'finite':
        connect = np.isfinite(x) & np.isfinite(y)
        arr[1:-1]['c'] = connect
    if connect == 'all':
        arr[1:-1]['c'] = 1
    elif isinstance(connect, np.ndarray):
        arr[1:-1]['c'] = connect
    else:
        raise Exception('connect argument must be "all", "pairs", or array')

    #prof.mark('fill array')
    # write last 0
    lastInd = 20*(n+1)
    byteview.data[lastInd:lastInd+4] = struct.pack('>i', 0)
    #prof.mark('footer')
    # create datastream object and stream into path

    ## Avoiding this method because QByteArray(str) leaks memory in PySide
    #buf = QtCore.QByteArray(arr.data[12:lastInd+4])  # I think one unnecessary copy happens here

    path.strn = byteview.data[12:lastInd+4] # make sure data doesn't run away
    try:
        buf = QtCore.QByteArray.fromRawData(path.strn)
    except TypeError:
        buf = QtCore.QByteArray(bytes(path.strn))
    #prof.mark('create buffer')
    ds = QtCore.QDataStream(buf)

    ds >> path
    #prof.mark('load')

    #prof.finish()

    return path

#def isosurface(data, level):
    #"""
    #Generate isosurface from volumetric data using marching tetrahedra algorithm.
    #See Paul Bourke, "Polygonising a Scalar Field Using Tetrahedrons"  (http://local.wasp.uwa.edu.au/~pbourke/geometry/polygonise/)
    
    #*data*   3D numpy array of scalar values
    #*level*  The level at which to generate an isosurface
    #"""
    
    #facets = []
    
    ### mark everything below the isosurface level
    #mask = data < level
    
    #### make eight sub-fields 
    #fields = np.empty((2,2,2), dtype=object)
    #slices = [slice(0,-1), slice(1,None)]
    #for i in [0,1]:
        #for j in [0,1]:
            #for k in [0,1]:
                #fields[i,j,k] = mask[slices[i], slices[j], slices[k]]
    
    
    
    ### split each cell into 6 tetrahedra
    ### these all have the same 'orienation'; points 1,2,3 circle 
    ### clockwise around point 0
    #tetrahedra = [
        #[(0,1,0), (1,1,1), (0,1,1), (1,0,1)],
        #[(0,1,0), (0,1,1), (0,0,1), (1,0,1)],
        #[(0,1,0), (0,0,1), (0,0,0), (1,0,1)],
        #[(0,1,0), (0,0,0), (1,0,0), (1,0,1)],
        #[(0,1,0), (1,0,0), (1,1,0), (1,0,1)],
        #[(0,1,0), (1,1,0), (1,1,1), (1,0,1)]
    #]
    
    ### each tetrahedron will be assigned an index
    ### which determines how to generate its facets.
    ### this structure is: 
    ###    facets[index][facet1, facet2, ...]
    ### where each facet is triangular and its points are each 
    ### interpolated between two points on the tetrahedron
    ###    facet = [(p1a, p1b), (p2a, p2b), (p3a, p3b)]
    ### facet points always circle clockwise if you are looking 
    ### at them from below the isosurface.
    #indexFacets = [
        #[],  ## all above
        #[[(0,1), (0,2), (0,3)]],  # 0 below
        #[[(1,0), (1,3), (1,2)]],   # 1 below
        #[[(0,2), (1,3), (1,2)], [(0,2), (0,3), (1,3)]],   # 0,1 below
        #[[(2,0), (2,1), (2,3)]],   # 2 below
        #[[(0,3), (1,2), (2,3)], [(0,3), (0,1), (1,2)]],   # 0,2 below
        #[[(1,0), (2,3), (2,0)], [(1,0), (1,3), (2,3)]],   # 1,2 below
        #[[(3,0), (3,1), (3,2)]],   # 3 above
        #[[(3,0), (3,2), (3,1)]],   # 3 below
        #[[(1,0), (2,0), (2,3)], [(1,0), (2,3), (1,3)]],   # 0,3 below
        #[[(0,3), (2,3), (1,2)], [(0,3), (1,2), (0,1)]],   # 1,3 below
        #[[(2,0), (2,3), (2,1)]], # 0,1,3 below
        #[[(0,2), (1,2), (1,3)], [(0,2), (1,3), (0,3)]],   # 2,3 below
        #[[(1,0), (1,2), (1,3)]], # 0,2,3 below
        #[[(0,1), (0,3), (0,2)]], # 1,2,3 below
        #[]  ## all below
    #]
    
    #for tet in tetrahedra:
        
        ### get the 4 fields for this tetrahedron
        #tetFields = [fields[c] for c in tet]
        
        ### generate an index for each grid cell
        #index = tetFields[0] + tetFields[1]*2 + tetFields[2]*4 + tetFields[3]*8
        
        ### add facets
        #for i in xrange(index.shape[0]):                 # data x-axis
            #for j in xrange(index.shape[1]):             # data y-axis
                #for k in xrange(index.shape[2]):         # data z-axis
                    #for f in indexFacets[index[i,j,k]]:  # faces to generate for this tet
                        #pts = []
                        #for l in [0,1,2]:      # points in this face
                            #p1 = tet[f[l][0]]  # tet corner 1
                            #p2 = tet[f[l][1]]  # tet corner 2
                            #pts.append([(p1[x]+p2[x])*0.5+[i,j,k][x]+0.5 for x in [0,1,2]]) ## interpolate between tet corners
                        #facets.append(pts)

    #return facets
    

def isocurve(data, level, connected=False, extendToEdge=False, path=False):
    """
    Generate isocurve from 2D data using marching squares algorithm.
    
    ============= =========================================================
    Arguments
    data          2D numpy array of scalar values
    level         The level at which to generate an isosurface
    connected     If False, return a single long list of point pairs
                  If True, return multiple long lists of connected point 
                  locations. (This is slower but better for drawing 
                  continuous lines)
    extendToEdge  If True, extend the curves to reach the exact edges of 
                  the data. 
    path          if True, return a QPainterPath rather than a list of 
                  vertex coordinates. This forces connected=True.
    ============= =========================================================
    
    This function is SLOW; plenty of room for optimization here.
    """    
    
    if path is True:
        connected = True
    
    if extendToEdge:
        d2 = np.empty((data.shape[0]+2, data.shape[1]+2), dtype=data.dtype)
        d2[1:-1, 1:-1] = data
        d2[0, 1:-1] = data[0]
        d2[-1, 1:-1] = data[-1]
        d2[1:-1, 0] = data[:, 0]
        d2[1:-1, -1] = data[:, -1]
        d2[0,0] = d2[0,1]
        d2[0,-1] = d2[1,-1]
        d2[-1,0] = d2[-1,1]
        d2[-1,-1] = d2[-1,-2]
        data = d2
    
    sideTable = [
    [],
    [0,1],
    [1,2],
    [0,2],
    [0,3],
    [1,3],
    [0,1,2,3],
    [2,3],
    [2,3],
    [0,1,2,3],
    [1,3],
    [0,3],
    [0,2],
    [1,2],
    [0,1],
    []
    ]
    
    edgeKey=[
    [(0,1), (0,0)],
    [(0,0), (1,0)],
    [(1,0), (1,1)],
    [(1,1), (0,1)]
    ]
    
    
    lines = []
    
    ## mark everything below the isosurface level
    mask = data < level
    
    ### make four sub-fields and compute indexes for grid cells
    index = np.zeros([x-1 for x in data.shape], dtype=np.ubyte)
    fields = np.empty((2,2), dtype=object)
    slices = [slice(0,-1), slice(1,None)]
    for i in [0,1]:
        for j in [0,1]:
            fields[i,j] = mask[slices[i], slices[j]]
            #vertIndex = i - 2*j*i + 3*j + 4*k  ## this is just to match Bourk's vertex numbering scheme
            vertIndex = i+2*j
            #print i,j,k," : ", fields[i,j,k], 2**vertIndex
            index += fields[i,j] * 2**vertIndex
            #print index
    #print index
    
    ## add lines
    for i in range(index.shape[0]):                 # data x-axis
        for j in range(index.shape[1]):             # data y-axis     
            sides = sideTable[index[i,j]]
            for l in range(0, len(sides), 2):     ## faces for this grid cell
                edges = sides[l:l+2]
                pts = []
                for m in [0,1]:      # points in this face
                    p1 = edgeKey[edges[m]][0] # p1, p2 are points at either side of an edge
                    p2 = edgeKey[edges[m]][1]
                    v1 = data[i+p1[0], j+p1[1]] # v1 and v2 are the values at p1 and p2
                    v2 = data[i+p2[0], j+p2[1]]
                    f = (level-v1) / (v2-v1)
                    fi = 1.0 - f
                    p = (    ## interpolate between corners
                        p1[0]*fi + p2[0]*f + i + 0.5, 
                        p1[1]*fi + p2[1]*f + j + 0.5
                        )
                    if extendToEdge:
                        ## check bounds
                        p = (
                            min(data.shape[0]-2, max(0, p[0]-1)),
                            min(data.shape[1]-2, max(0, p[1]-1)),                        
                        )
                    if connected:
                        gridKey = i + (1 if edges[m]==2 else 0), j + (1 if edges[m]==3 else 0), edges[m]%2
                        pts.append((p, gridKey))  ## give the actual position and a key identifying the grid location (for connecting segments)
                    else:
                        pts.append(p)
                
                lines.append(pts)

    if not connected:
        return lines
                
    ## turn disjoint list of segments into continuous lines

    #lines = [[2,5], [5,4], [3,4], [1,3], [6,7], [7,8], [8,6], [11,12], [12,15], [11,13], [13,14]]
    #lines = [[(float(a), a), (float(b), b)] for a,b in lines]
    points = {}  ## maps each point to its connections
    for a,b in lines:
        if a[1] not in points:
            points[a[1]] = []
        points[a[1]].append([a,b])
        if b[1] not in points:
            points[b[1]] = []
        points[b[1]].append([b,a])

    ## rearrange into chains
    for k in list(points.keys()):
        try:
            chains = points[k]
        except KeyError:   ## already used this point elsewhere
            continue
        #print "===========", k
        for chain in chains:
            #print "  chain:", chain
            x = None
            while True:
                if x == chain[-1][1]:
                    break ## nothing left to do on this chain
                    
                x = chain[-1][1]
                if x == k:  
                    break ## chain has looped; we're done and can ignore the opposite chain
                y = chain[-2][1]
                connects = points[x]
                for conn in connects[:]:
                    if conn[1][1] != y:
                        #print "    ext:", conn
                        chain.extend(conn[1:])
                #print "    del:", x
                del points[x]
            if chain[0][1] == chain[-1][1]:  # looped chain; no need to continue the other direction
                chains.pop()
                break
                

    ## extract point locations 
    lines = []
    for chain in points.values():
        if len(chain) == 2:
            chain = chain[1][1:][::-1] + chain[0]  # join together ends of chain
        else:
            chain = chain[0]
        lines.append([p[0] for p in chain])
    
    if not path:
        return lines ## a list of pairs of points
    
    path = QtGui.QPainterPath()
    for line in lines:
        path.moveTo(*line[0])
        for p in line[1:]:
            path.lineTo(*p)
    
    return path
    
    
def traceImage(image, values, smooth=0.5):
    """
    Convert an image to a set of QPainterPath curves.
    One curve will be generated for each item in *values*; each curve outlines the area
    of the image that is closer to its value than to any others.
    
    If image is RGB or RGBA, then the shape of values should be (nvals, 3/4)
    The parameter *smooth* is expressed in pixels.
    """
    import scipy.ndimage as ndi
    if values.ndim == 2:
        values = values.T
    values = values[np.newaxis, np.newaxis, ...].astype(float)
    image = image[..., np.newaxis].astype(float)
    diff = np.abs(image-values)
    if values.ndim == 4:
        diff = diff.sum(axis=2)
        
    labels = np.argmin(diff, axis=2)
    
    paths = []
    for i in range(diff.shape[-1]):    
        d = (labels==i).astype(float)
        d = ndi.gaussian_filter(d, (smooth, smooth))
        lines = isocurve(d, 0.5, connected=True, extendToEdge=True)
        path = QtGui.QPainterPath()
        for line in lines:
            path.moveTo(*line[0])
            for p in line[1:]:
                path.lineTo(*p)
        
        paths.append(path)
    return paths
    
    
    
IsosurfaceDataCache = None
def isosurface(data, level):
    """
    Generate isosurface from volumetric data using marching cubes algorithm.
    See Paul Bourke, "Polygonising a Scalar Field"  
    (http://paulbourke.net/geometry/polygonise/)
    
    *data*   3D numpy array of scalar values
    *level*  The level at which to generate an isosurface
    
    Returns an array of vertex coordinates (Nv, 3) and an array of 
    per-face vertex indexes (Nf, 3)    
    """
    ## For improvement, see:
    ## 
    ## Efficient implementation of Marching Cubes' cases with topological guarantees.
    ## Thomas Lewiner, Helio Lopes, Antonio Wilson Vieira and Geovan Tavares.
    ## Journal of Graphics Tools 8(2): pp. 1-15 (december 2003)
    
    ## Precompute lookup tables on the first run
    global IsosurfaceDataCache
    if IsosurfaceDataCache is None:
        ## map from grid cell index to edge index.
        ## grid cell index tells us which corners are below the isosurface,
        ## edge index tells us which edges are cut by the isosurface.
        ## (Data stolen from Bourk; see above.)
        edgeTable = np.array([
        0x0  , 0x109, 0x203, 0x30a, 0x406, 0x50f, 0x605, 0x70c,
        0x80c, 0x905, 0xa0f, 0xb06, 0xc0a, 0xd03, 0xe09, 0xf00,
        0x190, 0x99 , 0x393, 0x29a, 0x596, 0x49f, 0x795, 0x69c,
        0x99c, 0x895, 0xb9f, 0xa96, 0xd9a, 0xc93, 0xf99, 0xe90,
        0x230, 0x339, 0x33 , 0x13a, 0x636, 0x73f, 0x435, 0x53c,
        0xa3c, 0xb35, 0x83f, 0x936, 0xe3a, 0xf33, 0xc39, 0xd30,
        0x3a0, 0x2a9, 0x1a3, 0xaa , 0x7a6, 0x6af, 0x5a5, 0x4ac,
        0xbac, 0xaa5, 0x9af, 0x8a6, 0xfaa, 0xea3, 0xda9, 0xca0,
        0x460, 0x569, 0x663, 0x76a, 0x66 , 0x16f, 0x265, 0x36c,
        0xc6c, 0xd65, 0xe6f, 0xf66, 0x86a, 0x963, 0xa69, 0xb60,
        0x5f0, 0x4f9, 0x7f3, 0x6fa, 0x1f6, 0xff , 0x3f5, 0x2fc,
        0xdfc, 0xcf5, 0xfff, 0xef6, 0x9fa, 0x8f3, 0xbf9, 0xaf0,
        0x650, 0x759, 0x453, 0x55a, 0x256, 0x35f, 0x55 , 0x15c,
        0xe5c, 0xf55, 0xc5f, 0xd56, 0xa5a, 0xb53, 0x859, 0x950,
        0x7c0, 0x6c9, 0x5c3, 0x4ca, 0x3c6, 0x2cf, 0x1c5, 0xcc ,
        0xfcc, 0xec5, 0xdcf, 0xcc6, 0xbca, 0xac3, 0x9c9, 0x8c0,
        0x8c0, 0x9c9, 0xac3, 0xbca, 0xcc6, 0xdcf, 0xec5, 0xfcc,
        0xcc , 0x1c5, 0x2cf, 0x3c6, 0x4ca, 0x5c3, 0x6c9, 0x7c0,
        0x950, 0x859, 0xb53, 0xa5a, 0xd56, 0xc5f, 0xf55, 0xe5c,
        0x15c, 0x55 , 0x35f, 0x256, 0x55a, 0x453, 0x759, 0x650,
        0xaf0, 0xbf9, 0x8f3, 0x9fa, 0xef6, 0xfff, 0xcf5, 0xdfc,
        0x2fc, 0x3f5, 0xff , 0x1f6, 0x6fa, 0x7f3, 0x4f9, 0x5f0,
        0xb60, 0xa69, 0x963, 0x86a, 0xf66, 0xe6f, 0xd65, 0xc6c,
        0x36c, 0x265, 0x16f, 0x66 , 0x76a, 0x663, 0x569, 0x460,
        0xca0, 0xda9, 0xea3, 0xfaa, 0x8a6, 0x9af, 0xaa5, 0xbac,
        0x4ac, 0x5a5, 0x6af, 0x7a6, 0xaa , 0x1a3, 0x2a9, 0x3a0,
        0xd30, 0xc39, 0xf33, 0xe3a, 0x936, 0x83f, 0xb35, 0xa3c,
        0x53c, 0x435, 0x73f, 0x636, 0x13a, 0x33 , 0x339, 0x230,
        0xe90, 0xf99, 0xc93, 0xd9a, 0xa96, 0xb9f, 0x895, 0x99c,
        0x69c, 0x795, 0x49f, 0x596, 0x29a, 0x393, 0x99 , 0x190,
        0xf00, 0xe09, 0xd03, 0xc0a, 0xb06, 0xa0f, 0x905, 0x80c,
        0x70c, 0x605, 0x50f, 0x406, 0x30a, 0x203, 0x109, 0x0   ], dtype=np.uint16)
        
        ## Table of triangles to use for filling each grid cell.
        ## Each set of three integers tells us which three edges to
        ## draw a triangle between.
        ## (Data stolen from Bourk; see above.)
        triTable = [
            [],
            [0, 8, 3],
            [0, 1, 9],
            [1, 8, 3, 9, 8, 1],
            [1, 2, 10],
            [0, 8, 3, 1, 2, 10],
            [9, 2, 10, 0, 2, 9],
            [2, 8, 3, 2, 10, 8, 10, 9, 8],
            [3, 11, 2],
            [0, 11, 2, 8, 11, 0],
            [1, 9, 0, 2, 3, 11],
            [1, 11, 2, 1, 9, 11, 9, 8, 11],
            [3, 10, 1, 11, 10, 3],
            [0, 10, 1, 0, 8, 10, 8, 11, 10],
            [3, 9, 0, 3, 11, 9, 11, 10, 9],
            [9, 8, 10, 10, 8, 11],
            [4, 7, 8],
            [4, 3, 0, 7, 3, 4],
            [0, 1, 9, 8, 4, 7],
            [4, 1, 9, 4, 7, 1, 7, 3, 1],
            [1, 2, 10, 8, 4, 7],
            [3, 4, 7, 3, 0, 4, 1, 2, 10],
            [9, 2, 10, 9, 0, 2, 8, 4, 7],
            [2, 10, 9, 2, 9, 7, 2, 7, 3, 7, 9, 4],
            [8, 4, 7, 3, 11, 2],
            [11, 4, 7, 11, 2, 4, 2, 0, 4],
            [9, 0, 1, 8, 4, 7, 2, 3, 11],
            [4, 7, 11, 9, 4, 11, 9, 11, 2, 9, 2, 1],
            [3, 10, 1, 3, 11, 10, 7, 8, 4],
            [1, 11, 10, 1, 4, 11, 1, 0, 4, 7, 11, 4],
            [4, 7, 8, 9, 0, 11, 9, 11, 10, 11, 0, 3],
            [4, 7, 11, 4, 11, 9, 9, 11, 10],
            [9, 5, 4],
            [9, 5, 4, 0, 8, 3],
            [0, 5, 4, 1, 5, 0],
            [8, 5, 4, 8, 3, 5, 3, 1, 5],
            [1, 2, 10, 9, 5, 4],
            [3, 0, 8, 1, 2, 10, 4, 9, 5],
            [5, 2, 10, 5, 4, 2, 4, 0, 2],
            [2, 10, 5, 3, 2, 5, 3, 5, 4, 3, 4, 8],
            [9, 5, 4, 2, 3, 11],
            [0, 11, 2, 0, 8, 11, 4, 9, 5],
            [0, 5, 4, 0, 1, 5, 2, 3, 11],
            [2, 1, 5, 2, 5, 8, 2, 8, 11, 4, 8, 5],
            [10, 3, 11, 10, 1, 3, 9, 5, 4],
            [4, 9, 5, 0, 8, 1, 8, 10, 1, 8, 11, 10],
            [5, 4, 0, 5, 0, 11, 5, 11, 10, 11, 0, 3],
            [5, 4, 8, 5, 8, 10, 10, 8, 11],
            [9, 7, 8, 5, 7, 9],
            [9, 3, 0, 9, 5, 3, 5, 7, 3],
            [0, 7, 8, 0, 1, 7, 1, 5, 7],
            [1, 5, 3, 3, 5, 7],
            [9, 7, 8, 9, 5, 7, 10, 1, 2],
            [10, 1, 2, 9, 5, 0, 5, 3, 0, 5, 7, 3],
            [8, 0, 2, 8, 2, 5, 8, 5, 7, 10, 5, 2],
            [2, 10, 5, 2, 5, 3, 3, 5, 7],
            [7, 9, 5, 7, 8, 9, 3, 11, 2],
            [9, 5, 7, 9, 7, 2, 9, 2, 0, 2, 7, 11],
            [2, 3, 11, 0, 1, 8, 1, 7, 8, 1, 5, 7],
            [11, 2, 1, 11, 1, 7, 7, 1, 5],
            [9, 5, 8, 8, 5, 7, 10, 1, 3, 10, 3, 11],
            [5, 7, 0, 5, 0, 9, 7, 11, 0, 1, 0, 10, 11, 10, 0],
            [11, 10, 0, 11, 0, 3, 10, 5, 0, 8, 0, 7, 5, 7, 0],
            [11, 10, 5, 7, 11, 5],
            [10, 6, 5],
            [0, 8, 3, 5, 10, 6],
            [9, 0, 1, 5, 10, 6],
            [1, 8, 3, 1, 9, 8, 5, 10, 6],
            [1, 6, 5, 2, 6, 1],
            [1, 6, 5, 1, 2, 6, 3, 0, 8],
            [9, 6, 5, 9, 0, 6, 0, 2, 6],
            [5, 9, 8, 5, 8, 2, 5, 2, 6, 3, 2, 8],
            [2, 3, 11, 10, 6, 5],
            [11, 0, 8, 11, 2, 0, 10, 6, 5],
            [0, 1, 9, 2, 3, 11, 5, 10, 6],
            [5, 10, 6, 1, 9, 2, 9, 11, 2, 9, 8, 11],
            [6, 3, 11, 6, 5, 3, 5, 1, 3],
            [0, 8, 11, 0, 11, 5, 0, 5, 1, 5, 11, 6],
            [3, 11, 6, 0, 3, 6, 0, 6, 5, 0, 5, 9],
            [6, 5, 9, 6, 9, 11, 11, 9, 8],
            [5, 10, 6, 4, 7, 8],
            [4, 3, 0, 4, 7, 3, 6, 5, 10],
            [1, 9, 0, 5, 10, 6, 8, 4, 7],
            [10, 6, 5, 1, 9, 7, 1, 7, 3, 7, 9, 4],
            [6, 1, 2, 6, 5, 1, 4, 7, 8],
            [1, 2, 5, 5, 2, 6, 3, 0, 4, 3, 4, 7],
            [8, 4, 7, 9, 0, 5, 0, 6, 5, 0, 2, 6],
            [7, 3, 9, 7, 9, 4, 3, 2, 9, 5, 9, 6, 2, 6, 9],
            [3, 11, 2, 7, 8, 4, 10, 6, 5],
            [5, 10, 6, 4, 7, 2, 4, 2, 0, 2, 7, 11],
            [0, 1, 9, 4, 7, 8, 2, 3, 11, 5, 10, 6],
            [9, 2, 1, 9, 11, 2, 9, 4, 11, 7, 11, 4, 5, 10, 6],
            [8, 4, 7, 3, 11, 5, 3, 5, 1, 5, 11, 6],
            [5, 1, 11, 5, 11, 6, 1, 0, 11, 7, 11, 4, 0, 4, 11],
            [0, 5, 9, 0, 6, 5, 0, 3, 6, 11, 6, 3, 8, 4, 7],
            [6, 5, 9, 6, 9, 11, 4, 7, 9, 7, 11, 9],
            [10, 4, 9, 6, 4, 10],
            [4, 10, 6, 4, 9, 10, 0, 8, 3],
            [10, 0, 1, 10, 6, 0, 6, 4, 0],
            [8, 3, 1, 8, 1, 6, 8, 6, 4, 6, 1, 10],
            [1, 4, 9, 1, 2, 4, 2, 6, 4],
            [3, 0, 8, 1, 2, 9, 2, 4, 9, 2, 6, 4],
            [0, 2, 4, 4, 2, 6],
            [8, 3, 2, 8, 2, 4, 4, 2, 6],
            [10, 4, 9, 10, 6, 4, 11, 2, 3],
            [0, 8, 2, 2, 8, 11, 4, 9, 10, 4, 10, 6],
            [3, 11, 2, 0, 1, 6, 0, 6, 4, 6, 1, 10],
            [6, 4, 1, 6, 1, 10, 4, 8, 1, 2, 1, 11, 8, 11, 1],
            [9, 6, 4, 9, 3, 6, 9, 1, 3, 11, 6, 3],
            [8, 11, 1, 8, 1, 0, 11, 6, 1, 9, 1, 4, 6, 4, 1],
            [3, 11, 6, 3, 6, 0, 0, 6, 4],
            [6, 4, 8, 11, 6, 8],
            [7, 10, 6, 7, 8, 10, 8, 9, 10],
            [0, 7, 3, 0, 10, 7, 0, 9, 10, 6, 7, 10],
            [10, 6, 7, 1, 10, 7, 1, 7, 8, 1, 8, 0],
            [10, 6, 7, 10, 7, 1, 1, 7, 3],
            [1, 2, 6, 1, 6, 8, 1, 8, 9, 8, 6, 7],
            [2, 6, 9, 2, 9, 1, 6, 7, 9, 0, 9, 3, 7, 3, 9],
            [7, 8, 0, 7, 0, 6, 6, 0, 2],
            [7, 3, 2, 6, 7, 2],
            [2, 3, 11, 10, 6, 8, 10, 8, 9, 8, 6, 7],
            [2, 0, 7, 2, 7, 11, 0, 9, 7, 6, 7, 10, 9, 10, 7],
            [1, 8, 0, 1, 7, 8, 1, 10, 7, 6, 7, 10, 2, 3, 11],
            [11, 2, 1, 11, 1, 7, 10, 6, 1, 6, 7, 1],
            [8, 9, 6, 8, 6, 7, 9, 1, 6, 11, 6, 3, 1, 3, 6],
            [0, 9, 1, 11, 6, 7],
            [7, 8, 0, 7, 0, 6, 3, 11, 0, 11, 6, 0],
            [7, 11, 6],
            [7, 6, 11],
            [3, 0, 8, 11, 7, 6],
            [0, 1, 9, 11, 7, 6],
            [8, 1, 9, 8, 3, 1, 11, 7, 6],
            [10, 1, 2, 6, 11, 7],
            [1, 2, 10, 3, 0, 8, 6, 11, 7],
            [2, 9, 0, 2, 10, 9, 6, 11, 7],
            [6, 11, 7, 2, 10, 3, 10, 8, 3, 10, 9, 8],
            [7, 2, 3, 6, 2, 7],
            [7, 0, 8, 7, 6, 0, 6, 2, 0],
            [2, 7, 6, 2, 3, 7, 0, 1, 9],
            [1, 6, 2, 1, 8, 6, 1, 9, 8, 8, 7, 6],
            [10, 7, 6, 10, 1, 7, 1, 3, 7],
            [10, 7, 6, 1, 7, 10, 1, 8, 7, 1, 0, 8],
            [0, 3, 7, 0, 7, 10, 0, 10, 9, 6, 10, 7],
            [7, 6, 10, 7, 10, 8, 8, 10, 9],
            [6, 8, 4, 11, 8, 6],
            [3, 6, 11, 3, 0, 6, 0, 4, 6],
            [8, 6, 11, 8, 4, 6, 9, 0, 1],
            [9, 4, 6, 9, 6, 3, 9, 3, 1, 11, 3, 6],
            [6, 8, 4, 6, 11, 8, 2, 10, 1],
            [1, 2, 10, 3, 0, 11, 0, 6, 11, 0, 4, 6],
            [4, 11, 8, 4, 6, 11, 0, 2, 9, 2, 10, 9],
            [10, 9, 3, 10, 3, 2, 9, 4, 3, 11, 3, 6, 4, 6, 3],
            [8, 2, 3, 8, 4, 2, 4, 6, 2],
            [0, 4, 2, 4, 6, 2],
            [1, 9, 0, 2, 3, 4, 2, 4, 6, 4, 3, 8],
            [1, 9, 4, 1, 4, 2, 2, 4, 6],
            [8, 1, 3, 8, 6, 1, 8, 4, 6, 6, 10, 1],
            [10, 1, 0, 10, 0, 6, 6, 0, 4],
            [4, 6, 3, 4, 3, 8, 6, 10, 3, 0, 3, 9, 10, 9, 3],
            [10, 9, 4, 6, 10, 4],
            [4, 9, 5, 7, 6, 11],
            [0, 8, 3, 4, 9, 5, 11, 7, 6],
            [5, 0, 1, 5, 4, 0, 7, 6, 11],
            [11, 7, 6, 8, 3, 4, 3, 5, 4, 3, 1, 5],
            [9, 5, 4, 10, 1, 2, 7, 6, 11],
            [6, 11, 7, 1, 2, 10, 0, 8, 3, 4, 9, 5],
            [7, 6, 11, 5, 4, 10, 4, 2, 10, 4, 0, 2],
            [3, 4, 8, 3, 5, 4, 3, 2, 5, 10, 5, 2, 11, 7, 6],
            [7, 2, 3, 7, 6, 2, 5, 4, 9],
            [9, 5, 4, 0, 8, 6, 0, 6, 2, 6, 8, 7],
            [3, 6, 2, 3, 7, 6, 1, 5, 0, 5, 4, 0],
            [6, 2, 8, 6, 8, 7, 2, 1, 8, 4, 8, 5, 1, 5, 8],
            [9, 5, 4, 10, 1, 6, 1, 7, 6, 1, 3, 7],
            [1, 6, 10, 1, 7, 6, 1, 0, 7, 8, 7, 0, 9, 5, 4],
            [4, 0, 10, 4, 10, 5, 0, 3, 10, 6, 10, 7, 3, 7, 10],
            [7, 6, 10, 7, 10, 8, 5, 4, 10, 4, 8, 10],
            [6, 9, 5, 6, 11, 9, 11, 8, 9],
            [3, 6, 11, 0, 6, 3, 0, 5, 6, 0, 9, 5],
            [0, 11, 8, 0, 5, 11, 0, 1, 5, 5, 6, 11],
            [6, 11, 3, 6, 3, 5, 5, 3, 1],
            [1, 2, 10, 9, 5, 11, 9, 11, 8, 11, 5, 6],
            [0, 11, 3, 0, 6, 11, 0, 9, 6, 5, 6, 9, 1, 2, 10],
            [11, 8, 5, 11, 5, 6, 8, 0, 5, 10, 5, 2, 0, 2, 5],
            [6, 11, 3, 6, 3, 5, 2, 10, 3, 10, 5, 3],
            [5, 8, 9, 5, 2, 8, 5, 6, 2, 3, 8, 2],
            [9, 5, 6, 9, 6, 0, 0, 6, 2],
            [1, 5, 8, 1, 8, 0, 5, 6, 8, 3, 8, 2, 6, 2, 8],
            [1, 5, 6, 2, 1, 6],
            [1, 3, 6, 1, 6, 10, 3, 8, 6, 5, 6, 9, 8, 9, 6],
            [10, 1, 0, 10, 0, 6, 9, 5, 0, 5, 6, 0],
            [0, 3, 8, 5, 6, 10],
            [10, 5, 6],
            [11, 5, 10, 7, 5, 11],
            [11, 5, 10, 11, 7, 5, 8, 3, 0],
            [5, 11, 7, 5, 10, 11, 1, 9, 0],
            [10, 7, 5, 10, 11, 7, 9, 8, 1, 8, 3, 1],
            [11, 1, 2, 11, 7, 1, 7, 5, 1],
            [0, 8, 3, 1, 2, 7, 1, 7, 5, 7, 2, 11],
            [9, 7, 5, 9, 2, 7, 9, 0, 2, 2, 11, 7],
            [7, 5, 2, 7, 2, 11, 5, 9, 2, 3, 2, 8, 9, 8, 2],
            [2, 5, 10, 2, 3, 5, 3, 7, 5],
            [8, 2, 0, 8, 5, 2, 8, 7, 5, 10, 2, 5],
            [9, 0, 1, 5, 10, 3, 5, 3, 7, 3, 10, 2],
            [9, 8, 2, 9, 2, 1, 8, 7, 2, 10, 2, 5, 7, 5, 2],
            [1, 3, 5, 3, 7, 5],
            [0, 8, 7, 0, 7, 1, 1, 7, 5],
            [9, 0, 3, 9, 3, 5, 5, 3, 7],
            [9, 8, 7, 5, 9, 7],
            [5, 8, 4, 5, 10, 8, 10, 11, 8],
            [5, 0, 4, 5, 11, 0, 5, 10, 11, 11, 3, 0],
            [0, 1, 9, 8, 4, 10, 8, 10, 11, 10, 4, 5],
            [10, 11, 4, 10, 4, 5, 11, 3, 4, 9, 4, 1, 3, 1, 4],
            [2, 5, 1, 2, 8, 5, 2, 11, 8, 4, 5, 8],
            [0, 4, 11, 0, 11, 3, 4, 5, 11, 2, 11, 1, 5, 1, 11],
            [0, 2, 5, 0, 5, 9, 2, 11, 5, 4, 5, 8, 11, 8, 5],
            [9, 4, 5, 2, 11, 3],
            [2, 5, 10, 3, 5, 2, 3, 4, 5, 3, 8, 4],
            [5, 10, 2, 5, 2, 4, 4, 2, 0],
            [3, 10, 2, 3, 5, 10, 3, 8, 5, 4, 5, 8, 0, 1, 9],
            [5, 10, 2, 5, 2, 4, 1, 9, 2, 9, 4, 2],
            [8, 4, 5, 8, 5, 3, 3, 5, 1],
            [0, 4, 5, 1, 0, 5],
            [8, 4, 5, 8, 5, 3, 9, 0, 5, 0, 3, 5],
            [9, 4, 5],
            [4, 11, 7, 4, 9, 11, 9, 10, 11],
            [0, 8, 3, 4, 9, 7, 9, 11, 7, 9, 10, 11],
            [1, 10, 11, 1, 11, 4, 1, 4, 0, 7, 4, 11],
            [3, 1, 4, 3, 4, 8, 1, 10, 4, 7, 4, 11, 10, 11, 4],
            [4, 11, 7, 9, 11, 4, 9, 2, 11, 9, 1, 2],
            [9, 7, 4, 9, 11, 7, 9, 1, 11, 2, 11, 1, 0, 8, 3],
            [11, 7, 4, 11, 4, 2, 2, 4, 0],
            [11, 7, 4, 11, 4, 2, 8, 3, 4, 3, 2, 4],
            [2, 9, 10, 2, 7, 9, 2, 3, 7, 7, 4, 9],
            [9, 10, 7, 9, 7, 4, 10, 2, 7, 8, 7, 0, 2, 0, 7],
            [3, 7, 10, 3, 10, 2, 7, 4, 10, 1, 10, 0, 4, 0, 10],
            [1, 10, 2, 8, 7, 4],
            [4, 9, 1, 4, 1, 7, 7, 1, 3],
            [4, 9, 1, 4, 1, 7, 0, 8, 1, 8, 7, 1],
            [4, 0, 3, 7, 4, 3],
            [4, 8, 7],
            [9, 10, 8, 10, 11, 8],
            [3, 0, 9, 3, 9, 11, 11, 9, 10],
            [0, 1, 10, 0, 10, 8, 8, 10, 11],
            [3, 1, 10, 11, 3, 10],
            [1, 2, 11, 1, 11, 9, 9, 11, 8],
            [3, 0, 9, 3, 9, 11, 1, 2, 9, 2, 11, 9],
            [0, 2, 11, 8, 0, 11],
            [3, 2, 11],
            [2, 3, 8, 2, 8, 10, 10, 8, 9],
            [9, 10, 2, 0, 9, 2],
            [2, 3, 8, 2, 8, 10, 0, 1, 8, 1, 10, 8],
            [1, 10, 2],
            [1, 3, 8, 9, 1, 8],
            [0, 9, 1],
            [0, 3, 8],
            []
        ]    
        edgeShifts = np.array([  ## maps edge ID (0-11) to (x,y,z) cell offset and edge ID (0-2)
            [0, 0, 0, 0],   
            [1, 0, 0, 1],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
            [1, 0, 1, 1],
            [0, 1, 1, 0],
            [0, 0, 1, 1],
            [0, 0, 0, 2],
            [1, 0, 0, 2],
            [1, 1, 0, 2],
            [0, 1, 0, 2],
            #[9, 9, 9, 9]  ## fake
        ], dtype=np.ubyte)
        nTableFaces = np.array([len(f)/3 for f in triTable], dtype=np.ubyte)
        faceShiftTables = [None]
        for i in range(1,6):
            ## compute lookup table of index: vertexes mapping
            faceTableI = np.zeros((len(triTable), i*3), dtype=np.ubyte)
            faceTableInds = np.argwhere(nTableFaces == i)
            faceTableI[faceTableInds[:,0]] = np.array([triTable[j] for j in faceTableInds])
            faceTableI = faceTableI.reshape((len(triTable), i, 3))
            faceShiftTables.append(edgeShifts[faceTableI])
            
        ## Let's try something different:
        #faceTable = np.empty((256, 5, 3, 4), dtype=np.ubyte)   # (grid cell index, faces, vertexes, edge lookup)
        #for i,f in enumerate(triTable):
            #f = np.array(f + [12] * (15-len(f))).reshape(5,3)
            #faceTable[i] = edgeShifts[f]
        
        
        IsosurfaceDataCache = (faceShiftTables, edgeShifts, edgeTable, nTableFaces)
    else:
        faceShiftTables, edgeShifts, edgeTable, nTableFaces = IsosurfaceDataCache


    
    ## mark everything below the isosurface level
    mask = data < level
    
    ### make eight sub-fields and compute indexes for grid cells
    index = np.zeros([x-1 for x in data.shape], dtype=np.ubyte)
    fields = np.empty((2,2,2), dtype=object)
    slices = [slice(0,-1), slice(1,None)]
    for i in [0,1]:
        for j in [0,1]:
            for k in [0,1]:
                fields[i,j,k] = mask[slices[i], slices[j], slices[k]]
                vertIndex = i - 2*j*i + 3*j + 4*k  ## this is just to match Bourk's vertex numbering scheme
                index += fields[i,j,k] * 2**vertIndex
    
    ### Generate table of edges that have been cut
    cutEdges = np.zeros([x+1 for x in index.shape]+[3], dtype=np.uint32)
    edges = edgeTable[index]
    for i, shift in enumerate(edgeShifts[:12]):        
        slices = [slice(shift[j],cutEdges.shape[j]+(shift[j]-1)) for j in range(3)]
        cutEdges[slices[0], slices[1], slices[2], shift[3]] += edges & 2**i
    
    ## for each cut edge, interpolate to see where exactly the edge is cut and generate vertex positions
    m = cutEdges > 0
    vertexInds = np.argwhere(m)   ## argwhere is slow!
    vertexes = vertexInds[:,:3].astype(np.float32)
    dataFlat = data.reshape(data.shape[0]*data.shape[1]*data.shape[2])
    
    ## re-use the cutEdges array as a lookup table for vertex IDs
    cutEdges[vertexInds[:,0], vertexInds[:,1], vertexInds[:,2], vertexInds[:,3]] = np.arange(vertexInds.shape[0])
    
    for i in [0,1,2]:
        vim = vertexInds[:,3] == i
        vi = vertexInds[vim, :3]
        viFlat = (vi * (np.array(data.strides[:3]) // data.itemsize)[np.newaxis,:]).sum(axis=1)
        v1 = dataFlat[viFlat]
        v2 = dataFlat[viFlat + data.strides[i]//data.itemsize]
        vertexes[vim,i] += (level-v1) / (v2-v1)
    
    ### compute the set of vertex indexes for each face. 
    
    ## This works, but runs a bit slower.
    #cells = np.argwhere((index != 0) & (index != 255))  ## all cells with at least one face
    #cellInds = index[cells[:,0], cells[:,1], cells[:,2]]
    #verts = faceTable[cellInds]
    #mask = verts[...,0,0] != 9
    #verts[...,:3] += cells[:,np.newaxis,np.newaxis,:]  ## we now have indexes into cutEdges
    #verts = verts[mask]
    #faces = cutEdges[verts[...,0], verts[...,1], verts[...,2], verts[...,3]]  ## and these are the vertex indexes we want.
    
    
    ## To allow this to be vectorized efficiently, we count the number of faces in each 
    ## grid cell and handle each group of cells with the same number together.
    ## determine how many faces to assign to each grid cell
    nFaces = nTableFaces[index]
    totFaces = nFaces.sum()
    faces = np.empty((totFaces, 3), dtype=np.uint32)
    ptr = 0
    #import debug
    #p = debug.Profiler('isosurface', disabled=False)
    
    ## this helps speed up an indexing operation later on
    cs = np.array(cutEdges.strides)//cutEdges.itemsize
    cutEdges = cutEdges.flatten()

    ## this, strangely, does not seem to help.
    #ins = np.array(index.strides)/index.itemsize
    #index = index.flatten()

    for i in range(1,6):
        ### expensive:
        #p.mark('1')
        cells = np.argwhere(nFaces == i)  ## all cells which require i faces  (argwhere is expensive)
        #p.mark('2')
        if cells.shape[0] == 0:
            continue
        #cellInds = index[(cells*ins[np.newaxis,:]).sum(axis=1)]
        cellInds = index[cells[:,0], cells[:,1], cells[:,2]]   ## index values of cells to process for this round
        #p.mark('3')
        
        ### expensive:
        verts = faceShiftTables[i][cellInds]
        #p.mark('4')
        verts[...,:3] += cells[:,np.newaxis,np.newaxis,:]  ## we now have indexes into cutEdges
        verts = verts.reshape((verts.shape[0]*i,)+verts.shape[2:])
        #p.mark('5')
        
        ### expensive:
        #print verts.shape
        verts = (verts * cs[np.newaxis, np.newaxis, :]).sum(axis=2)
        #vertInds = cutEdges[verts[...,0], verts[...,1], verts[...,2], verts[...,3]]  ## and these are the vertex indexes we want.
        vertInds = cutEdges[verts]
        #p.mark('6')
        nv = vertInds.shape[0]
        #p.mark('7')
        faces[ptr:ptr+nv] = vertInds #.reshape((nv, 3))
        #p.mark('8')
        ptr += nv
        
    return vertexes, faces


    
def invertQTransform(tr):
    """Return a QTransform that is the inverse of *tr*.
    Rasises an exception if tr is not invertible.
    
    Note that this function is preferred over QTransform.inverted() due to
    bugs in that method. (specifically, Qt has floating-point precision issues
    when determining whether a matrix is invertible)
    """
    if not HAVE_SCIPY:
        inv = tr.inverted()
        if inv[1] is False:
            raise Exception("Transform is not invertible.")
        return inv[0]
    arr = np.array([[tr.m11(), tr.m12(), tr.m13()], [tr.m21(), tr.m22(), tr.m23()], [tr.m31(), tr.m32(), tr.m33()]])
    inv = scipy.linalg.inv(arr)
    return QtGui.QTransform(inv[0,0], inv[0,1], inv[0,2], inv[1,0], inv[1,1], inv[1,2], inv[2,0], inv[2,1])
    
    
def pseudoScatter(data, spacing=None, shuffle=True, bidir=False):
    """
    Used for examining the distribution of values in a set. Produces scattering as in beeswarm or column scatter plots.
    
    Given a list of x-values, construct a set of y-values such that an x,y scatter-plot
    will not have overlapping points (it will look similar to a histogram).
    """
    inds = np.arange(len(data))
    if shuffle:
        np.random.shuffle(inds)
        
    data = data[inds]
    
    if spacing is None:
        spacing = 2.*np.std(data)/len(data)**0.5
    s2 = spacing**2
    
    yvals = np.empty(len(data))
    if len(data) == 0:
        return yvals
    yvals[0] = 0
    for i in range(1,len(data)):
        x = data[i]     # current x value to be placed
        x0 = data[:i]   # all x values already placed
        y0 = yvals[:i]  # all y values already placed
        y = 0
        
        dx = (x0-x)**2  # x-distance to each previous point
        xmask = dx < s2  # exclude anything too far away
        
        if xmask.sum() > 0:
            if bidir:
                dirs = [-1, 1]
            else:
                dirs = [1]
            yopts = []
            for direction in dirs:
                y = 0
                dx2 = dx[xmask]
                dy = (s2 - dx2)**0.5   
                limits = np.empty((2,len(dy)))  # ranges of y-values to exclude
                limits[0] = y0[xmask] - dy
                limits[1] = y0[xmask] + dy    
                while True:
                    # ignore anything below this y-value
                    if direction > 0:
                        mask = limits[1] >= y
                    else:
                        mask = limits[0] <= y
                        
                    limits2 = limits[:,mask]
                    
                    # are we inside an excluded region?
                    mask = (limits2[0] < y) & (limits2[1] > y)
                    if mask.sum() == 0:
                        break
                        
                    if direction > 0:
                        y = limits2[:,mask].max()
                    else:
                        y = limits2[:,mask].min()
                yopts.append(y)
            if bidir:
                y = yopts[0] if -yopts[0] < yopts[1] else yopts[1]
            else:
                y = yopts[0]
        yvals[i] = y
    
    return yvals[np.argsort(inds)]  ## un-shuffle values before returning
