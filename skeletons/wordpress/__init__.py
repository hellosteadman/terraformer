from os import path, write, close, remove
from zipfile import ZipFile
from tempfile import mkstemp
import requests, string, random

HTACCESS = """# BEGIN WordPress
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteBase /
RewriteRule ^index\.php$ - [L]
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.php [L]
</IfModule>
# END WordPress"""

APACHE = """<VirtualHost *:80>
	ServerName %(domain)s
	ServerAlias %(alias)s
	DocumentRoot %(htdocs)s
	ErrorLog %(logs)s/error.log
	TransferLog %(logs)s/access.log
</VirtualHost>"""

class Skeleton(object):
	def go(self, context):
		domain = context.ask('Domain name')
		if not '.' in domain:
			context.error('Domain name', domain, 'doesn\'t seem to be valid.')
			return
	
		suffix = context.config('suffix', '.com')
		prefix = '.'.join(domain.split('.')[:-1])
		alias = prefix + suffix
		alias = context.ask('Domain name alias', default = alias)
		password = context.ask('Password for database', required = False)
		apachebin = context.config('apachebin', '/etc/init.d/apache2')
		apachedir = context.config('apachedir', '/etc/apache2/sites-enabled')
		dbuser = context.config('dbuser', 'root')
		dbpass = context.config('dbpass', '')
	
		if not password:
			password = ''.join(
				random.sample(string.letters + string.digits, 16)
			)
		
			context.info('Password automatically generated:', password)
	
		dirname = context.mkdir(
			path.join(context.config('basedir'), domain)
		)
	
		if not dirname:
			return
	
		htdocs = context.mkdir(
			path.join(dirname, 'htdocs')
		)
	
		logs = context.mkdir(
			path.join(dirname, 'logs')
		)
	
		answer = None
		for row in context.plugin('mysql').query('SHOW DATABASES LIKE \'%s\'' % prefix, dbuser, dbpass):
			while True:
				answer = context.ask(
					'This database already exists. ' \
					'Type "drop" to drop the database, "cancel" to cancel the process or "continue" carry on',
					default = 'continue'
				)
			
				if not answer in ('drop', 'cancel', 'continue'):
					context.error('That\'s not a valid option.')
				else:
					break
		
			if answer == 'drop':
				context.plugin('mysql').execute('DROP DATABASE `%s`' % prefix, dbuser, dbpass)
			elif answer == 'cancel':
				return False
		
			break
	
		if answer != 'continue':
			context.plugin('mysql').execute('CREATE DATABASE `%s`' % prefix, dbuser, dbpass)
	
		answer = None
		for row in context.plugin('mysql').query('SELECT User, Host from mysql.user WHERE Host = \'localhost\' AND User = \'%s\'' % prefix, dbuser, dbpass):
			while True:
				answer = context.ask(
					'This user already exists. ' \
					'Type "drop" to drop the user, "cancel" to cancel the process or "continue" carry on',
					default = 'continue'
				)
			
				if not answer in ('drop', 'cancel', 'continue'):
					context.error('That\'s not a valid option.')
				else:
					break
		
			if answer == 'drop':
				context.plugin('mysql').execute('DROP USER \'%s\'@\'localhost\'' % prefix, dbuser, dbpass)
			elif answer == 'cancel':
				return False
		
			break
	
		if answer != 'continue':
			context.plugin('mysql').execute(
				'CREATE USER \'%s\'@\'localhost\' IDENTIFIED BY \'%s\'' % (prefix, password),
				dbuser, dbpass
			)
	
		context.plugin('mysql').execute(
			'GRANT ALL PRIVILEGES ON `%(prefix)s`.* TO \'%(prefix)s\'@\'localhost\'' % {
				'prefix': prefix
			}, dbuser, dbpass
		)
	
		context.info('Downloading latest copy of WordPress...')
		request = requests.get('http://wordpress.org/latest.zip', stream = True)
		handle, filename = mkstemp('.zip')
	
		for block in request.iter_content(1024):
			write(handle, block)
	
		close(handle)
	
		context.info('Extracting archive to %s...' % htdocs)
		archive = ZipFile(filename, 'r')
		for infile in archive.namelist():
			if infile == 'wordpress/wp-config-sample.php':
				context.save(
					path.join(htdocs, 'wp-config.php'),
					archive.read(infile).replace(
						'database_name_here', prefix
					).replace(
						'username_here', prefix
					).replace(
						'password_here', password
					)
				)
			elif infile.startswith('wordpress/') and infile != 'wordpress/':
				dest = path.join(htdocs, infile[10:])
			
				if infile.endswith('/'):
					if not context.mkdir(dest):
						context.error('The Zip extraction couldn\'t be completed')
						return
				else:
					context.save(dest, archive.read(infile))
	
		context.save(path.join(htdocs, '.htaccess'), HTACCESS)
		remove(filename)
	
		apache = path.join(apachedir, domain)
		context.save(apache,
			APACHE % {
				'domain': domain,
				'alias': alias,
				'htdocs': htdocs,
				'logs': logs
			}
		)
	
		context.sh(apachebin, 'reload')
		return True