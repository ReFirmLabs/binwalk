__all__ = ['scan', 'execute', 'ModuleException']

from binwalk.core.module import Modules, ModuleException

# Convenience functions
def scan(*args, **kwargs):
    with Modules(*args, **kwargs) as m:
        objs = m.execute()
    return objs
def execute(*args, **kwargs):
    return scan(*args, **kwargs)
