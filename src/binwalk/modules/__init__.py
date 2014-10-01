from binwalk.modules.signature import Signature
#from binwalk.modules.binvis import Plotter
from binwalk.modules.hexdiff import HexDiff
#from binwalk.modules.hashmatch import HashMatch
from binwalk.modules.general import General
from binwalk.modules.extractor import Extractor
from binwalk.modules.entropy import Entropy
from binwalk.modules.heuristics import HeuristicCompressionAnalyzer
from binwalk.modules.compression import RawCompression
try:
    from binwalk.modules.disasm import Disasm
except ImportError:
    pass
