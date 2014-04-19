

class PlotData(object):
    """
    Class used for managing plot data
      - allows data sharing between multiple graphics items (curve, scatter, graph..)
      - each item may define the columns it needs
      - column groupings ('pos' or x, y, z)
      - efficiently appendable 
      - log, fft transformations
      - color mode conversion (float/byte/qcolor)
      - pen/brush conversion
      - per-field cached masking
        - allows multiple masking fields (different graphics need to mask on different criteria) 
        - removal of nan/inf values
      - option for single value shared by entire column
      - cached downsampling
      - cached min / max / hasnan / isuniform
    """
    def __init__(self):
        self.fields = {}
        
        self.maxVals = {}  ## cache for max/min
        self.minVals = {}

    def addFields(self, **fields):
        for f in fields:
            if f not in self.fields:
                self.fields[f] = None

    def hasField(self, f):
        return f in self.fields

    def __getitem__(self, field):
        return self.fields[field]
    
    def __setitem__(self, field, val):
        self.fields[field] = val
    
    def max(self, field):
        mx = self.maxVals.get(field, None)
        if mx is None:
            mx = np.max(self[field])
            self.maxVals[field] = mx
        return mx
    
    def min(self, field):
        mn = self.minVals.get(field, None)
        if mn is None:
            mn = np.min(self[field])
            self.minVals[field] = mn
        return mn
    
    
    
    