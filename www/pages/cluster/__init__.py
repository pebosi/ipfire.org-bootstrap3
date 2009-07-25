#!/usr/bin/python

import web
import web.elements
from web.javascript import Javascript

class Content(web.Content):
	def __init__(self):
		web.Content.__init__(self)

	def __call__(self, lang):
		ret = """<h3>Icecream Cluster Monitoring</h3>
			<p>Cluster's CPU load: <span id="loadbar"></span> - Job load: <span id="jobbar"></span></p>
				<table id="nodes">
					<thead>
						<tr>
							<th>Name</th>
							<th>Arch</th>
							<th>Load</th>
							<th>Jobs</th>
							<th>Speed</th>
						</tr>
					</thead>
					<tbody>
					</tbody>
				</table>
				<p>&nbsp;<br />Number of nodes: <span id="count">-</span></p>"""

		return ret

page = web.Page()
page.content = Content()
page.sidebar = web.elements.DevelopmentSidebar()

page.javascript = Javascript(jquery=1)
page.javascript.jquery_plugin("progressbar")
page.javascript.write("""<script type="text/javascript">
				nodes = new Array();
				id = 0;
				busy = false;

				update = function() {
					$.getJSON("/rpc.py", { method: "cluster_get_info", id : id++ },
						function(data) {
							// If we are already busy then exit
							if (busy == true) return;

							var count = 0;

							if (data.error != "null") return;
							
							busy = true;

							$.each(data.result.nodes, function(i, node) {
								var nodeid = node.hostname.replace(/\./g, "");
								count++;

								nodes[nodeid] = true;

								if ($("#" + nodeid).length) {
									$("#" + nodeid + "_speed").html(node.speed);
								} else {
									row  = "<tr id=\\"" + nodeid + "\\" class=\\"node\\">";
									row += "  <td id=\\"" + nodeid + "_hostname\\"></td>";
									row += "  <td id=\\"" + nodeid + "_arch\\">" + node.arch + "</td>";
									row += "  <td><span id=\\"" + nodeid + "_loadbar\\"></span></td>";
									row += "  <td><span id=\\"" + nodeid + "_jobs\\"></span></td>";
									row += "  <td id=\\"" + nodeid + "_speed\\">" + node.speed + "</td>";
									row += "</tr>";
									$("#nodes").append(row);
								}
								$("#" + nodeid + "_loadbar").progressBar(node.load, {showText: false});
								$("#" + nodeid + "_jobs").progressBar(node.jobcount.split("/")[0], { max: node.jobcount.split("/")[1], textFormat: 'fraction'});
								if (node.installing == true) {
									$("#" + nodeid + "_hostname").html(node.hostname + " *");
								} else {
									$("#" + nodeid + "_hostname").html(node.hostname);
								}
							});

							$("#loadbar").progressBar(data.result.cluster.load);
							$("#jobbar").progressBar(data.result.cluster.jobcount.split("/")[0], { max: data.result.cluster.jobcount.split("/")[1], textFormat: 'fraction'});
							for (var nodeid in nodes) {
								if (nodes[nodeid] == false) {
									$("#" + nodeid).remove();
									nodes.pop(nodeid);
								} else {
									nodes[nodeid] = false;
								}
							}
							$("#count").html(count);
							busy = false;
					});
				}

				$(document).ready(function(){
					// Init loadbar
					$("#loadbar").progressBar();

					update();
					setInterval("update()", 2000);
				})
			</script>""")
