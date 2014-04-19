"""
Helper functions which smooth out the differences between python 2 and 3.
"""
import sys

def asUnicode(x):
    if sys.version_info[0] == 2:
        if isinstance(x, unicode):
            return x
        elif isinstance(x, str):
            return x.decode('UTF-8')
        else:
            return unicode(x)
    else:
        return str(x)
        
def cmpToKey(mycmp):
    'Convert a cmp= function into a key= function'
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K

def sortList(l, cmpFunc):
    if sys.version_info[0] == 2:
        l.sort(cmpFunc)
    else:
        l.sort(key=cmpToKey(cmpFunc))

if sys.version_info[0] == 3:
    import builtins
    builtins.basestring = str
    #builtins.asUnicode = asUnicode
    #builtins.sortList = sortList
    basestring = str
    def cmp(a,b):
        if a>b:
            return 1
        elif b > a:
            return -1
        else:
            return 0
    builtins.cmp = cmp
    builtins.xrange = range
#else:    ## don't use __builtin__  -- this confuses things like pyshell and ActiveState's lazy import recipe
    #import __builtin__
    #__builtin__.asUnicode = asUnicode
    #__builtin__.sortList = sortList
