# Zotero HTML Import Guide

## 1. Export from Zotero

In Zotero, select the items or collection you want to export as a bibliography.

Recommended settings:

```text
Output Mode: Bibliography
Output Method: Save as HTML
```

Citation style can be APA, Chicago, Elsevier, Nature, etc. The citation style is less important than the metadata inside the HTML.

## 2. Upload to BibFlow

Open BibFlow and go to:

```text
🌐 Zotero HTML Import
```

Upload the `.html` file. BibFlow will extract DOI values and show a preview.

## 3. Generate BibTeX

Click:

```text
Generate BibTeX from extracted DOIs
```

BibFlow will fetch clean BibTeX metadata using DOI content negotiation.

## 4. Export

You can download:

```text
bibflow_from_zotero_html.bib
merged_references_from_zotero_html.bib
bibflow_extracted_dois_from_zotero_html.txt
```

## Limitations

Citation-only HTML, such as only `(Author et al., Year)`, is not reliable because it usually lacks DOI and journal metadata.

RTF and clipboard text are not supported in Version 2.3.
