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


def search_crossref_by_title(title: str, author: str = "", rows: int = 8) -> list:
    """
    Search Crossref metadata by paper title.
    Optional author input improves the search quality.
    """
    url = "https://api.crossref.org/works"

    params = {
        "query.title": title,
        "rows": rows,
        "select": "DOI,title,author,issued,container-title,type,publisher,score,URL"
    }

    if author.strip():
        params["query.author"] = author.strip()

    headers = {
        "User-Agent": "BibFlow Streamlit App"
    }

    response = requests.get(url, params=params, headers=headers, timeout=20)
    response.raise_for_status()

    data = response.json()
    items = data.get("message", {}).get("items", [])

    # Keep only candidates with DOI, because BibFlow needs DOI to fetch BibTeX.
    items_with_doi = [
        item for item in items
        if item.get("DOI")
    ]

    return items_with_doi


def get_first_list_value(value, default=""):
    """
    Crossref often stores title and journal as lists.
    This helper extracts the first value safely.
    """
    if isinstance(value, list) and value:
        return value[0]
    if isinstance(value, str):
        return value
    return default


def get_crossref_year(item: dict) -> str:
    """
    Extract publication year from Crossref item.
    """
    issued = item.get("issued", {})
    date_parts = issued.get("date-parts", [])

    if date_parts and isinstance(date_parts, list):
        first_date = date_parts[0]
        if first_date:
            return str(first_date[0])

    return "Unknown year"


def get_crossref_authors(item: dict, max_authors: int = 3) -> str:
    """
    Format Crossref authors for display.
    """
    authors = item.get("author", [])

    if not authors:
        return "Unknown author"

    names = []

    for author in authors[:max_authors]:
        given = author.get("given", "")
        family = author.get("family", "")

        full_name = f"{given} {family}".strip()
        if full_name:
            names.append(full_name)

    if len(authors) > max_authors:
        names.append("et al.")

    return ", ".join(names) if names else "Unknown author"


def format_crossref_candidate(item: dict) -> str:
    """
    Format one Crossref search candidate for selectbox display.
    """
    title = get_first_list_value(item.get("title"), "Untitled")
    year = get_crossref_year(item)
    authors = get_crossref_authors(item)
    journal = get_first_list_value(item.get("container-title"), "Unknown venue")
    doi = item.get("DOI", "")

    return f"{title} | {authors} | {year} | {journal} | DOI: {doi}"


def crossref_items_to_rows(items: list) -> list:
    """
    Convert Crossref search results into rows for Streamlit dataframe.
    """
    rows = []

    for item in items:
        rows.append(
            {
                "Title": get_first_list_value(item.get("title"), "Untitled"),
                "Authors": get_crossref_authors(item),
                "Year": get_crossref_year(item),
                "Venue": get_first_list_value(item.get("container-title"), "Unknown venue"),
                "Type": item.get("type", ""),
                "DOI": item.get("DOI", ""),
                "Score": round(float(item.get("score", 0)), 2),
            }
        )

    return rows


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
    Make citation key unique against existing keys and generated keys.
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


def parse_bibtex_entries(raw_bibtex: str) -> list:
    """
    Parse raw BibTeX text and return all entries.
    """
    if not raw_bibtex.strip():
        return []

    parser = bibtexparser.bparser.BibTexParser(common_strings=True)
    database = bibtexparser.loads(raw_bibtex, parser=parser)

    return database.entries


def protect_title_capitalization(title: str) -> str:
    """
    Protect title capitalization for BibTeX by wrapping important capitalized words in braces.

    This is a light-touch cleaner. It avoids changing the whole title too aggressively.
    """
    if not title:
        return title

    # If the title already has braces, keep it as it is.
    if "{" in title or "}" in title:
        return title

    protected_words = []

    for word in title.split():
        clean_word = re.sub(r"[^A-Za-z0-9]", "", word)

        # Protect likely acronyms or important capitalized terms.
        if clean_word.isupper() and len(clean_word) > 1:
            protected_words.append(word.replace(clean_word, "{" + clean_word + "}"))
        else:
            protected_words.append(word)

    return " ".join(protected_words)


def clean_bibtex_entry(
    entry: dict,
    used_keys: set,
    regenerate_key: bool = True,
    protect_titles: bool = True,
    remove_extra_fields: bool = True,
) -> dict:
    """
    Clean a single BibTeX entry.
    """
    cleaned = dict(entry)

    # Normalize DOI
    if "doi" in cleaned:
        cleaned["doi"] = normalize_doi(cleaned["doi"])

    # Clean title
    if "title" in cleaned:
        cleaned["title"] = clean_text(cleaned["title"])
        if protect_titles:
            cleaned["title"] = protect_title_capitalization(cleaned["title"])

    # Clean journal / booktitle / publisher fields
    for field in ["journal", "journaltitle", "booktitle", "publisher"]:
        if field in cleaned:
            cleaned[field] = clean_text(cleaned[field])

    # Clean author field lightly
    if "author" in cleaned:
        cleaned["author"] = re.sub(r"\s+", " ", cleaned["author"]).strip()

    # Remove noisy fields that are often not needed in Overleaf papers
    if remove_extra_fields:
        fields_to_remove = {
            "abstract",
            "file",
            "keywords",
            "mendeley-groups",
            "timestamp",
            "urldate",
            "language",
            "langid",
            "annotation",
        }

        for field in fields_to_remove:
            cleaned.pop(field, None)

    # Generate or validate citation key
    old_key = cleaned.get("ID", "")

    if regenerate_key or not old_key:
        base_key = generate_citation_key(cleaned)
    else:
        base_key = re.sub(r"[^A-Za-z0-9_:-]", "", old_key)

    final_key = make_unique_key(base_key, used_keys)
    cleaned["ID"] = final_key
    used_keys.add(final_key)

    return cleaned


def clean_bibtex_entries(
    entries: list,
    existing_dois: set,
    existing_keys: set,
    skip_existing_doi: bool = True,
    regenerate_key: bool = True,
    protect_titles: bool = True,
    remove_extra_fields: bool = True,
):
    """
    Clean multiple BibTeX entries and return cleaned entries + summary rows.
    """
    cleaned_entries = []
    result_rows = []
    used_keys = set(existing_keys)

    skipped_count = 0

    for entry in entries:
        original_key = entry.get("ID", "")
        raw_doi = normalize_doi(entry.get("doi", "")).lower()

        if raw_doi and skip_existing_doi and raw_doi in existing_dois:
            skipped_count += 1

            result_rows.append(
                {
                    "Original Key": original_key,
                    "New Key": "",
                    "DOI": raw_doi,
                    "Action": "Skipped",
                    "Status": "Skipped because DOI already exists in uploaded .bib",
                }
            )
            continue

        cleaned = clean_bibtex_entry(
            entry=entry,
            used_keys=used_keys,
            regenerate_key=regenerate_key,
            protect_titles=protect_titles,
            remove_extra_fields=remove_extra_fields,
        )

        cleaned_entries.append(cleaned)

        new_key = cleaned.get("ID", "")
        cleaned_doi = normalize_doi(cleaned.get("doi", "")).lower()

        if original_key and original_key != new_key:
            action = "Cleaned with renamed key"
        else:
            action = "Cleaned"

        result_rows.append(
            {
                "Original Key": original_key,
                "New Key": new_key,
                "DOI": cleaned_doi,
                "Action": action,
                "Status": "Cleaned successfully",
            }
        )

    return cleaned_entries, result_rows, skipped_count



# ============================================================
# Session state
# ============================================================

if "title_search_results" not in st.session_state:
    st.session_state.title_search_results = []


# ============================================================
# App layout
# ============================================================

st.title("📚 BibFlow")
st.subheader("A Streamlit Assistant for Zotero–Overleaf BibTeX Workflows")

st.markdown(
    """
    BibFlow helps researchers generate, clean, deduplicate, and export Overleaf-ready BibTeX entries.

    **Version 1.3 features:**

    - Single DOI to BibTeX
    - Batch DOI to BibTeX
    - Clean merge with existing `references.bib`
    - Title search when DOI is unknown
    - Duplicate DOI checking
    - Unique citation key generation
    """
)

st.divider()


# ============================================================
# Sidebar
# ============================================================

st.sidebar.title("Settings")

allow_manual_key = st.sidebar.checkbox(
    "Allow manual citation key editing in Single DOI / Title Search mode",
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
st.sidebar.caption("BibFlow Version 1.3")


# ============================================================
# Tabs
# ============================================================


single_tab, batch_tab, title_tab, cleaner_tab = st.tabs(
    ["Single DOI", "Batch DOI + Clean Merge", "Title Search", "BibTeX Cleaner"]
)


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


# ============================================================
# Title Search workflow
# ============================================================

with title_tab:

    st.markdown("## Title Search when DOI is Unknown")

    st.markdown(
        """
        Use this mode when you know the paper title but do not know the DOI.

        Workflow:

        ```text
        Paper title → Crossref search → choose candidate → generate BibTeX
        ```
        """
    )

    title_query = st.text_input(
        "Paper title",
        placeholder="Example: Variance risk premiums"
    )

    author_query = st.text_input(
        "Author name, optional",
        placeholder="Example: Bollerslev"
    )

    rows_to_return = st.slider(
        "Number of search candidates",
        min_value=3,
        max_value=15,
        value=8
    )

    search_title_button = st.button(
        "Search by Title",
        type="primary",
        key="title_search_button"
    )

    if search_title_button:

        if not title_query.strip():
            st.warning("Please enter a paper title.")
            st.stop()

        with st.spinner("Searching Crossref metadata..."):
            try:
                results = search_crossref_by_title(
                    title=title_query,
                    author=author_query,
                    rows=rows_to_return
                )
                st.session_state.title_search_results = results
            except Exception as e:
                st.error(f"Title search failed: {e}")
                st.stop()

        if not st.session_state.title_search_results:
            st.warning("No DOI-based candidates found. Try a shorter title or add/remove the author name.")
        else:
            st.success(f"Found {len(st.session_state.title_search_results)} candidate(s) with DOI.")

    results = st.session_state.title_search_results

    if results:

        st.markdown("### Search Results")
        st.dataframe(
            crossref_items_to_rows(results),
            use_container_width=True
        )

        candidate_labels = [
            format_crossref_candidate(item)
            for item in results
        ]

        selected_index = st.selectbox(
            "Select the correct paper",
            options=list(range(len(results))),
            format_func=lambda i: candidate_labels[i],
            key="title_candidate_selectbox"
        )

        selected_item = results[selected_index]

        selected_title = get_first_list_value(selected_item.get("title"), "Untitled")
        selected_doi = normalize_doi(selected_item.get("DOI", ""))
        selected_year = get_crossref_year(selected_item)
        selected_authors = get_crossref_authors(selected_item)
        selected_venue = get_first_list_value(selected_item.get("container-title"), "Unknown venue")

        st.markdown("### Selected Candidate")

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Title:** {selected_title}")
            st.write(f"**Authors:** {selected_authors}")
            st.write(f"**Year:** {selected_year}")

        with col2:
            st.write(f"**Venue:** {selected_venue}")
            st.write(f"**DOI:** `{selected_doi}`")

        generate_from_title_button = st.button(
            "Generate BibTeX from Selected Paper",
            type="primary",
            key="title_generate_bibtex_button"
        )

        if generate_from_title_button:

            if not selected_doi:
                st.error("The selected candidate has no DOI.")
                st.stop()

            selected_doi_lower = selected_doi.lower()

            if uploaded_bib is not None and skip_existing_doi and selected_doi_lower in existing_dois:
                st.warning("This DOI already exists in your uploaded .bib file. It was not regenerated.")
                st.stop()

            with st.spinner("Fetching BibTeX from selected DOI..."):
                try:
                    raw_bibtex = fetch_bibtex_from_doi(selected_doi)
                except Exception as e:
                    st.error(f"Failed to fetch BibTeX from selected DOI: {e}")
                    st.stop()

            entry = parse_bibtex(raw_bibtex)

            if entry is None:
                st.error("Could not parse the BibTeX entry.")
                st.stop()

            suggested_key = generate_citation_key(entry)
            final_suggested_key = make_unique_key(suggested_key, set(existing_keys))

            st.success("BibTeX generated successfully from title search.")

            col1, col2 = st.columns(2)

            with col1:
                if selected_doi_lower in existing_dois:
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
                    key="title_citation_key"
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
                key="title_single_download_button"
            )

            if uploaded_bib is not None:
                merged_title_bibtex = build_merged_bib(existing_bib_content, cleaned_bibtex)

                st.markdown("### Clean Merge Preview")
                st.caption("Your uploaded .bib content is preserved. The new entry is appended at the end.")
                st.code(merged_title_bibtex, language="bibtex")

                st.download_button(
                    label="Download merged .bib file",
                    data=merged_title_bibtex,
                    file_name="merged_references.bib",
                    mime="text/plain",
                    key="title_merged_download_button"
                )


# ============================================================
# BibTeX Cleaner workflow
# ============================================================

with cleaner_tab:

    st.markdown("## BibTeX Cleaner & Validator")

    st.markdown(
        """
        Use this mode when you already have raw BibTeX from Google Scholar, Zotero,
        SSRN, arXiv, a journal page, or another reference manager.

        BibFlow can clean the entries, regenerate citation keys, check duplicate DOI records,
        and optionally merge the cleaned entries into your uploaded Overleaf `references.bib`.
        """
    )

    cleaner_col1, cleaner_col2, cleaner_col3 = st.columns(3)

    with cleaner_col1:
        cleaner_regenerate_key = st.checkbox(
            "Regenerate citation keys",
            value=True,
            key="cleaner_regenerate_key"
        )

    with cleaner_col2:
        cleaner_protect_titles = st.checkbox(
            "Protect title acronyms",
            value=True,
            key="cleaner_protect_titles"
        )

    with cleaner_col3:
        cleaner_remove_extra_fields = st.checkbox(
            "Remove noisy extra fields",
            value=True,
            key="cleaner_remove_extra_fields"
        )

    st.markdown("### Input raw BibTeX")

    raw_bibtex_text = st.text_area(
        "Paste raw BibTeX here",
        height=260,
        placeholder="""@article{example,
  title={Example Paper Title},
  author={Smith, John and Doe, Jane},
  journal={Journal of Example Studies},
  year={2024},
  doi={10.xxxx/example}
}""",
        key="cleaner_raw_bibtex_text"
    )

    raw_bibtex_file = st.file_uploader(
        "Or upload a raw .bib file to clean",
        type=["bib"],
        key="cleaner_raw_bibtex_file"
    )

    clean_button = st.button(
        "Clean BibTeX",
        type="primary",
        key="cleaner_clean_button"
    )

    if clean_button:

        file_content = ""

        if raw_bibtex_file is not None:
            file_content = raw_bibtex_file.getvalue().decode("utf-8", errors="ignore")

        combined_raw_bibtex = ""

        if raw_bibtex_text.strip():
            combined_raw_bibtex += raw_bibtex_text.strip()

        if file_content.strip():
            if combined_raw_bibtex:
                combined_raw_bibtex += "\n\n"
            combined_raw_bibtex += file_content.strip()

        if not combined_raw_bibtex.strip():
            st.warning("Please paste raw BibTeX or upload a .bib file.")
            st.stop()

        try:
            raw_entries = parse_bibtex_entries(combined_raw_bibtex)
        except Exception as e:
            st.error(f"Failed to parse BibTeX: {e}")
            st.stop()

        if not raw_entries:
            st.warning("No BibTeX entries were found.")
            st.stop()

        cleaned_entries, cleaner_rows, cleaner_skipped_count = clean_bibtex_entries(
            entries=raw_entries,
            existing_dois=existing_dois,
            existing_keys=existing_keys,
            skip_existing_doi=skip_existing_doi,
            regenerate_key=cleaner_regenerate_key,
            protect_titles=cleaner_protect_titles,
            remove_extra_fields=cleaner_remove_extra_fields,
        )

        st.divider()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Raw entries", len(raw_entries))

        with col2:
            st.metric("Cleaned entries", len(cleaned_entries))

        with col3:
            st.metric("Skipped duplicates", cleaner_skipped_count)

        st.markdown("### Cleaning Summary")
        st.dataframe(cleaner_rows, use_container_width=True)

        if cleaned_entries:

            cleaned_bibtex = entries_to_bibtex(cleaned_entries)

            st.markdown("### Cleaned BibTeX")
            st.code(cleaned_bibtex, language="bibtex")

            st.download_button(
                label="Download cleaned BibTeX",
                data=cleaned_bibtex,
                file_name="bibflow_cleaned_references.bib",
                mime="text/plain",
                key="cleaner_download_cleaned_button"
            )

            if uploaded_bib is not None:
                merged_cleaned_bibtex = build_merged_bib(
                    existing_bib_content,
                    cleaned_bibtex
                )

                st.markdown("### Clean Merged BibTeX")
                st.caption(
                    "Your uploaded .bib content is preserved. Cleaned non-duplicate entries are appended."
                )
                st.code(merged_cleaned_bibtex, language="bibtex")

                st.download_button(
                    label="Download merged cleaned .bib file",
                    data=merged_cleaned_bibtex,
                    file_name="merged_references.bib",
                    mime="text/plain",
                    key="cleaner_download_merged_button"
                )
            else:
                st.info("Upload an existing references.bib file in the sidebar to enable clean merge output.")

        else:
            st.warning("No cleaned entries were generated. They may all be duplicates or invalid entries.")