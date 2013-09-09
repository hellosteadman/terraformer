#!/usr/bin/env python

HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
RESET = '\033[m\n'

from optparse import OptionParser
from shutil import rmtree
from subprocess import call
from datetime import datetime
import os, sys, simplejson

class TerraException(Exception):
	pass

class TerraContext(object):
	def __init__(self, template):
		filename = os.path.join(
			os.path.abspath(os.path.dirname(__file__)),
			'conf', '%s.json' % template
		)
		
		self.valid = True
		if os.path.exists(filename):
			try:
				self._config = simplejson.loads(
					open(filename, 'r').read()
				)
			except simplejson.decoder.JSONDecodeError, ex:
				self.error('Skeleton config file contains invalid JSON (%s)' % ex)
				self.valid = False
		else:
			self.warn('Config file for skeleton not found')
			self._config = {}
		
		if not os.path.exists(
			os.path.join(
				os.path.dirname(__file__),
				'logs'
			)
		):
			os.mkdir(
				os.path.join(
					os.path.dirname(__file__),
					'logs'
				)
			)
		
		if not os.path.exists(
			os.path.join(
				os.path.dirname(__file__),
				'logs', template
			)
		):
			os.mkdir(
				os.path.join(
					os.path.dirname(__file__),
					'logs', template
				)
			)
		
		self._dirs = []
		self._files = []
		self._plugins = {}
		self._logfile = open(
			os.path.join(
				os.path.dirname(__file__),
				'logs',
				template,
				datetime.now().strftime('%b-%d-%y_%H%M') + '.log'
			),
			'w'
		)
	
	def log(self, event, *text):
		if any(text):
			self._logfile.write(
				'\t'.join(
					(
						datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
						event,
						' '.join([t for t in text if t])
					)
				)
			)
			
			self._logfile.write('\n')
	
	def header(self, *text):
		if any(text):
			sys.stdout.write(HEADER + ' '.join(t for t in text if t) + RESET)
			self.log('INFO', *text)
	
	def info(self, *text):
		if any(text):
			sys.stdout.write(OKBLUE + ' '.join(t for t in text if t) + RESET)
			self.log('INFO', *text)
	
	def success(self, *text):
		if any(text):
			sys.stdout.write(OKGREEN + ' '.join(t for t in text if t) + RESET)
			self.log('SUCCESS', *text)
	
	def warn(self, *text):
		if any(text):
			sys.stdout.write(WARNING + ' '.join(t for t in text if t) + RESET)
			self.log('WARN', *text)
	
	def error(self, *text):
		if any(text):
			sys.stdout.write(FAIL + ' '.join(t for t in text if t) + RESET)
			self.log('ERROR', *text)
	
	def ask(self, question, required = True, default = None):
		retrying = False
		
		while True:
			if retrying:
				prompt = 'An answer is required. %s: ' % question
			elif default:
				prompt = question + ' (defaults to %s): ' % default
			else:
				prompt = question + (not required and ' (optional)' or '') + ': '
			
			answer = raw_input(prompt)
			if answer:
				return answer
			
			if not required:
				return None
			
			if default:
				return default
			
			retrying = True
	
	def config(self, key, default = None):
		return self._config.get(key, default)
	
	def mkdir(self, dirname):
		if not dirname:
			return None
		
		creating = not os.path.exists(dirname)
		if not creating:
			self.warn('Directory', dirname, 'already exists.')
			return dirname
		
		try:
			os.mkdir(dirname)
			self._dirs.append(os.path.abspath(dirname))
		except Exception, ex:
			self.error('Unable to create directory %s: %s.' % (dirname, ex))
			return None
		else:
			self.success('Created directory %s.' % dirname)
			return dirname
	
	def save(self, filename, data):
		exists = os.path.exists(filename)
		open(filename, 'wb').write(data)
		
		if not exists:
			self._files.append(os.path.abspath(filename))
			self.success('Created file %s.' % filename)
		else:
			self.warn('Overwrote file %s.' % filename)
	
	def sh(self, *args):
		try:
			call(args)
			return True
		except:
			self.error('Error calling shell command %s' % ' '.join(args))
		
		return False
	
	def plugin(self, name, **kwargs):
		if not name in self._plugins:
			try:
				module = __import__('plugins.%s' % name)
			except ImportError:
				raise TerraException('Plugin with name "%s" not found' % name)
			else:
				klass = getattr(getattr(module, name), 'Plugin')
				self._plugins[name] = klass(self, **kwargs)
		
		return self._plugins[name]
	
	def cleanup(self, success = True):
		if not success:
			while any(self._files):
				os.remove(
					self._files.pop()
				)
		
			while any(self._dirs):
				rmtree(
					self._dirs.pop()
				)
		
		for plugin in self._plugins.values():
			if hasattr(plugin, 'cleanup'):
				plugin.cleanup(success)

parser = OptionParser()
(options, args) = parser.parse_args()

if any(args):
	try:
		skeleton = args.pop(0)
		context = TerraContext(skeleton)
		
		if context.valid:
			try:
				module = __import__('skeletons.%s' % skeleton)
			except ImportError:
				raise TerraException('Skeleton with name "%s" not found' % skeleton)
			else:
				try:
					skeleton = getattr(module, skeleton).Skeleton()
					if not skeleton.go(context):
						context.cleanup(False)
					else:
						context.cleanup(True)
				except:
					context.cleanup(False)
					raise
	
	except TerraException, ex:
		sys.stderr.write(FAIL + str(ex) + RESET)
else:
	sys.stderr.write(FAIL + 'Specify a site skeleton' + RESET)