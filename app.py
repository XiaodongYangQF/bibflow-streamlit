import re
import requests
import streamlit as st
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase


# ============================================================
# Page config
# ============================================================

st.set_page_config(
    page_title="BibFlow",
    page_icon="📚",
    layout="wide"
)


# ============================================================
# Helper functions
# ============================================================

def normalize_doi(raw_doi: str) -> str:
    """
    Clean DOI copied from browser, article page, or DOI link.
    """
    doi = raw_doi.strip()

    doi = doi.replace("https://doi.org/", "")
    doi = doi.replace("http://doi.org/", "")
    doi = doi.replace("doi.org/", "")
    doi = doi.replace("DOI:", "")
    doi = doi.replace("doi:", "")

    return doi.strip()


def fetch_bibtex_from_doi(doi: str) -> str:
    """
    Fetch BibTeX from DOI.
    """
    url = f"https://doi.org/{doi}"

    headers = {
        "Accept": "application/x-bibtex",
        "User-Agent": "BibFlow Streamlit App"
    }

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    return response.text.strip()


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_first_author_lastname(author_field: str) -> str:
    """
    Extract first author's last name.
    """
    if not author_field:
        return "Unknown"

    first_author = author_field.split(" and ")[0].strip()

    if "," in first_author:
        last_name = first_author.split(",")[0].strip()
    else:
        parts = first_author.split()
        last_name = parts[-1] if parts else "Unknown"

    last_name = re.sub(r"[^A-Za-z0-9]", "", last_name)

    return last_name or "Unknown"


def extract_title_keyword(title: str) -> str:
    """
    Extract a useful keyword from the title.
    """
    stopwords = {
        "a", "an", "the", "and", "or", "of", "in", "on", "for",
        "to", "with", "by", "from", "using", "based", "evidence",
        "new", "some", "towards", "toward"
    }

    title = clean_text(title)
    words = re.findall(r"[A-Za-z0-9]+", title)

    for word in words:
        word_lower = word.lower()
        if word_lower not in stopwords and len(word_lower) > 2:
            return word.capitalize()

    return "Paper"


def generate_citation_key(entry: dict) -> str:
    """
    Generate citation key:
    LastnameYearKeyword

    Example:
    Carr2009Variance
    """
    author = entry.get("author", "")
    year = entry.get("year", "")
    title = entry.get("title", "")

    last_name = extract_first_author_lastname(author)

    year_match = re.search(r"\d{4}", year)
    year_clean = year_match.group(0) if year_match else "YYYY"

    keyword = extract_title_keyword(title)

    key = f"{last_name}{year_clean}{keyword}"
    key = re.sub(r"[^A-Za-z0-9_:-]", "", key)

    return key


def parse_bibtex(raw_bibtex: str):
    """
    Parse BibTeX and return the first entry.
    """
    parser = bibtexparser.bparser.BibTexParser(common_strings=True)
    database = bibtexparser.loads(raw_bibtex, parser=parser)

    if not database.entries:
        return None

    return database.entries[0]


def entry_to_bibtex(entry: dict) -> str:
    """
    Convert BibTeX entry dictionary back to BibTeX string.
    """
    db = BibDatabase()
    db.entries = [entry]

    writer = BibTexWriter()
    writer.indent = "  "
    writer.order_entries_by = None

    return writer.write(db).strip()


def parse_existing_bib(uploaded_file):
    """
    Parse uploaded .bib file and return existing citation keys and DOIs.
    """
    if uploaded_file is None:
        return set(), set()

    content = uploaded_file.read().decode("utf-8", errors="ignore")
    database = bibtexparser.loads(content)

    existing_keys = set()
    existing_dois = set()

    for entry in database.entries:
        if "ID" in entry:
            existing_keys.add(entry["ID"])

        if "doi" in entry:
            existing_dois.add(normalize_doi(entry["doi"]).lower())

    return existing_keys, existing_dois


# ============================================================
# App layout
# ============================================================

st.title("📚 BibFlow")
st.subheader("A Streamlit Assistant for Zotero–Overleaf BibTeX Workflows")

st.markdown(
    """
    BibFlow helps researchers generate clean, Overleaf-ready BibTeX entries from DOI.
    
    Current MVP features:
    
    - Convert DOI to BibTeX
    - Generate a clean citation key
    - Edit citation key manually
    - Upload existing `.bib` file for duplicate checking
    - Download cleaned `.bib` entry
    """
)

st.divider()


# ============================================================
# Sidebar
# ============================================================

st.sidebar.title("Settings")

allow_manual_key = st.sidebar.checkbox(
    "Allow manual citation key editing",
    value=True
)

st.sidebar.markdown("---")

uploaded_bib = st.sidebar.file_uploader(
    "Optional: upload existing references.bib",
    type=["bib"]
)

existing_keys, existing_dois = parse_existing_bib(uploaded_bib)

if uploaded_bib is not None:
    st.sidebar.success(
        f"Loaded {len(existing_keys)} citation keys and {len(existing_dois)} DOI records."
    )


# ============================================================
# Main input
# ============================================================

doi_input = st.text_input(
    "Enter DOI",
    placeholder="Example: 10.1093/rfs/hhq032"
)

generate_button = st.button("Generate BibTeX", type="primary")


# ============================================================
# Main workflow
# ============================================================

if generate_button:

    if not doi_input.strip():
        st.warning("Please enter a DOI.")
        st.stop()

    doi = normalize_doi(doi_input)

    with st.spinner("Fetching BibTeX metadata..."):
        try:
            raw_bibtex = fetch_bibtex_from_doi(doi)
        except Exception as e:
            st.error(f"Failed to fetch BibTeX from DOI: {e}")
            st.stop()

    entry = parse_bibtex(raw_bibtex)

    if entry is None:
        st.error("Could not parse the BibTeX entry.")
        st.stop()

    suggested_key = generate_citation_key(entry)
    doi_lower = doi.lower()

    st.success("BibTeX generated successfully.")

    # Duplicate checks
    col1, col2 = st.columns(2)

    with col1:
        if doi_lower in existing_dois:
            st.warning("This DOI may already exist in your uploaded .bib file.")
        else:
            st.info("No duplicate DOI detected.")

    with col2:
        if suggested_key in existing_keys:
            st.warning("Suggested citation key already exists.")
        else:
            st.info("Suggested citation key is available.")

    st.divider()

    # Citation key editing
    if allow_manual_key:
        final_key = st.text_input(
            "Citation key",
            value=suggested_key
        )
    else:
        final_key = suggested_key
        st.write(f"Suggested citation key: `{final_key}`")

    entry["ID"] = final_key
    cleaned_bibtex = entry_to_bibtex(entry)

    left_col, right_col = st.columns(2)

    with left_col:
        st.markdown("### Original BibTeX")
        st.code(raw_bibtex, language="bibtex")

    with right_col:
        st.markdown("### Cleaned BibTeX")
        st.code(cleaned_bibtex, language="bibtex")

    st.download_button(
        label="Download cleaned .bib file",
        data=cleaned_bibtex,
        file_name=f"{final_key}.bib",
        mime="text/plain"
    )