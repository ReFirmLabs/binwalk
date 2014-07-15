import sys
import binwalk.core.common

# This is so the built-in pyqtgraph can find itself
sys.path.append(binwalk.core.common.get_module_path())

from binwalk.core.module import Modules, ModuleException
