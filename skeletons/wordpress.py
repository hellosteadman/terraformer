from os import path, remove
from zipfile import ZipFile
from mixins import DatabaseMixin, DomainMixin, DownloadableMixin, PasswordMixin, TopAndTailMixin

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

class Skeleton(DatabaseMixin, DomainMixin, DownloadableMixin, PasswordMixin, TopAndTailMixin):
	def go(self, context):
		self.prerun(context)
		
		domain, prefix, alias = self.get_domain_and_alias(context)
		if not domain and not alias:
			return
		
		password = self.generate_password(context)
		apachedir = context.config('apachedir', '/etc/apache2/sites-enabled')
		
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
		
		context.info('Downloading latest copy of WordPress...')
		filename = self.download(context, 'http://wordpress.org/latest.zip')
		
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
		
		remove(filename)
		
		context.save(path.join(htdocs, '.htaccess'), HTACCESS)
		self.create_database(context, prefix, password)
		
		apache = path.join(apachedir, domain)
		context.save(apache,
			APACHE % {
				'domain': domain,
				'alias': alias,
				'htdocs': htdocs,
				'logs': logs
			}
		)
		
		self.postrun(context)
		return True