from os import path, write, close
from tempfile import mkstemp
import requests

class DownloadableMixin(object):
	def download(self, context, url):
		request = requests.get(url)
		handle, filename = mkstemp(path.splitext(url)[-1])
		
		for block in request.iter_content(1024):
			write(handle, block)
		
		close(handle)
		return filename