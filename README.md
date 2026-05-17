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