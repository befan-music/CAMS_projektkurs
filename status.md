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
4. Also store up to 50 sample row indices per cluster for the drill-down preview

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
- **Label**: the last filter column's value is shown inside the bubble if the bubble is large enough
- **Colour**: cycles through a 17-colour palette, one colour per cluster in sorted order
- **Tooltip**: hover shows all filter values for that cluster + exact count + share of total

---

## List view

Clusters are shown as rows, sorted by count (or alphabetically):

- A proportional bar shows each cluster's size relative to the largest cluster
- The percentage shown is share of the **total row count** (not just the largest cluster)
- Click any row to expand it and see up to 50 sample values from a non-filter column (defaults to column index 2 = the title/name column if available)

---

## Filter chain & reordering

- Active filters are shown as numbered chips in the left panel
- Chips can be **dragged** to reorder — changing order does not change which clusters exist, but changes how the composite key is built (which affects the alpha sort order and the label shown in bubbles/list)
- Removing a filter immediately re-clusters using only the remaining filters
- The column picker shows how many unique values each column has, helping you predict cluster count before adding it
