__all__ = ['scan', 'execute', 'Modules', 'ModuleException']

from binwalk.core.module import Modules, ModuleException

# Convenience functions
def scan(*args, **kwargs):
    return Modules(*args, **kwargs).execute()
def execute(*args, **kwargs):
    return Modules(*args, **kwargs).execute()
