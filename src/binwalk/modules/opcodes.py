import sys
import inspect
import binwalk.core.common
from binwalk.core.compat import *
from binwalk.core.module import Module, Option, Kwarg

class Operand(object):

	def __init__(self, **kwargs):
		self.valid = False
		self.value = None
		self.mnem = None

		for (k, v) in iterator(kwargs):
			setattr(self, k, v)

class Instruction(object):

	BIG = 'big'
	LITTLE = 'little'

	def __init__(self, **kwargs):
		self.valid = False
		self.opcode = None
		self.mnem = None
		self.endianess = None
		self.operands = []
		self.size = 0

		for (k, v) in iterator(kwargs):
			setattr(self, k, v)

class Disassembler(object):

	INSTRUCTION_SIZE = 4
	OPCODE_INDEX = 0
	OPCODE_MASK = 0
	ENDIANESS = Instruction.BIG

	def __init__(self):
		self.confidence = 0.0

	def pre_processor(self, data):
		d = ''

		if self.ENDIANESS == Instruction.LITTLE:
			d = data[::-1]
		else:
			d = data

		return d

	def validate(self, instruction):
		return None

	def disassemble_opcode(self, ins, data):
		ins.opcode = ord(data[self.OPCODE_INDEX]) & self.OPCODE_MASK
		if ins.opcode in self.OPCODES:
			ins.valid = True
		else:
			ins.valid = False

	def disassemble(self, data):
		data = self.pre_processor(data)
		ins = Instruction(size=self.INSTRUCTION_SIZE, endianess=self.ENDIANESS)
		self.disassemble_opcode(ins, data)
		self.validate(ins)
		return ins

class MIPS(Disassembler):

	OPCODE_MASK = (0x3F << 2)
	OPCODES = [
		0x04 << 2, # beq
		0x05 << 2, # bne
		0x09 << 2, # addiu
		0x08 << 2, # addi
		0x0D << 2, # ori
		0x23 << 2, # lw
		0x2B << 2, # sw
		0x0F << 2, # lui
	]

class MIPSEL(MIPS):

	ENDIANESS = Instruction.LITTLE

class ARMEB(Disassembler):

	OPCODE_MASK = 0xF0
	OPCODES = [0xE0]

class ARM(ARMEB):
	
	ENDIANESS = Instruction.LITTLE

class OpcodeValidator(Module):

	MIN_INS_COUNT = 6
	MIN_CONFIDENCE = 0.0

	TITLE = 'Opcode'

	CLI = [
			Option(short='A',
				   long='opcodes',
				   kwargs={'enabled' : True},
				   description='Scan files for executable opcodes'),
			Option(short='a',
				   long='unaligned',
				   kwargs={'honor_instruction_alignment' : False},
				   description='Scan for opcodes at unaligned offsets'),
	]

	KWARGS = [
			Kwarg(name='enabled', default=False),
			Kwarg(name='honor_instruction_alignment', default=True),
	]

	def init(self):
		self.disassemblers = {}

		for (name, cls) in inspect.getmembers(sys.modules[__name__], inspect.isclass):
			try:
				obj = cls()
				if isinstance(obj, Disassembler) and name != 'Disassembler':
					self.disassemblers[obj] = 0
			except TypeError:
				pass

		if self.config.verbose:
			self.HEADER[-1] = 'EXECUTABLE CODE'
		else:
			self.HEADER = ['CONFIDENCE', 'FILE ARCHITECTURE']
			self.HEADER_FORMAT = '%s      %s'
			self.RESULT = ['confidence', 'description']
			self.RESULT_FORMAT = '%-7.2f         %s'

	def run(self):
		for fp in self.config.target_files:
			
			self.header()

			for disassembler in self.search(fp):
				if not self.config.verbose and disassembler.confidence > self.MIN_CONFIDENCE:
					desc = disassembler.__class__.__name__ + " executable code, endianess: " + disassembler.ENDIANESS
					self.result(description=desc, confidence=disassembler.confidence, file=fp, plot=False)
			
			self.footer()

	def is_valid_sequence(self, disassembler, data):
		j = 0
		retval = True

		# Ignore blocks of NULL bytes
		if data == "\x00" * len(data):
			return False

		while j < len(data):
			ins = disassembler.disassemble(data[j:j+disassembler.INSTRUCTION_SIZE])
			if not ins.valid:
				retval = False
				break
			else:
				j += disassembler.INSTRUCTION_SIZE

		return retval

	def search(self, fp):
		while True:
			i = 0
			(data, dlen) = fp.read_block()
			if not data:
				break

			while i < dlen:
				count = 1

				for disassembler in get_keys(self.disassemblers):
					if self.honor_instruction_alignment and (i % disassembler.INSTRUCTION_SIZE):
						continue

					ins = disassembler.disassemble(data[i:i+disassembler.INSTRUCTION_SIZE])
					if ins.valid:
						sequence_size = self.MIN_INS_COUNT * disassembler.INSTRUCTION_SIZE
						sequence = data[i:i+sequence_size]

						if len(sequence) == sequence_size and self.is_valid_sequence(disassembler, sequence):
							self.result(description=disassembler.__class__.__name__ + " instructions, endianess: " + disassembler.ENDIANESS,
										offset=(fp.total_read - dlen + i),
										file=fp,
										display=self.config.verbose)

							self.disassemblers[disassembler] += 1
							count = disassembler.INSTRUCTION_SIZE * self.MIN_INS_COUNT
							break
				i += count

		total_hits = 0

		for (k, v) in iterator(self.disassemblers):
			total_hits += v

		for (k, v) in iterator(self.disassemblers):
			k.confidence = ((v / float(total_hits)) * 100)

		return sorted(self.disassemblers, key=self.disassemblers.get, reverse=True)

