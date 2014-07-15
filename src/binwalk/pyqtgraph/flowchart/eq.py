# -*- coding: utf-8 -*-
from numpy import ndarray, bool_
from pyqtgraph.metaarray import MetaArray

def eq(a, b):
    """The great missing equivalence function: Guaranteed evaluation to a single bool value."""
    if a is b:
        return True
        
    try:
        e = a==b
    except ValueError:
        return False
    except AttributeError: 
        return False
    except:
        print("a:", str(type(a)), str(a))
        print("b:", str(type(b)), str(b))
        raise
    t = type(e)
    if t is bool:
        return e
    elif t is bool_:
        return bool(e)
    elif isinstance(e, ndarray) or (hasattr(e, 'implements') and e.implements('MetaArray')):
        try:   ## disaster: if a is an empty array and b is not, then e.all() is True
            if a.shape != b.shape:
                return False
        except:
            return False
        if (hasattr(e, 'implements') and e.implements('MetaArray')):
             return e.asarray().all()
        else:
            return e.all()
    else:
        raise Exception("== operator returned type %s" % str(type(e)))
