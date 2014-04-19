# -*- coding: utf-8 -*-
from ..Node import Node

class UniOpNode(Node):
    """Generic node for performing any operation like Out = In.fn()"""
    def __init__(self, name, fn):
        self.fn = fn
        Node.__init__(self, name, terminals={
            'In': {'io': 'in'},
            'Out': {'io': 'out', 'bypass': 'In'}
        })
        
    def process(self, **args):
        return {'Out': getattr(args['In'], self.fn)()}

class BinOpNode(Node):
    """Generic node for performing any operation like A.fn(B)"""
    def __init__(self, name, fn):
        self.fn = fn
        Node.__init__(self, name, terminals={
            'A': {'io': 'in'},
            'B': {'io': 'in'},
            'Out': {'io': 'out', 'bypass': 'A'}
        })
        
    def process(self, **args):
        if isinstance(self.fn, tuple):
            for name in self.fn:
                try:
                    fn = getattr(args['A'], name)
                    break
                except AttributeError:
                    pass
        else:
            fn = getattr(args['A'], self.fn)
        out = fn(args['B'])
        if out is NotImplemented:
            raise Exception("Operation %s not implemented between %s and %s" % (fn, str(type(args['A'])), str(type(args['B']))))
        #print "     ", fn, out
        return {'Out': out}


class AbsNode(UniOpNode):
    """Returns abs(Inp). Does not check input types."""
    nodeName = 'Abs'
    def __init__(self, name):
        UniOpNode.__init__(self, name, '__abs__')

class AddNode(BinOpNode):
    """Returns A + B. Does not check input types."""
    nodeName = 'Add'
    def __init__(self, name):
        BinOpNode.__init__(self, name, '__add__')

class SubtractNode(BinOpNode):
    """Returns A - B. Does not check input types."""
    nodeName = 'Subtract'
    def __init__(self, name):
        BinOpNode.__init__(self, name, '__sub__')

class MultiplyNode(BinOpNode):
    """Returns A * B. Does not check input types."""
    nodeName = 'Multiply'
    def __init__(self, name):
        BinOpNode.__init__(self, name, '__mul__')

class DivideNode(BinOpNode):
    """Returns A / B. Does not check input types."""
    nodeName = 'Divide'
    def __init__(self, name):
        # try truediv first, followed by div
        BinOpNode.__init__(self, name, ('__truediv__', '__div__'))
        

