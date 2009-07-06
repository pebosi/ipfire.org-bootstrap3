#!/usr/bin/python

import web
import web.cluster

class Content(web.Content):
	def __init__(self, name):
		web.Content.__init__(self, name)
		
		self.cluster = web.cluster.Cluster("minerva.ipfire.org")

	def __call__(self, lang):
		ret = "<h3>Icecream Cluster Monitoring</h4>"

		ret += """<script type="text/javascript">
				nodes = new Array();

				update = function() {
					$.getJSON("http://www.ipfire.org/rpc.py", { type: "cluster" },
						function(data) {
							var count = 0;
							$.each(data.nodes, function(i, node) {
								var nodeid = node.hostname.replace(/\./g, "");
								count++;

								nodes[nodeid] = true;

								if ($("#" + nodeid).length) {
									$("#" + nodeid + "_speed").html(node.speed);
								} else {
									row  = "<tr id=\\"" + nodeid + "\\" class=\\"node\\">";
									row += "  <td id=\\"" + nodeid + "_hostname\\">" + node.hostname + "</td>";
									row += "  <td id=\\"" + nodeid + "_arch\\">" + node.arch + "</td>";
									row += "  <td><span id=\\"" + nodeid + "_loadbar\\"></span></td>";
									row += "  <td><span id=\\"" + nodeid + "_jobs\\"></span></td>";
									row += "  <td id=\\"" + nodeid + "_speed\\">" + node.speed + "</td>";
									row += "</tr>";
									$("#nodes").append(row);
								}
								$("#" + nodeid + "_loadbar").progressBar(node.load, {showText: false});
								$("#" + nodeid + "_jobs").progressBar(node.jobs.split("/")[0], { max: node.jobs.split("/")[1], textFormat: 'fraction'}); 
							});
							$("#loadbar").progressBar(data.cluster.load);
							for (var nodeid in nodes) {
								if (nodes[nodeid] == false) {
									$("#" + nodeid).remove();
									nodes.pop(nodeid);
								} else {
									nodes[nodeid] = false;
								}
							}
							$("#count").html(count);
					});
				}

				$(document).ready(function(){
					// Init loadbar
					$("#loadbar").progressBar();

					update();
					setInterval("update()", 2000);
				})
			</script>"""		

		ret += """<p>Cluster's load: <span id="loadbar"></span>  - Number of nodes: <span id="count">-</span></p>
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
				</table>"""

		return ret

Sidebar = web.Sidebar