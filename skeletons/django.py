from os import path, remove, sys, environ
from zipfile import ZipFile
from mixins import DatabaseMixin, DomainMixin, PasswordMixin, TopAndTailMixin
import string, random, simplejson

APACHE = """<VirtualHost *:80>
	ServerName %(domain)s
	ServerAlias %(alias)s
	DocumentRoot %(root)s
	ErrorLog %(logs)s/error.log
	TransferLog %(logs)s/access.log
	
	WSGIDaemonProcess %(prefix)s processes=5 threads=25
	WSGIProcessGroup %(prefix)s
	WSGIScriptAlias / %(root)s/%(prefix)s.wsgi
	WSGIPassAuthorization On
	
	Alias /media %(root)s/media
	Alias /static %(root)s/static
</VirtualHost>"""

class Skeleton(DatabaseMixin, DomainMixin, PasswordMixin, TopAndTailMixin):
	def go(self, context):
		self.prerun(context)
		
		domain, prefix, alias = self.get_domain_and_alias(context)
		if not domain and not alias:
			return
		
		password = self.generate_password(context)
		admin_name = context.config('admin_name')
		admin_email = context.config('admin_email')
		apachedir = context.config('apachedir', '/etc/apache2/sites-enabled')
		
		installed_apps = context.config('installed_apps',
			(
				'django.contrib.auth',
				'django.contrib.contenttypes',
				'django.contrib.sessions',
				'django.contrib.sites',
				'django.contrib.messages',
				'django.contrib.staticfiles',
				'django.contrib.admin',
				'django.contrib.admindocs',
				'django.contrib.humanize',
				'django.contrib.markup',
				'south'
			)
		)
		
		dirname = context.mkdir(
			path.join(context.config('basedir'), domain)
		)
		
		if not dirname:
			return
		
		logs = context.mkdir(
			path.join(dirname, 'logs')
		)
		
		filename = path.dirname(__file__) + '/../fixtures/django.zip'
		archive = ZipFile(filename, 'r')
		
		for infile in archive.namelist():
			if infile == 'app.wsgi':
				context.save(
					path.join(dirname, '%s.wsgi' % prefix),
					archive.read(infile) % {
						'prefix': prefix
					}
				)
			elif infile == 'app/':
				dest = path.join(dirname, prefix)
				if not context.mkdir(dest):
					context.error('The Zip extraction couldn\'t be completed')
					return
			else:
				if infile.startswith('app/'):
					dest = path.join(dirname, prefix, infile[4:])
				else:
					dest = path.join(dirname, infile)
				
				if infile.endswith('/'):
					if not context.mkdir(dest):
						context.error('The Zip extraction couldn\'t be completed')
						return
				else:
					context.save(dest,
						archive.read(infile) % {
							'prefix': prefix,
							'admin_name': admin_name,
							'admin_email': admin_email,
							'password': password,
							'key': ''.join(
								random.sample(
									[
										c for c in string.printable if not c in string.whitespace and not c in ('"', "'")
									],
									62
								)
							),
							'installed_apps': simplejson.dumps(installed_apps),
							'dbengine': 'mysql'
						}
					)
		
		self.create_database(context, prefix, password)
		apache = path.join(apachedir, domain)
		context.save(apache,
			APACHE % {
				'domain': domain,
				'alias': alias,
				'prefix': prefix,
				'root': dirname,
				'logs': logs
			}
		)
		
		context.sh('python', path.join(dirname, 'manage.py'), 'syncdb')
		context.sh('python', path.join(dirname, 'manage.py'), 'migrate')
		context.sh('python', path.join(dirname, 'manage.py'), 'collectstatic')
		
		self.postrun(context)
		return True