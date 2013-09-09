import string, random

class PasswordMixin(object):
	def generate_password(self, context):
		password = context.ask('Password for database', required = False)
		if not password:
			password = ''.join(
				random.sample(string.letters + string.digits, 16)
			)
			
			context.info('Password automatically generated:', password)
		
		return password