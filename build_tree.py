import json, os

with open('flowchart_data.json', encoding='utf-8') as f:
    raw_data = json.load(f)
data_str = json.dumps(raw_data, ensure_ascii=False)

HTML = r"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>LMU Course Tree</title>
<style>
:root {
  --bg: #1e1e1e;
  --sidebar-bg: #252526;
  --header-bg: #2d2d2d;
  --border: #3e3e3e;
  --text: #cccccc;
  --text-dim: #858585;
  --text-bright: #ffffff;
  --accent: #0078d4;
  --accent-hover: #1a8fe3;
  --hover-bg: #2a2d2e;
  --selected-bg: #094771;
  --selected-border: #007fd4;
  --icon-folder: #e8b64c;
  --icon-folder-open: #e8b64c;
  --icon-file: #c5c5c5;
  --icon-sem: #4ec9b0;
  --icon-deg: #c586c0;
  --icon-prog: #9cdcfe;
  --icon-exam: #ce9178;
  --scrollbar-bg: #1e1e1e;
  --scrollbar-thumb: #424242;
  --drag-bg: #3a3d3e;
  --drag-border: #007fd4;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; overflow: hidden; }

body {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  font-size: 13px;
  background: var(--bg);
  color: var(--text);
  display: flex;
  flex-direction: column;
}

/* ── TOP BAR ── */
#topbar {
  background: var(--header-bg);
  border-bottom: 1px solid var(--border);
  padding: 6px 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
  flex-wrap: wrap;
  min-height: 42px;
}
#topbar h1 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-bright);
  white-space: nowrap;
}
#topbar h1 em { color: #4ec9b0; font-style: normal; }

.tb-sep { width: 1px; height: 18px; background: var(--border); flex-shrink: 0; }

#search-box {
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 3px 8px;
  border-radius: 3px;
  font-size: 12px;
  outline: none;
  width: 200px;
  transition: border-color 0.15s;
}
#search-box:focus { border-color: var(--accent); }

#stats {
  margin-left: auto;
  font-size: 11px;
  color: var(--text-dim);
  white-space: nowrap;
}

/* ── LAYOUT ── */
#layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ── LEVEL CONFIG SIDEBAR ── */
#sidebar {
  width: 220px;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
}

#sidebar-title {
  padding: 8px 12px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  background: var(--header-bg);
}

#level-list {
  padding: 8px 0;
  flex: 1;
  overflow-y: auto;
}

.level-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  cursor: grab;
  user-select: none;
  border: 1px solid transparent;
  border-radius: 3px;
  margin: 1px 6px;
  transition: background 0.1s;
}
.level-item:hover { background: var(--hover-bg); }
.level-item.dragging { opacity: 0.4; }
.level-item.drag-over {
  background: var(--drag-bg);
  border-color: var(--drag-border);
}

.drag-handle {
  color: var(--text-dim);
  font-size: 14px;
  cursor: grab;
  flex-shrink: 0;
  line-height: 1;
}
.drag-handle:active { cursor: grabbing; }

.level-num {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
}
.lnum-0 { background: #1a6b3a; color: #4ec9b0; }
.lnum-1 { background: #4a1b6b; color: #c586c0; }
.lnum-2 { background: #1a3a6b; color: #9cdcfe; }
.lnum-3 { background: #6b2f1a; color: #ce9178; }

.level-name {
  font-size: 12px;
  color: var(--text);
  flex: 1;
}

.level-icon {
  font-size: 13px;
  flex-shrink: 0;
}

#sidebar-hint {
  padding: 8px 12px;
  font-size: 10px;
  color: var(--text-dim);
  border-top: 1px solid var(--border);
  line-height: 1.5;
}

/* ── TREE PANEL ── */
#tree-panel {
  flex: 1;
  overflow: auto;
  padding: 4px 0;
}

#tree-panel::-webkit-scrollbar { width: 8px; height: 8px; }
#tree-panel::-webkit-scrollbar-track { background: var(--scrollbar-bg); }
#tree-panel::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb); border-radius: 4px; }

/* ── TREE NODES ── */
.tree-node { }

.tree-row {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 1px 0;
  cursor: pointer;
  white-space: nowrap;
  border: 1px solid transparent;
  border-radius: 2px;
  min-height: 22px;
}
.tree-row:hover { background: var(--hover-bg); }
.tree-row.selected {
  background: var(--selected-bg);
  border-color: var(--selected-border);
}

/* Indent spacers */
.indent { display: inline-block; width: 16px; flex-shrink: 0; }

/* Expand toggle */
.toggle {
  width: 16px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--text-dim);
  font-size: 9px;
  transition: transform 0.1s;
}
.toggle.open { transform: none; }
.toggle svg { display: block; }
.no-toggle { width: 16px; flex-shrink: 0; }

/* File/folder icon */
.row-icon {
  width: 18px;
  text-align: center;
  flex-shrink: 0;
  font-size: 13px;
  margin-right: 4px;
}

/* Label */
.row-label {
  flex: 1;
  font-size: 13px;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 8px;
}
.row-label.l0 { color: #4ec9b0; }
.row-label.l1 { color: #c586c0; }
.row-label.l2 { color: #9cdcfe; }
.row-label.l3 { color: #ce9178; }

/* Count badge */
.row-count {
  font-size: 10px;
  color: var(--text-dim);
  background: #2a2a2a;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0 6px;
  margin-right: 8px;
  flex-shrink: 0;
}

/* Children container */
.tree-children { }
.tree-children.collapsed { display: none; }

/* Exam leaf */
.exam-row {
  display: flex;
  align-items: flex-start;
  gap: 0;
  padding: 1px 0;
  cursor: default;
  border: 1px solid transparent;
  border-radius: 2px;
  min-height: 20px;
}
.exam-row:hover { background: var(--hover-bg); }

.exam-label {
  font-size: 12px;
  color: #ce9178;
  white-space: normal;
  word-break: break-word;
  line-height: 1.4;
  padding: 1px 8px 1px 0;
}

mark {
  background: #f9c74f44;
  color: #f9c74f;
  border-radius: 2px;
}

/* Empty / loading */
#tree-msg {
  padding: 40px 20px;
  color: var(--text-dim);
  font-size: 12px;
  text-align: center;
}

/* Expand/Collapse buttons */
.tb-btn {
  background: #3a3a3a;
  border: 1px solid var(--border);
  color: var(--text);
  padding: 3px 9px;
  border-radius: 3px;
  font-size: 11px;
  cursor: pointer;
  transition: background 0.1s;
  white-space: nowrap;
}
.tb-btn:hover { background: #4a4a4a; }

/* LEVEL COLOR indicators in sidebar */
.lc-0 { color: #4ec9b0; }
.lc-1 { color: #c586c0; }
.lc-2 { color: #9cdcfe; }
.lc-3 { color: #ce9178; }
</style>
</head>
<body>

<div id="topbar">
  <h1>&#128193; LMU <em>Course Explorer</em></h1>
  <div class="tb-sep"></div>
  <input type="text" id="search-box" placeholder="&#128269;  Search exams or programs...">
  <button class="tb-btn" id="btn-expand-all">Expand All</button>
  <button class="tb-btn" id="btn-collapse-all">Collapse All</button>
  <div class="tb-sep"></div>
  <div id="stats"></div>
</div>

<div id="layout">

  <!-- SIDEBAR: drag-to-reorder levels -->
  <div id="sidebar">
    <div id="sidebar-title">Tree Levels — drag to reorder</div>
    <div id="level-list">
      <!-- populated by JS -->
    </div>
    <div id="sidebar-hint">
      Drag levels up/down to change<br>the tree hierarchy order.
    </div>
  </div>

  <!-- TREE -->
  <div id="tree-panel">
    <div id="tree-root"></div>
    <div id="tree-msg">Building tree&hellip;</div>
  </div>

</div>

<script>
// ── DATA ──
const RAW_DATA = DATA_PLACEHOLDER;

// Flatten to records
const ALL_RECORDS = [];
for (const [sem, degrees] of Object.entries(RAW_DATA)) {
  for (const [deg, programs] of Object.entries(degrees)) {
    for (const [prog, exams] of Object.entries(programs)) {
      for (const exam of exams) {
        ALL_RECORDS.push({ sem, deg, prog, exam });
      }
    }
  }
}

const SEM_LABELS = {
  '20242': 'WS 2024/25  [20242]',
  '20251': 'SS 2025  [20251]',
  '20252': 'WS 2025/26  [20252]'
};

// ── LEVEL CONFIG ──
const LEVEL_DEFS = [
  { key: 'sem',  label: 'Semester',    icon: '📅', color: 0 },
  { key: 'deg',  label: 'Degree Type', icon: '🎓', color: 1 },
  { key: 'prog', label: 'Program',     icon: '📚', color: 2 },
  { key: 'exam', label: 'Exam',        icon: '📄', color: 3 },
];

// Current order (indices into LEVEL_DEFS)
let levelOrder = [0, 1, 2, 3]; // sem → deg → prog → exam

// ── SEARCH ──
let searchQuery = '';

// ── HELPERS ──
function displayVal(key, val) {
  if (key === 'sem') return SEM_LABELS[val] || val;
  return val;
}

function escHtml(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function hlText(text, q) {
  if (!q) return escHtml(text);
  const lower = text.toLowerCase();
  const qi = q.toLowerCase();
  let result = '';
  let i = 0;
  while (i < text.length) {
    const idx = lower.indexOf(qi, i);
    if (idx === -1) { result += escHtml(text.slice(i)); break; }
    result += escHtml(text.slice(i, idx));
    result += '<mark>' + escHtml(text.slice(idx, idx + q.length)) + '</mark>';
    i = idx + q.length;
  }
  return result;
}

// ── BUILD TREE DATA ──
function buildTreeData(records) {
  // levels[0..2] are grouping levels; levels[3] is always exam leaf
  const keys = levelOrder.map(i => LEVEL_DEFS[i].key);
  // keys = ['sem','deg','prog','exam'] in current order
  // We group by keys[0], keys[1], keys[2]; leaves are keys[3] (always 'exam')

  const tree = {};
  for (const r of records) {
    const a = r[keys[0]], b = r[keys[1]], c = r[keys[2]], d = r[keys[3]];
    if (!tree[a]) tree[a] = {};
    if (!tree[a][b]) tree[a][b] = {};
    if (!tree[a][b][c]) tree[a][b][c] = new Set();
    tree[a][b][c].add(d);
  }
  return tree;
}

// ── RENDER TREE ──
let selectedRow = null;

function render() {
  const q = searchQuery.trim().toLowerCase();
  let records = ALL_RECORDS;
  if (q) {
    records = records.filter(r =>
      r.exam.toLowerCase().includes(q) ||
      r.prog.toLowerCase().includes(q) ||
      r.deg.toLowerCase().includes(q) ||
      r.sem.toLowerCase().includes(q)
    );
  }

  const tree = buildTreeData(records);
  const keys = levelOrder.map(i => LEVEL_DEFS[i].key);

  const root = document.getElementById('tree-root');
  root.innerHTML = '';
  document.getElementById('tree-msg').style.display = 'none';

  if (records.length === 0) {
    document.getElementById('tree-msg').style.display = 'block';
    document.getElementById('tree-msg').textContent = 'No exams match the search.';
    document.getElementById('stats').textContent = '0 results';
    return;
  }

  const uSem = new Set(records.map(r=>r.sem)).size;
  const uDeg = new Set(records.map(r=>r.deg)).size;
  const uProg = new Set(records.map(r=>r.prog)).size;
  document.getElementById('stats').textContent =
    records.length.toLocaleString() + ' exams · ' +
    uSem + ' semesters · ' + uDeg + ' degree types · ' + uProg + ' programs';

  // Auto-expand first level when searching
  const autoExpand = q.length > 0;

  for (const [l1val, l2obj] of Object.entries(tree).sort()) {
    let l1count = 0;
    for (const l2 in l2obj) for (const l3 in l2obj[l2]) l1count += l2obj[l2][l3].size;

    const node1 = makeGroupNode(keys[0], l1val, l1count, 0, 0, autoExpand);
    const children1 = node1.querySelector('.tree-children');

    for (const [l2val, l3obj] of Object.entries(l2obj).sort()) {
      let l2count = 0;
      for (const l3 in l3obj) l2count += l3obj[l3].size;

      const node2 = makeGroupNode(keys[1], l2val, l2count, 1, 1, autoExpand);
      const children2 = node2.querySelector('.tree-children');

      for (const [l3val, examSet] of Object.entries(l3obj).sort()) {
        const exams = [...examSet].sort();
        const node3 = makeGroupNode(keys[2], l3val, exams.length, 2, 2, false);
        const children3 = node3.querySelector('.tree-children');

        for (const exam of exams) {
          children3.appendChild(makeExamRow(exam, 3, q));
        }
        children2.appendChild(node3);
      }
      children1.appendChild(node2);
    }
    root.appendChild(node1);
  }
}

function makeGroupNode(key, val, count, levelIdx, depth, expanded) {
  const levelDef = LEVEL_DEFS[levelOrder[levelIdx]];
  const wrapper = document.createElement('div');
  wrapper.className = 'tree-node';

  const row = document.createElement('div');
  row.className = 'tree-row';

  // indent
  for (let i = 0; i < depth; i++) {
    const sp = document.createElement('span');
    sp.className = 'indent';
    row.appendChild(sp);
  }

  // toggle arrow
  const tog = document.createElement('span');
  tog.className = 'toggle' + (expanded ? ' open' : '');
  tog.innerHTML = expanded
    ? '<svg width="9" height="9" viewBox="0 0 9 9"><path d="M1 2.5l3.5 4 3.5-4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/></svg>'
    : '<svg width="9" height="9" viewBox="0 0 9 9"><path d="M2.5 1l4 3.5-4 3.5" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/></svg>';
  row.appendChild(tog);

  // icon
  const icon = document.createElement('span');
  icon.className = 'row-icon';
  icon.textContent = levelDef.icon;
  row.appendChild(icon);

  // label
  const lbl = document.createElement('span');
  lbl.className = 'row-label l' + levelDef.color;
  lbl.textContent = displayVal(key, val);
  row.appendChild(lbl);

  // count
  const cnt = document.createElement('span');
  cnt.className = 'row-count';
  cnt.textContent = count.toLocaleString();
  row.appendChild(cnt);

  // children container
  const children = document.createElement('div');
  children.className = 'tree-children' + (expanded ? '' : ' collapsed');

  // click to toggle
  row.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = !children.classList.contains('collapsed');
    if (isOpen) {
      children.classList.add('collapsed');
      tog.classList.remove('open');
      tog.innerHTML = '<svg width="9" height="9" viewBox="0 0 9 9"><path d="M2.5 1l4 3.5-4 3.5" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/></svg>';
    } else {
      children.classList.remove('collapsed');
      tog.classList.add('open');
      tog.innerHTML = '<svg width="9" height="9" viewBox="0 0 9 9"><path d="M1 2.5l3.5 4 3.5-4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/></svg>';
    }
    if (selectedRow) selectedRow.classList.remove('selected');
    row.classList.add('selected');
    selectedRow = row;
  });

  wrapper.appendChild(row);
  wrapper.appendChild(children);
  return wrapper;
}

function makeExamRow(exam, depth, q) {
  const row = document.createElement('div');
  row.className = 'exam-row';

  for (let i = 0; i < depth; i++) {
    const sp = document.createElement('span');
    sp.className = 'indent';
    row.appendChild(sp);
  }

  const noTog = document.createElement('span');
  noTog.className = 'no-toggle';
  row.appendChild(noTog);

  const icon = document.createElement('span');
  icon.className = 'row-icon';
  icon.textContent = '📄';
  row.appendChild(icon);

  const lbl = document.createElement('span');
  lbl.className = 'exam-label';
  lbl.innerHTML = hlText(exam, q);
  row.appendChild(lbl);

  return row;
}

// ── SIDEBAR: drag-to-reorder ──
function buildSidebar() {
  const list = document.getElementById('level-list');
  list.innerHTML = '';

  levelOrder.forEach((defIdx, pos) => {
    const def = LEVEL_DEFS[defIdx];
    const item = document.createElement('div');
    item.className = 'level-item';
    item.draggable = true;
    item.dataset.pos = pos;

    item.innerHTML =
      '<span class="drag-handle">&#8942;&#8942;</span>' +
      '<span class="level-num lnum-' + pos + '">' + (pos + 1) + '</span>' +
      '<span class="level-icon lc-' + pos + '">' + def.icon + '</span>' +
      '<span class="level-name lc-' + pos + '">' + def.label + '</span>';

    // Drag events
    item.addEventListener('dragstart', e => {
      e.dataTransfer.setData('text/plain', pos);
      item.classList.add('dragging');
    });
    item.addEventListener('dragend', () => {
      item.classList.remove('dragging');
      document.querySelectorAll('.level-item').forEach(el => el.classList.remove('drag-over'));
    });
    item.addEventListener('dragover', e => {
      e.preventDefault();
      document.querySelectorAll('.level-item').forEach(el => el.classList.remove('drag-over'));
      item.classList.add('drag-over');
    });
    item.addEventListener('dragleave', () => item.classList.remove('drag-over'));
    item.addEventListener('drop', e => {
      e.preventDefault();
      item.classList.remove('drag-over');
      const fromPos = parseInt(e.dataTransfer.getData('text/plain'));
      const toPos = parseInt(item.dataset.pos);
      if (fromPos === toPos) return;

      // Swap in levelOrder
      const newOrder = [...levelOrder];
      const tmp = newOrder[fromPos];
      newOrder[fromPos] = newOrder[toPos];
      newOrder[toPos] = tmp;
      levelOrder = newOrder;

      buildSidebar();
      render();
    });

    list.appendChild(item);
  });
}

// ── EXPAND / COLLAPSE ALL ──
document.getElementById('btn-expand-all').addEventListener('click', () => {
  document.querySelectorAll('.tree-children').forEach(el => el.classList.remove('collapsed'));
  document.querySelectorAll('.toggle').forEach(el => {
    el.classList.add('open');
    el.innerHTML = '<svg width="9" height="9" viewBox="0 0 9 9"><path d="M1 2.5l3.5 4 3.5-4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/></svg>';
  });
});
document.getElementById('btn-collapse-all').addEventListener('click', () => {
  document.querySelectorAll('.tree-children').forEach(el => el.classList.add('collapsed'));
  document.querySelectorAll('.toggle').forEach(el => {
    el.classList.remove('open');
    el.innerHTML = '<svg width="9" height="9" viewBox="0 0 9 9"><path d="M2.5 1l4 3.5-4 3.5" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/></svg>';
  });
});

// ── SEARCH ──
let searchTimer;
document.getElementById('search-box').addEventListener('input', e => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    searchQuery = e.target.value;
    render();
  }, 300);
});

// ── INIT ──
buildSidebar();
render();
</script>
</body>
</html>"""

HTML_FINAL = HTML.replace('DATA_PLACEHOLDER', data_str)

with open('LMU_Course_Tree.html', 'w', encoding='utf-8') as f:
    f.write(HTML_FINAL)

size = os.path.getsize('LMU_Course_Tree.html')
print(f'Written LMU_Course_Tree.html — {size:,} bytes ({size//1024} KB)')
