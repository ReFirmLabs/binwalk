# Don't load the disasm module if the capstone module can't be found
try:
    from binwalk.modules.disasm import Disasm
except ImportError:
    pass

# Don't load the compression module if the lzma module can't be found
try:
    from binwalk.modules.compression import RawCompression
except ImportError:
    pass

from binwalk.modules.signature import Signature
from binwalk.modules.hexdiff import HexDiff
from binwalk.modules.general import General
from binwalk.modules.extractor import Extractor
from binwalk.modules.entropy import Entropy

# These are depreciated.
#from binwalk.modules.binvis import Plotter
#from binwalk.modules.hashmatch import HashMatch
#from binwalk.modules.heuristics import HeuristicCompressionAnalyzer
