class DatabaseMixin(object):
	def create_database(self, context, name, password):
		dbuser = context.config('dbuser', 'root')
		dbpass = context.config('dbpass', '')
		answer = None
		
		for row in context.plugin('mysql').query('SHOW DATABASES LIKE \'%s\'' % name, dbuser, dbpass):
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
				context.plugin('mysql').execute('DROP DATABASE `%s`' % name, dbuser, dbpass)
			elif answer == 'cancel':
				return False
			
			break
		
		if answer != 'continue':
			context.plugin('mysql').execute('CREATE DATABASE `%s`' % name, dbuser, dbpass)
		
		answer = None
		for row in context.plugin('mysql').query('SELECT User, Host from mysql.user WHERE Host = \'localhost\' AND User = \'%s\'' % name, dbuser, dbpass):
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
				context.plugin('mysql').execute('DROP USER \'%s\'@\'localhost\'' % name, dbuser, dbpass)
			elif answer == 'cancel':
				return False
			
			break
		
		if answer != 'continue':
			context.plugin('mysql').execute(
				'CREATE USER \'%s\'@\'localhost\' IDENTIFIED BY \'%s\'' % (name, password),
				dbuser, dbpass
			)
		
		context.plugin('mysql').execute(
			'GRANT ALL PRIVILEGES ON `%(name)s`.* TO \'%(name)s\'@\'localhost\'' % {
				'name': name
			}, dbuser, dbpass
		)