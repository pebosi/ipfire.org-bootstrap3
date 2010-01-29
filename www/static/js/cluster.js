nodes = new Array();
id = 0;
busy = false;

update = function() {
	$.getJSON("/api/cluster_info", { id : id++ },
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
					row  = "<tr id=\"" + nodeid + "\" class=\"node\">";
					row += "  <td id=\"" + nodeid + "_hostname\"></td>";
					row += "  <td id=\"" + nodeid + "_arch\">" + node.arch + "</td>";
					row += "  <td><span id=\"" + nodeid + "_loadbar\"></span></td>";
					row += "  <td><span id=\"" + nodeid + "_jobs\"></span></td>";
					row += "  <td id=\"" + nodeid + "_speed\">" + node.speed + "</td>";
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
