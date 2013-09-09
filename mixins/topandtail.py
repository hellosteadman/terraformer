class TopAndTailMixin(object):
	def prerun(self, context):
		prerun = context.config('prerun')
		if prerun:
			context.sh(*prerun.split())
	
	def postrun(self, context):
		postrun = context.config('postrun')
		if postrun:
			context.sh(*postrun.split())