"""For starting up remote processes"""
import sys, pickle, os

if __name__ == '__main__':
    if hasattr(os, 'setpgrp'):
        os.setpgrp()  ## prevents signals (notably keyboard interrupt) being forwarded from parent to this process
    if sys.version[0] == '3':
        #name, port, authkey, ppid, targetStr, path, pyside = pickle.load(sys.stdin.buffer)
        opts = pickle.load(sys.stdin.buffer)
    else:
        #name, port, authkey, ppid, targetStr, path, pyside = pickle.load(sys.stdin)
        opts = pickle.load(sys.stdin)
    #print "key:",  ' '.join([str(ord(x)) for x in authkey])
    path = opts.pop('path', None)
    if path is not None:
        ## rewrite sys.path without assigning a new object--no idea who already has a reference to the existing list.
        while len(sys.path) > 0:
            sys.path.pop()
        sys.path.extend(path)
        
    if opts.pop('pyside', False):
        import PySide
        
    
    targetStr = opts.pop('targetStr')
    target = pickle.loads(targetStr)  ## unpickling the target should import everything we need
    target(**opts)  ## Send all other options to the target function
    sys.exit(0)
