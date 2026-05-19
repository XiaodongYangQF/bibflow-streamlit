# BibFlow Version 2.2B — Advanced Ranking Table Cleanup

## Purpose

Version 2.2B cleans the Research Library ranking display after adding multi-ranking support.

The main table keeps the compact, high-value ranking view:

```text
AJG Rating
AJG Field
FT50
ABDC Rating
JCR Quartile
SJR Quartile
SSCI
```

## Changed

Removed these mostly empty or future-use columns from the Advanced ranking and matching details table:

```text
ABDC Field
CSSCI
Chinese Core
School Tier
```

The advanced table now focuses on useful checking/debugging fields:

```text
AJG Source Year
SSCI Categories
Custom Rating
Ranking Tags
Matched Journal
Match Method
Match Score
Ranking Source
Ranking Match Note
Annotation ID
```

## Notes

The removed columns are not deleted from the internal data model. They are only hidden from the current UI. They can be reintroduced later when CSSCI, Chinese Core, or school-specific rankings become part of the active workflow.
