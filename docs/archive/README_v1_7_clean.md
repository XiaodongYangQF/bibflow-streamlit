# BibFlow

**BibFlow** is a lightweight Streamlit research workflow assistant for researchers who use **Zotero**, **BibTeX**, and **Overleaf**.

It helps users generate, clean, deduplicate, merge, validate, and export Overleaf-ready BibTeX entries from DOI metadata, title search, batch DOI input, or raw BibTeX.

---

## Motivation

Many researchers manage papers in Zotero but write manuscripts in Overleaf. Moving references into an Overleaf `.bib` file can become repetitive and error-prone, especially when:

- citation keys are inconsistent;
- duplicate references appear;
- DOI fields are missing or messy;
- Google Scholar BibTeX contains noisy fields;
- Overleaf `references.bib` becomes difficult to maintain over time.

BibFlow aims to simplify this workflow.

---

## Core Features

- DOI to BibTeX generation
- Batch DOI processing
- Clean merge with an existing `references.bib`
- Title search when DOI is unknown
- Raw BibTeX cleaning and validation
- Duplicate DOI checking
- Citation key regeneration
- Citation key style presets
- BibTeX export presets
- Cleaned and merged `.bib` downloads

---

## Current Version

### Version 1.7 — Citation Key Style Presets

Version 1.7 adds flexible citation key style options.

New features:

- Citation key style selector
- `AuthorYearKeyword` style
- `AuthorYear` style
- `AuthorYearJournal` style
- `AuthorYearShortTitle` style
- Journal abbreviation rules for common finance and economics journals
- Citation key style support across DOI, batch, title search, and BibTeX cleaner workflows

---

## App Modes

### 1. Single DOI

Generate a BibTeX entry from one DOI.

### 2. Batch + Merge

Paste multiple DOIs, generate BibTeX entries, skip duplicates, and merge with an uploaded `references.bib`.

### 3. Title Search

Search by paper title when the DOI is unknown, select the correct candidate, and generate BibTeX.

### 4. BibTeX Cleaner

Paste raw BibTeX or upload a raw `.bib` file, then clean entries, regenerate keys, and remove noisy fields.

---

## Citation Key Styles

BibFlow supports multiple citation key styles:

| Style | Example |
|---|---|
| `AuthorYearKeyword` | `Bollerslev2009Variance` |
| `AuthorYear` | `Bollerslev2009` |
| `AuthorYearJournal` | `Bollerslev2009RFS` |
| `AuthorYearShortTitle` | `Bollerslev2009VarianceRisk` |

---

## BibTeX Export Presets

| Preset | Purpose |
|---|---|
| `Overleaf Clean` | Recommended default for academic LaTeX writing |
| `Minimal Citation` | Compact manuscript-ready output |
| `DOI + URL Friendly` | Keeps DOI and URL for easier reference tracking |
| `Full Metadata` | Preserves all parsed fields |

---

## Research Workflow

```text
Zotero / DOI / paper title / raw BibTeX
→ BibFlow
→ clean Overleaf-ready references.bib
→ LaTeX writing
```

---

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Requirements

```text
streamlit
requests
bibtexparser==1.4.3
```

---

## Suggested Repository Structure

```text
bibflow-streamlit/
│
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
│
├── .streamlit/
│   └── config.toml
│
├── examples/
│   ├── sample_references.bib
│   └── problematic_references.bib
│
└── docs/
    └── screenshots/
        ├── home.png
        ├── single-doi.png
        ├── batch-merge.png
        ├── title-search.png
        └── cleaner.png
```

---

## Deployment

This app is designed for Streamlit Community Cloud deployment.

Recommended deployment settings:

```text
Repository: XiaodongYangQF/bibflow-streamlit
Branch: main
Main file path: app.py
```

---

## Roadmap

- Version 1.8: Deployment polish, sample files, screenshots, and documentation
- Version 1.9: Better error handling and user messages
- Version 2.0: Zotero API integration
- Version 2.1: Project-level reference library management
- Version 2.2: Better BibTeX-compatible key rules

---

## Author

**Xiaodong Yang**  
PhD Candidate in Quantitative Finance  
University College Dublin

---

## License

You can add an MIT License if you want this to be an open-source portfolio project.
