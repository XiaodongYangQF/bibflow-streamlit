# BibFlow Version 2.1B — Sample Files and Demo Data

This folder contains public demo files for testing BibFlow without using private or licensed ranking data.

## Files

- `examples/sample_references.bib`  
  Demo BibTeX library for Research Library testing.

- `examples/sample_journal_rankings_demo.csv`  
  Small public demo ranking file. It is **not** the official AJG/ABS dataset.

- `examples/sample_annotated_library.csv`  
  Example enriched/annotated library export for testing annotation restore.

## Suggested test workflow

1. Open BibFlow.
2. Go to `📚 Research Library`.
3. Upload `examples/sample_references.bib`.
4. Upload `examples/sample_journal_rankings_demo.csv`.
5. Check that AJG/FT50 matching works.
6. Edit reading status, tags, priority, citation candidate, and notes.
7. Download the annotated CSV.
8. Refresh the app.
9. Upload the same `.bib` file again.
10. Restore annotations using `examples/sample_annotated_library.csv`.

## Important note

The ranking file in this folder is intentionally small and for demonstration only.
Do not present it as the official AJG/ABS ranking data.
