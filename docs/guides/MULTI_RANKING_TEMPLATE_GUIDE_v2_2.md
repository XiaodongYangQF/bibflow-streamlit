# BibFlow Version 2.2 — Multi-Ranking Template Guide

Version 2.2 lets BibFlow match one reference library against a richer journal ranking file.

## Supported columns

BibFlow detects these columns flexibly. You do not need to use every column.

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
abdc_rating
abdc_field
jcr_quartile
sjr_quartile
cssci
chinese_core
school_tier
custom_rating
ranking_tags
ranking_source
match_note
```

## Recommended workflow

1. Upload your `.bib` file in the Research Library tab.
2. Upload a multi-ranking CSV/XLSX file.
3. Check the matched/unmatched counts.
4. Use filters such as AJG 3+, FT50, ABDC A/A*, JCR Q1, CSSCI, Chinese Core, school tier, or custom rating.
5. Download the full annotated CSV.
6. Manually check fuzzy matches and unmatched journals.

## Important interpretation note

Journal rankings classify journals or list membership. They do not directly measure individual paper quality.

The included `sample_multi_rankings_demo.csv` is a small demo file only. It is not an official AJG, ABDC, JCR, SJR, CSSCI, or Chinese Core dataset.
