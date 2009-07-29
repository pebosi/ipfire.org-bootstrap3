#!/usr/bin/python

try:
	import cStringIO as StringIO
except ImportError:
	import StringIO

class Javascript(object):
	def __init__(self, jquery=0, jqueryui=0):
		self.io = StringIO.StringIO()

		if jquery:
			self.io.write("""<script src="/include/jquery.min.js" type="text/javascript"></script>""")
		
		if jqueryui:
			self.io.write("""<script src="/include/jquery-ui.min.js" type="text/javascript"></script>""")
	
	def __call__(self, lang="en"):
		return self.io.getvalue()

	def jquery_plugin(self, plugin):
		self.io.write("""<script src="/include/jquery.%s.min.js" type="text/javascript"></script>""" % plugin)

	def write(self, s):
		self.io.write(s)
