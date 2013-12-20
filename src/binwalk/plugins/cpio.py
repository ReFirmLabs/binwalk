class Plugin(object):
	'''
	Ensures that ASCII CPIO archive entries only get extracted once.	
	'''

	def __init__(self, module):
		self.found_archive = False
		self.enabled = (module.name == 'Signature')
		
	def pre_scan(self, module):
		# Be sure to re-set this at the beginning of every scan
		self.found_archive = False

	def scan(self, result):
		if self.enabled and result.valid:
			# ASCII CPIO archives consist of multiple entries, ending with an entry named 'TRAILER!!!'.
			# Displaying each entry is useful, as it shows what files are contained in the archive,
			# but we only want to extract the archive when the first entry is found.
			if result.description.startswith('ASCII cpio archive'):
				if not self.found_archive:
					# This is the first entry. Set found_archive and allow the scan to continue normally.
					self.found_archive = True
					result.extract = True
				elif 'TRAILER!!!' in results['description']:
					# This is the last entry, un-set found_archive.
					self.found_archive = False
	
				# The first entry has already been found and this is the last entry, or the last entry 
				# has not yet been found. Don't extract.
				result.extract = False
