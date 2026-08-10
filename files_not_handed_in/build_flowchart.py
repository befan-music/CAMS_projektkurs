import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('flowchart_data.json', encoding='utf-8') as f:
    raw_data = json.load(f)
data_str = json.dumps(raw_data, ensure_ascii=False)

HTML = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LMU Exam Flowchart</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Segoe UI", system-ui, sans-serif; background: #0f1117; color: #e2e8f0; min-height: 100vh; }

/* HEADER */
header {
  background: linear-gradient(135deg, #1a1f2e 0%, #12151f 100%);
  border-bottom: 1px solid #2d3748;
  padding: 14px 20px;
  display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
  position: sticky; top: 0; z-index: 100;
  box-shadow: 0 4px 20px rgba(0,0,0,0.5);
}
header h1 { font-size: 1.05rem; font-weight: 700; color: #63b3ed; white-space: nowrap; flex-shrink: 0; }
header h1 span { color: #68d391; }
.controls { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; flex: 1; }
.ctrl-group { display: flex; align-items: center; gap: 5px; }
.ctrl-group label { font-size: 0.73rem; color: #a0aec0; white-space: nowrap; }
select, input[type=text] {
  background: #2d3748; border: 1px solid #4a5568; color: #e2e8f0;
  padding: 4px 9px; border-radius: 6px; font-size: 0.78rem;
  outline: none; cursor: pointer; transition: border-color 0.2s;
}
select:hover, input[type=text]:hover { border-color: #63b3ed; }
select:focus, input[type=text]:focus { border-color: #63b3ed; box-shadow: 0 0 0 2px rgba(99,179,237,0.2); }
input[type=text] { width: 200px; cursor: text; }
.btn {
  background: #2b4a7a; border: 1px solid #3182ce; color: #90cdf4;
  padding: 4px 11px; border-radius: 6px; font-size: 0.76rem;
  cursor: pointer; transition: all 0.2s; white-space: nowrap;
}
.btn:hover { background: #3182ce; color: #fff; }
.btn.danger { background: #742a2a; border-color: #e53e3e; color: #fc8181; }
.btn.danger:hover { background: #e53e3e; color: #fff; }
.stats { margin-left: auto; font-size: 0.7rem; color: #718096; white-space: nowrap; }
.stats strong { color: #a0aec0; }

/* MAIN */
#main { padding: 20px; overflow-x: auto; }
.flow-root { display: flex; flex-direction: column; align-items: center; }

/* NODES */
.node {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 14px; border-radius: 8px; font-weight: 600;
  cursor: pointer; user-select: none; transition: all 0.15s;
}
.node-root {
  background: linear-gradient(135deg, #1a365d, #2c5282);
  border: 2px solid #3182ce; color: #bee3f8;
  font-size: 1rem; padding: 11px 26px; border-radius: 12px;
  box-shadow: 0 4px 20px rgba(49,130,206,0.3);
  cursor: default;
}
.node-semester {
  background: linear-gradient(135deg, #1c2a1e, #276749);
  border: 1.5px solid #38a169; color: #9ae6b4; font-size: 0.85rem;
}
.node-semester:hover { box-shadow: 0 0 12px rgba(56,161,105,0.4); }
.node-degree {
  background: linear-gradient(135deg, #2d1f4e, #553c9a);
  border: 1.5px solid #805ad5; color: #d6bcfa; font-size: 0.8rem;
  max-width: 280px; white-space: normal; text-align: center; line-height: 1.3;
}
.node-degree:hover { box-shadow: 0 0 10px rgba(128,90,213,0.4); }
.node-program {
  background: linear-gradient(135deg, #2c2a1a, #744210);
  border: 1.5px solid #d69e2e; color: #fefcbf; font-size: 0.76rem;
  max-width: 280px; white-space: normal; text-align: center; line-height: 1.3;
}
.node-program:hover { box-shadow: 0 0 10px rgba(214,158,46,0.4); }
.node-exam {
  background: #1a202c; border: 1px solid #2d3748; color: #cbd5e0;
  font-size: 0.71rem; font-weight: 400;
  max-width: 400px; white-space: normal; text-align: left; line-height: 1.4;
  cursor: default; padding: 4px 11px; border-radius: 4px;
}
.node-exam:hover { border-color: #4a5568; background: #232b3a; }

.arrow { font-size: 0.6rem; transition: transform 0.2s; opacity: 0.7; flex-shrink: 0; }
.collapsed .arrow { transform: rotate(-90deg); }
.badge {
  background: rgba(255,255,255,0.1); border-radius: 10px;
  padding: 1px 6px; font-size: 0.65rem; font-weight: 700; opacity: 0.8;
}

/* TREE CONNECTORS */
.connector-v { width: 2px; background: #2d3748; flex-shrink: 0; }
.children-wrap { display: flex; flex-direction: column; align-items: center; }
.h-bar-wrap { display: flex; flex-direction: row; align-items: flex-start; }
.branch-col { display: flex; flex-direction: column; align-items: center; padding: 0 5px; }

/* EXAM LIST */
.exam-list {
  display: flex; flex-direction: column; gap: 2px;
  align-items: flex-start; max-height: 380px;
  overflow-y: auto; width: 420px; padding: 0 2px;
}
.exam-list::-webkit-scrollbar { width: 4px; }
.exam-list::-webkit-scrollbar-track { background: #1a202c; }
.exam-list::-webkit-scrollbar-thumb { background: #4a5568; border-radius: 2px; }

.hidden { display: none !important; }
.highlight-exam { background: #1e3a1e !important; border-color: #68d391 !important; color: #c6f6d5 !important; }
mark { background: #f6e05e; color: #1a202c; border-radius: 2px; padding: 0 1px; }

#empty-msg { text-align: center; padding: 60px; color: #4a5568; font-size: 1rem; }

/* LEGEND */
.legend {
  display: flex; gap: 12px; align-items: center; flex-wrap: wrap;
  padding: 8px 20px; background: #0d1117; border-bottom: 1px solid #1a202c;
  font-size: 0.68rem;
}
.leg-item { display: flex; align-items: center; gap: 5px; }
.leg-dot { width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; }
.leg-sem { background: #38a169; }
.leg-deg { background: #805ad5; }
.leg-prog { background: #d69e2e; }
.leg-exam { background: #4a5568; }
</style>
</head>
<body>

<header>
  <h1>LMU <span>Exam Explorer</span></h1>
  <div class="controls">
    <div class="ctrl-group">
      <label>Hierarchy</label>
      <select id="sel-hierarchy">
        <option value="sem-deg-prog">Semester &rarr; Degree &rarr; Program</option>
        <option value="deg-sem-prog">Degree &rarr; Semester &rarr; Program</option>
        <option value="deg-prog-sem">Degree &rarr; Program &rarr; Semester</option>
        <option value="prog-deg-sem">Program &rarr; Degree &rarr; Semester</option>
      </select>
    </div>
    <div class="ctrl-group">
      <label>Semester</label>
      <select id="sel-semester">
        <option value="all">All semesters</option>
        <option value="20242">20242 &ndash; WS 2024/25</option>
        <option value="20251">20251 &ndash; SS 2025</option>
        <option value="20252">20252 &ndash; WS 2025/26</option>
      </select>
    </div>
    <div class="ctrl-group">
      <label>Degree type</label>
      <select id="sel-degree"><option value="all">All degrees</option></select>
    </div>
    <div class="ctrl-group">
      <label>Search</label>
      <input type="text" id="search-input" placeholder="exam or program name...">
    </div>
    <button class="btn" id="btn-expand">Expand All</button>
    <button class="btn danger" id="btn-collapse">Collapse All</button>
  </div>
  <div class="stats" id="stats-bar">Loading&hellip;</div>
</header>

<div class="legend">
  <span style="color:#718096; font-weight:600">Color guide:</span>
  <span class="leg-item"><span class="leg-dot leg-sem"></span> Semester</span>
  <span class="leg-item"><span class="leg-dot leg-deg"></span> Degree type</span>
  <span class="leg-item"><span class="leg-dot leg-prog"></span> Program / Subject</span>
  <span class="leg-item"><span class="leg-dot leg-exam"></span> Individual exam</span>
  <span style="margin-left:8px; color:#4a5568">Click any node to expand/collapse &bull; Search highlights matching exams</span>
</div>

<div id="main">
  <div id="flowchart" class="flow-root"></div>
  <div id="empty-msg" class="hidden">No exams match the current filters.</div>
</div>

<script>
const RAW_DATA = DATA_PLACEHOLDER;

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

// Populate degree filter
const ALL_DEGREES = [...new Set(ALL_RECORDS.map(r => r.deg))].sort();
const selDeg = document.getElementById('sel-degree');
ALL_DEGREES.forEach(d => {
  const opt = document.createElement('option');
  opt.value = d; opt.textContent = d;
  selDeg.appendChild(opt);
});

let currentHierarchy = 'sem-deg-prog';
let currentSemFilter = 'all';
let currentDegFilter = 'all';
let currentSearch = '';

function getFiltered() {
  const sq = currentSearch.toLowerCase().trim();
  return ALL_RECORDS.filter(r => {
    if (currentSemFilter !== 'all' && r.sem !== currentSemFilter) return false;
    if (currentDegFilter !== 'all' && r.deg !== currentDegFilter) return false;
    if (sq && !r.exam.toLowerCase().includes(sq) && !r.prog.toLowerCase().includes(sq)) return false;
    return true;
  });
}

function buildTree(records, hierarchy) {
  const levels = hierarchy.split('-');
  const tree = {};
  for (const r of records) {
    const l1 = r[levels[0]], l2 = r[levels[1]], l3 = r[levels[2]];
    if (!tree[l1]) tree[l1] = {};
    if (!tree[l1][l2]) tree[l1][l2] = {};
    if (!tree[l1][l2][l3]) tree[l1][l2][l3] = new Set();
    tree[l1][l2][l3].add(r.exam);
  }
  return tree;
}

const SEM_LABELS = {
  '20242': 'WS 2024/25 (20242)',
  '20251': 'SS 2025 (20251)',
  '20252': 'WS 2025/26 (20252)'
};
function nodeLabel(type, val) {
  return type === 'sem' ? (SEM_LABELS[val] || val) : val;
}

function escHtml(s) {
  return String(s)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}
function hlText(text, query) {
  if (!query) return escHtml(text);
  const lower = text.toLowerCase();
  const idx = lower.indexOf(query.toLowerCase());
  if (idx === -1) return escHtml(text);
  return escHtml(text.slice(0,idx))
    + '<mark>' + escHtml(text.slice(idx, idx+query.length)) + '</mark>'
    + hlText(text.slice(idx+query.length), query);
}

function vLine(h) {
  const d = document.createElement('div');
  d.className = 'connector-v';
  d.style.height = h + 'px';
  return d;
}

function makeNode(cls, labelHtml, count, collapsible) {
  const d = document.createElement('div');
  d.className = 'node ' + cls;
  if (collapsible) {
    const arr = document.createElement('span');
    arr.className = 'arrow';
    arr.textContent = '▼';
    d.appendChild(arr);
  }
  const txt = document.createElement('span');
  txt.innerHTML = labelHtml;
  d.appendChild(txt);
  if (count !== null) {
    const b = document.createElement('span');
    b.className = 'badge';
    b.textContent = count.toLocaleString();
    d.appendChild(b);
  }
  return d;
}

function toggle(nodeEl, childWrap) {
  if (childWrap.classList.contains('hidden')) {
    childWrap.classList.remove('hidden');
    nodeEl.classList.remove('collapsed');
  } else {
    childWrap.classList.add('hidden');
    nodeEl.classList.add('collapsed');
  }
}

function levelClass(type) {
  if (type === 'sem') return 'node-semester';
  if (type === 'deg') return 'node-degree';
  return 'node-program';
}

function render() {
  const records = getFiltered();
  const levels = currentHierarchy.split('-');
  const tree = buildTree(records, currentHierarchy);
  const fc = document.getElementById('flowchart');
  const emptyMsg = document.getElementById('empty-msg');
  fc.innerHTML = '';

  if (records.length === 0) {
    emptyMsg.classList.remove('hidden');
    document.getElementById('stats-bar').innerHTML = '<strong>0</strong> exams match filters';
    return;
  }
  emptyMsg.classList.add('hidden');

  const sq = currentSearch.toLowerCase().trim();
  const uDeg = new Set(records.map(r=>r.deg)).size;
  const uProg = new Set(records.map(r=>r.prog)).size;
  const uSem = new Set(records.map(r=>r.sem)).size;
  document.getElementById('stats-bar').innerHTML =
    '<strong>' + records.length.toLocaleString() + '</strong> exams &middot; ' +
    '<strong>' + uDeg + '</strong> degree types &middot; ' +
    '<strong>' + uProg + '</strong> programs &middot; ' +
    '<strong>' + uSem + '</strong> semesters';

  // ROOT
  const root = makeNode('node-root', '&#127891; LMU Examinations', records.length, false);
  fc.appendChild(root);
  fc.appendChild(vLine(20));

  const l1keys = Object.keys(tree).sort();
  const l1row = document.createElement('div');
  l1row.className = 'h-bar-wrap';

  for (const l1 of l1keys) {
    const col1 = document.createElement('div');
    col1.className = 'branch-col';
    col1.appendChild(vLine(16));

    const l2obj = tree[l1];
    let l1Count = 0;
    for (const l2 in l2obj) for (const l3 in l2obj[l2]) l1Count += l2obj[l2][l3].size;

    const n1 = makeNode(levelClass(levels[0]), escHtml(nodeLabel(levels[0], l1)), l1Count, true);
    const cw1 = document.createElement('div');
    cw1.className = 'children-wrap';
    n1.addEventListener('click', () => toggle(n1, cw1));
    col1.appendChild(n1);
    col1.appendChild(vLine(12));
    col1.appendChild(cw1);

    const l2keys = Object.keys(l2obj).sort();
    const l2row = document.createElement('div');
    l2row.className = 'h-bar-wrap';

    for (const l2 of l2keys) {
      const col2 = document.createElement('div');
      col2.className = 'branch-col';
      col2.appendChild(vLine(12));

      const l3obj = l2obj[l2];
      let l2Count = 0;
      for (const l3 in l3obj) l2Count += l3obj[l3].size;

      const n2 = makeNode(levelClass(levels[1]), escHtml(nodeLabel(levels[1], l2)), l2Count, true);
      const cw2 = document.createElement('div');
      cw2.className = 'children-wrap';
      n2.addEventListener('click', () => toggle(n2, cw2));
      col2.appendChild(n2);
      col2.appendChild(vLine(10));
      col2.appendChild(cw2);

      const l3keys = Object.keys(l3obj).sort();
      const l3row = document.createElement('div');
      l3row.className = 'h-bar-wrap';

      for (const l3 of l3keys) {
        const col3 = document.createElement('div');
        col3.className = 'branch-col';
        col3.appendChild(vLine(10));

        const exams = [...l3obj[l3]].sort();
        const n3 = makeNode(levelClass(levels[2]), escHtml(nodeLabel(levels[2], l3)), exams.length, true);
        const cw3 = document.createElement('div');
        cw3.className = 'children-wrap hidden';
        n3.addEventListener('click', () => toggle(n3, cw3));
        col3.appendChild(n3);

        const examList = document.createElement('div');
        examList.className = 'exam-list';
        for (const exam of exams) {
          const eNode = document.createElement('div');
          eNode.className = 'node node-exam';
          eNode.innerHTML = hlText(exam, sq);
          if (sq && exam.toLowerCase().includes(sq)) eNode.classList.add('highlight-exam');
          examList.appendChild(eNode);
        }
        cw3.appendChild(examList);
        col3.appendChild(cw3);
        l3row.appendChild(col3);
      }
      cw2.appendChild(l3row);
      l2row.appendChild(col2);
    }
    cw1.appendChild(l2row);
    l1row.appendChild(col1);
  }
  fc.appendChild(l1row);
}

document.getElementById('btn-expand').addEventListener('click', () => {
  document.querySelectorAll('.children-wrap').forEach(el => el.classList.remove('hidden'));
  document.querySelectorAll('.node').forEach(el => el.classList.remove('collapsed'));
});
document.getElementById('btn-collapse').addEventListener('click', () => {
  document.querySelectorAll('.children-wrap').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.node').forEach(el => el.classList.add('collapsed'));
});
document.getElementById('sel-hierarchy').addEventListener('change', e => { currentHierarchy = e.target.value; render(); });
document.getElementById('sel-semester').addEventListener('change', e => { currentSemFilter = e.target.value; render(); });
document.getElementById('sel-degree').addEventListener('change', e => { currentDegFilter = e.target.value; render(); });

let searchTimer;
document.getElementById('search-input').addEventListener('input', e => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => { currentSearch = e.target.value; render(); }, 350);
});

render();
</script>
</body>
</html>"""

HTML_FINAL = HTML.replace('DATA_PLACEHOLDER', data_str)

with open('LMU_Exam_Flowchart.html', 'w', encoding='utf-8') as f:
    f.write(HTML_FINAL)

size = os.path.getsize('LMU_Exam_Flowchart.html')
print(f'Written LMU_Exam_Flowchart.html — {size:,} bytes ({size//1024} KB)')
