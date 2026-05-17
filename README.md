# BibFlow

**BibFlow** is a Streamlit research workflow assistant for researchers who work with **BibTeX**, **Overleaf**, journal-ranking lists, and literature-review notes.

It started as a lightweight DOI-to-BibTeX cleaner. Version 2 expands it into a small research library manager: users can clean references, merge BibTeX files, check reference quality, match journals against uploaded ranking files, annotate papers, restore previous annotations, and export literature-review summaries.

> Current public-demo target: **Version 2.1A — README + Public Demo Documentation**

---

## Why BibFlow?

Academic writing often involves repetitive reference work:

- copying BibTeX from Google Scholar or publisher pages,
- cleaning noisy BibTeX fields before using Overleaf,
- checking duplicate DOI entries,
- improving citation keys,
- identifying journal rankings for literature-review strategy,
- tracking which papers have been read, cited, or marked as important.

BibFlow combines these tasks in one simple Streamlit app.

---

## Main Features

### 1. DOI to BibTeX

Generate clean BibTeX entries from a DOI.

- Normalises DOI input.
- Fetches BibTeX metadata.
- Suggests clean citation keys.
- Allows manual citation-key editing.
- Exports Overleaf-ready `.bib` entries.

### 2. Batch DOI Processing + Clean Merge

Paste multiple DOI values and create a combined BibTeX file.

- Removes duplicate DOI inputs.
- Skips DOI entries already present in an uploaded `.bib` file.
- Generates unique citation keys.
- Appends only new entries to the existing BibTeX file.

### 3. Title-Based Paper Search

Search Crossref metadata by paper title, optionally with author information.

- Useful when you know a paper title but not the DOI.
- Lets you inspect candidate metadata.
- Fetches BibTeX from the selected DOI result.

### 4. BibTeX Cleaner

Upload or paste raw BibTeX and clean it for Overleaf.

- Cleans titles, journals, DOI fields, and author spacing.
- Removes noisy fields such as `abstract`, `file`, `timestamp`, and `urldate`.
- Regenerates citation keys using selected key styles.
- Supports export presets:
  - Overleaf Clean,
  - Minimal Citation,
  - DOI + URL Friendly,
  - Full Metadata.

### 5. Reference Quality Report

Check whether a BibTeX file is ready for academic writing.

The report detects common issues such as:

- missing author,
- missing title,
- missing year,
- missing journal or booktitle,
- missing DOI,
- duplicate citation keys,
- duplicate DOI values,
- possible duplicate titles,
- weak or very long citation keys,
- noisy metadata fields.

### 6. Research Library Explorer

Upload a `.bib` file and turn it into a searchable library table.

The table includes:

- citation key,
- title,
- authors,
- year,
- journal or venue,
- DOI,
- ISSN,
- journal-ranking fields,
- annotation fields.

You can search and filter by:

- title,
- author,
- journal,
- year,
- DOI,
- ISSN,
- citation key,
- AJG rating,
- FT50 flag,
- reading status,
- paper type,
- priority,
- citation-candidate flag,
- important-paper flag.

### 7. Journal Ranking Matching

BibFlow can match references against a user-supplied journal-ranking file.

Supported ranking-style fields include:

- AJG / ABS rating,
- AJG field,
- AJG source year,
- FT50 flag,
- journal aliases,
- ISSN matching.

Matching priority:

1. ISSN exact match,
2. FT50 ISSN exact match,
3. exact normalised journal-name match,
4. exact alias-normalised journal-name match,
5. conservative fuzzy journal-name match.

> Important: BibFlow does **not** redistribute the full official AJG/ABS list. For public deployment, users should upload their own authorised ranking file or use a small demo ranking file.

### 8. Research Annotations

BibFlow supports literature-review annotation fields:

- Reading Status,
- Paper Type,
- Priority,
- Research Tags,
- Citation Candidate,
- Important,
- Notes.

These fields are editable directly in the Research Library table.

### 9. Restore Previous Annotations

Users can upload a previously exported annotated CSV/XLSX file and restore their notes, tags, reading status, and flags.

This allows users to continue their literature-review workflow across sessions.

### 10. Research Library Dashboard + Report

BibFlow summarises the research library with:

- AJG rating distribution,
- FT50 count,
- ranking match summary,
- reading progress,
- priority distribution,
- paper type distribution,
- top journals,
- research tag frequency,
- core papers,
- citation candidates,
- important papers.

Users can export:

- full annotated research library CSV,
- filtered annotated research library CSV,
- annotations-only CSV,
- unmatched journals CSV,
- dashboard summary tables CSV,
- literature-review Markdown report.

---

## App Tabs

BibFlow currently contains six main tabs:

```text
Single DOI
Batch + Merge
Title Search
BibTeX Cleaner
Quality Report
Research Library
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/bibflow-streamlit.git
cd bibflow-streamlit
```

Create and activate a virtual environment if desired:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
streamlit run app.py
```

---

## Recommended Requirements

Your `requirements.txt` should include at least:

```text
streamlit
requests
pandas
bibtexparser==1.4.3
openpyxl
```

---

## Example Files

Recommended demo files:

```text
examples/sample_references.bib
examples/sample_journal_rankings_demo.csv
examples/sample_annotated_library.csv
```

The demo ranking file should be a small manually prepared example, not the full official AJG/ABS dataset.

A typical demo ranking file can use this structure:

```csv
journal,issn,ajg_rating,ajg_field,ajg_source_year,ft50
Journal of Finance,0022-1082,4*,Finance,2024,Yes
Journal of Financial Economics,0304-405X,4*,Finance,2024,Yes
Review of Financial Studies,0893-9454,4*,Finance,2024,Yes
Journal of Banking & Finance,0378-4266,3,Finance,2024,
Journal of Futures Markets,0270-7314,3,Finance,2024,
Quantitative Finance,1469-7688,3,Finance,2024,
Finance Research Letters,1544-6123,2,Finance,2024,
```

---

## Private Ranking Files

For local/private use, BibFlow can load a private ranking file from:

```text
data/private/journal_rankings_combined_for_bibflow.csv
```

This file should **not** be committed to a public GitHub repository unless redistribution is allowed.

Recommended `.gitignore` entries:

```gitignore
data/private/
*.xlsx
*.xls
```

You may keep a small demo CSV under `examples/` for public testing.

---

## Ranking File Columns

BibFlow tries to detect ranking columns flexibly. Recommended columns:

```text
journal
journal_normalized
journal_alias_normalized
issn
ajg_rating
ajg_field
ajg_source_year
ft50
ft50_issn
ft50_title
match_note
ranking_source
```

Minimum useful columns:

```text
journal, ajg_rating
```

Better matching columns:

```text
journal, issn, ajg_rating, ajg_field, ajg_source_year
```

---

## Correct Interpretation of Journal Rankings

Journal rankings classify **journals**, not individual papers.

Use this wording:

> This paper is published in an AJG 3 journal.

Avoid this wording:

> This paper is an AJG 3 paper.

BibFlow is designed to support research organisation, not to replace academic judgement.

---

## Suggested Public Demo Workflow

1. Open the app.
2. Go to **Research Library**.
3. Upload `examples/sample_references.bib`.
4. Load the demo ranking file or upload `examples/sample_journal_rankings_demo.csv`.
5. Check ranking match results.
6. Edit reading status, priority, tags, and notes.
7. Mark citation candidates and important papers.
8. Download the annotated library CSV.
9. Refresh the app.
10. Restore the annotated CSV.
11. Download the literature-review Markdown report.

---

## Suggested Screenshots

For a polished GitHub README and personal website, add screenshots under:

```text
assets/screenshots/
```

Recommended screenshots:

```text
01_home_single_doi.png
02_batch_merge.png
03_title_search.png
04_bibtex_cleaner.png
05_quality_report.png
06_research_library_table.png
07_ranking_dashboard.png
08_literature_review_report.png
```

Then embed them in this README:

```markdown
![Research Library](assets/screenshots/06_research_library_table.png)
```

---

## Roadmap

### Version 2.0 series — Completed

```text
2.0A — Research Library Explorer
2.0B — AJG / ABS ranking match
2.0C — Reading status, tags, notes
2.0D — Restore annotated CSV
2.0E — Research Library dashboard and report
2.0F — Polish and testing update
```

### Version 2.1 series — Public Demo and Portfolio Release

```text
2.1A — README and public demo documentation
2.1B — Sample files and demo data
2.1C — Streamlit deployment polish
2.1D — Personal website integration
2.1E — Screenshots and release notes
```

### Future ideas

```text
Additional ranking systems: ABDC, FT50-only view, school-specific lists, Chinese journal lists
Improved citation-key rule engine
Zotero API integration
Collection-level literature review summaries
Duplicate-resolution assistant
Export to structured literature review table
```

---

## Disclaimer

BibFlow is a research workflow assistant. It helps clean references, organise papers, and match journal names to user-supplied ranking files. Users are responsible for verifying metadata, ranking matches, and licensing restrictions for any ranking data they upload.

---

## Author

Built by **Xiaodong Yang** as part of a research and quantitative-finance tool portfolio.
