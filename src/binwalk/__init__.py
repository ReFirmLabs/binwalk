__all__ = ['execute', 'Modules', 'ModuleException']

import sys
import binwalk.core.common

# This allows importing of the built-in pyqtgraph if it
# is not available on the system at run time.
sys.path.append(binwalk.core.common.get_libs_path())

from binwalk.core.module import Modules, ModuleException

def execute(*args, **kwargs):
    return Modules(*args, **kwargs).execute()
