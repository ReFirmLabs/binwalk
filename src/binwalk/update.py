import os
import urllib2
from config import *

class Update:
	'''
	Class for updating binwalk configuration and signatures files from the subversion trunk.

	Example usage:

		from binwalk import Update

		Update().update()
	'''
	BASE_URL = "https://raw.github.com/devttys0/binwalk/master/src/binwalk/"
	MAGIC_PREFIX = "magic/"
	CONFIG_PREFIX = "config/"

	def __init__(self, verbose=False):
		'''
		Class constructor.

		@verbose - Verbose flag.

		Returns None.
		'''
		self.verbose = verbose
		self.config = Config()

	def update(self):
		'''
		Updates all system wide signatures and config files.

		Returns None.
		'''
		self.update_binwalk()
		self.update_bincast()
		self.update_binarch()
		self.update_extract()
		self.update_zlib()
		self.update_compressd()

	def _do_update_from_svn(self, prefix, fname):
		'''
		Updates the specified file to the latest version of that file in SVN.

		@prefix - The URL subdirectory where the file is located.
		@fname  - The name of the file to update.

		Returns None.
		'''
		# Get the local http proxy, if any
		# csoban.kesmarki
		proxy_url = os.getenv('HTTP_PROXY')
		if proxy_url:
			proxy_support = urllib2.ProxyHandler({'http' : proxy_url})
			opener = urllib2.build_opener(proxy_support)
			urllib2.install_opener(opener)

		url = self.BASE_URL + prefix + fname
		
		try:
			if self.verbose:
				print "Fetching %s..." % url
			
			data = urllib2.urlopen(url).read()
			open(self.config.paths['system'][fname], "wb").write(data)
		except Exception, e:
			raise Exception("Update._do_update_from_svn failed to update file '%s': %s" % (url, str(e)))

	def update_binwalk(self):
		'''
		Updates the binwalk signature file.

		Returns None.
		'''
		self._do_update_from_svn(self.MAGIC_PREFIX, self.config.BINWALK_MAGIC_FILE)
	
	def update_bincast(self):
		'''
		Updates the bincast signature file.

		Returns None.
		'''
		self._do_update_from_svn(self.MAGIC_PREFIX, self.config.BINCAST_MAGIC_FILE)
	
	def update_binarch(self):
		'''
		Updates the binarch signature file.
	
		Returns None.
		'''
		self._do_update_from_svn(self.MAGIC_PREFIX, self.config.BINARCH_MAGIC_FILE)
	
	def update_zlib(self):
		'''
		Updates the zlib signature file.

		Returns None.
		'''
		self._do_update_from_svn(self.MAGIC_PREFIX, self.config.ZLIB_MAGIC_FILE)

	def update_compressd(self):
		'''
		Updates the compress'd signature file.
		
		Returns None.
		'''
		self._do_update_from_svn(self.MAGIC_PREFIX, self.config.COMPRESSD_MAGIC_FILE)

	def update_extract(self):
		'''
		Updates the extract.conf file.
	
		Returns None.
		'''
		self._do_update_from_svn(self.CONFIG_PREFIX, self.config.EXTRACT_FILE)


