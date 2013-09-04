import MySQLdb

class Plugin(object):
	def __init__(self, context):
		self.context = context
		self.connections = {}
		
		print 'Startup'
		super(Plugin, self).__init__()
	
	def cleanup(self, success):
		print 'Cleanup'
		
		for key, connection in self.connections.items():
			connection.close()
			self.connections.pop(key)
	
	def execute(self, sql, username, password):
		if (username, password) in self.connections:
			db = self.connections[(username, password)]
		else:
			db = MySQLdb.connect('localhost', user = username, passwd = password)
			self.connections[(username, password)] = db
		
		cur = db.cursor()
		cur.execute(sql)
		
		return cur
	
	def query(self, sql, username, password):
		cur = self.execute(sql, username, password)
		
		for row in cur.fetchall():
			yield row