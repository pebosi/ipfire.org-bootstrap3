#!/bin/bash

import web
import web.elements
from web.javascript import Javascript
from web.urieldb import Urieldb

from web.info import Info
info = Info()

class Content(web.Content):
	def __init__(self):
		web.Content.__init__(self)
		
		# ID, function, lang tuple
		self.tabs = [ ("tab-os",     self.tab_os,     { "en" : "OS", "de" : "System",},),
					  ("tab-arch",   self.tab_arch,   { "en" : "Architecture", "de": "Architektur",},),
					  ("tab-lang",   self.tab_lang,   { "en" : "Languages", "de" : "Sprache",},),
					  ("tab-cpu",    self.tab_cpu,    { "en" : "CPU", "de" : "Prozessor",},),
					  ("tab-ram",    self.tab_ram,    { "en" : "RAM", "de" : "RAM",},),
					  ("tab-vendor", self.tab_vendor, { "en" : "Vendor", "de" : "Hersteller",},),
					  ("tab-model",  self.tab_model,  { "en" : "Model", "de" : "Modell",},),
					  ("tab-formfactor", self.tab_formfactor, { "en" : "Formfactor", "de" : "Formfaktor",},),
					  ("tab-storage", self.tab_storage, { "en" : "Storage", "de" : "Datenspeicher",},),]

		self.db = Urieldb()

	def __call__(self, lang):
		ret = """<h3>IPFire Uriel</h3>
					<table class="uriel">
						<tr>
							<td class="header">Total hosts:</td>
							<td>""" + "%s" % self.db.count() + """</td>
						</tr>
					</table><br />"""

		ret +=	"""<div id="tabs">
					<ul>"""

		# Create the links
		for tab, function, langs in self.tabs:
			ret += """<li><a href="#%s">%s</a></li>""" % (tab, langs[lang],)
		ret += "</ul>"

		# Do the div containers
		for tab, function, langs in self.tabs:
			ret += """<div id="%s">%s</div>""" % (tab, function(lang),)

		ret += "</div>"

		return ret

	def table(self, item, lang):
		ret = """<table class="uriel">"""

		results, total = self.db.table(item, sort=1, consolidate=1)

		if not total:
			ret += """<tr><td class="item" colspan="2">There is no data available.</td></tr>"""

		else:
			for result, value in results:
				ret += """<tr><td class="item">%s</td><td class="value">%d%%</td></tr>""" % \
					(result, int(value * 100 / total))

			ret += """<tr>
						<td class="footer" colspan="2">%s/%s (%d%%) of the known hosts provide this information</td>
					  </tr>""" % (total, self.db.count(), total * 100 / int(self.db.count()))

		return ret + "</table>"
	
	def table_range(self, item, lang, unit, ranges):
		ret = """<table class="uriel">"""

		ranges2 = {}
		i = 0
		for min, max in ranges:
			ranges2[i] = { "min"   : min,
						   "max"   : max,
						   "count" : 0, }
			i += 1
		ranges = ranges2
		
		results, total = self.db.table(item)

		if not total:
			ret += """<tr><td class="item" colspan="2">There is no data available.</td></tr>"""

		else:
			for i in results:
				for range in ranges.keys():
					if i >= ranges[range]["min"] and i <= ranges[range]["max"]:
						ranges[range]["count"] += 1
						break

			for range in ranges.keys():
				ret += """<tr><td class="item">%s</td><td class="value">%d%%</td></tr>""" % \
					("in between %s and %s %s" % (ranges[range]["min"], ranges[range]["max"], unit),
					ranges[range]["count"] * 100 / total)
	
			ret += """<tr>
						<td class="footer" colspan="2">%s/%s (%d%%) of the known hosts provide this information</td>
					  </tr>""" % (total, self.db.count(), total * 100 / int(self.db.count()))

		return ret + "</table>"

	def tab_os(self, lang):
		return self.table("system", lang)

	def tab_arch(self, lang):
		return self.table("arch", lang)

	def tab_lang(self, lang):
		return self.table("lang", lang)

	def tab_cpu(self, lang):
		return self.table("cpu_model", lang) + \
			self.table_range("cpu_mhz", lang, unit="MHz", ranges=((1, 132), (133, 265),
				(266, 511), (512, 1023), (1024, 1535), (1536, 2047), (2048, 2559),
				(2560, 3071), (3072, 4096)))

	def tab_ram(self, lang):
		return self.table_range("ram_mb", lang, unit="MBytes", 
			ranges=((1,63),	(64, 127), (128, 255), (256, 511), (512, 1023),
					(1024, 4095), (4096, 16383)),)
	
	def tab_vendor(self, lang):
		return self.table("vendor", lang)

	def tab_model(self, lang):
		return self.table("model", lang)
	
	def tab_formfactor(self, lang):
		return self.table("formfactor", lang)
	
	def tab_storage(self, lang):
		return self.table("storage", lang)


page = web.Page()
page.content = Content()
page.sidebar = web.elements.DevelopmentSidebar()
page.javascript = Javascript(1, 1)
page.javascript.write("""
	<script type="text/javascript">
		$(function() {
			$("#tabs").tabs();
		});
	</script>
""")
