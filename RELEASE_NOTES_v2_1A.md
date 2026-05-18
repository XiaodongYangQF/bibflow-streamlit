# BibFlow Version 2.1A — README and Public Demo Documentation

## Purpose

Version 2.1A starts the public-demo and portfolio-release stage of BibFlow.

The Version 2.0 series focused on building research-library features. Version 2.1 focuses on making the project easier to understand, test, deploy, and present on GitHub and a personal website.

## Main deliverables

- New professional `README.md`.
- New `PUBLIC_DEMO_GUIDE.md`.
- Clear public-demo workflow.
- Private ranking-file guidance.
- Suggested repository structure.
- Suggested `.gitignore` rules.
- Screenshot checklist.
- Public website card text.
- Release notes for Version 2.1A.

## What changed conceptually

BibFlow is now positioned as:

> A research bibliography and journal-ranking workflow assistant for BibTeX, Overleaf, and literature-review management.

This is broader and stronger than a DOI-to-BibTeX cleaner.

## Public demo focus

The public demo should let visitors test:

```text
Single DOI generation
Batch DOI processing
Title-based search
BibTeX cleaning
Reference quality report
Research Library Explorer
AJG/ABS-style demo ranking match
FT50 flag display
Research annotations
Annotation restore workflow
Dashboard and report export
```

## Private data policy

The app should not publicly redistribute full official or licensed journal-ranking files unless redistribution is permitted.

Recommended pattern:

```text
data/private/                         # local/private only
examples/sample_journal_rankings_demo.csv   # public demo only
```

## Suggested commit message

```bash
git add README.md PUBLIC_DEMO_GUIDE.md RELEASE_NOTES_v2_1A.md
git commit -m "Add Version 2.1A public demo documentation"
git push
```

## Next suggested version

Version 2.1B should prepare clean demo files:

```text
examples/sample_references.bib
examples/sample_journal_rankings_demo.csv
examples/sample_annotated_library.csv
```
