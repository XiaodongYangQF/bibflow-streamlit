# BibFlow Version 2.3 — Zotero HTML Bibliography Import

## Purpose

Version 2.3 adds a practical bridge between Zotero and BibFlow before the full Zotero API integration.

Users can export a Zotero bibliography as HTML, upload it to BibFlow, extract DOI values, and generate clean Overleaf-ready BibTeX entries.

## Added

- New tab: `🌐 Zotero HTML Import`
- Upload `.html` / `.htm` bibliography files
- Optional pasted HTML input
- DOI extraction from visible DOI links
- DOI extraction from Zotero Z3988 metadata
- DOI deduplication
- CSL bibliography entry preview
- DOI-to-BibTeX generation from extracted DOI list
- New entries `.bib` download
- Clean merge with existing uploaded `.bib` file
- Extracted DOI list download

## Recommended Zotero export settings

```text
Output Mode: Bibliography
Output Method: Save as HTML
```

## Notes

- Different citation styles are okay if the HTML still contains DOI links or Z3988 metadata.
- Citation-only HTML is not reliable because it lacks full metadata.
- RTF and Clipboard parsing are intentionally not supported in this version.
- Full Zotero API integration remains a future Version 3.0 feature.
