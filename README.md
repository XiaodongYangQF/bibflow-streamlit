# BibFlow

BibFlow is a lightweight Streamlit assistant for Zotero–Overleaf BibTeX workflows.

It helps researchers generate, clean, deduplicate, and export Overleaf-ready BibTeX entries from DOI metadata.

## Features

- Convert DOI to BibTeX
- Generate clean citation keys
- Edit citation keys manually
- Upload existing `.bib` files for duplicate checking
- Download cleaned BibTeX entries

## Motivation

Many researchers use Zotero for reference management and Overleaf for LaTeX writing. However, moving references from Zotero, Google Scholar, or journal pages into Overleaf `.bib` files can be repetitive and error-prone.

BibFlow aims to simplify this workflow.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Current Version

### Version 1.0 — DOI to BibTeX MVP

The first stable version supports:

- DOI-based BibTeX generation
- Automatic citation key generation
- Manual citation key editing
- Existing `.bib` upload
- Duplicate DOI checking
- Duplicate citation key checking
- Cleaned BibTeX download

This version provides a minimal but complete workflow for researchers who use Zotero, BibTeX, and Overleaf.


## Version 1.1 — Batch DOI Processing

Version 1.1 adds batch DOI processing.

New features:

- Paste multiple DOIs, one per line
- Fetch BibTeX entries in batch
- Generate unique citation keys
- Detect duplicate DOI records against uploaded `.bib` files
- Download a combined `.bib` file
- Preview uploaded `.bib` plus newly generated entries


## Version 1.2 — Clean Merge with Existing `.bib` File

Version 1.2 adds a practical clean-merge workflow for Overleaf users.

New features:

- Upload an existing `references.bib`
- Paste one or multiple DOI entries
- Skip DOI records that already exist in the uploaded `.bib`
- Generate unique citation keys against existing keys
- Append only new entries to the existing `.bib`
- Download a clean `merged_references.bib` file


## Version 1.3 — Title Search when DOI is Unknown

Version 1.3 adds title-based reference search.

New features:

- Search papers by title using Crossref metadata
- Add optional author name to improve search quality
- Display candidate papers with title, author, year, venue, DOI, and score
- Select the correct candidate
- Generate BibTeX from the selected DOI
- Check duplicate DOI and citation key records
- Download or merge the generated BibTeX entry


## Version 1.4 — BibTeX Cleaner & Validator

Version 1.4 adds a raw BibTeX cleaning workflow.

New features:

- Paste raw BibTeX entries
- Upload raw `.bib` files for cleaning
- Regenerate citation keys
- Protect title acronyms
- Remove noisy fields such as abstracts, local file paths, keywords, timestamps, and annotations
- Skip duplicated DOI entries against uploaded `references.bib`
- Download cleaned BibTeX
- Merge cleaned entries into an existing Overleaf `.bib` file



# BibFlow

**BibFlow** is a lightweight Streamlit research workflow assistant for researchers who use **Zotero**, **BibTeX**, and **Overleaf**.

It helps users generate, clean, deduplicate, merge, and export Overleaf-ready BibTeX entries from DOI metadata, title search, batch DOI input, or raw BibTeX.

## Motivation

Many researchers manage papers in Zotero but write manuscripts in Overleaf. Moving references into an Overleaf `.bib` file can become repetitive and error-prone, especially when citation keys are inconsistent, duplicate references appear, or BibTeX entries from Google Scholar contain noisy fields.

BibFlow aims to simplify this workflow.

## Current Version

### Version 1.5 — UI and Project Polish

Version 1.5 improves the app interface and project presentation.

Main improvements:

- Cleaner Streamlit interface
- Branded app header
- Feature cards
- More readable sidebar
- Professional tab names
- App footer
- Streamlit theme configuration
- Improved GitHub/portfolio readiness

## Core Features

- DOI to BibTeX generation
- Batch DOI processing
- Clean merge with an existing `references.bib`
- Title search when DOI is unknown
- Raw BibTeX cleaning and validation
- Duplicate DOI checking
- Citation key regeneration
- Cleaned and merged `.bib` downloads

## Research Workflow

```text
Zotero / DOI / paper title / raw BibTeX
→ BibFlow
→ clean Overleaf-ready references.bib
→ LaTeX writing


## Version 1.6 — Export Options and BibTeX Style Presets

Version 1.6 adds flexible BibTeX export options.

New features:

- Export preset selector
- Overleaf Clean preset
- Minimal Citation preset
- DOI + URL Friendly preset
- Full Metadata preset
- Optional citation-key sorting
- Optional BibFlow export header
- Cleaner output control for different LaTeX writing workflows