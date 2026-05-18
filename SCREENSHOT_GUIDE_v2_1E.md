# BibFlow Version 2.1E — Screenshot Guide

This guide helps you create professional screenshots for GitHub, your personal website, Streamlit, and portfolio use.

## 1. Prepare the app

Run BibFlow locally:

```bash
cd ~/GitHub/bibflow-streamlit
streamlit run app.py
```

Recommended browser setup:

```text
Browser width: 1400–1600 px
Theme: light mode
Zoom: 90% or 100%
Use public demo files only
Avoid private ranking data
```

## 2. Use demo files

Use:

```text
examples/sample_references.bib
examples/sample_journal_rankings_demo.csv
examples/sample_annotated_library.csv
```

## 3. Screenshot list

Save screenshots as:

```text
docs/screenshots/home.png
docs/screenshots/single-doi.png
docs/screenshots/batch-merge.png
docs/screenshots/title-search.png
docs/screenshots/cleaner.png
docs/screenshots/quality-report.png
docs/screenshots/research-library.png
docs/screenshots/ajg-ranking.png
docs/screenshots/annotation-dashboard.png
docs/screenshots/restore-annotations.png
docs/screenshots/literature-review-report.png
```

## 4. Recommended screenshot order

| File | Section | What to show |
|---|---|---|
| `home.png` | Home/header | App title, version badge, tabs, feature cards |
| `single-doi.png` | Single DOI | DOI input, BibTeX output, download button |
| `batch-merge.png` | Batch + Merge | Multiple DOI processing and summary metrics |
| `title-search.png` | Title Search | Title search input and Crossref candidates |
| `cleaner.png` | BibTeX Cleaner | Raw input and cleaned BibTeX output |
| `quality-report.png` | Quality Report | Issue summary and metadata quality table |
| `research-library.png` | Research Library | Library metrics and searchable reference table |
| `ajg-ranking.png` | AJG/ABS Ranking | Matched/unmatched metrics and AJG/FT50 columns |
| `annotation-dashboard.png` | Annotations | Reading status, tags, priority, citation flags, notes |
| `restore-annotations.png` | Restore annotations | Upload previous annotated CSV and restore workflow |
| `literature-review-report.png` | Report export | Dashboard/report tables and markdown export |

## 5. macOS screenshot commands

Capture selected area:

```text
Command + Shift + 4
```

Capture window:

```text
Command + Shift + 4, then Space
```

## 6. Commit screenshots

```bash
git add docs/screenshots
git commit -m "Add Version 2.1E screenshots"
git push
```

## 7. Privacy note

Do not screenshot private AJG/ABS ranking files, unpublished notes, API keys, or sensitive local paths.
