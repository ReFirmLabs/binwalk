try:
    import numpy as np
    
    ## Wrap np.concatenate to catch and avoid a segmentation fault bug
    ## (numpy trac issue #2084)
    if not hasattr(np, 'concatenate_orig'):
        np.concatenate_orig = np.concatenate
    def concatenate(vals, *args, **kwds):
        """Wrapper around numpy.concatenate (see pyqtgraph/numpy_fix.py)"""
        dtypes = [getattr(v, 'dtype', None) for v in vals]
        names = [getattr(dt, 'names', None) for dt in dtypes]
        if len(dtypes) < 2 or all([n is None for n in names]):
            return np.concatenate_orig(vals, *args, **kwds)
        if any([dt != dtypes[0] for dt in dtypes[1:]]):
            raise TypeError("Cannot concatenate structured arrays of different dtype.")
        return np.concatenate_orig(vals, *args, **kwds)
    
    np.concatenate = concatenate
    
except ImportError:
    pass

