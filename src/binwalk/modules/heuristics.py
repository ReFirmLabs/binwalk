# Routines to perform Chi Squared tests. 
# Used for fingerprinting unknown areas of high entropy (e.g., is this block of high entropy data compressed or encrypted?).
# Inspired by people who actually know what they're doing: http://www.fourmilab.ch/random/

import math
from binwalk.core.compat import *
from binwalk.core.module import Module, Kwarg, Option, Dependency

class ChiSquare(object):
    '''
    Performs a Chi Squared test against the provided data.
    '''

    IDEAL = 256.0

    def __init__(self):
        '''
        Class constructor.

        Returns None.
        '''
        self.bytes = {}
        self.freedom = self.IDEAL - 1 
        
        # Initialize the self.bytes dictionary with keys for all possible byte values (0 - 255)
        for i in range(0, int(self.IDEAL)):
            self.bytes[chr(i)] = 0
        
        self.reset()

    def reset(self):
        self.xc2 = 0.0
        self.byte_count = 0

        for key in self.bytes.keys():
            self.bytes[key] = 0        

    def update(self, data):
        '''
        Updates the current byte counts with new data.

        @data - String of bytes to update.

        Returns None.
        '''
        # Count the number of occurances of each byte value
        for i in data:
            self.bytes[i] += 1

        self.byte_count += len(data)

    def chisq(self):
        '''
        Calculate the Chi Square critical value.

        Returns the critical value.
        '''
        expected = self.byte_count / self.IDEAL

        if expected:
            for byte in self.bytes.values():
                self.xc2 += ((byte - expected) ** 2 ) / expected

        return self.xc2

class EntropyBlock(object):

    def __init__(self, **kwargs):
        self.start = None
        self.end = None
        self.length = None
        for (k,v) in iterator(kwargs):
            setattr(self, k, v)

class HeuristicCompressionAnalyzer(Module):
    '''
    Performs analysis and attempts to interpret the results.
    '''

    BLOCK_SIZE = 32
    CHI_CUTOFF = 512
    ENTROPY_TRIGGER = .90
    MIN_BLOCK_SIZE = 4096
    BLOCK_OFFSET = 1024
    ENTROPY_BLOCK_SIZE = 1024

    TITLE = "Heuristic Compression"

    DEPENDS = [
            Dependency(name='Entropy',
                       attribute='entropy',
                       kwargs={'enabled' : True, 'do_plot' : False, 'display_results' : False, 'block_size' : ENTROPY_BLOCK_SIZE}),
    ]
    
    CLI = [
            Option(short='H',
                   long='heuristic',
                   kwargs={'enabled' : True},
                   description='Heuristically classify high entropy data'),
            Option(short='a',
                   long='trigger',
                   kwargs={'trigger_level' : 0},
                   type=float,
                   description='Set the entropy trigger level (0.0 - 1.0, default: %.2f)' % ENTROPY_TRIGGER),
    ]

    KWARGS = [
            Kwarg(name='enabled', default=False),
            Kwarg(name='trigger_level', default=ENTROPY_TRIGGER),
    ]

    def init(self):
        self.blocks = {}

        self.HEADER[-1] = "HEURISTIC ENTROPY ANALYSIS"

        # Trigger level sanity check
        if self.trigger_level > 1.0:
            self.trigger_level = 1.0
        elif self.trigger_level < 0.0:
            self.trigger_level = 0.0

        if self.config.block:
            self.block_size = self.config.block
        else:
            self.block_size = self.BLOCK_SIZE

        for result in self.entropy.results:
            if not has_key(self.blocks, result.file.name):
                self.blocks[result.file.name] = []

            if result.entropy >= self.trigger_level and (not self.blocks[result.file.name] or self.blocks[result.file.name][-1].end is not None):
                self.blocks[result.file.name].append(EntropyBlock(start=result.offset + self.BLOCK_OFFSET))
            elif result.entropy < self.trigger_level and self.blocks[result.file.name] and self.blocks[result.file.name][-1].end is None:
                self.blocks[result.file.name][-1].end = result.offset - self.BLOCK_OFFSET

    def run(self):
        for fp in iter(self.next_file, None):
            
            if has_key(self.blocks, fp.name):

                self.header()
                
                for block in self.blocks[fp.name]:

                    if block.end is None:
                        block.length = fp.offset + fp.length - block.start
                    else:
                        block.length = block.end - block.start

                    if block.length >= self.MIN_BLOCK_SIZE:
                        self.analyze(fp, block)

                self.footer()

    def analyze(self, fp, block):
        '''
        Perform analysis and interpretation.
        '''
        i = 0
        num_error = 0
        analyzer_results = []

        chi = ChiSquare()
        fp.seek(block.start)

        while i < block.length:
            j = 0
            (d, dlen) = fp.read_block()
            if not d:
                break

            while j < dlen:
                chi.reset()

                data = d[j:j+self.block_size]
                if len(data) < self.block_size:
                    break

                chi.update(data)

                if chi.chisq() >= self.CHI_CUTOFF:
                    num_error += 1
                
                j += self.block_size

                if (j + i) > block.length:
                    break

            i += dlen

        if num_error > 0:
            verdict = 'Moderate entropy data, best guess: compressed'
        else:
            verdict = 'High entropy data, best guess: encrypted'

        desc = '%s, size: %d, %d low entropy blocks' % (verdict, block.length, num_error)
        self.result(offset=block.start, description=desc, file=fp)
