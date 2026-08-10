python -m http.server 8080 --directory "c:\Users\einos\Documents\LMU Master\2. Semester\Projektkurs\Raw input"; Start-Process "http://localhost:8080/LMU_Cluster_Explorer.html"

# Cluster Explorer — How It Works

## What the tool does

The Cluster Explorer is a browser-based data analysis tool that loads any CSV file and lets you group its rows into "clusters" based on column values you choose. You build up a chain of filters, and the tool instantly counts how many rows share each unique combination — showing the result either as sized bubbles or a sorted list.

---

## Data loading & parsing

When you drop or select a CSV file, the tool reads it entirely in the browser (no server involved). A character-by-character RFC-4180 state machine parser processes the raw text:

- It tracks whether the current character is inside a quoted field (`"..."`)
- Inside quotes, newlines and delimiters are treated as plain characters, not row/cell boundaries — this correctly handles multi-line cell values
- A row boundary is only recognised when a newline appears *outside* quotes
- The delimiter is auto-detected from the first line (counts semicolons, commas, tabs, pipes — whichever appears most wins)

After parsing, each column's values are **vocabulary-encoded**: every unique string value is replaced with an integer index, and a lookup table (vocab array) maps each index back to its string. This compresses the data significantly and makes grouping very fast.

---

## Cluster logic

A **cluster** is one unique combination of values across the selected filter columns.

The algorithm:
1. For each row, read the integer vocab-index for every active filter column
2. Join those indices with `|` to form a composite key (e.g. `"2|5|14"`)
3. Count how many rows produce the same key → that count is the cluster's size
4. Store all row indices per cluster (used for drill-down analysis)

**Examples:**
- 1 filter = `Semester` → 3 clusters (one per unique semester value)
- 1 filter = `PORGNR` → 83,276 clusters (every row is unique)
- 2 filters = `Semester` + `AbschlussTxT` → one cluster per existing Semester/Degree combination
- 17 filters = every column → one cluster per row (83,276)

The number of clusters equals the number of **distinct value combinations** that actually exist in the data — not the theoretical maximum product of unique values per column.

---

## Subset pre-filter

Before clustering, you can restrict which rows are considered at all using the **Subset** selector:

- Choose one column and enter a match value
- Only rows where that column's value **contains** the typed string (case-insensitive) are passed to the cluster engine
- The stats bar updates to show how many rows are in the active subset
- All cluster counts and bubble sizes reflect only the subset, not the full dataset

---

## Bubble view

Each cluster is drawn as a circle on an SVG canvas:

- **Size**: radius is proportional to `sqrt(count / maxCount)` — area therefore scales with count, which is perceptually more accurate than linear radius scaling
- **Position**: row-packed layout (left to right, wrapping to next row when the SVG width is exceeded)
- **Label**: the current level's value is shown inside the bubble if the bubble is large enough
- **Colour**: cycles through a 17-colour palette, one colour per cluster in sorted order
- **Tooltip**: hover shows the filter value for that level + row count + share of total

### Hierarchical drill-in (multiple filters)

When more than one filter is active, the bubble view becomes a **zoomable hierarchy**:

- The top level shows one bubble per unique value of the *first* filter — its size reflects the total row count across all sub-combinations
- A dashed inner ring and a "N sub" badge indicate the bubble contains sub-clusters
- The tooltip shows "click to zoom in →"
- **Clicking a bubble** replaces the canvas with the sub-clusters at the next filter level (grouped by the second filter value, then third, etc.)
- A **breadcrumb bar** appears above the canvas showing the current drill path (e.g. `All › Speaking Skills 1 › Bachelor`); clicking any crumb navigates back up to that level
- At the deepest filter level (leaf), bubbles are no longer clickable for drill-in — use the **ⓘ button** instead
- The **ⓘ button** (top-right of every bubble) opens the within-cluster analysis panel at any level

---

## List view

When only one filter is active, clusters are shown as a flat sorted list. With two or more filters active, the list becomes a **collapsible hierarchy**:

- Top level shows one row per unique value of the first filter, with the total row count across all its sub-combinations
- Clicking a top-level row expands it to show the second-filter breakdown as indented child rows
- Child rows expand further to show the third-filter level, and so on — recursively until the last filter
- Each row at every level has an **ⓘ button** that opens the within-cluster analysis panel for that node

In all modes:
- A proportional bar shows each entry's size relative to the largest entry at that level
- The percentage shown is share of the **total row count**
- Sorting (by count or alphabetically) applies at every level independently

---

## Within-cluster analysis (ⓘ panel)

Clicking the **ⓘ button** on any bubble or list row opens a slide-in panel that answers: *"Given these rows share the same combination — what internal differences explain why they appear multiple times?"*

The panel shows every column not used as a filter, broken down by value frequency:

- **Varying columns** (2+ unique values) appear first, sorted by number of distinct values descending, each with a proportional mini-bar chart and percentage
- **Uniform columns** (same value for all rows in the cluster) are shown collapsed below — they're definitionally uninteresting for explaining variation
- Filter columns themselves are listed as uniform by definition
- A **diversity indicator** (● dots, 1–5) summarises how many distinct values each column has at a glance

---

## Filter chain & reordering

- Active filters are shown as numbered chips in the left panel
- Chips can be **dragged** to reorder — changing order does not change which clusters exist, but changes the hierarchy structure in both bubble drill-in and list view (first filter = top level)
- Removing a filter immediately re-clusters using only the remaining filters and resets the bubble drill stack to the top level
- The column picker shows how many unique values each column has, helping you predict cluster count before adding it

---

## inLAB column — special treatment in Tiefenanalyse

The dataset has a column named `inLAB` (also matched as `inlab`, case-insensitive) that records whether a student actually attended the exam they were registered for (`1` / `TRUE` = attended, `0` / anything else = did not attend).

### What is special about it

All other columns are shown in the Tiefenanalyse panel as generic value-frequency breakdowns. The `inLAB` column gets a **dedicated summary card** prepended at the top of the breakdown grid because it answers a binary question — attended vs. not attended — that is more meaningful as a split bar than as a generic sorted value list.

### How it works

When the Tiefenanalyse panel opens for any cluster or breakdown node, the code:

1. Looks for a column whose header matches `inlab` (case-insensitive) or exactly `inLAB`
2. If found, iterates over every row in the cluster (`item.allRows`) and classifies each row as *attended* (`val === '1'` or `val.toUpperCase() === 'TRUE'`) or *not attended* (everything else)
3. Renders a special full-width card (spans all grid columns via `gridColumn: '1 / -1'`) with:
   - A green/red segmented bar showing the attended vs. not-attended split proportionally
   - Two legend rows: `1 (teilgenommen)` in green and `0 (nicht teilgenommen)` in red, each with absolute count and percentage
   - A highlighted blue border and subtle green background to visually distinguish it from generic column cards
4. This card is **prepended** before the generic column analysis cards — it is always first

The generic column analysis that follows still includes `inLAB` as one of the regular columns (it is not excluded), so users can also see the raw value distribution there if needed.

### CSV file used

The default CSV that auto-loads when the tool is opened via HTTP server is `allePolyvalenzen_inLabSpalte.csv` — the version of the dataset that includes the `inLAB` column. The tool also works with any other CSV (the inLAB card is only shown when the column is present).

---

## Polyvalenzen page (`polyvalenzen.html`)

A companion analysis page that answers pre-defined "polyvalence" questions about the exam data. Opened via the **⬡ Zentrale Erkenntnisse** button in the topbar of the main tool.

### Data passing

When the button is clicked, the main tool serialises `{ filename, delimiter, headers }` into `sessionStorage` under the key `polyvData`. The polyvalenzen page reads this on load and fetches the CSV file directly from the running HTTP server (same origin) using the stored filename, then parses it independently using the same RFC-4180 parser.

### Structure

The page has two sections:

**1. Q & A** — three ranked-list cards, each answering one question by scanning all rows directly:
- **Q1**: Which exam appears in the most distinct degree programmes? (counts distinct `StudiengangTxT` per `Veranstaltungstitel`)
- **Q2**: Which degree programmes share the most exams with at least one other programme? (counts exams that appear in >1 Studiengang)
- **Q3**: Which exam spans the most degree types (Abschlussarten)? (counts distinct `AbschlussTxT` per exam)

Each card shows results as a ranked list with proportional bars. Clicking a result row focuses the main tool tab and pre-applies a subset filter for that value.

**2. Predefined Visualizations** — one card: **Polyvalenzen** (Venn diagram + radial clustering).

### Subset filter (polyvalenzen.html)

A subset selector bar at the top of the page lets the user restrict which rows all Q1/Q2/Q3 computations and the visualisation use. The active subset is applied via `getActiveRows()`, which all compute functions call instead of accessing the raw `rows` array directly. The Tiefenanalyse detail table also respects the active subset.

### Venn diagram

Groups rows by a user-selected dimension (e.g. `StudiengangTxT`) and computes for each group: which exam titles appear only in that group (unique) vs. in multiple groups (polyvalent). Circles are drawn in an SVG canvas with radii proportional to total exam count. Clicking a circle opens a right-panel detail showing shared-exam overlap with every other group plus collapsible unique/polyvalent exam lists. Clicking an exam title opens a full data-table overlay of all matching CSV rows.

### Radial clustering (V1)

Draws a radial dendrogram where:
- **Outer arcs**: one per unique value of a user-selected dimension (outer ring); arc width = number of distinct exam titles in that group
- **Inner circles**: one per unique exam title; radius = number of outer groups the exam appears in
- **Connecting lines**: link each exam circle to every outer arc it belongs to
- **Toggle**: *polyvalente Prüfungen* mode shows only exams that appear in ≥2 outer groups; *Einzigartige Prüfungen* mode shows only exams that appear in exactly 1 outer group

---

## Full German translation

Both `cluster_explorer.html` and `polyvalenzen.html` have been fully translated to German. All user-visible strings — HTML labels, JS-generated text, button titles, tooltips, placeholders, alert messages, and data-value fallbacks — are in German. Key translated areas:

- **cluster_explorer.html**: drop-zone, stats bar, subset controls, filter chips, view buttons, sort options, bubble tooltips, list view, treemap tooltips, matrix stats, Tiefenanalyse panel section headers (`Variable Spalten`, `Filterspalten`, `Einheitliche Spalten`), breakdown view, Venn panel (badges, overlap section, exam sections), inLAB card labels, empty-value fallback `(leer)`, breadcrumb root `Alle`, cluster count, error alerts
- **polyvalenzen.html**: all Q card titles and subtitles, show/hide buttons, computing indicator, subset controls, section labels for unique/polyvalent exams, score labels, row counts, load-more buttons, radial chart legend, info panel text, Venn detail panel

---

## Venn diagram — detailed algorithm (`polyvalenzen.html`)

The Venn diagram is technically a **bubble network diagram**, not a geometrically accurate Venn diagram. The physical overlap of circles carries no meaning — it is a side-effect of ring layout and circle sizes. Only circle sizes and connecting lines are data-driven.

### What each circle represents

Each circle is one unique value of the currently selected grouping column (`poly-group-sel`), which is populated from all columns in the CSV. Default groupings are `StudiengangTxT` (degree programme) and `AbschlussTxT` (degree type).

### How polyvalence is measured

The algorithm runs in two passes over `getActiveRows()` (the active subset):

**Pass 1 — build forward and reverse indexes:**
- `groupMap`: groupValue → Map of `(examTitle → rowCount)` — all exam titles that appear in each group
- `examGroups`: examTitle → Set of groupValues — which groups each exam title belongs to

**Pass 2 — classify every exam inside each group:**
- If `examGroups.get(title).size === 1` → **einzigartig** (unique to this group)
- If `examGroups.get(title).size > 1` → **polyvalent** (shared with ≥1 other group)

The unit of comparison is the `Veranstaltungstitel` column (exact string match). No fuzzy matching, no credit-hour or semester comparison is performed.

### Card bar

Each group card shows a horizontal bar split into:
- **Grey segment** = share of unique exams (`uniqueExams.length / total`)
- **Purple segment** = share of polyvalent exams (`polyExams.length / total`)
- Counts are shown as `Xu einzigartig` and `Xp polyvalent`

### Circle sizing

```
radius = MIN_R + (MAX_R − MIN_R) × √(groupExamCount / maxGroupExamCount)
```
Square-root scaling is used so large groups don't visually dominate.

### Circle positioning

All circles are placed on a fixed ring, equally spaced by index:
```
angle = (2π × i / n) − π/2
x = centerX + ringRadius × cos(angle)
y = centerY + ringRadius × sin(angle)
```
Position on the ring is arbitrary (data insertion order). The physical overlap of neighbouring circles is a coincidence of being adjacent on the ring with large radii — it does not represent the amount of shared exams.

### Connecting lines (the meaningful signal)

Between every pair of groups that share ≥1 exam, a line is drawn:
```
lineThickness = 7 × (sharedExams / maxSharedExams)
lineOpacity   = 0.04 + 0.18 × (sharedExams / maxSharedExams)
```
Thicker and darker = more exams shared between those two groups. This is the only geometrically meaningful element in the diagram.

### Focus mode (click a circle)

Clicking a circle enters focus mode: the selected circle moves to the left, all connected circles are arranged in columns to the right (sorted by overlap count descending), and unconnected groups are hidden off-screen. The right panel shows the detail breakdown for the selected group vs. every other group.

### Overlap matrix (`_pvVennOverlaps`)

A full n×n integer matrix is pre-computed at render time: `overlaps[i][j]` = number of exam titles shared between group i and group j. This matrix drives both the line rendering and the focus-mode panel.

---

## polyvalenzen.html — UI structure changes

### Layout

- **Polyvalenzen card**: title ("Polyvalenzen") sits above the horizontal border line; below the line is the "Cards" button and the card grid. This matches the Q&A card layout.
- **Q&A section**: wrapped in a card with the same width and border style as the Polyvalenzen card. Has its own "Q & A" title above the border line.
- Both cards sit inside `#main` with consistent `margin: 20px 20px 0` spacing.

### Info button (`i`)

A circular `i` button appears in the topbar of both `polyvalenzen.html` and `cluster_explorer.html`. Clicking it toggles an explanatory panel that describes the tool's methodology in plain language. The panel slides in below the topbar and can be dismissed by clicking the button again.

### Third card: "Theoretisch belegbar vs. Tatsächlich belegte Prüfungen"

Sits between the Polyvalenzen card and the Q&A section. Collapsed by default (click the header to expand). Shows, for each group (Studiengang or Abschluss), a stacked bar comparing offered vs. taken exams.

**Controls:**
- **Gruppieren**: Studiengang / Abschluss dropdown
- **Alle / Nur Polyvalente / Nur Einzigartige**: filter which exams are counted
- **↓ Belegt / ↑ Belegt**: sort descending or ascending by taken count
- **Absolut / Prozent**: toggle label display mode

**Bar logic:**
- Each group row has a single bar. The bar track (purple, always full width) represents the number of exams offered in that group. The green fill represents the subset actually taken (`inLAB === '1'`). Bar width is always `taken / offered × 100%` regardless of display mode — the green bar is always a geometrically correct fraction of the purple track.
- In **Absolut** mode: label shows `X belegt` with grey secondary `Y%`
- In **Prozent** mode: label shows `Y%` with grey secondary `X`

**Filtering (Polyvalente / Einzigartige):**
- Only exams that were offered inside the group AND match the filter type are counted. "Nur Polyvalente" counts exams appearing in >1 group; "Nur Einzigartige" counts exams appearing in exactly 1 group. Filter is applied independently per row before computing offered/taken counts.

### inLAB column fix (`cluster_explorer.html`)

The inLAB card in the Tiefenanalyse panel previously tested for `val === 'TRUE'` (string), causing 100% "not taken" display. Fixed to `val === '1' || val.toUpperCase() === 'TRUE'` because the CSV stores `1`/`0` as strings, not `TRUE`/`FALSE`.

### List view background fix (`cluster_explorer.html`)

Second-layer rows in list view were hardcoded to `background: #0a0c12` (black). Fixed to `background: var(--sidebar)` so they match the beige design system.

---

## Radial clustering — removed

The radial chart (V1, described above) has been fully removed from `polyvalenzen.html`. Both its HTML/CSS and all associated JavaScript (state variables, event listeners, helper functions, `renderRadial()`) were deleted. The Polyvalenzen card now opens directly to the card grid view.

---

## `polyvalenz_metriken.html` — new page

A standalone analysis page (`polyvalenz_metriken.html`) accessible via the **⬡ Metriken** button in the `polyvalenzen.html` topbar. Loads the same default CSV (`allePolyvalenzen_inLabSpalte.csv`) independently. Navigation links back to both `polyvalenzen.html` and `cluster_explorer.html`.

Four collapsed analysis cards:

### Card 1 — Globale Vernetzungskennzahl

Computes three aggregate metrics across all group pairs (grouped by Studiengang or Abschluss):

- **Mittlerer Sørensen-Dice-Koeffizient**: `mean(2|A∩B| / (|A|+|B|))` over all pairs — 0 = no pair shares any exam, 1 = all groups identical
- **Netzwerkdichte**: fraction of all possible pairs that share ≥1 exam (`connectedPairs / (n(n−1)/2)`)
- **Polyvalente Prüfungstitel**: count and percentage of exam titles that appear in >1 group

Displayed as four stat tiles. Grouping selector (Studiengang / Abschluss) re-triggers computation on change.

### Card 2 — Paarweise Ähnlichkeit (Sørensen-Dice)

For every pair of groups that share ≥1 exam, computes `Dice(A,B) = 2|A∩B| / (|A|+|B|)`.

**Two views, toggled by "Liste" / "Heatmap" buttons:**

**Liste**: ranked list of pairs sorted by Dice score descending. Shows pair names, a proportional bar, Dice percentage, and shared exam count. "Top 50" / "Alle" toggle limits rows shown.

**Heatmap**: full n×n colour-coded matrix. Rows and columns are groups sorted by total exam count descending (largest group top-left). Cell colour interpolates from cream (0% Dice) to deep purple (100% Dice). Cells ≥10% Dice show the percentage as text (white on dark cells, dark on light). Diagonal cells (self-similarity) are grey. Hover tooltip shows `Group A ↔ Group B: X% Dice (Y gemeinsam)`. A colour-scale legend strip appears below the table. The matrix is scrollable.

Groups are pre-sorted by size descending when `buildPairwise()` runs, and cached in `_pairGroupsCache` so the heatmap can reuse them without recomputing.

### Card 3 — Spalten-Fragmentierungsanalyse

Answers: *which column, when added to the base key, causes the most exam groups to split apart?*

**Base key**: `Abschluss + StudiengangTxT + Prüfungstext` — the minimum set of columns needed to identify an exam group. Produces a baseline group count (`baseN`).

For every other column in the CSV, an extended key is formed (`baseKey + '|' + columnValue`) and the resulting group count (`extN`) is measured.

**Fragmentation score** = `(extN − baseN) / baseN` — how many additional groups that column creates, as a fraction of the baseline. Score 0 = column adds no information; high score = column splits many otherwise-identical exam groups.

Results shown as a ranked bar list sorted by score descending. Interpretation: a high-scoring column is a "hidden differentiator" — omitting it makes exams that are actually different look the same.

### Card 4 — Prädiktoren für Polyvalenz

Answers: *which column values are disproportionately associated with polyvalent exams?*

For each column × value combination:
1. Find all exam titles (by `Veranstaltungstitel`) that have that column value as their dominant value (mode across all rows for that exam)
2. Of those exam titles, count how many appear in >1 group (polyvalent)
3. **Polyvalenzrate** = `polyCount / totalWithValue`

Results sorted by polyvalenzrate descending. A minimum-N filter (5 / 10 / 20 / 50 exams) excludes rare values. A column filter dropdown restricts to one column at a time.

Colour coding: green ≥70%, yellow 40–69%, red <40%. Displayed as a ranked list with bars, percentage, and `poly / total` count.

Controls: Gruppierspalte (Studiengang / Abschluss), Mind. Prüfungen (min-N), Spalten filter.
