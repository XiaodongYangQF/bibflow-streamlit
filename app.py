import re
import requests
import pandas as pd
import streamlit as st
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

from pathlib import Path
from difflib import SequenceMatcher

# ============================================================
# Private ranking file paths
# ============================================================


PRIVATE_RANKING_PATH = Path("data/private/journal_rankings_combined_for_bibflow.csv")
DEMO_RANKING_PATH = Path("examples/sample_journal_rankings_demo.csv")


# ============================================================
# Page config
# ============================================================

st.set_page_config(
    page_title="BibFlow",
    page_icon="📚",
    layout="wide"
)


# ============================================================
# App branding and UI helpers
# ============================================================

APP_VERSION = "2.0B"
APP_NAME = "BibFlow"
APP_TAGLINE = "A Research Library Assistant for BibTeX, Overleaf, and Academic Journal Ranking Workflows"


EXPORT_PRESETS = {
    "Overleaf Clean": {
        "description": "Recommended default. Keeps the most useful academic BibTeX fields and removes noisy metadata.",
        "keep_fields": {
            "author", "title", "journal", "journaltitle", "booktitle",
            "year", "date", "volume", "number", "pages", "month",
            "publisher", "doi", "url", "eprint", "archiveprefix",
            "primaryclass", "note"
        },
        "keep_all_fields": False,
    },
    "Minimal Citation": {
        "description": "Compact output for clean LaTeX manuscripts. Keeps only core citation fields.",
        "keep_fields": {
            "author", "title", "journal", "journaltitle", "booktitle",
            "year", "volume", "number", "pages", "doi"
        },
        "keep_all_fields": False,
    },
    "DOI + URL Friendly": {
        "description": "Keeps DOI and URL fields for easier reference tracking.",
        "keep_fields": {
            "author", "title", "journal", "journaltitle", "booktitle",
            "year", "volume", "number", "pages", "publisher",
            "doi", "url"
        },
        "keep_all_fields": False,
    },
    "Full Metadata": {
        "description": "Preserves all parsed BibTeX fields except the citation key is still cleaned if requested.",
        "keep_fields": set(),
        "keep_all_fields": True,
    },
}

# Add citation key style presets

CITATION_KEY_STYLES = {
    "AuthorYearKeyword": {
        "description": "Default style. Example: Bollerslev2009Variance"
    },
    "AuthorYear": {
        "description": "Short and clean. Example: Bollerslev2009"
    },
    "AuthorYearJournal": {
        "description": "Useful when venue matters. Example: Bollerslev2009RFS"
    },
    "AuthorYearShortTitle": {
        "description": "More descriptive key. Example: Bollerslev2009VarianceRisk"
    },
}


JOURNAL_ABBREVIATIONS = {
    "review of financial studies": "RFS",
    "journal of finance": "JF",
    "journal of financial economics": "JFE",
    "journal of financial and quantitative analysis": "JFQA",
    "management science": "MS",
    "econometrica": "ECMA",
    "american economic review": "AER",
    "quarterly journal of economics": "QJE",
    "journal of political economy": "JPE",
    "journal of econometrics": "JE",
}


FIELD_ORDER = [
    "author",
    "title",
    "journal",
    "journaltitle",
    "booktitle",
    "year",
    "date",
    "volume",
    "number",
    "pages",
    "month",
    "publisher",
    "doi",
    "url",
    "eprint",
    "archiveprefix",
    "primaryclass",
    "note",
]



def apply_custom_css():
    """
    Light custom styling for a cleaner portfolio/product look.
    """
    st.markdown(
        """
        <style>
        .bibflow-hero {
            padding: 1.6rem 1.8rem;
            border-radius: 1.2rem;
            background: linear-gradient(135deg, #F8FAFC 0%, #EEF2FF 100%);
            border: 1px solid #E2E8F0;
            margin-bottom: 1.2rem;
        }

        .bibflow-title {
            font-size: 2.35rem;
            font-weight: 800;
            color: #0F172A;
            margin-bottom: 0.25rem;
        }

        .bibflow-subtitle {
            font-size: 1.05rem;
            color: #475569;
            margin-bottom: 0.85rem;
        }

        .bibflow-badge {
            display: inline-block;
            padding: 0.28rem 0.7rem;
            border-radius: 999px;
            background-color: #DBEAFE;
            color: #1D4ED8;
            font-size: 0.85rem;
            font-weight: 700;
            margin-right: 0.4rem;
            margin-top: 0.25rem;
        }

        .feature-card {
            padding: 1rem;
            border-radius: 1rem;
            border: 1px solid #E2E8F0;
            background-color: #FFFFFF;
            min-height: 120px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
        }

        .feature-card-title {
            font-weight: 750;
            color: #0F172A;
            margin-bottom: 0.3rem;
        }

        .feature-card-text {
            color: #475569;
            font-size: 0.92rem;
            line-height: 1.45;
        }

        .small-muted {
            color: #64748B;
            font-size: 0.9rem;
        }

        .bibflow-footer {
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #E2E8F0;
            color: #64748B;
            font-size: 0.88rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def render_header():
    """
    Render the polished app header.
    """
    st.markdown(
        f"""
        <div class="bibflow-hero">
            <div class="bibflow-title">📚 {APP_NAME}</div>
            <div class="bibflow-subtitle">{APP_TAGLINE}</div>
            <span class="bibflow-badge">Version {APP_VERSION}</span>
            <span class="bibflow-badge">Research Workflow Tool</span>
            <span class="bibflow-badge">Overleaf-ready BibTeX</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-card-title">DOI → BibTeX</div>
                <div class="feature-card-text">
                    Generate clean BibTeX entries directly from DOI metadata.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-card-title">Batch Processing</div>
                <div class="feature-card-text">
                    Paste multiple DOIs and export a combined references file.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-card-title">Clean Merge</div>
                <div class="feature-card-text">
                    Upload your current Overleaf .bib file and append only new entries.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-card-title">Cleaner + Quality Report</div>
                <div class="feature-card-text">
                    Clean raw BibTeX and check whether your references file is Overleaf-ready.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with st.expander("How BibFlow fits into the research workflow", expanded=False):
        st.markdown(
            """
            BibFlow is designed for researchers who use **Zotero**, **BibTeX**, and **Overleaf**.

            Typical workflow:

            ```text
            Zotero / DOI / paper title / raw BibTeX
            → BibFlow
            → clean Overleaf-ready references.bib
            → LaTeX writing
            ```

            It helps reduce repetitive manual work such as copying BibTeX from Google Scholar,
            fixing citation keys, removing noisy fields, and checking duplicate references.
            """
        )


def render_footer():
    """
    Render app footer.
    """
    st.markdown(
        f"""
        <div class="bibflow-footer">
            <strong>{APP_NAME}</strong> Version {APP_VERSION} · Built with Streamlit ·
            Designed as a lightweight research workflow assistant for LaTeX and Overleaf users.
        </div>
        """,
        unsafe_allow_html=True
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


def extract_title_keywords(title: str, n_words: int = 2) -> str:
    """
    Extract multiple meaningful title keywords.
    """
    stopwords = {
        "a", "an", "the", "and", "or", "of", "in", "on", "for",
        "to", "with", "by", "from", "using", "based", "evidence",
        "new", "some", "towards", "toward", "into", "across",
        "through", "between", "among", "over", "under", "its",
        "their", "our", "your", "this", "that", "are", "is",
        "be", "as", "at", "we"
    }

    title = clean_text(title)
    words = re.findall(r"[A-Za-z0-9]+", title)

    keywords = []

    for word in words:
        word_lower = word.lower()

        if word_lower not in stopwords and len(word_lower) > 2:
            keywords.append(word.capitalize())

        if len(keywords) >= n_words:
            break

    if not keywords:
        return "Paper"

    return "".join(keywords)


def extract_journal_abbreviation(entry: dict) -> str:
    """
    Extract a short journal abbreviation for citation keys.
    """
    journal = (
        entry.get("journal")
        or entry.get("journaltitle")
        or entry.get("container-title")
        or entry.get("booktitle")
        or ""
    )

    journal_clean = clean_text(journal).lower()

    if journal_clean in JOURNAL_ABBREVIATIONS:
        return JOURNAL_ABBREVIATIONS[journal_clean]

    words = re.findall(r"[A-Za-z]+", journal)

    if not words:
        return "Venue"

    # Use first letters from important words.
    stopwords = {"of", "the", "and", "in", "for"}

    initials = [
        word[0].upper()
        for word in words
        if word.lower() not in stopwords
    ]

    abbreviation = "".join(initials[:4])

    return abbreviation or "Venue"




def generate_citation_key(
    entry: dict,
    citation_key_style: str = "AuthorYearKeyword"
) -> str:
    """
    Generate citation key using selected style.

    Supported styles:
    - AuthorYearKeyword
    - AuthorYear
    - AuthorYearJournal
    - AuthorYearShortTitle
    """
    author = entry.get("author", "")
    year = entry.get("year", "") or entry.get("date", "")
    title = entry.get("title", "")

    last_name = extract_first_author_lastname(author)

    year_match = re.search(r"\d{4}", year)
    year_clean = year_match.group(0) if year_match else "YYYY"

    if citation_key_style == "AuthorYear":
        key = f"{last_name}{year_clean}"

    elif citation_key_style == "AuthorYearJournal":
        journal_abbrev = extract_journal_abbreviation(entry)
        key = f"{last_name}{year_clean}{journal_abbrev}"

    elif citation_key_style == "AuthorYearShortTitle":
        short_title = extract_title_keywords(title, n_words=2)
        key = f"{last_name}{year_clean}{short_title}"

    else:
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


def apply_export_preset_to_entry(entry: dict, export_preset: str) -> dict:
    """
    Apply a BibTeX export preset to one entry.
    """
    preset = EXPORT_PRESETS.get(export_preset, EXPORT_PRESETS["Overleaf Clean"])

    exported = {}

    # BibTeX parser/writer needs these metadata fields.
    if "ENTRYTYPE" in entry:
        exported["ENTRYTYPE"] = entry["ENTRYTYPE"]

    if "ID" in entry:
        exported["ID"] = entry["ID"]

    if preset["keep_all_fields"]:
        for key, value in entry.items():
            if key not in {"ENTRYTYPE", "ID"}:
                exported[key] = value
        return exported

    keep_fields = preset["keep_fields"]

    # Add fields in a stable, readable order.
    for field in FIELD_ORDER:
        if field in keep_fields and field in entry:
            exported[field] = entry[field]

    # Add any remaining allowed fields not included in FIELD_ORDER.
    for key, value in entry.items():
        if key in {"ENTRYTYPE", "ID"}:
            continue

        if key in keep_fields and key not in exported:
            exported[key] = value

    return exported


def apply_export_preset_to_entries(entries: list, export_preset: str) -> list:
    """
    Apply a BibTeX export preset to multiple entries.
    """
    return [
        apply_export_preset_to_entry(entry, export_preset)
        for entry in entries
    ]


def sort_entries_by_key(entries: list) -> list:
    """
    Sort BibTeX entries by citation key.
    """
    return sorted(entries, key=lambda x: x.get("ID", "").lower())


def build_export_header(export_preset: str) -> str:
    """
    Build optional BibFlow export header.
    """
    return (
        "% ============================================================\n"
        f"% Generated by BibFlow Version {APP_VERSION}\n"
        f"% Export preset: {export_preset}\n"
        "% ============================================================\n\n"
    )


def entry_to_bibtex(
    entry: dict,
    export_preset: str = "Overleaf Clean",
    sort_entries: bool = False,
    include_header: bool = False,
) -> str:
    """
    Convert one BibTeX entry dictionary back to BibTeX string.
    """
    return entries_to_bibtex(
        [entry],
        export_preset=export_preset,
        sort_entries=sort_entries,
        include_header=include_header,
    )


def entries_to_bibtex(
    entries: list,
    export_preset: str = "Overleaf Clean",
    sort_entries: bool = False,
    include_header: bool = False,
) -> str:
    """
    Convert multiple BibTeX entries into one BibTeX string using export options.
    """
    export_entries = apply_export_preset_to_entries(entries, export_preset)

    if sort_entries:
        export_entries = sort_entries_by_key(export_entries)

    db = BibDatabase()
    db.entries = export_entries

    writer = BibTexWriter()
    writer.indent = "  "
    writer.order_entries_by = None

    output = writer.write(db).strip()

    if include_header:
        output = build_export_header(export_preset) + output

    return output





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
    citation_key_style: str = "AuthorYearKeyword",
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
        base_key = generate_citation_key(cleaned, citation_key_style=citation_key_style)
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
    citation_key_style: str = "AuthorYearKeyword",
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
            citation_key_style=citation_key_style,
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
# Reference quality report helper functions
# ============================================================

def normalize_text_for_matching(text: str) -> str:
    """
    Normalize text for duplicate-title detection.
    """
    text = clean_text(text).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_weak_citation_key(key: str) -> bool:
    """
    Detect weak or uninformative citation keys.
    """
    if not key:
        return True

    key_clean = key.strip()
    key_lower = key_clean.lower()

    weak_prefixes = (
        "key", "test", "paper", "article", "citation", "ref",
        "unknown", "default", "sample", "example"
    )

    if key_lower.startswith(weak_prefixes):
        return True

    if len(key_clean) <= 4:
        return True

    # Examples: a, b, ref1, paper2, test3
    if re.fullmatch(r"[A-Za-z]+\d?", key_clean) and not re.search(r"\d{4}", key_clean):
        return True

    return False


def build_reference_quality_report(entries: list) -> list:
    """
    Build a quality report for BibTeX entries.
    """
    report_rows = []

    key_counts = {}
    doi_counts = {}
    title_counts = {}

    for entry in entries:
        key = entry.get("ID", "")
        doi = normalize_doi(entry.get("doi", "")).lower()
        title_norm = normalize_text_for_matching(entry.get("title", ""))

        if key:
            key_counts[key] = key_counts.get(key, 0) + 1

        if doi:
            doi_counts[doi] = doi_counts.get(doi, 0) + 1

        if title_norm:
            title_counts[title_norm] = title_counts.get(title_norm, 0) + 1

    for entry in entries:
        key = entry.get("ID", "")
        entry_type = entry.get("ENTRYTYPE", "").lower()
        doi = normalize_doi(entry.get("doi", "")).lower()
        title = clean_text(entry.get("title", ""))
        title_norm = normalize_text_for_matching(title)

        author = clean_text(entry.get("author", ""))
        year = clean_text(entry.get("year", "") or entry.get("date", ""))
        venue = clean_text(
            entry.get("journal", "")
            or entry.get("journaltitle", "")
            or entry.get("booktitle", "")
            or entry.get("publisher", "")
        )

        # Required field checks
        if not key:
            report_rows.append(
                {
                    "Citation Key": key,
                    "Issue": "Missing citation key",
                    "Severity": "High",
                    "Suggestion": "Generate a stable citation key.",
                }
            )

        if not author:
            report_rows.append(
                {
                    "Citation Key": key,
                    "Issue": "Missing author",
                    "Severity": "High",
                    "Suggestion": "Check the source metadata or edit the BibTeX entry manually.",
                }
            )

        if not title:
            report_rows.append(
                {
                    "Citation Key": key,
                    "Issue": "Missing title",
                    "Severity": "High",
                    "Suggestion": "Add the paper title.",
                }
            )

        if not year:
            report_rows.append(
                {
                    "Citation Key": key,
                    "Issue": "Missing year/date",
                    "Severity": "Medium",
                    "Suggestion": "Add the publication year or date.",
                }
            )

        if entry_type in {"article", "inproceedings", "conference"} and not venue:
            report_rows.append(
                {
                    "Citation Key": key,
                    "Issue": "Missing journal/booktitle",
                    "Severity": "Medium",
                    "Suggestion": "Add the journal, conference, booktitle, or publisher field.",
                }
            )

        if not doi and entry_type in {"article", "inproceedings", "conference"}:
            report_rows.append(
                {
                    "Citation Key": key,
                    "Issue": "Missing DOI",
                    "Severity": "Medium",
                    "Suggestion": "Add DOI if available. This helps duplicate detection and reference tracking.",
                }
            )

        # Duplicate checks
        if key and key_counts.get(key, 0) > 1:
            report_rows.append(
                {
                    "Citation Key": key,
                    "Issue": "Duplicate citation key",
                    "Severity": "High",
                    "Suggestion": "Rename one of the duplicated citation keys.",
                }
            )

        if doi and doi_counts.get(doi, 0) > 1:
            report_rows.append(
                {
                    "Citation Key": key,
                    "Issue": "Duplicate DOI",
                    "Severity": "High",
                    "Suggestion": "Remove duplicate entries that refer to the same paper.",
                }
            )

        if title_norm and title_counts.get(title_norm, 0) > 1:
            report_rows.append(
                {
                    "Citation Key": key,
                    "Issue": "Possible duplicate title",
                    "Severity": "Medium",
                    "Suggestion": "Check whether these entries refer to the same work.",
                }
            )

        # Citation key quality
        if is_weak_citation_key(key):
            report_rows.append(
                {
                    "Citation Key": key,
                    "Issue": "Weak citation key",
                    "Severity": "Low",
                    "Suggestion": "Use a clearer key such as AuthorYearKeyword.",
                }
            )

        if len(key) > 45:
            report_rows.append(
                {
                    "Citation Key": key,
                    "Issue": "Very long citation key",
                    "Severity": "Low",
                    "Suggestion": "Consider using a shorter citation key style.",
                }
            )

        if re.search(r"\s", key):
            report_rows.append(
                {
                    "Citation Key": key,
                    "Issue": "Citation key contains spaces",
                    "Severity": "High",
                    "Suggestion": "Remove spaces from citation keys.",
                }
            )

        noisy_fields = [
            field for field in [
                "abstract", "file", "keywords", "timestamp", "annotation",
                "mendeley-groups", "urldate", "language", "langid"
            ]
            if field in entry
        ]

        if noisy_fields:
            report_rows.append(
                {
                    "Citation Key": key,
                    "Issue": f"Noisy fields detected: {', '.join(noisy_fields)}",
                    "Severity": "Low",
                    "Suggestion": "Use BibTeX Cleaner to remove noisy fields before exporting.",
                }
            )

    return report_rows


def summarize_quality_report(report_rows: list) -> dict:
    """
    Summarize issue counts by severity.
    """
    summary = {"High": 0, "Medium": 0, "Low": 0}

    for row in report_rows:
        severity = row.get("Severity", "")

        if severity in summary:
            summary[severity] += 1

    return summary


# ============================================================
# Research Library + Journal Ranking helper functions
# ============================================================

def get_entry_year(entry: dict) -> str:
    """
    Extract publication year from a BibTeX entry.
    """
    year = clean_text(entry.get("year", "") or entry.get("date", ""))

    year_match = re.search(r"\d{4}", year)
    if year_match:
        return year_match.group(0)

    return ""


def get_entry_journal(entry: dict) -> str:
    """
    Extract journal / venue name from a BibTeX entry.
    """
    journal = (
        entry.get("journal", "")
        or entry.get("journaltitle", "")
        or entry.get("booktitle", "")
        or entry.get("publisher", "")
    )

    return clean_text(journal)


def normalize_issn(value: str) -> str:
    """
    Normalize ISSN for matching.
    """
    if value is None or pd.isna(value):
        return ""

    value = str(value).strip().upper()
    value = re.sub(r"[^0-9X]", "", value)

    return value


def get_entry_issn(entry: dict) -> str:
    """
    Extract ISSN / eISSN from BibTeX entry if available.
    """
    issn = (
        entry.get("issn", "")
        or entry.get("eissn", "")
        or entry.get("e-issn", "")
        or entry.get("printissn", "")
        or entry.get("print_issn", "")
    )

    return normalize_issn(issn)


def get_entry_authors_short(entry: dict, max_authors: int = 3) -> str:
    """
    Convert BibTeX author field into a readable short author string.
    """
    author_field = clean_text(entry.get("author", ""))

    if not author_field:
        return ""

    authors = [a.strip() for a in author_field.split(" and ") if a.strip()]

    formatted_authors = []

    for author in authors[:max_authors]:
        if "," in author:
            last, first = author.split(",", 1)
            formatted_authors.append(f"{first.strip()} {last.strip()}".strip())
        else:
            formatted_authors.append(author)

    if len(authors) > max_authors:
        formatted_authors.append("et al.")

    return ", ".join(formatted_authors)


def normalize_journal_name_for_matching(name: str) -> str:
    """
    Normalize journal names for ranking matching.
    """
    if name is None or pd.isna(name):
        return ""

    name = str(name).lower().strip()

    name = name.replace("&", " and ")
    name = name.replace("{", "").replace("}", "")

    # Remove leading article
    name = re.sub(r"^the\s+", "", name)

    # Remove punctuation
    name = re.sub(r"[^a-z0-9\s]", " ", name)

    # Collapse spaces
    name = re.sub(r"\s+", " ", name).strip()

    return name


def normalize_column_name(col: str) -> str:
    """
    Normalize dataframe column names for flexible detection.
    """
    return re.sub(r"[^a-z0-9]", "", str(col).lower())


def find_column(df: pd.DataFrame, candidates: list) -> str:
    """
    Find a column from possible candidate names.
    """
    normalized_cols = {
        normalize_column_name(col): col
        for col in df.columns
    }

    normalized_candidates = [normalize_column_name(c) for c in candidates]

    for candidate in normalized_candidates:
        if candidate in normalized_cols:
            return normalized_cols[candidate]

    for norm_col, original_col in normalized_cols.items():
        for candidate in normalized_candidates:
            if candidate and candidate in norm_col:
                return original_col

    return ""


def standardize_ajg_rating(value: str) -> str:
    """
    Standardize AJG rating values.
    """
    if value is None or pd.isna(value):
        return ""

    value = str(value).strip().upper()
    value = value.replace(" ", "")

    if value in ["4*", "4STAR", "4STARS", "4-STAR", "4-STARS"]:
        return "4*"

    if value in ["4", "3", "2", "1"]:
        return value

    return value


def rating_value(rating: str) -> int:
    """
    Convert AJG rating to numeric order for filtering.
    """
    rating = str(rating).strip()

    mapping = {
        "4*": 5,
        "4": 4,
        "3": 3,
        "2": 2,
        "1": 1,
    }

    return mapping.get(rating, 0)


def standardize_yes_no(value: str) -> str:
    """
    Standardize FT50 indicator.
    """
    if value is None or pd.isna(value):
        return ""

    value = str(value).strip().lower()

    if value in ["yes", "y", "true", "1", "ft50"]:
        return "Yes"

    return ""


def load_ranking_file(uploaded_file) -> pd.DataFrame:
    """
    Load uploaded ranking file.

    Supported:
    - CSV
    - XLSX
    - XLS
    """
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        try:
            return pd.read_csv(uploaded_file)
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding="latin1")

    if file_name.endswith(".xlsx") or file_name.endswith(".xls"):
        return pd.read_excel(uploaded_file)

    raise ValueError("Unsupported ranking file format. Please upload CSV, XLSX, or XLS.")


def load_default_ranking_file() -> tuple:
    """
    Load a default journal ranking file if available.

    Priority:
    1. Private full ranking file
    2. Public demo ranking file
    3. No ranking file

    Returns:
    - raw dataframe or None
    - source label
    - source type
    """
    if PRIVATE_RANKING_PATH.exists():
        raw_df = pd.read_csv(PRIVATE_RANKING_PATH)
        return raw_df, str(PRIVATE_RANKING_PATH), "private"

    if DEMO_RANKING_PATH.exists():
        raw_df = pd.read_csv(DEMO_RANKING_PATH)
        return raw_df, str(DEMO_RANKING_PATH), "demo"

    return None, "", "none"


def standardize_ranking_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize AJG + FT50 ranking data.

    Works with the cleaned combined file:

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
    match_note
    """
    df = raw_df.copy()

    journal_col = find_column(
        df,
        [
            "journal",
            "journal title",
            "journal_title",
            "title",
            "ttitle",
            "source title",
            "publication",
        ],
    )

    journal_norm_col = find_column(
        df,
        [
            "journal_normalized",
            "journal normalized",
            "ranking journal normalized",
        ],
    )

    journal_alias_col = find_column(
        df,
        [
            "journal_alias_normalized",
            "journal alias normalized",
            "alias normalized",
        ],
    )

    issn_col = find_column(
        df,
        [
            "issn",
            "print issn",
            "print_issn",
            "eissn",
            "e-issn",
            "online issn",
        ],
    )

    ajg_col = find_column(
        df,
        [
            "ajg_rating",
            "ajg rating",
            "ajg2024",
            "ajg_2024",
            "abs_rating",
            "abs rank",
            "abs_rank",
            "rating",
            "grade",
            "rank",
        ],
    )

    field_col = find_column(
        df,
        [
            "ajg_field",
            "ajg field",
            "field",
            "subject",
            "subject area",
            "category",
            "area",
            "discipline",
        ],
    )

    source_year_col = find_column(
        df,
        [
            "ajg_source_year",
            "source_year",
            "source year",
            "year",
            "ajg_year",
            "ajg year",
        ],
    )

    ft50_col = find_column(
        df,
        [
            "ft50",
            "ft_50",
            "financial times 50",
            "financial_times_50",
        ],
    )

    ft50_issn_col = find_column(
        df,
        [
            "ft50_issn",
            "ft50 issn",
            "ft_50_issn",
        ],
    )

    ft50_title_col = find_column(
        df,
        [
            "ft50_title",
            "ft50 title",
            "ft_50_title",
        ],
    )

    match_note_col = find_column(
        df,
        [
            "match_note",
            "match note",
            "note",
            "notes",
        ],
    )

    ranking_source_col = find_column(
        df,
        [
            "ranking_source",
            "ranking source",
            "source",
        ],
    )

    if not journal_col:
        raise ValueError(
            "Could not find the journal title column. "
            "Please include a column such as 'journal', 'journal_title', 'title', or 'Ttitle'."
        )

    standardized = pd.DataFrame()

    standardized["Ranking Journal"] = df[journal_col].fillna("").astype(str).str.strip()

    if journal_norm_col:
        standardized["Ranking Journal Normalized"] = (
            df[journal_norm_col]
            .fillna("")
            .astype(str)
            .apply(normalize_journal_name_for_matching)
        )
    else:
        standardized["Ranking Journal Normalized"] = standardized["Ranking Journal"].apply(
            normalize_journal_name_for_matching
        )

    if journal_alias_col:
        standardized["Ranking Journal Alias Normalized"] = (
            df[journal_alias_col]
            .fillna("")
            .astype(str)
            .apply(normalize_journal_name_for_matching)
        )
    else:
        standardized["Ranking Journal Alias Normalized"] = standardized[
            "Ranking Journal Normalized"
        ]

    if issn_col:
        standardized["ISSN"] = df[issn_col].apply(normalize_issn)
    else:
        standardized["ISSN"] = ""

    if ajg_col:
        standardized["AJG Rating"] = df[ajg_col].apply(standardize_ajg_rating)
    else:
        standardized["AJG Rating"] = ""

    if field_col:
        standardized["AJG Field"] = df[field_col].fillna("").astype(str).str.strip()
    else:
        standardized["AJG Field"] = ""

    if source_year_col:
        standardized["AJG Source Year"] = (
            df[source_year_col]
            .fillna("")
            .astype(str)
            .str.strip()
        )
    else:
        standardized["AJG Source Year"] = ""

    if ft50_col:
        standardized["FT50"] = df[ft50_col].apply(standardize_yes_no)
    else:
        standardized["FT50"] = ""

    if ft50_issn_col:
        standardized["FT50 ISSN"] = df[ft50_issn_col].apply(normalize_issn)
    else:
        standardized["FT50 ISSN"] = ""

    if ft50_title_col:
        standardized["FT50 Title"] = df[ft50_title_col].fillna("").astype(str).str.strip()
    else:
        standardized["FT50 Title"] = ""

    if match_note_col:
        standardized["Ranking Match Note"] = df[match_note_col].fillna("").astype(str).str.strip()
    else:
        standardized["Ranking Match Note"] = ""

    if ranking_source_col:
        standardized["Ranking Source"] = df[ranking_source_col].fillna("").astype(str).str.strip()
    else:
        standardized["Ranking Source"] = ""

    standardized = standardized[
        standardized["Ranking Journal Normalized"].str.len() > 0
    ].copy()

    standardized = standardized.drop_duplicates(
        subset=["Ranking Journal Normalized"],
        keep="first"
    )

    return standardized


def bibtex_entries_to_library_rows(entries: list) -> list:
    """
    Convert BibTeX entries into rows for the Research Library table.
    """
    rows = []

    for entry in entries:
        citation_key = entry.get("ID", "")
        entry_type = entry.get("ENTRYTYPE", "")
        title = clean_text(entry.get("title", ""))
        authors = get_entry_authors_short(entry)
        year = get_entry_year(entry)
        journal = get_entry_journal(entry)
        doi = normalize_doi(entry.get("doi", ""))
        issn = get_entry_issn(entry)

        rows.append(
            {
                "Citation Key": citation_key,
                "Entry Type": entry_type,
                "Title": title,
                "Authors": authors,
                "Year": year,
                "Journal / Venue": journal,
                "Journal Normalized": normalize_journal_name_for_matching(journal),
                "DOI": doi,
                "ISSN": issn,

                # Ranking columns
                "AJG Rating": "",
                "AJG Field": "",
                "AJG Source Year": "",
                "FT50": "",
                "Matched Journal": "",
                "Ranking Match Status": "No ranking file loaded",
                "Match Method": "",
                "Match Score": "",
                "Ranking Source": "",
                "Ranking Match Note": "",
            }
        )

    return rows


def match_library_with_ranking(
    library_df: pd.DataFrame,
    ranking_df: pd.DataFrame,
    fuzzy_threshold: float = 0.92,
    enable_fuzzy_matching: bool = True,
) -> pd.DataFrame:
    """
    Match Research Library references with journal ranking data.

    Priority:
    1. ISSN exact match
    2. FT50 ISSN exact match
    3. Exact normalized journal-name match
    4. Exact alias-normalized journal-name match
    5. Conservative fuzzy journal-name match
    """
    enriched = library_df.copy()

    if ranking_df is None or ranking_df.empty:
        return enriched

    ranking_by_journal = (
        ranking_df
        .drop_duplicates(subset=["Ranking Journal Normalized"], keep="first")
        .set_index("Ranking Journal Normalized")
        .to_dict(orient="index")
    )

    ranking_by_alias = (
        ranking_df
        .drop_duplicates(subset=["Ranking Journal Alias Normalized"], keep="first")
        .set_index("Ranking Journal Alias Normalized")
        .to_dict(orient="index")
    )

    ranking_by_issn = {}

    if "ISSN" in ranking_df.columns:
        issn_df = ranking_df[
            ranking_df["ISSN"].fillna("").astype(str).str.len() > 0
        ].copy()

        if not issn_df.empty:
            ranking_by_issn.update(
                issn_df
                .drop_duplicates(subset=["ISSN"], keep="first")
                .set_index("ISSN")
                .to_dict(orient="index")
            )

    if "FT50 ISSN" in ranking_df.columns:
        ft50_issn_df = ranking_df[
            ranking_df["FT50 ISSN"].fillna("").astype(str).str.len() > 0
        ].copy()

        if not ft50_issn_df.empty:
            ranking_by_issn.update(
                ft50_issn_df
                .drop_duplicates(subset=["FT50 ISSN"], keep="first")
                .set_index("FT50 ISSN")
                .to_dict(orient="index")
            )

    ranking_journal_keys = list(ranking_by_journal.keys())

    for idx, row in enriched.iterrows():
        journal_norm = row.get("Journal Normalized", "")
        issn = row.get("ISSN", "")

        matched = None
        match_method = ""
        match_score = ""

        if issn and issn in ranking_by_issn:
            matched = ranking_by_issn[issn]
            match_method = "ISSN exact"
            match_score = "1.00"

        elif journal_norm and journal_norm in ranking_by_journal:
            matched = ranking_by_journal[journal_norm]
            match_method = "Journal exact"
            match_score = "1.00"

        elif journal_norm and journal_norm in ranking_by_alias:
            matched = ranking_by_alias[journal_norm]
            match_method = "Journal alias exact"
            match_score = "1.00"

        elif enable_fuzzy_matching and journal_norm:
            best_key = ""
            best_score = 0.0

            for candidate_key in ranking_journal_keys:
                score = SequenceMatcher(None, journal_norm, candidate_key).ratio()

                if score > best_score:
                    best_score = score
                    best_key = candidate_key

            if best_key and best_score >= fuzzy_threshold:
                matched = ranking_by_journal[best_key]
                match_method = "Journal fuzzy"
                match_score = f"{best_score:.2f}"

        if matched:
            enriched.at[idx, "AJG Rating"] = matched.get("AJG Rating", "")
            enriched.at[idx, "AJG Field"] = matched.get("AJG Field", "")
            enriched.at[idx, "AJG Source Year"] = matched.get("AJG Source Year", "")
            enriched.at[idx, "FT50"] = matched.get("FT50", "")
            enriched.at[idx, "Matched Journal"] = matched.get("Ranking Journal", "")
            enriched.at[idx, "Ranking Match Status"] = "Matched"
            enriched.at[idx, "Match Method"] = match_method
            enriched.at[idx, "Match Score"] = match_score
            enriched.at[idx, "Ranking Source"] = matched.get("Ranking Source", "")
            enriched.at[idx, "Ranking Match Note"] = matched.get("Ranking Match Note", "")
        else:
            enriched.at[idx, "Ranking Match Status"] = "Unmatched"
            enriched.at[idx, "Match Method"] = ""
            enriched.at[idx, "Match Score"] = ""

    return enriched


def filter_library_dataframe(
    df: pd.DataFrame,
    search_text: str = "",
    selected_years: list = None,
    selected_journals: list = None,
    selected_entry_types: list = None,
    selected_ajg_ratings: list = None,
    selected_ft50: list = None,
    selected_match_status: list = None,
    only_ajg_3_plus: bool = False,
    only_ft50: bool = False,
) -> pd.DataFrame:
    """
    Apply search and filters to the Research Library dataframe.
    """
    filtered = df.copy()

    if search_text.strip():
        search_cols = [
            "Citation Key",
            "Title",
            "Authors",
            "Year",
            "Journal / Venue",
            "DOI",
            "ISSN",
            "Entry Type",
            "AJG Rating",
            "AJG Field",
            "FT50",
            "Matched Journal",
            "Ranking Match Status",
        ]

        search_cols = [col for col in search_cols if col in filtered.columns]

        search_blob = (
            filtered[search_cols]
            .fillna("")
            .astype(str)
            .agg(" ".join, axis=1)
            .str.lower()
        )

        filtered = filtered[
            search_blob.str.contains(search_text.strip().lower(), regex=False)
        ]

    if selected_years:
        filtered = filtered[filtered["Year"].isin(selected_years)]

    if selected_journals:
        filtered = filtered[filtered["Journal / Venue"].isin(selected_journals)]

    if selected_entry_types:
        filtered = filtered[filtered["Entry Type"].isin(selected_entry_types)]

    if selected_ajg_ratings:
        filtered = filtered[filtered["AJG Rating"].isin(selected_ajg_ratings)]

    if selected_ft50:
        filtered = filtered[filtered["FT50"].isin(selected_ft50)]

    if selected_match_status:
        filtered = filtered[filtered["Ranking Match Status"].isin(selected_match_status)]

    if only_ajg_3_plus:
        filtered = filtered[
            filtered["AJG Rating"].apply(rating_value) >= rating_value("3")
        ]

    if only_ft50:
        filtered = filtered[filtered["FT50"] == "Yes"]

    return filtered


def summarize_research_library(df: pd.DataFrame) -> dict:
    """
    Build simple summary statistics for the Research Library tab.
    """
    total_references = len(df)

    doi_count = 0
    missing_doi_count = 0
    journal_count = 0
    year_range = "N/A"

    if total_references > 0:
        doi_count = df["DOI"].fillna("").astype(str).str.strip().ne("").sum()
        missing_doi_count = total_references - doi_count

        journal_count = (
            df["Journal / Venue"]
            .fillna("")
            .astype(str)
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .nunique()
        )

        years = (
            df["Year"]
            .fillna("")
            .astype(str)
            .str.extract(r"(\d{4})")[0]
            .dropna()
            .astype(int)
        )

        if not years.empty:
            year_range = f"{years.min()}–{years.max()}"

    return {
        "total_references": total_references,
        "doi_count": int(doi_count),
        "missing_doi_count": int(missing_doi_count),
        "journal_count": int(journal_count),
        "year_range": year_range,
    }


def summarize_ranking_matches(df: pd.DataFrame) -> dict:
    """
    Summarize AJG / FT50 matching results.
    """
    total = len(df)

    matched = 0
    unmatched = 0
    ajg_3_plus = 0
    ajg_4_plus = 0
    ft50_count = 0

    if total > 0:
        matched = (df["Ranking Match Status"] == "Matched").sum()
        unmatched = (df["Ranking Match Status"] == "Unmatched").sum()
        ajg_3_plus = df["AJG Rating"].apply(rating_value).ge(3).sum()
        ajg_4_plus = df["AJG Rating"].apply(rating_value).ge(4).sum()
        ft50_count = (df["FT50"] == "Yes").sum()

    return {
        "matched": int(matched),
        "unmatched": int(unmatched),
        "ajg_3_plus": int(ajg_3_plus),
        "ajg_4_plus": int(ajg_4_plus),
        "ft50_count": int(ft50_count),
    }





# ============================================================
# Session state
# ============================================================

if "title_search_results" not in st.session_state:
    st.session_state.title_search_results = []






# ============================================================
# Custom UI
# ============================================================

apply_custom_css()
render_header()
st.divider()


# ============================================================
# Sidebar
# ============================================================

st.sidebar.title("Settings")


st.sidebar.markdown(
    """
    Use the sidebar to upload your existing Overleaf `references.bib`
    and control duplicate-handling behaviour.
    """
)



allow_manual_key = st.sidebar.checkbox(
    "Allow manual citation key editing in Single DOI / Title Search mode",
    value=True
)

skip_existing_doi = st.sidebar.checkbox(
    "Skip DOI entries already in uploaded .bib",
    value=True
)

# Add citation key selector to sidebar

st.sidebar.markdown("---")
st.sidebar.subheader("Citation Key Options")

citation_key_style = st.sidebar.selectbox(
    "Citation key style",
    options=list(CITATION_KEY_STYLES.keys()),
    index=0
)

st.sidebar.caption(CITATION_KEY_STYLES[citation_key_style]["description"])


st.sidebar.markdown("---")
st.sidebar.subheader("Export Options")

export_preset = st.sidebar.selectbox(
    "BibTeX export preset",
    options=list(EXPORT_PRESETS.keys()),
    index=0
)

st.sidebar.caption(EXPORT_PRESETS[export_preset]["description"])

sort_bib_entries = st.sidebar.checkbox(
    "Sort entries by citation key",
    value=True
)

include_export_header = st.sidebar.checkbox(
    "Add BibFlow export header",
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
st.sidebar.caption(f"BibFlow Version {APP_VERSION}")


# ============================================================
# Tabs
# ============================================================




single_tab, batch_tab, title_tab, cleaner_tab, quality_tab, library_tab = st.tabs(
    [
        "🔎 Single DOI",
        "📦 Batch + Merge",
        "📝 Title Search",
        "🧹 BibTeX Cleaner",
        "📊 Quality Report",
        "📚 Research Library",
    ]
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

        suggested_key = generate_citation_key(entry, citation_key_style=citation_key_style)
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
        cleaned_bibtex = entry_to_bibtex(
            entry,
            export_preset=export_preset,
            sort_entries=sort_bib_entries,
            include_header=include_export_header,
        )

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

                suggested_key = generate_citation_key(entry, citation_key_style=citation_key_style)
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

            new_entries_bibtex = entries_to_bibtex(
                generated_entries,
                export_preset=export_preset,
                sort_entries=sort_bib_entries,
                include_header=include_export_header,
            )

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

            suggested_key = generate_citation_key(entry, citation_key_style=citation_key_style)
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

            cleaned_bibtex = entry_to_bibtex(
                entry,
                export_preset=export_preset,
                sort_entries=sort_bib_entries,
                include_header=include_export_header,
            )

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
            citation_key_style=citation_key_style,
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

            cleaned_bibtex = entries_to_bibtex(
                cleaned_entries,
                export_preset=export_preset,
                sort_entries=sort_bib_entries,
                include_header=include_export_header,
            )

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



# ============================================================
# Reference Quality Report workflow
# ============================================================

with quality_tab:

    st.markdown("## Reference Quality Report")

    st.markdown(
        """
        Use this mode to check whether your `.bib` file is clean and ready for Overleaf.

        BibFlow checks common reference problems such as missing fields, duplicate DOI records,
        duplicate citation keys, weak citation keys, and noisy metadata fields.
        """
    )

    quality_file = st.file_uploader(
        "Upload a .bib file for quality checking",
        type=["bib"],
        key="quality_report_file"
    )

    use_sidebar_bib = False

    if uploaded_bib is not None:
        use_sidebar_bib = st.checkbox(
            "Use the references.bib uploaded in the sidebar",
            value=True,
            key="quality_use_sidebar_bib"
        )

    run_quality_button = st.button(
        "Run Quality Report",
        type="primary",
        key="quality_report_button"
    )

    if run_quality_button:

        quality_content = ""

        if use_sidebar_bib and uploaded_bib is not None:
            quality_content = existing_bib_content

        elif quality_file is not None:
            quality_content = quality_file.getvalue().decode("utf-8", errors="ignore")

        else:
            st.warning("Please upload a .bib file or use the file uploaded in the sidebar.")
            st.stop()

        try:
            quality_entries = parse_bibtex_entries(quality_content)
        except Exception as e:
            st.error(f"Failed to parse .bib file: {e}")
            st.stop()

        if not quality_entries:
            st.warning("No BibTeX entries were found.")
            st.stop()

        report_rows = build_reference_quality_report(quality_entries)
        quality_summary = summarize_quality_report(report_rows)

        st.divider()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total entries", len(quality_entries))

        with col2:
            st.metric("High severity", quality_summary["High"])

        with col3:
            st.metric("Medium severity", quality_summary["Medium"])

        with col4:
            st.metric("Low severity", quality_summary["Low"])

        if not report_rows:
            st.success("No major reference quality issues detected.")
        else:
            st.markdown("### Issues Detected")
            st.dataframe(report_rows, use_container_width=True)

            # Download report as CSV
            import csv
            import io

            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=["Citation Key", "Issue", "Severity", "Suggestion"]
            )
            writer.writeheader()
            writer.writerows(report_rows)

            st.download_button(
                label="Download quality report as CSV",
                data=output.getvalue(),
                file_name="bibflow_reference_quality_report.csv",
                mime="text/csv",
                key="quality_report_download_button"
            )

        st.markdown("### Suggested Next Step")

        if quality_summary["High"] > 0:
            st.warning(
                "High-severity issues were found. Fix duplicate keys, duplicate DOI records, or missing core fields first."
            )
        elif quality_summary["Medium"] > 0:
            st.info(
                "Medium-severity issues were found. The file is usable, but you may want to improve metadata completeness."
            )
        elif quality_summary["Low"] > 0:
            st.info(
                "Only low-severity issues were found. You can use BibTeX Cleaner to remove noisy fields or improve citation keys."
            )
        else:
            st.success("Your `.bib` file looks clean and ready for Overleaf.")



# ============================================================
# Research Library workflow
# ============================================================

with library_tab:

    st.markdown("## Research Library Explorer")

    st.markdown(
        """
        Upload a `.bib` file and turn your references into a searchable research library.

        **Version 2.0B** adds optional journal ranking matching using **AJG 2024** and **FT50**.

        Ranking data is not required:
        - If a private full ranking file exists, BibFlow loads it automatically.
        - If no private file exists, BibFlow can use a small demo ranking file.
        - Users can also upload their own ranking file in the advanced section.
        """
    )

    st.info(
        "For public deployment, the full ranking file should stay private. "
        "Keep it in `data/private/` and exclude this folder from GitHub."
    )

    st.markdown("### 1. Upload BibTeX Library")

    library_bib_file = st.file_uploader(
        "Upload a .bib file for Research Library Explorer",
        type=["bib"],
        key="research_library_bib_file"
    )

    library_content = ""

    if library_bib_file is not None:
        library_content = library_bib_file.getvalue().decode("utf-8", errors="ignore")
    elif existing_bib_content.strip():
        library_content = existing_bib_content

    if not library_content.strip():
        st.warning("Please upload a `.bib` file to explore your research library.")

    else:
        try:
            library_entries = parse_bibtex_entries(library_content)
        except Exception as e:
            st.error(f"Failed to parse the uploaded `.bib` file: {e}")
            library_entries = []

        if not library_entries:
            st.warning("No valid BibTeX entries were found in this file.")

        else:
            library_rows = bibtex_entries_to_library_rows(library_entries)
            library_df = pd.DataFrame(library_rows)

            st.markdown("### 2. Optional Journal Ranking Match")

            st.markdown(
                """
                Journal ranking data is optional.  
                BibFlow can still build your research library even when no ranking file is available.
                """
            )

            default_ranking_raw_df, default_ranking_source, default_ranking_type = load_default_ranking_file()

            ranking_df = None
            ranking_source_label = ""
            ranking_loaded = False
            ranking_source_type = "none"

            if default_ranking_raw_df is not None:
                try:
                    ranking_df = standardize_ranking_dataframe(default_ranking_raw_df)
                    ranking_source_label = default_ranking_source
                    ranking_loaded = True
                    ranking_source_type = default_ranking_type

                    if default_ranking_type == "private":
                        st.success(
                            f"Private ranking file loaded automatically: `{default_ranking_source}`"
                        )

                    elif default_ranking_type == "demo":
                        st.info(
                            f"Small demo ranking file loaded: `{default_ranking_source}`. "
                            "This is only for demonstration and does not contain the full AJG/FT50 list."
                        )

                except Exception as e:
                    st.warning(f"A default ranking file was found but could not be loaded: {e}")
                    ranking_df = None
                    ranking_loaded = False
                    ranking_source_type = "none"

            else:
                st.info(
                    "No default ranking file was found. "
                    "The research library will still work without journal rankings."
                )

            with st.expander("Advanced: upload your own journal ranking file", expanded=False):

                st.markdown(
                    """
                    Uploading a ranking file is optional.

                    Use this when you want to match your references with a full AJG, FT50, ABDC,
                    CSSCI, JCR, or school-specific journal ranking list.

                    Recommended columns:

                    ```text
                    journal
                    issn
                    ajg_rating
                    ajg_field
                    ajg_source_year
                    ft50
                    ft50_issn
                    ft50_title
                    ```
                    """
                )

                ranking_file = st.file_uploader(
                    "Upload optional ranking file",
                    type=["csv", "xlsx", "xls"],
                    key="journal_ranking_file"
                )

                if ranking_file is not None:
                    try:
                        raw_ranking_df = load_ranking_file(ranking_file)
                        ranking_df = standardize_ranking_dataframe(raw_ranking_df)
                        ranking_source_label = ranking_file.name
                        ranking_loaded = True
                        ranking_source_type = "uploaded"

                        st.success(
                            f"Uploaded ranking file loaded successfully: `{ranking_file.name}`"
                        )

                    except Exception as e:
                        st.error(f"Failed to load uploaded ranking file: {e}")
                        ranking_df = None
                        ranking_loaded = False
                        ranking_source_type = "none"

            enable_fuzzy_matching = True
            fuzzy_threshold = 0.92

            if ranking_df is not None and not ranking_df.empty:

                setting_col1, setting_col2 = st.columns(2)

                with setting_col1:
                    enable_fuzzy_matching = st.checkbox(
                        "Enable conservative fuzzy journal-name matching",
                        value=True,
                        key="enable_fuzzy_journal_matching"
                    )

                with setting_col2:
                    fuzzy_threshold = st.slider(
                        "Fuzzy match threshold",
                        min_value=0.80,
                        max_value=1.00,
                        value=0.92,
                        step=0.01,
                        key="fuzzy_match_threshold"
                    )

                with st.expander("Preview standardized ranking data", expanded=False):
                    st.caption(f"Ranking source: {ranking_source_label}")
                    st.caption(f"Ranking source type: {ranking_source_type}")
                    st.dataframe(
                        ranking_df.head(30),
                        use_container_width=True,
                        hide_index=True,
                    )

                library_df = match_library_with_ranking(
                    library_df=library_df,
                    ranking_df=ranking_df,
                    fuzzy_threshold=fuzzy_threshold,
                    enable_fuzzy_matching=enable_fuzzy_matching,
                )

            summary = summarize_research_library(library_df)
            ranking_summary = summarize_ranking_matches(library_df)

            st.markdown("### Library Summary")

            metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)

            with metric_col1:
                st.metric("Total References", summary["total_references"])

            with metric_col2:
                st.metric("With DOI", summary["doi_count"])

            with metric_col3:
                st.metric("Missing DOI", summary["missing_doi_count"])

            with metric_col4:
                st.metric("Unique Journals", summary["journal_count"])

            with metric_col5:
                st.metric("Year Range", summary["year_range"])

            if ranking_loaded:
                st.markdown("### Journal Ranking Summary")

                rank_col1, rank_col2, rank_col3, rank_col4, rank_col5 = st.columns(5)

                with rank_col1:
                    st.metric("Matched", ranking_summary["matched"])

                with rank_col2:
                    st.metric("Unmatched", ranking_summary["unmatched"])

                with rank_col3:
                    st.metric("AJG 3+", ranking_summary["ajg_3_plus"])

                with rank_col4:
                    st.metric("AJG 4 / 4*", ranking_summary["ajg_4_plus"])

                with rank_col5:
                    st.metric("FT50", ranking_summary["ft50_count"])

                ajg_counts = (
                    library_df["AJG Rating"]
                    .fillna("")
                    .replace("", "Unmatched")
                    .value_counts()
                    .reset_index()
                )

                ajg_counts.columns = ["AJG Rating", "Count"]

                ft50_counts = (
                    library_df["FT50"]
                    .fillna("")
                    .replace("", "No")
                    .value_counts()
                    .reset_index()
                )

                ft50_counts.columns = ["FT50", "Count"]

                dist_col1, dist_col2 = st.columns(2)

                with dist_col1:
                    with st.expander("AJG rating distribution", expanded=False):
                        st.dataframe(
                            ajg_counts,
                            use_container_width=True,
                            hide_index=True,
                        )

                with dist_col2:
                    with st.expander("FT50 distribution", expanded=False):
                        st.dataframe(
                            ft50_counts,
                            use_container_width=True,
                            hide_index=True,
                        )

            st.divider()

            st.markdown("### Search and Filter")

            search_text = st.text_input(
                "Search references",
                placeholder="Search by title, author, journal, DOI, ISSN, AJG field, or citation key",
                key="library_search_text"
            )

            filter_col1, filter_col2, filter_col3 = st.columns(3)

            with filter_col1:
                year_options = sorted(
                    [
                        y for y in library_df["Year"].dropna().astype(str).unique()
                        if y.strip()
                    ],
                    reverse=True
                )

                selected_years = st.multiselect(
                    "Filter by year",
                    options=year_options,
                    key="library_year_filter"
                )

            with filter_col2:
                journal_options = sorted(
                    [
                        j for j in library_df["Journal / Venue"].dropna().astype(str).unique()
                        if j.strip()
                    ]
                )

                selected_journals = st.multiselect(
                    "Filter by journal / venue",
                    options=journal_options,
                    key="library_journal_filter"
                )

            with filter_col3:
                entry_type_options = sorted(
                    [
                        t for t in library_df["Entry Type"].dropna().astype(str).unique()
                        if t.strip()
                    ]
                )

                selected_entry_types = st.multiselect(
                    "Filter by entry type",
                    options=entry_type_options,
                    key="library_entry_type_filter"
                )

            rank_filter_col1, rank_filter_col2, rank_filter_col3 = st.columns(3)

            with rank_filter_col1:
                ajg_rating_options = sorted(
                    [
                        r for r in library_df["AJG Rating"].dropna().astype(str).unique()
                        if r.strip()
                    ],
                    key=rating_value,
                    reverse=True
                )

                selected_ajg_ratings = st.multiselect(
                    "Filter by AJG rating",
                    options=ajg_rating_options,
                    key="library_ajg_rating_filter"
                )

            with rank_filter_col2:
                ft50_options = sorted(
                    [
                        r for r in library_df["FT50"].dropna().astype(str).unique()
                        if r.strip()
                    ]
                )

                selected_ft50 = st.multiselect(
                    "Filter by FT50",
                    options=ft50_options,
                    key="library_ft50_filter"
                )

            with rank_filter_col3:
                match_status_options = sorted(
                    [
                        s for s in library_df["Ranking Match Status"].dropna().astype(str).unique()
                        if s.strip()
                    ]
                )

                selected_match_status = st.multiselect(
                    "Filter by match status",
                    options=match_status_options,
                    key="library_match_status_filter"
                )

            quick_filter_col1, quick_filter_col2 = st.columns(2)

            with quick_filter_col1:
                only_ajg_3_plus = st.checkbox(
                    "Show only AJG 3+",
                    value=False,
                    key="only_ajg_3_plus_filter"
                )

            with quick_filter_col2:
                only_ft50 = st.checkbox(
                    "Show only FT50",
                    value=False,
                    key="only_ft50_filter"
                )

            filtered_library_df = filter_library_dataframe(
                df=library_df,
                search_text=search_text,
                selected_years=selected_years,
                selected_journals=selected_journals,
                selected_entry_types=selected_entry_types,
                selected_ajg_ratings=selected_ajg_ratings,
                selected_ft50=selected_ft50,
                selected_match_status=selected_match_status,
                only_ajg_3_plus=only_ajg_3_plus,
                only_ft50=only_ft50,
            )

            display_columns = [
                "Citation Key",
                "Title",
                "Authors",
                "Year",
                "Journal / Venue",
                "DOI",
                "ISSN",
                "AJG Rating",
                "AJG Field",
                "AJG Source Year",
                "FT50",
                "Matched Journal",
                "Ranking Match Status",
                "Match Method",
                "Match Score",
                "Entry Type",
            ]

            display_columns = [
                col for col in display_columns
                if col in filtered_library_df.columns
            ]

            st.markdown("### Library Table")

            st.caption(
                f"Showing {len(filtered_library_df)} of {len(library_df)} references."
            )

            st.dataframe(
                filtered_library_df[display_columns],
                use_container_width=True,
                hide_index=True,
            )

            st.divider()

            st.markdown("### Export")

            csv_data = filtered_library_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="Download filtered enriched research library as CSV",
                data=csv_data,
                file_name="bibflow_enriched_research_library_filtered.csv",
                mime="text/csv",
                key="download_enriched_research_library_csv"
            )

            full_csv_data = library_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="Download full enriched research library as CSV",
                data=full_csv_data,
                file_name="bibflow_enriched_research_library_full.csv",
                mime="text/csv",
                key="download_full_enriched_research_library_csv"
            )

            unmatched_df = library_df[
                library_df["Ranking Match Status"] == "Unmatched"
            ].copy()

            if ranking_loaded and not unmatched_df.empty:
                unmatched_csv = unmatched_df.to_csv(index=False).encode("utf-8")

                st.download_button(
                    label="Download unmatched journals for manual checking",
                    data=unmatched_csv,
                    file_name="bibflow_unmatched_journals.csv",
                    mime="text/csv",
                    key="download_unmatched_journals_csv"
                )

            st.markdown("### Interpretation Notes")

            st.markdown(
                """
                - AJG ranks **journals**, not individual papers.
                - The correct interpretation is: *this paper is published in an AJG 3 journal*.
                - FT50 also identifies journals, not paper quality directly.
                - Fuzzy matches should be manually checked, especially when the match score is below 1.00.
                - Keep the full ranking file private unless redistribution is clearly allowed.
                """
            )


render_footer()