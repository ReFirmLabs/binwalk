__all__ = ['scan', 'execute', 'Modules', 'ModuleException']

import sys
import binwalk.core.common

from binwalk.core.module import Modules, ModuleException

# Convenience functions
def scan(*args, **kwargs):
    return Modules(*args, **kwargs).execute()
def execute(*args, **kwargs):
    return Modules(*args, **kwargs).execute()
