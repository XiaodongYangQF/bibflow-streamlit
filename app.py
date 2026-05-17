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
    Clean DOI copied from browser, article page, DOI link, or BibTeX field.
    """
    if raw_doi is None:
        return ""

    doi = str(raw_doi).strip()

    doi = doi.replace("https://doi.org/", "")
    doi = doi.replace("http://doi.org/", "")
    doi = doi.replace("https://dx.doi.org/", "")
    doi = doi.replace("http://dx.doi.org/", "")
    doi = doi.replace("doi.org/", "")
    doi = doi.replace("dx.doi.org/", "")
    doi = doi.replace("DOI:", "")
    doi = doi.replace("doi:", "")

    doi = doi.strip().strip(".").strip()

    return doi


def fetch_bibtex_from_doi(doi: str) -> str:
    """
    Fetch BibTeX from DOI using DOI content negotiation.
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
    """
    Remove braces and unnecessary spaces from BibTeX fields.
    """
    if not text:
        return ""

    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_first_author_lastname(author_field: str) -> str:
    """
    Extract first author's last name from BibTeX author field.
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
    Extract one meaningful keyword from title for citation key.
    """
    stopwords = {
        "a", "an", "the", "and", "or", "of", "in", "on", "for",
        "to", "with", "by", "from", "using", "based", "evidence",
        "new", "some", "towards", "toward", "into", "across",
        "through", "between", "among", "over", "under", "its",
        "their", "our", "your", "this", "that"
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


def make_unique_key(base_key: str, used_keys: set) -> str:
    """
    Make citation key unique against existing keys and batch-generated keys.
    """
    if base_key not in used_keys:
        return base_key

    counter = 2

    while f"{base_key}_{counter}" in used_keys:
        counter += 1

    return f"{base_key}_{counter}"


def parse_bibtex(raw_bibtex: str):
    """
    Parse BibTeX and return first entry.
    """
    parser = bibtexparser.bparser.BibTexParser(common_strings=True)
    database = bibtexparser.loads(raw_bibtex, parser=parser)

    if not database.entries:
        return None

    return database.entries[0]


def entry_to_bibtex(entry: dict) -> str:
    """
    Convert one BibTeX entry dictionary back to BibTeX string.
    """
    db = BibDatabase()
    db.entries = [entry]

    writer = BibTexWriter()
    writer.indent = "  "
    writer.order_entries_by = None

    return writer.write(db).strip()


def entries_to_bibtex(entries: list) -> str:
    """
    Convert multiple BibTeX entries into one BibTeX string.
    """
    db = BibDatabase()
    db.entries = entries

    writer = BibTexWriter()
    writer.indent = "  "
    writer.order_entries_by = None

    return writer.write(db).strip()


def parse_existing_bib(uploaded_file):
    """
    Parse uploaded .bib file and return:
    - existing citation keys
    - existing DOIs
    - original .bib content
    - number of entries
    """
    if uploaded_file is None:
        return set(), set(), "", 0

    content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    database = bibtexparser.loads(content)

    existing_keys = set()
    existing_dois = set()

    for entry in database.entries:
        if "ID" in entry:
            existing_keys.add(entry["ID"])

        if "doi" in entry:
            normalized = normalize_doi(entry["doi"]).lower()
            if normalized:
                existing_dois.add(normalized)

    return existing_keys, existing_dois, content, len(database.entries)


def split_doi_input(batch_text: str) -> list:
    """
    Split batch DOI input by line.
    Empty lines are removed.
    Duplicate input DOIs are removed while preserving order.
    """
    raw_lines = batch_text.splitlines()

    dois = []
    seen = set()

    for line in raw_lines:
        doi = normalize_doi(line)

        if not doi:
            continue

        doi_lower = doi.lower()

        if doi_lower not in seen:
            dois.append(doi)
            seen.add(doi_lower)

    return dois


def build_merged_bib(existing_bib_content: str, new_bibtex: str) -> str:
    """
    Build a clean merged .bib file by preserving the uploaded .bib content
    and appending only newly generated entries.
    """
    existing_clean = existing_bib_content.strip()
    new_clean = new_bibtex.strip()

    if existing_clean and new_clean:
        return existing_clean + "\n\n% ===== Entries added by BibFlow =====\n\n" + new_clean

    if existing_clean:
        return existing_clean

    return new_clean


# ============================================================
# App layout
# ============================================================

st.title("📚 BibFlow")
st.subheader("A Streamlit Assistant for Zotero–Overleaf BibTeX Workflows")

st.markdown(
    """
    BibFlow helps researchers generate, clean, deduplicate, and export Overleaf-ready BibTeX entries.

    **Version 1.2 features:**

    - Single DOI to BibTeX
    - Batch DOI to BibTeX
    - Upload existing `references.bib`
    - Skip DOI entries that already exist
    - Generate unique citation keys
    - Download a clean merged `.bib` file
    """
)

st.divider()


# ============================================================
# Sidebar
# ============================================================

st.sidebar.title("Settings")

allow_manual_key = st.sidebar.checkbox(
    "Allow manual citation key editing in Single DOI mode",
    value=True
)

skip_existing_doi = st.sidebar.checkbox(
    "Skip DOI entries already in uploaded .bib",
    value=True
)

st.sidebar.markdown("---")

uploaded_bib = st.sidebar.file_uploader(
    "Optional: upload existing references.bib",
    type=["bib"]
)

existing_keys, existing_dois, existing_bib_content, existing_entry_count = parse_existing_bib(uploaded_bib)

if uploaded_bib is not None:
    st.sidebar.success(
        f"Loaded {existing_entry_count} entries, {len(existing_keys)} keys, and {len(existing_dois)} DOI records."
    )

st.sidebar.markdown("---")
st.sidebar.caption("BibFlow Version 1.2")


# ============================================================
# Tabs
# ============================================================

single_tab, batch_tab = st.tabs(["Single DOI", "Batch DOI + Clean Merge"])


# ============================================================
# Single DOI workflow
# ============================================================

with single_tab:

    st.markdown("## Single DOI to BibTeX")

    doi_input = st.text_input(
        "Enter DOI",
        placeholder="Example: 10.1093/rfs/hhq032"
    )

    generate_single_button = st.button(
        "Generate BibTeX",
        type="primary",
        key="single_generate_button"
    )

    if generate_single_button:

        if not doi_input.strip():
            st.warning("Please enter a DOI.")
            st.stop()

        doi = normalize_doi(doi_input)
        doi_lower = doi.lower()

        if uploaded_bib is not None and skip_existing_doi and doi_lower in existing_dois:
            st.warning("This DOI already exists in your uploaded .bib file. It was not regenerated.")
            st.stop()

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
        final_suggested_key = make_unique_key(suggested_key, set(existing_keys))

        st.success("BibTeX generated successfully.")

        col1, col2 = st.columns(2)

        with col1:
            if doi_lower in existing_dois:
                st.warning("This DOI may already exist in your uploaded .bib file.")
            else:
                st.info("No duplicate DOI detected.")

        with col2:
            if suggested_key in existing_keys:
                st.warning(f"Suggested key already exists. Suggested new key: `{final_suggested_key}`")
            else:
                st.info("Suggested citation key is available.")

        st.divider()

        if allow_manual_key:
            final_key = st.text_input(
                "Citation key",
                value=final_suggested_key,
                key="single_citation_key"
            )
        else:
            final_key = final_suggested_key
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
            mime="text/plain",
            key="single_download_button"
        )

        if uploaded_bib is not None:
            merged_single_bibtex = build_merged_bib(existing_bib_content, cleaned_bibtex)

            st.markdown("### Clean Merge Preview")
            st.caption("Your uploaded .bib content is preserved. The new entry is appended at the end.")
            st.code(merged_single_bibtex, language="bibtex")

            st.download_button(
                label="Download merged .bib file",
                data=merged_single_bibtex,
                file_name="merged_references.bib",
                mime="text/plain",
                key="single_merged_download_button"
            )


# ============================================================
# Batch DOI + Clean Merge workflow
# ============================================================

with batch_tab:

    st.markdown("## Batch DOI to BibTeX + Clean Merge")

    st.markdown(
        """
        Paste multiple DOIs below, one DOI per line.

        If you upload an existing `references.bib`, BibFlow can automatically skip DOI entries
        that already exist and append only new references.
        """
    )

    batch_input = st.text_area(
        "Enter multiple DOIs",
        height=220,
        placeholder="Paste one DOI per line..."
    )

    generate_batch_button = st.button(
        "Generate and Merge BibTeX",
        type="primary",
        key="batch_generate_button"
    )

    if generate_batch_button:

        dois = split_doi_input(batch_input)

        if not dois:
            st.warning("Please enter at least one DOI.")
            st.stop()

        st.info(f"Detected {len(dois)} unique DOI(s) from your input.")

        generated_entries = []
        result_rows = []

        used_keys = set(existing_keys)
        progress_bar = st.progress(0)

        skipped_count = 0
        failed_count = 0

        for i, doi in enumerate(dois, start=1):

            doi_lower = doi.lower()

            if uploaded_bib is not None and skip_existing_doi and doi_lower in existing_dois:
                skipped_count += 1

                result_rows.append(
                    {
                        "DOI": doi,
                        "Citation Key": "",
                        "Duplicate DOI in uploaded .bib": True,
                        "Action": "Skipped",
                        "Status": "Skipped because DOI already exists in uploaded .bib",
                    }
                )

                progress_bar.progress(i / len(dois))
                continue

            try:
                raw_bibtex = fetch_bibtex_from_doi(doi)
                entry = parse_bibtex(raw_bibtex)

                if entry is None:
                    raise ValueError("Could not parse BibTeX entry.")

                entry_doi = normalize_doi(entry.get("doi", "")).lower()
                duplicate_by_returned_doi = uploaded_bib is not None and entry_doi in existing_dois

                if skip_existing_doi and duplicate_by_returned_doi:
                    skipped_count += 1

                    result_rows.append(
                        {
                            "DOI": doi,
                            "Citation Key": "",
                            "Duplicate DOI in uploaded .bib": True,
                            "Action": "Skipped",
                            "Status": "Skipped because returned DOI already exists in uploaded .bib",
                        }
                    )

                    progress_bar.progress(i / len(dois))
                    continue

                suggested_key = generate_citation_key(entry)
                final_key = make_unique_key(suggested_key, used_keys)

                entry["ID"] = final_key

                used_keys.add(final_key)
                generated_entries.append(entry)

                if final_key != suggested_key:
                    action = "Generated with renamed key"
                    status = f"Original key `{suggested_key}` already existed. Used `{final_key}`."
                else:
                    action = "Generated"
                    status = "New BibTeX entry generated."

                result_rows.append(
                    {
                        "DOI": doi,
                        "Citation Key": final_key,
                        "Duplicate DOI in uploaded .bib": False,
                        "Action": action,
                        "Status": status,
                    }
                )

            except Exception as e:
                failed_count += 1

                result_rows.append(
                    {
                        "DOI": doi,
                        "Citation Key": "",
                        "Duplicate DOI in uploaded .bib": False,
                        "Action": "Failed",
                        "Status": f"Failed: {e}",
                    }
                )

            progress_bar.progress(i / len(dois))

        st.divider()

        successful_count = len(generated_entries)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Input DOIs", len(dois))

        with col2:
            st.metric("New entries", successful_count)

        with col3:
            st.metric("Skipped duplicates", skipped_count)

        with col4:
            st.metric("Failed", failed_count)

        st.markdown("### Processing Summary")
        st.dataframe(result_rows, use_container_width=True)

        if generated_entries:

            new_entries_bibtex = entries_to_bibtex(generated_entries)

            st.markdown("### New BibTeX Entries")
            st.code(new_entries_bibtex, language="bibtex")

            st.download_button(
                label="Download new entries only",
                data=new_entries_bibtex,
                file_name="bibflow_new_entries.bib",
                mime="text/plain",
                key="batch_new_entries_download_button"
            )

            if uploaded_bib is not None:
                merged_bibtex = build_merged_bib(existing_bib_content, new_entries_bibtex)

                st.markdown("### Clean Merged BibTeX")
                st.caption(
                    "Your uploaded .bib content is preserved. Only new non-duplicate entries are appended."
                )
                st.code(merged_bibtex, language="bibtex")

                st.download_button(
                    label="Download clean merged .bib file",
                    data=merged_bibtex,
                    file_name="merged_references.bib",
                    mime="text/plain",
                    key="batch_merged_download_button"
                )
            else:
                st.info("Upload an existing references.bib file to enable clean merge output.")

        else:
            if skipped_count > 0 and failed_count == 0:
                st.warning("No new entries were generated because all input DOIs already exist in your uploaded .bib file.")
            elif failed_count > 0:
                st.warning("No new entries were generated. Please check the failed DOI(s).")