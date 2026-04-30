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
