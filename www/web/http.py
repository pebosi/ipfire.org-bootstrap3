#!/usr/bin/python
# -*- coding: utf-8 -*-

code2msg = { 200 : "OK",
			 302 : "Temporarily Moved",
			 404 : "Not found",
			 500 : "Internal Server Error", }

class HTTPResponse:
	def __init__(self, code, header=None, type="text/html"):
		self.code = code

		print "Status: %s - %s" % (self.code, code2msg[self.code],)
		if self.code == 302:
			print "Pragma: no-cache"
		if type:
			print "Content-type: " + type
		if header:
			for (key, value,) in header:
				print "%s: %s" % (key, value,)
		print

	def execute(self, content=""):
		if self.code == 200:
			print content

class WebError(Exception):
	pass
