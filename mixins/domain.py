class DomainMixin(object):
	def get_domain_and_alias(self, context):
		domain = context.ask('Domain name')
		if not '.' in domain:
			context.error('Domain name', domain, 'doesn\'t seem to be valid.')
			return None, None
		
		suffix = context.config('suffix', '.com')
		prefix = '.'.join(domain.split('.')[:-1])
		alias = prefix + suffix
		alias = context.ask('Domain name alias', default = alias)
		return domain, prefix, alias