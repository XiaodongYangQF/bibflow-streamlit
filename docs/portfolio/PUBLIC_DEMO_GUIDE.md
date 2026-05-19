# BibFlow Public Demo Guide

This guide explains how to prepare BibFlow for a public GitHub or Streamlit demo.

## Goal

The public demo should let visitors understand BibFlow quickly without requiring access to private journal-ranking files.

The demo should show that BibFlow can:

```text
clean BibTeX
process DOI inputs
merge references
check reference quality
explore a research library
match journals against a demo ranking file
annotate papers
restore annotations
export literature-review reports
```

## Public demo principles

### 1. Do not redistribute private or licensed ranking data

Do not commit the full official AJG/ABS file unless redistribution is clearly allowed.

Use this structure instead:

```text
data/private/                         # ignored by Git
examples/sample_journal_rankings_demo.csv
```

`examples/sample_journal_rankings_demo.csv` should contain only a small demonstration dataset.

### 2. Keep the demo simple

The demo should work with three files:

```text
examples/sample_references.bib
examples/sample_journal_rankings_demo.csv
examples/sample_annotated_library.csv
```

### 3. Explain ranking interpretation clearly

Use:

> This paper is published in an AJG 3 journal.

Do not use:

> This is an AJG 3 paper.

## Recommended repository structure

```text
bibflow-streamlit/
├── app.py
├── README.md
├── requirements.txt
├── RELEASE_NOTES_v2_1A.md
├── PUBLIC_DEMO_GUIDE.md
├── examples/
│   ├── sample_references.bib
│   ├── sample_journal_rankings_demo.csv
│   └── sample_annotated_library.csv
├── assets/
│   └── screenshots/
│       ├── 01_home_single_doi.png
│       ├── 02_batch_merge.png
│       ├── 03_title_search.png
│       ├── 04_bibtex_cleaner.png
│       ├── 05_quality_report.png
│       ├── 06_research_library_table.png
│       ├── 07_ranking_dashboard.png
│       └── 08_literature_review_report.png
└── data/
    └── private/
        └── journal_rankings_combined_for_bibflow.csv   # ignored by Git
```

## Recommended `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
venv/
.env

# Streamlit secrets
.streamlit/secrets.toml

# Private data
data/private/

# Large or licensed ranking files
*.xlsx
*.xls

# OS files
.DS_Store
```

## Demo ranking file format

Recommended columns:

```text
journal,issn,ajg_rating,ajg_field,ajg_source_year,ft50
```

Example:

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

## Local test checklist

Run:

```bash
streamlit run app.py
```

Then test:

```text
1. Single DOI tab: generate BibTeX from one DOI.
2. Batch + Merge tab: paste 2-3 DOI values.
3. Title Search tab: search by paper title.
4. BibTeX Cleaner tab: upload a messy .bib file.
5. Quality Report tab: upload a problematic .bib file.
6. Research Library tab: upload sample_references.bib.
7. Load the demo ranking file.
8. Confirm AJG/FT50 columns appear.
9. Edit Reading Status, Priority, Tags, Important, Citation Candidate, and Notes.
10. Download full annotated CSV.
11. Refresh app and restore the annotated CSV.
12. Download literature-review Markdown report.
13. Download dashboard summary CSV.
14. Download unmatched journals CSV if unmatched journals exist.
```

## Screenshot checklist

Take screenshots after the app is stable:

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

Suggested screenshot size:

```text
1600 x 900
```

## Streamlit deployment notes

Before deploying publicly:

```text
Check requirements.txt
Check .gitignore
Remove private ranking files
Keep only demo ranking data
Add screenshots to README
Add link from personal website Interactive Tools page
```

## Suggested website card

Title:

> BibFlow — Research Bibliography & Journal Ranking Assistant

Description:

> A Streamlit app for cleaning BibTeX references, managing research libraries, matching user-supplied journal rankings, and tracking literature-review progress.

Tags:

```text
Streamlit · BibTeX · Overleaf · Research Workflow · Journal Rankings · Literature Review
```
