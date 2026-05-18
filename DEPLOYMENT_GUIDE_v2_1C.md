# BibFlow Version 2.1C — Deployment Guide

This guide prepares BibFlow for public deployment, especially on Streamlit Community Cloud.

## 1. Required repo files

The repository should include:

```text
app.py
requirements.txt
README.md
PUBLIC_DEMO_GUIDE.md
examples/
.streamlit/config.toml
```

Recommended example files:

```text
examples/sample_references.bib
examples/sample_journal_rankings_demo.csv
examples/sample_annotated_library.csv
```

## 2. Do not commit private ranking data

BibFlow supports journal ranking matching, but the public repo should not redistribute private, licensed, or restricted ranking datasets.

Keep private files in:

```text
data/private/
```

The `.gitignore` additions in this release exclude:

```text
data/private/
*.private.csv
*.private.xlsx
.streamlit/secrets.toml
```

For public demos, use only:

```text
examples/sample_journal_rankings_demo.csv
```

This file should be clearly described as demo data, not official AJG/ABS data.

## 3. Local test before deployment

Run:

```bash
cd ~/GitHub/bibflow-streamlit
streamlit run app.py
```

Test the following:

```text
1. Single DOI lookup
2. Batch DOI processing
3. Title search
4. BibTeX cleaner
5. Quality report
6. Research Library upload
7. Demo ranking file matching
8. Annotation editing
9. Restore annotated CSV
10. Dashboard/report export
```

## 4. Streamlit deployment checklist

Before deploying:

```bash
git status
git add app.py requirements.txt README.md PUBLIC_DEMO_GUIDE.md examples .streamlit/config.toml
git commit -m "Prepare BibFlow Version 2.1C for deployment"
git push
```

Then deploy from your GitHub repository.

Recommended settings:

```text
Main file path: app.py
Python version: compatible with Streamlit and pandas
Required packages: requirements.txt
```

## 5. Public-demo warning text

Use this wording in README, app notes, or deployment page:

> BibFlow does not redistribute the official AJG/ABS ranking dataset. Users may upload their own ranking file. The included ranking file is a small demo file for testing only.

## 6. After deployment

Check:

```text
The app loads correctly
The demo files work
No private ranking files appear in the repository
Download buttons work
Research Library table is editable
Reports export correctly
```

## 7. Suggested release tag

After testing:

```bash
git tag v2.1C
git push origin v2.1C
```

Optional release title:

```text
BibFlow v2.1C — Deployment Polish
```
