# BibFlow Private Ranking Files Guide

Generated cleaned and combined ranking files from the four uploaded sources:

1. `ABS2024_clean_for_bibflow(1).csv`
2. `ft50_clean_for_bibflow(1).csv`
3. `ABDC-JQL-2025-v1-260326(1).xlsx`
4. `SSCI-List_160424(1).csv`

## Output files

- `ajg_2024_clean_for_bibflow_checked.csv`
- `ft50_clean_for_bibflow_checked.csv`
- `abdc_2025_clean_for_bibflow.csv`
- `ssci_clean_for_bibflow.csv`
- `journal_rankings_combined_for_bibflow.csv`
- `ranking_combination_summary.csv`

## Recommended local placement

```text
bibflow-streamlit/
└── data/
    └── private/
        ├── source_rankings/
        │   ├── ABS2024_clean_for_bibflow.csv
        │   ├── ft50_clean_for_bibflow.csv
        │   ├── abdc_2025_clean_for_bibflow.csv
        │   └── ssci_clean_for_bibflow.csv
        └── journal_rankings_combined_for_bibflow.csv
```

The main file used by BibFlow should be:

```text
data/private/journal_rankings_combined_for_bibflow.csv
```

## Summary

- AJG rows: 1,822
- FT50 rows: 50
- ABDC rows: 2,651
- SSCI rows: 3,551
- Combined rows: 5,489
- Combined rows with AJG rating: 1,813
- Combined rows with FT50: 50
- Combined rows with ABDC rating: 2,650
- Combined rows with SSCI flag: 3,551

## Cleaning notes

- ABDC uses the `2025 JQL` sheet.
- SSCI is treated as an index flag, not a rating: `ssci = Yes`.
- CSSCI is not included at this stage.
- FT50 is matched conservatively by exact journal-normalized name first. This avoids false merges from duplicated or inconsistent ISSNs in the FT50 source file.

## Privacy

Do not commit private ranking files to GitHub.

Make sure `.gitignore` includes:

```text
data/private/
*.private.csv
*.private.xlsx
```

Then check:

```bash
git status
```

If `data/private/` files appear in Git status, do not commit them.
