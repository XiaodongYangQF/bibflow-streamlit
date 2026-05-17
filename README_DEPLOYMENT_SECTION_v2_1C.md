## Deployment

BibFlow can be deployed as a Streamlit app.

### Public demo data

The repository includes small demo files:

```text
examples/sample_references.bib
examples/sample_journal_rankings_demo.csv
examples/sample_annotated_library.csv
```

The demo ranking file is only for testing the matching workflow. It is not the official AJG/ABS ranking dataset.

### Private ranking files

Do not commit private or restricted ranking files. Store them locally under:

```text
data/private/
```

BibFlow can still load local private ranking files when running on your own machine, but the public app should rely on user-uploaded ranking files or demo data.

### Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
