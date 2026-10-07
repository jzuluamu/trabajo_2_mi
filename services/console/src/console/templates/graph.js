(function () {
  "use strict";
  var data = JSON.parse(document.getElementById("graph-data").textContent);
  var container = document.getElementById("graph");
  if (!data.nodes.length) { return; }
  var nodes = new vis.DataSet(data.nodes);
  var edges = new vis.DataSet(data.edges);
  var network = new vis.Network(container, { nodes: nodes, edges: edges }, data.options);
  var EASE = { duration: 450, easingFunction: "easeInOutCubic" };
  var originalEdgeColor = {};
  edges.forEach(function (e) { originalEdgeColor[e.id] = e.color; });

  function focus(id) {
    var keep = {};
    keep[id] = true;
    network.getConnectedNodes(id).forEach(function (n) { keep[n] = true; });
    var linked = {};
    network.getConnectedEdges(id).forEach(function (e) { linked[e] = true; });
    nodes.update(nodes.getIds().map(function (n) { return { id: n, opacity: keep[n] ? 1 : 0.22 }; }));
    edges.update(edges.getIds().map(function (e) {
      var base = originalEdgeColor[e] || {};
      var color = Object.assign({}, base, { opacity: linked[e] ? 1 : 0.15 });
      if (linked[e] && e !== "__draft__") { color.color = "#1F5FBF"; }
      return { id: e, color: color, width: linked[e] ? 3 : 2 };
    }));
    network.selectNodes([id]);
  }

  function clear() {
    nodes.update(nodes.getIds().map(function (n) { return { id: n, opacity: 1 }; }));
    edges.update(edges.getIds().map(function (e) {
      return { id: e, color: originalEdgeColor[e], width: e === "__draft__" ? 3 : 2 };
    }));
  }

  network.on("click", function (params) {
    if (params.nodes.length) { focus(params.nodes[0]); } else { clear(); network.unselectAll(); }
  });
  var settled = false;
  function settle() {
    if (settled) { return; }
    settled = true;
    network.setOptions({ physics: { enabled: false } });
    network.fit({ animation: EASE });
    if (data.selected) { focus(data.selected); }
    container.classList.add("ready");
  }
  network.once("stabilizationIterationsDone", settle);
  setTimeout(settle, 2500);

  var refit = null;
  window.addEventListener("resize", function () {
    clearTimeout(refit);
    refit = setTimeout(function () { network.fit({ animation: EASE }); }, 150);
  });

  function zoom(factor) {
    network.moveTo({ scale: network.getScale() * factor, animation: { duration: 280, easingFunction: "easeOutQuad" } });
  }
  document.getElementById("zoom-in").addEventListener("click", function () { zoom(1.25); });
  document.getElementById("zoom-out").addEventListener("click", function () { zoom(0.8); });
  document.getElementById("zoom-fit").addEventListener("click", function () { network.fit({ animation: EASE }); });
  document.getElementById("relayout").addEventListener("click", function () {
    clear();
    network.setOptions({ physics: { enabled: true } });
    network.stabilize(300);
    network.once("stabilizationIterationsDone", function () {
      network.setOptions({ physics: { enabled: false } });
      network.fit({ animation: EASE });
    });
  });
})();
