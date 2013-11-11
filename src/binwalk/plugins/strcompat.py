
class Plugin:
	'''
	Modifies string analysis output to mimic that of the Unix strings utility.
	'''

	ENABLED = False

	def __init__(self, binwalk):
		self.modify_output = False

		if binwalk.scan_type == binwalk.STRINGS:
			binwalk.display.quiet = True
			self.modify_output = True

	def callback(self, results):
		if self.modify_output:
			try:
				print results['description']
			except Exception, e:
				pass
