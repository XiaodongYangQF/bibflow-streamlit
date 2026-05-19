## Version 2.3 — Zotero HTML Bibliography Import

BibFlow now supports Zotero-exported bibliography HTML files.

Recommended Zotero export setting:

```text
Output Mode: Bibliography
Output Method: Save as HTML
```

Workflow:

```text
Zotero HTML bibliography
→ BibFlow extracts DOI values
→ BibFlow fetches clean BibTeX metadata
→ Export Overleaf-ready .bib
→ Optional merge with existing references.bib
```

This feature is designed as a lightweight bridge before full Zotero API integration. It works best when the HTML file contains DOI links or Zotero Z3988 metadata.

Citation-only HTML exports are not recommended because they usually do not contain enough metadata to generate clean BibTeX.
