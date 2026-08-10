R-Code
# ==============================================================================
# POLYVALENZ-CLUSTER: NETZWERKANALYSE UND VISUALISIERUNG (ANHANG)
# ==============================================================================

library(visNetwork)
library(htmlwidgets)
library(dplyr)
library(igraph)

final_file_name <- "Polyvalenz_Cluster_vorl_finl_5.html"

# --- 1. Datenimport und Datenbereinigung ---
load_and_clean <- function(file) {
  if(!file.exists(file)) return(data.frame(V2=character(), V4=character(), V7=character(), V8=character()))
  raw <- readLines(file, warn = FALSE)
  clean <- raw %>%
    gsub("Ã¤", "ä", .) %>% gsub("Ã¶", "ö", .) %>% gsub("Ã¼", "ü", .) %>%
    gsub("Ã„", "Ä", .) %>% gsub("Ã–", "Ö", .) %>% gsub("Ãœ", "Ü", .) %>%
    gsub("ÃŸ", "ß", .)
  df <- read.csv2(text = clean, sep = ";", colClasses = "character", header = FALSE, fill = TRUE, quote = "\"", skip = 1)
  zsl_mods <- df %>% filter(V7 == "ZSL" | grepl("Zusatzleistung", V8, ignore.case = TRUE)) %>% pull(V4) %>% unique()
  df %>% filter(V7 != "ZSL" & !(V4 %in% zsl_mods))
}

theory_raw <- load_and_clean("Alle_poly.csv")
real_raw <- load_and_clean("Reale_Belegungen.csv")
clean_string <- function(x) trimws(as.character(x))

# --- 2. Netzwerkmodellierung und Adjazenzstrukturen ---
edges_theory <- theory_raw %>%
  transmute(from = clean_string(V4), to = clean_string(V8)) %>%
  filter(from != "" & to != "") %>%
  distinct() %>%
  group_by(from) %>% filter(n() >= 2) %>% ungroup() %>%
  mutate(eid = paste0("t_", row_number()), is_real = FALSE)

edges_real <- real_raw %>%
  transmute(from = clean_string(V4), to = clean_string(V8)) %>%
  filter(from %in% edges_theory$from) %>%
  distinct() %>%
  mutate(eid = paste0("r_", row_number()), is_real = TRUE)

all_edges <- bind_rows(edges_theory, edges_real) %>% rename(id = eid)

get_adj <- function(df) {
  df %>% group_by(from) %>% summarize(nb = list(to)) %>% rename(id = from) %>%
    bind_rows(df %>% group_by(to) %>% summarize(nb = list(from)) %>% rename(id = to)) %>%
    group_by(id) %>% summarize(neighbors = list(unique(unlist(nb))))
}
adj_t <- get_adj(edges_theory) %>% rename(nb_t = neighbors)
adj_r <- get_adj(edges_real) %>% rename(nb_r = neighbors)

# --- 3. Clusteranalyse und Knoteneigenschaften ---
set.seed(1)
g <- graph_from_data_frame(edges_theory, directed = FALSE)
cl <- cluster_louvain(g)

# Generierung eines initialen Fruchterman-Reingold-Layouts als Simulationsgrundlage
layout_coords <- layout_with_fr(g, niter = 150)
layout_df <- data.frame(
  id = V(g)$name,
  x  = layout_coords[, 1] * 1000,
  y  = layout_coords[, 2] * 1000,
  stringsAsFactors = FALSE
)

cluster_df <- data.frame(id = names(membership(cl)), cid = as.character(as.vector(membership(cl))))
node_importance <- as.data.frame(table(c(edges_theory$from, edges_theory$to)))
colnames(node_importance) <- c("id", "count")

id_lookup <- bind_rows(
  theory_raw %>% transmute(name = clean_string(V4), real_id = V2),
  theory_raw %>% transmute(name = clean_string(V8), real_id = V7)
) %>% distinct(name, .keep_all = TRUE)

nodes_final <- data.frame(id = unique(c(edges_theory$from, edges_theory$to))) %>%
  left_join(node_importance, by = "id") %>%
  left_join(cluster_df, by = "id") %>%
  left_join(adj_t, by = "id") %>%
  left_join(adj_r, by = "id") %>%
  left_join(id_lookup, by = c("id" = "name")) %>%
  left_join(layout_df, by = "id") %>%
  mutate(
    label = id, is_studiengang = id %in% edges_theory$to,
    group = paste("Bereich", cid),
    size = ifelse(is_studiengang, 12 + (count / 1.5), 4 + (count / 5)),
    shape = ifelse(is_studiengang, "square", "dot"),
    cid_val = cid,
    poly_val = ifelse(is_studiengang, 999, count)
  )

# --- 4. Definition der Benutzeroberfläche und Steuerungsskripte (JavaScript) ---
js_code_lines <- c(
  "function () {",
  "  if (window.ui_initialized) return;",
  "  window.ui_initialized = true;",
  "  this.setOptions({ physics: false });", # Einfrieren der Physik-Engine nach Abschluss der Initialisierungsphase
  "  document.body.style.backgroundColor = '#0a0a0a';",
  "  var style = document.createElement('style');",
  "  style.innerHTML = '.glass-panel { background: rgba(25,25,25,0.98); backdrop-filter: blur(10px); border: 1px solid #444; border-radius: 12px; color: white; font-family: sans-serif; padding: 20px; position: fixed; z-index: 1000; }' +",
  "                    '#searchBox { top: 20px; left: 20px; width: 320px; }' +",
  "                    '#infoPanel { top: 20px; right: 20px; width: 360px; display: none; max-height: 85vh; overflow-y: auto; border-left: 3px solid #ff4d4d; }' +",
  "                    '#clusterPanel { top: 420px; left: 20px; width: 320px; display: none; max-height: 45vh; overflow-y: auto; border-left: 3px solid #ff4d4d; }' +",
  "                    '.ui-section { margin-top: 15px; border-top: 1px solid #444; padding-top: 15px; }' +",
  "                    '.mode-switch { display: flex; background: #111; border-radius: 8px; padding: 4px; border: 1px solid #444; }' +",
  "                    '.m-btn { flex: 1; padding: 8px; text-align: center; cursor: pointer; border-radius: 6px; font-size: 11px; color: #888; }' +",
  "                    '.m-btn.active { background: #ff4d4d; color: black; font-weight: bold; }' +",
  "                    'input[type=range] { width: 100%; cursor: pointer; accent-color: #ff4d4d; }' +",
  "                    'input[type=text] { width: 100%; background: #000; border: 1px solid #555; color: white; padding: 12px; border-radius: 6px; margin-top: 10px; box-sizing: border-box; }' +",
  "                    '.search-results { background: #111; border: 1px solid #ff4d4d; border-radius: 6px; max-height: 200px; overflow-y: auto; display: none; margin-top: 5px; position: relative; z-index: 1001;}' +",
  "                    '.search-item { padding: 12px; cursor: pointer; border-bottom: 1px solid #333; font-size: 13px; }' +",
  "                    '.tag-ui { display: inline-block; background: #333; padding: 4px 8px; border-radius: 4px; margin: 3px; font-size: 11px; color: #ff4d4d; border: 1px solid #555; }' +",
  "                    '#modalSheet { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); backdrop-filter: blur(15px); z-index: 2000; overflow-y: auto; padding: 50px; box-sizing: border-box; color: white; font-family: sans-serif; display: none; }' +",
  "                    '.modal-content { max-width: 1000px; margin: 0 auto; }' +",
  "                    '.modal-close { position: fixed; top: 20px; right: 30px; font-size: 40px; cursor: pointer; color: #ff4d4d; }' +",
  "                    '.index-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 25px; margin-top: 30px; }' +",
  "                    '.index-card { background: rgba(255,255,255,0.05); border: 1px solid #444; border-radius: 8px; padding: 18px; }' +",
  "                    '.index-card h3 { color: #ff4d4d; margin-top: 0; border-bottom: 1px solid #444; padding-bottom: 8px; font-size: 16px; }' +",
  "                    '.index-card ul { list-style: none; padding: 0; font-size: 12px; color: #ccc; line-height: 1.6; }';",
  "  document.head.appendChild(style);",
  "  var dash = document.createElement('div'); dash.id = 'searchBox'; dash.className = 'glass-panel';",
  "  dash.innerHTML = \"<b style='color:#ff4d4d; font-size:18px;'>POLYVALENZ-CLUSTER</b><br><input type='text' id='sIn' placeholder='Suche...' autocomplete='off'><div id='sRes' class='search-results'></div><div class='ui-section'><div style='font-size:11px; color:#aaa; margin-bottom:5px;'>Min. Polyvalenz: <span id='vL'>2</span></div><input type='range' id='sli' min='2' max='15' value='2'></div><div id='modeContainer' class='ui-section' style='display:none;'><div style='font-size:11px; color:#aaa; margin-bottom:8px;'>Ansichtsmodus (Fokus):</div><div class='mode-switch'><div id='btnT' class='m-btn active'>THEORIE</div><div id='btnR' class='m-btn'>REALITÄT</div></div></div><div class='ui-section'><button id='openSheet' style='width:100%; padding:12px; background:#ff4d4d; color:black; font-weight:bold; border:0; border-radius:6px; cursor:pointer;'>Cluster-Index öffnen</button><button id='resV' style='width:100%; padding:10px; margin-top:10px; background:#333; color:white; border:0; border-radius:6px; cursor:pointer;'>Ansicht Reset</button></div>\";",
  "  document.body.appendChild(dash);",
  "  var modal = document.createElement('div'); modal.id = 'modalSheet';",
  "  modal.innerHTML = \"<div class='modal-close' id='closeSheet'>&times;</div><div class='modal-content'><h1 style='color:#ff4d4d; margin-bottom:10px;'>Cluster-Inventar</h1><p style='color:#888;'>Vollständige Liste aller Fachbereiche und der zugehörigen Studiengänge (Louvain-Partitionierung).</p><hr style='border:0; border-top:1px solid #333; margin:20px 0;'><div class='index-grid' id='indexGrid'></div></div>\";",
  "  document.body.appendChild(modal);",
  "  var info = document.createElement('div'); info.id = 'infoPanel'; info.className = 'glass-panel'; document.body.appendChild(info);",
  "  var cp = document.createElement('div'); cp.id = 'clusterPanel'; cp.className = 'glass-panel'; document.body.appendChild(cp);",
  "  var net = this, allN = net.body.data.nodes.get(), allE = net.body.data.edges.get(), mode = 'T', sel = [];",
  "  function buildIndex() {",
  "    var grid = document.getElementById('indexGrid'); grid.innerHTML = ''; var clusters = {};",
  "    allN.forEach(function(n) { if(n.is_studiengang) { if(!clusters[n.cid_val]) clusters[n.cid_val] = []; clusters[n.cid_val].push(n.id); } });",
  "    Object.keys(clusters).sort((a,b) => a-b).forEach(function(c) {",
  "      var card = document.createElement('div'); card.className = 'index-card';",
  "      card.innerHTML = '<h3>Bereich ' + c + '</h3><ul>' + clusters[c].sort().map(s => '<li>• ' + s + '</li>').join('') + '</ul>';",
  "      grid.appendChild(card);",
  "    });",
  "  }",
  "  document.getElementById('openSheet').onclick = function() { buildIndex(); document.getElementById('modalSheet').style.display = 'block'; };",
  "  document.getElementById('closeSheet').onclick = function() { document.getElementById('modalSheet').style.display = 'none'; };",
  "  function applyEdges(visibleNodes) {",
  "    var isReal = (mode === 'R');",
  "    net.body.data.edges.update(allE.map(function(e) {",
  "      var rightType = isReal ? e.is_real : !e.is_real;",
  "      var connected = !visibleNodes || (visibleNodes.includes(e.from) && visibleNodes.includes(e.to));",
  "      return { id: e.id, hidden: !(rightType && connected), color: isReal ? 'rgba(77,255,77,0.5)' : 'rgba(200,200,200,0.15)', width: isReal ? 0.5 : 0.1 };",
  "    }));",
  "  }",
  "  function update() {",
  "    var p = document.getElementById('infoPanel'), mc = document.getElementById('modeContainer'), sli = document.getElementById('sli'), cp = document.getElementById('clusterPanel');",
  "    var sliVal = parseInt(sli.value);",
  "    if (sel.length === 0) {",
  "      mode = 'T'; document.getElementById('btnT').className = 'm-btn active'; document.getElementById('btnR').className = 'm-btn';",
  "      p.style.display = 'none'; mc.style.display = 'none'; cp.style.display = 'none';",
  "      net.body.data.nodes.update(allN.map(n => ({ id: n.id, opacity: (n.is_studiengang || n.poly_val >= sliVal) ? 1 : 0.05 })));",
  "      applyEdges(null); return;",
  "    }",
  "    mc.style.display = 'block'; p.style.display = 'block';",
  "    var arrays = sel.map(id => { var n = net.body.data.nodes.get(id); return (mode === 'T' ? n.nb_t : n.nb_r) || []; });",
  "    if (sel.length >= 2) {",
  "      cp.style.display = 'none';",
  "      var inter = arrays.reduce((a, b) => a.filter(c => b.includes(c))) || [];",
  "      p.innerHTML = '<b style=\"color:#ff4d4d;\">Schnittmenge</b><hr>' + sel.map(id => '<span class=\"tag-ui\">'+id+'</span>').join('') + '<br><br>Gemeinsame Verbindungen: ' + inter.length + '<br><br><b>Gemeinsame Nachbarn:</b><br>• ' + (inter.length > 0 ? inter.join('<br>• ') : 'Keine');",
  "      var hlNodes = sel.concat(inter);",
  "      net.body.data.nodes.update(allN.map(n => ({ id: n.id, opacity: hlNodes.includes(n.id) ? 1 : (n.is_studiengang ? 0.35 : 0.05) })));",
  "      applyEdges(hlNodes);",
  "    } else {",
  "      var n = net.body.data.nodes.get(sel[0]);",
  "      var nbs = (mode === 'T' ? n.nb_t : n.nb_r) || [];",
  "      var directSG = nbs.filter(function(id) { var nb = net.body.data.nodes.get(id); return nb && nb.is_studiengang; });",
  "      p.innerHTML = '<b style=\"color:#ff4d4d;\">' + n.id + '</b><hr>' + (n.is_studiengang ? '<span style=\"background:#ff4d4d;color:black;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:bold;\">STUDIENGANG</span><br><br>' : '') + 'ID: ' + (n.real_id || 'N/A') + '<br>Bereich: ' + (n.cid_val || 'N/A') + '<br>Vernetzung: ' + nbs.length + (!n.is_studiengang && directSG.length > 0 ? '<br><br><b>Gehört zu:</b><br>• ' + directSG.join('<br>• ') : '') + '<br><br><b>Nachbarn:</b><br>• ' + (nbs.length > 0 ? nbs.join('<br>• ') : 'Keine');",
  "      var clusterPeers = allN.filter(function(x) { return x.is_studiengang && x.cid_val === n.cid_val && x.id !== n.id; }).map(function(x) { return x.id; }).sort();",
  "      cp.style.display = 'block';",
  "      cp.innerHTML = '<b style=\"color:#ff4d4d;\">Bereich ' + n.cid_val + '</b><hr style=\"border:0;border-top:1px solid #444;margin:8px 0;\">' + '<div style=\"font-size:11px;color:#aaa;margin-bottom:8px;\">Weitere Studiengänge im selben Cluster:</div>' + (clusterPeers.length > 0 ? clusterPeers.map(function(s) { return '<div style=\"padding:5px 0;border-bottom:1px solid #2a2a2a;font-size:12px;\">• ' + s + '</div>'; }).join('') : '<span style=\"color:#555;font-size:12px;\">Keine weiteren</span>');",
  "      var hl = [sel[0]].concat(nbs);",
  "      net.body.data.nodes.update(allN.map(node => ({ id: node.id, opacity: hl.includes(node.id) ? 1 : (node.is_studiengang ? 0.35 : 0.05) })));",
  "      applyEdges(hl);",
  "    }",
  "  }",
  "  document.getElementById('sIn').oninput = function() {",
  "    var q = this.value.trim().toLowerCase(); var res = document.getElementById('sRes');",
  "    if (q.length < 1) { res.style.display = 'none'; res.innerHTML = ''; return; }",
  "    var hits = allN.filter(n => n.id.toLowerCase().includes(q)).slice(0, 10); if (hits.length === 0) { res.style.display = 'none'; return; }",
  "    res.innerHTML = hits.map(n => '<div class=\"search-item\" data-id=\"' + n.id + '\">' + n.id + '</div>').join(''); res.style.display = 'block';",
  "    res.querySelectorAll('.search-item').forEach(function(el) { el.onclick = function() { var id = this.getAttribute('data-id'); sel = [id]; document.getElementById('sIn').value = id; res.style.display = 'none'; net.focus(id, { scale: 1.2, animation: true }); update(); }; });",
  "  };",
  "  document.addEventListener('click', function(e) { if (!e.target.closest('#searchBox')) document.getElementById('sRes').style.display = 'none'; });",
  "  document.getElementById('sli').oninput = function() { document.getElementById('vL').innerHTML = this.value; update(); };",
  "  document.getElementById('btnT').onclick = function() { mode = 'T'; this.className='m-btn active'; document.getElementById('btnR').className='m-btn'; update(); };",
  "  document.getElementById('btnR').onclick = function() { mode = 'R'; this.className='m-btn active'; document.getElementById('btnT').className='m-btn'; update(); };",
  " net.on('click', params => { if (params.nodes.length > 0) { var id = params.nodes[0]; if (params.event.srcEvent.ctrlKey) { if (sel.includes(id)) sel = sel.filter(x => x !== id); else sel.push(id); } else { sel = [id]; } update(); } else { sel = []; update(); } });",
  "  document.getElementById('resV').onclick = function() { sel = []; document.getElementById('sli').value = 2; document.getElementById('vL').innerHTML = 2; update(); net.moveTo({ scale: 0.6, animation: true }); };",
  "  update();",
  "}"
)
js_stabilization_done <- paste0(js_code_lines, collapse = "\n")

# --- 5. Netzwerkintegration und Parameterisierung der physikalischen Engine ---
network <- visNetwork(nodes_final, all_edges, width = "100%", height = "100vh") %>%
  visNodes(font = list(size = 0)) %>%
  visEdges(smooth = FALSE) %>%
  
  # Parametrisierung des ForceAtlas2-Solvers mit begrenzter Iterationsanzahl zur Performance-Optimierung
  visPhysics(
    solver = "forceAtlas2Based", 
    forceAtlas2Based = list(gravitationalConstant = -250),
    stabilization = list(enabled = TRUE, iterations = 100)
  ) %>%
  
  # Event-Listener zur einmaligen UI-Generierung nach Beendigung der Stabilisierungsphase
  visEvents(stabilizationIterationsDone = js_stabilization_done) %>%
  visInteraction(dragNodes = FALSE, hover = TRUE)

saveWidget(network, final_file_name, selfcontained = TRUE)
browseURL(final_file_name)
