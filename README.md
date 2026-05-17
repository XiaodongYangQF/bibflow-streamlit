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