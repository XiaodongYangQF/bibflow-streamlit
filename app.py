import re
import html as html_lib
from urllib.parse import unquote
from datetime import datetime
import traceback
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

APP_VERSION = "2.5"
APP_NAME = "BibFlow"
APP_TAGLINE = "A polished research library assistant for BibTeX, Overleaf, Zotero HTML exports, journal rankings, and literature review workflows"


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
                <div class="feature-card-title">Library + Dashboard</div>
                <div class="feature-card-text">
                    Explore references, match rankings, restore notes, and export literature-review reports.
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
            → clean references.bib + annotated research library
            → Overleaf writing + literature-review planning
            ```

            It helps reduce repetitive manual work such as copying BibTeX from Google Scholar,
            fixing citation keys, removing noisy fields, checking duplicate references, tracking reading progress,
            and preparing literature-review summaries.
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



DOI_REGEX = re.compile(r"10\.\d{4,9}/[^\s<>'\"\\]+", flags=re.IGNORECASE)


def clean_extracted_doi(candidate: str) -> str:
    """
    Clean a DOI extracted from HTML, links, or Z3988 metadata.
    """
    if not candidate:
        return ""

    doi = html_lib.unescape(str(candidate))
    doi = unquote(doi)
    doi = normalize_doi(doi)

    # Cut off common HTML/query-string artifacts after DOI extraction.
    doi = re.split(r"[\s<>\"']", doi)[0]
    doi = doi.split("&")[0]
    doi = doi.split("#")[0]

    # Remove trailing punctuation often attached in rendered bibliographies.
    doi = doi.strip().strip(".,;:)]}")

    return doi


def extract_dois_from_text(raw_text: str) -> list:
    """
    Extract unique DOIs from arbitrary text.
    """
    if not raw_text:
        return []

    decoded_texts = [
        str(raw_text),
        html_lib.unescape(str(raw_text)),
        unquote(html_lib.unescape(str(raw_text))),
    ]

    found = []
    seen = set()

    for text in decoded_texts:
        for match in DOI_REGEX.findall(text):
            doi = clean_extracted_doi(match)
            doi_lower = doi.lower()
            if doi and doi_lower not in seen:
                seen.add(doi_lower)
                found.append(doi)

    return found


def extract_dois_from_zotero_html(html_content: str) -> dict:
    """
    Extract DOI candidates from Zotero-exported bibliography HTML.

    Supports:
    - visible DOI links, e.g. https://doi.org/10.xxxx/xxxxx
    - Z3988 metadata spans, e.g. rft_id=info:doi/10.xxxx/xxxxx
    - plain DOI text in rendered bibliography entries
    """
    if not html_content:
        return {
            "unique_dois": [],
            "all_dois": [],
            "csl_entry_count": 0,
            "z3988_count": 0,
            "doi_link_count": 0,
        }

    raw = str(html_content)
    decoded = unquote(html_lib.unescape(raw))

    # Count useful Zotero/CSL markers for diagnostics.
    csl_entry_count = len(re.findall(r'class=["\'][^"\']*csl-entry[^"\']*["\']', raw, flags=re.IGNORECASE))
    z3988_count = len(re.findall(r'class=["\'][^"\']*Z3988[^"\']*["\']', raw, flags=re.IGNORECASE))
    doi_link_count = len(re.findall(r'https?://(?:dx\.)?doi\.org/', raw, flags=re.IGNORECASE))

    candidate_sources = []
    candidate_sources.extend(extract_dois_from_text(raw))
    candidate_sources.extend(extract_dois_from_text(decoded))

    # Explicitly target Z3988 OpenURL DOI fields after URL decoding.
    for match in re.findall(r'(?:rft_id=info:doi/|rft_id=doi:)(10\.\d{4,9}/[^&"\'<>\s]+)', decoded, flags=re.IGNORECASE):
        candidate_sources.append(clean_extracted_doi(match))

    # Explicitly target DOI links.
    for match in re.findall(r'https?://(?:dx\.)?doi\.org/(10\.\d{4,9}/[^"\'<>\s]+)', decoded, flags=re.IGNORECASE):
        candidate_sources.append(clean_extracted_doi(match))

    unique_dois = []
    seen = set()
    for doi in candidate_sources:
        cleaned = clean_extracted_doi(doi)
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            unique_dois.append(cleaned)

    return {
        "unique_dois": unique_dois,
        "all_dois": candidate_sources,
        "csl_entry_count": csl_entry_count,
        "z3988_count": z3988_count,
        "doi_link_count": doi_link_count,
    }


def strip_html_tags(value: str) -> str:
    """
    Very small HTML-to-text helper used only for bibliography previews.
    """
    if not value:
        return ""
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html_lib.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def extract_csl_entry_preview(html_content: str, max_entries: int = 20) -> list:
    """
    Extract a lightweight preview of visible CSL bibliography entries from Zotero HTML.
    """
    if not html_content:
        return []

    entries = re.findall(
        r'<div[^>]*class=["\'][^"\']*csl-entry[^"\']*["\'][^>]*>(.*?)</div>',
        html_content,
        flags=re.IGNORECASE | re.DOTALL,
    )

    preview = []
    for i, entry_html in enumerate(entries[:max_entries], start=1):
        preview.append({"#": i, "Bibliography Entry Preview": strip_html_tags(entry_html)})

    return preview


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

    BibTeX metadata fetched from DOI/Crossref can contain HTML entities
    such as S&amp;P or Journal of Banking &amp; Finance. Decode them here so
    previews, citation-key generation, ranking matching, and exports all use
    normal text before LaTeX escaping is applied at export time.
    """
    if not text:
        return ""

    text = html_lib.unescape(str(text))
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


MONTH_MAP = {
    "1": "jan", "01": "jan", "jan": "jan", "january": "jan",
    "2": "feb", "02": "feb", "feb": "feb", "february": "feb",
    "3": "mar", "03": "mar", "mar": "mar", "march": "mar",
    "4": "apr", "04": "apr", "apr": "apr", "april": "apr",
    "5": "may", "05": "may", "may": "may",
    "6": "jun", "06": "jun", "jun": "jun", "june": "jun",
    "7": "jul", "07": "jul", "jul": "jul", "july": "jul",
    "8": "aug", "08": "aug", "aug": "aug", "august": "aug",
    "9": "sep", "09": "sep", "sep": "sep", "sept": "sep", "september": "sep",
    "10": "oct", "oct": "oct", "october": "oct",
    "11": "nov", "nov": "nov", "november": "nov",
    "12": "dec", "dec": "dec", "december": "dec",
}


def normalize_bibtex_month(value) -> str:
    """
    Normalize month values to BibTeX-safe short forms.
    Examples:
    june -> jun
    sept -> sep
    September -> sep
    """
    if value is None:
        return ""

    key = str(value).strip().strip("{}").strip('"').strip("'").lower().replace(".", "")

    return MONTH_MAP.get(key, key)


def normalize_raw_bibtex_month_field(raw_bibtex: str) -> str:
    """
    Fix problematic month fields before bibtexparser reads the entry.

    This version handles both multi-line and one-line BibTeX entries, for example:

        month = june,
        month = {june},
        month={sept},
        year={2025}, month = sept, pages={1--10}

    The previous version only matched month fields at the beginning of a line.
    Some DOI providers return one-line BibTeX, so `month = june` or
    `month = sept` could still reach bibtexparser and fail.
    """
    if not raw_bibtex:
        return raw_bibtex

    def replace_month(match):
        prefix = match.group(1)
        raw_value = match.group(2)
        suffix = match.group(3)

        normalized = normalize_bibtex_month(raw_value)

        if normalized:
            return f"{prefix}{{{normalized}}}{suffix}"

        return match.group(0)

    # Do not anchor at line start. DOI/Crossref often returns one-line BibTeX.
    # The value part supports {month}, "month", and unbraced month tokens.
    return re.sub(
        r"(?i)(\bmonth\s*=\s*)(\{[^{}]*\}|\"[^\"]*\"|'[^']*'|[^,\n}]+)(\s*,?)",
        replace_month,
        raw_bibtex,
    )


def load_bibtex_database(raw_bibtex: str):
    """
    Load BibTeX robustly after normalizing month fields.

    First try common_strings=True, which understands standard BibTeX
    month macros. If a provider still gives a non-standard macro, fall
    back to common_strings=False instead of failing the whole DOI.
    """
    raw_bibtex = normalize_raw_bibtex_month_field(raw_bibtex)

    parser = bibtexparser.bparser.BibTexParser(common_strings=True)

    try:
        return bibtexparser.loads(raw_bibtex, parser=parser)
    except KeyError:
        fallback_parser = bibtexparser.bparser.BibTexParser(common_strings=False)
        return bibtexparser.loads(raw_bibtex, parser=fallback_parser)


def parse_bibtex(raw_bibtex: str):
    """
    Parse BibTeX and return first entry.
    """
    database = load_bibtex_database(raw_bibtex)

    if not database.entries:
        return None

    return database.entries[0]


# ============================================================
# BibTeX / LaTeX export safety helpers
# ============================================================

BIBTEX_RAW_EXPORT_FIELDS = {
    "doi",
    "url",
    "link",
    "file",
    "eprint",
    "archiveprefix",
    "primaryclass",
    "issn",
    "isbn",
}


def decode_bibtex_html_entities(value) -> str:
    """
    Decode HTML entities commonly returned by metadata providers.

    Examples:
    - S&amp;P 500 -> S&P 500
    - Journal of Banking &amp; Finance -> Journal of Banking & Finance
    """
    if value is None:
        return ""

    return html_lib.unescape(str(value)).strip()


def normalize_bibtex_page_range(value) -> str:
    """
    Normalize page ranges for BibTeX output.

    Metadata providers may return an en dash, em dash, or mojibake
    caused by encoding problems. BibTeX page ranges should use double
    hyphens, e.g. 151--180.
    """
    text = decode_bibtex_html_entities(value)

    replacements = {
        "â€“": "--",   # mojibake for en dash
        "â€”": "--",   # mojibake for em dash
        "–": "--",    # en dash
        "—": "--",    # em dash
        "−": "-",     # mathematical minus sign
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Normalize accidental spaces around page ranges.
    text = re.sub(r"\s*--\s*", "--", text)

    return text


def escape_latex_special_chars(value) -> str:
    """
    Decode HTML entities first, then escape LaTeX special characters in
    normal BibTeX text fields.

    This prevents LaTeX/BibTeX errors such as:
    - Misplaced alignment tab character &

    Examples:
    - S&amp;P 500 -> S\\&P 500
    - Journal of Banking &amp; Finance -> Journal of Banking \\& Finance
    """
    text = decode_bibtex_html_entities(value)

    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
    }

    result = ""

    for i, char in enumerate(text):
        previous = text[i - 1] if i > 0 else ""

        # Avoid double escaping existing LaTeX, e.g. keep \& as \&.
        if char in replacements and previous != "\\":
            result += replacements[char]
        else:
            result += char

    return result


def prepare_bibtex_export_value(key: str, value) -> str:
    """
    Prepare one BibTeX field value before BibTexWriter writes the entry.
    """
    key_lower = str(key).lower()

    if key_lower == "pages":
        return normalize_bibtex_page_range(value)

    if key_lower == "month":
        return normalize_bibtex_month(value)

    if key_lower in BIBTEX_RAW_EXPORT_FIELDS:
        return decode_bibtex_html_entities(value)

    return escape_latex_special_chars(value)


def apply_export_preset_to_entry(
    entry: dict,
    export_preset: str,
    remove_url_when_doi_exists: bool = True,
) -> dict:
    """
    Apply a BibTeX export preset to one entry.

    This is also the central BibTeX export-safety layer. Every exported
    normal text field is HTML-decoded and LaTeX-escaped here, so all workflows
    that call entry_to_bibtex() / entries_to_bibtex() benefit from the fix:
    Single DOI, Batch DOI, Title Search, Zotero HTML Import, and BibTeX Cleaner.
    """
    preset = EXPORT_PRESETS.get(export_preset, EXPORT_PRESETS["Overleaf Clean"])

    exported = {}

    # BibTeX parser/writer needs these metadata fields.
    if "ENTRYTYPE" in entry:
        exported["ENTRYTYPE"] = entry["ENTRYTYPE"]

    if "ID" in entry:
        exported["ID"] = entry["ID"]

    has_doi = bool(normalize_doi(decode_bibtex_html_entities(entry.get("doi", ""))))

    def should_skip_export_field(field_name: str) -> bool:
        """
        Optionally remove URL when DOI is available.

        For journal articles, DOI is usually cleaner than repeating
        http://dx.doi.org/... in the bibliography. This keeps exported
        references shorter and avoids bold "URL:" lines in some LaTeX styles.
        """
        return (
            remove_url_when_doi_exists
            and has_doi
            and str(field_name).lower() == "url"
        )

    if preset["keep_all_fields"]:
        for key, value in entry.items():
            if key in {"ENTRYTYPE", "ID"} or should_skip_export_field(key):
                continue
            exported[key] = prepare_bibtex_export_value(key, value)
        return exported

    keep_fields = preset["keep_fields"]

    # Add fields in a stable, readable order.
    for field in FIELD_ORDER:
        if field in keep_fields and field in entry:
            if should_skip_export_field(field):
                continue
            exported[field] = prepare_bibtex_export_value(field, entry[field])

    # Add any remaining allowed fields not included in FIELD_ORDER.
    for key, value in entry.items():
        if key in {"ENTRYTYPE", "ID"} or should_skip_export_field(key):
            continue

        if key in keep_fields and key not in exported:
            exported[key] = prepare_bibtex_export_value(key, value)

    return exported


def apply_export_preset_to_entries(
    entries: list,
    export_preset: str,
    remove_url_when_doi_exists: bool = True,
) -> list:
    """
    Apply a BibTeX export preset to multiple entries.
    """
    return [
        apply_export_preset_to_entry(
            entry,
            export_preset,
            remove_url_when_doi_exists=remove_url_when_doi_exists,
        )
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
    remove_url_when_doi_exists: bool = True,
) -> str:
    """
    Convert one BibTeX entry dictionary back to BibTeX string.
    """
    return entries_to_bibtex(
        [entry],
        export_preset=export_preset,
        sort_entries=sort_entries,
        include_header=include_header,
        remove_url_when_doi_exists=remove_url_when_doi_exists,
    )


def entries_to_bibtex(
    entries: list,
    export_preset: str = "Overleaf Clean",
    sort_entries: bool = False,
    include_header: bool = False,
    remove_url_when_doi_exists: bool = True,
) -> str:
    """
    Convert multiple BibTeX entries into one BibTeX string using export options.
    """
    export_entries = apply_export_preset_to_entries(
        entries,
        export_preset,
        remove_url_when_doi_exists=remove_url_when_doi_exists,
    )

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
    database = load_bibtex_database(content)

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

    database = load_bibtex_database(raw_bibtex)

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

    name = html_lib.unescape(str(name)).lower().strip()

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



def standardize_abdc_rating(value: str) -> str:
    """
    Standardize ABDC-style ratings.
    """
    if value is None or pd.isna(value):
        return ""

    value = str(value).strip().upper()
    value = value.replace(" ", "")

    if value in ["A*", "A+", "APLUS", "A-STAR", "ASTAR"]:
        return "A*"

    if value in ["A", "B", "C"]:
        return value

    return value


def abdc_rating_value(rating: str) -> int:
    """
    Convert ABDC-style ratings to numeric order.
    """
    rating = str(rating).strip().upper()

    mapping = {
        "A*": 4,
        "A+": 4,
        "A": 3,
        "B": 2,
        "C": 1,
    }

    return mapping.get(rating, 0)


def standardize_quartile(value: str) -> str:
    """
    Standardize JCR/SJR-style quartiles.
    """
    if value is None or pd.isna(value):
        return ""

    value = str(value).strip().upper()
    value = value.replace(" ", "")

    if value in ["1", "Q1", "QUARTILE1"]:
        return "Q1"
    if value in ["2", "Q2", "QUARTILE2"]:
        return "Q2"
    if value in ["3", "Q3", "QUARTILE3"]:
        return "Q3"
    if value in ["4", "Q4", "QUARTILE4"]:
        return "Q4"

    return value


def quartile_value(value: str) -> int:
    """
    Convert quartile to numeric order where Q1 is highest.
    """
    value = str(value).strip().upper()

    mapping = {
        "Q1": 4,
        "Q2": 3,
        "Q3": 2,
        "Q4": 1,
    }

    return mapping.get(value, 0)


def standardize_list_indicator(value: str) -> str:
    """
    Standardize journal-list membership indicators such as CSSCI or Chinese Core.
    """
    if value is None or pd.isna(value):
        return ""

    value = str(value).strip()
    value_lower = value.lower()

    if value_lower in ["yes", "y", "true", "1", "included", "core", "cssci", "中文核心", "北大核心", "c"]:
        return "Yes"

    if value_lower in ["no", "n", "false", "0", "not included", "none", "nan"]:
        return ""

    return value

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
    Standardize uploaded journal ranking data for Version 2.2 multi-ranking support.

    Supported ranking columns are optional. BibFlow tries to detect them flexibly:
    - AJG/ABS rating and field
    - FT50 membership
    - ABDC rating and field
    - JCR/SJR quartiles
    - CSSCI / Chinese-core indicators
    - school-specific tiers
    - custom user-defined ratings and tags
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

    abdc_col = find_column(
        df,
        [
            "abdc_rating",
            "abdc rating",
            "abdc",
            "abdc_rank",
            "abdc rank",
            "abdc2022",
            "abdc_2022",
        ],
    )

    abdc_field_col = find_column(
        df,
        [
            "abdc_field",
            "abdc field",
            "abdc_for_code",
            "abdc for code",
            "abdc_subject",
            "abdc subject",
        ],
    )

    jcr_quartile_col = find_column(
        df,
        [
            "jcr_quartile",
            "jcr quartile",
            "jcr",
            "jif_quartile",
            "jif quartile",
            "wos_quartile",
            "web of science quartile",
        ],
    )

    sjr_quartile_col = find_column(
        df,
        [
            "sjr_quartile",
            "sjr quartile",
            "sjr",
            "scimago_quartile",
            "scimago quartile",
        ],
    )

    cssci_col = find_column(
        df,
        [
            "cssci",
            "cssci_status",
            "cssci status",
            "cssci_source",
            "cssci source",
        ],
    )

    ssci_col = find_column(
        df,
        [
            "ssci",
            "ssci_status",
            "ssci status",
            "ssci_indexed",
            "ssci indexed",
            "social sciences citation index",
        ],
    )

    ssci_categories_col = find_column(
        df,
        [
            "ssci_categories",
            "ssci categories",
            "web of science categories",
            "wos categories",
            "categories",
        ],
    )

    chinese_core_col = find_column(
        df,
        [
            "chinese_core",
            "chinese core",
            "pkucore",
            "pku core",
            "beida_core",
            "beida core",
            "北大核心",
            "中文核心",
        ],
    )

    school_tier_col = find_column(
        df,
        [
            "school_tier",
            "school tier",
            "school_rank",
            "school rank",
            "ucd_tier",
            "university_tier",
            "internal_tier",
            "internal tier",
        ],
    )

    custom_rating_col = find_column(
        df,
        [
            "custom_rating",
            "custom rating",
            "custom_rank",
            "custom rank",
            "user_rating",
            "user rating",
            "personal_rating",
            "personal rating",
        ],
    )

    ranking_tags_col = find_column(
        df,
        [
            "ranking_tags",
            "ranking tags",
            "tags",
            "ranking_label",
            "ranking label",
            "list_name",
            "list name",
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

    standardized["ISSN"] = df[issn_col].apply(normalize_issn) if issn_col else ""
    standardized["AJG Rating"] = df[ajg_col].apply(standardize_ajg_rating) if ajg_col else ""
    standardized["AJG Field"] = df[field_col].fillna("").astype(str).str.strip() if field_col else ""
    standardized["AJG Source Year"] = df[source_year_col].fillna("").astype(str).str.strip() if source_year_col else ""

    standardized["FT50"] = df[ft50_col].apply(standardize_yes_no) if ft50_col else ""
    standardized["FT50 ISSN"] = df[ft50_issn_col].apply(normalize_issn) if ft50_issn_col else ""
    standardized["FT50 Title"] = df[ft50_title_col].fillna("").astype(str).str.strip() if ft50_title_col else ""

    standardized["ABDC Rating"] = df[abdc_col].apply(standardize_abdc_rating) if abdc_col else ""
    standardized["ABDC Field"] = df[abdc_field_col].fillna("").astype(str).str.strip() if abdc_field_col else ""
    standardized["JCR Quartile"] = df[jcr_quartile_col].apply(standardize_quartile) if jcr_quartile_col else ""
    standardized["SJR Quartile"] = df[sjr_quartile_col].apply(standardize_quartile) if sjr_quartile_col else ""
    standardized["CSSCI"] = df[cssci_col].apply(standardize_list_indicator) if cssci_col else ""
    standardized["SSCI"] = df[ssci_col].apply(standardize_list_indicator) if ssci_col else ""
    standardized["SSCI Categories"] = df[ssci_categories_col].fillna("").astype(str).str.strip() if ssci_categories_col else ""
    standardized["Chinese Core"] = df[chinese_core_col].apply(standardize_list_indicator) if chinese_core_col else ""
    standardized["School Tier"] = df[school_tier_col].fillna("").astype(str).str.strip() if school_tier_col else ""
    standardized["Custom Rating"] = df[custom_rating_col].fillna("").astype(str).str.strip() if custom_rating_col else ""
    standardized["Ranking Tags"] = df[ranking_tags_col].fillna("").astype(str).str.strip() if ranking_tags_col else ""

    standardized["Ranking Match Note"] = df[match_note_col].fillna("").astype(str).str.strip() if match_note_col else ""
    standardized["Ranking Source"] = df[ranking_source_col].fillna("").astype(str).str.strip() if ranking_source_col else ""

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
                "ABDC Rating": "",
                "ABDC Field": "",
                "JCR Quartile": "",
                "SJR Quartile": "",
                "CSSCI": "",
                "SSCI": "",
                "SSCI Categories": "",
                "Chinese Core": "",
                "School Tier": "",
                "Custom Rating": "",
                "Ranking Tags": "",
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

    ranking_columns_to_copy = [
        "AJG Rating",
        "AJG Field",
        "AJG Source Year",
        "FT50",
        "ABDC Rating",
        "ABDC Field",
        "JCR Quartile",
        "SJR Quartile",
        "CSSCI",
        "SSCI",
        "SSCI Categories",
        "Chinese Core",
        "School Tier",
        "Custom Rating",
        "Ranking Tags",
        "Ranking Source",
        "Ranking Match Note",
    ]

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
            for col in ranking_columns_to_copy:
                if col in enriched.columns:
                    enriched.at[idx, col] = matched.get(col, "")

            enriched.at[idx, "Matched Journal"] = matched.get("Ranking Journal", "")
            enriched.at[idx, "Ranking Match Status"] = "Matched"
            enriched.at[idx, "Match Method"] = match_method
            enriched.at[idx, "Match Score"] = match_score
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
    selected_abdc_ratings: list = None,
    selected_jcr_quartiles: list = None,
    selected_sjr_quartiles: list = None,
    selected_cssci: list = None,
    selected_ssci: list = None,
    selected_chinese_core: list = None,
    selected_school_tiers: list = None,
    selected_custom_ratings: list = None,
    selected_match_status: list = None,
    only_ajg_3_plus: bool = False,
    only_ft50: bool = False,
    only_abdc_a_plus: bool = False,
    only_abdc_a_or_above: bool = False,
    only_jcr_q1: bool = False,
    only_sjr_q1: bool = False,
    only_cssci: bool = False,
    only_ssci: bool = False,
    only_chinese_core: bool = False,
    selected_reading_status: list = None,
    selected_priorities: list = None,
    selected_paper_types: list = None,
    only_citation_candidates: bool = False,
    only_important: bool = False,
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
            "ABDC Rating",
            "ABDC Field",
            "JCR Quartile",
            "SJR Quartile",
            "CSSCI",
            "SSCI",
            "SSCI Categories",
            "Chinese Core",
            "School Tier",
            "Custom Rating",
            "Ranking Tags",
            "Matched Journal",
            "Ranking Match Status",
            "Reading Status",
            "Paper Type",
            "Priority",
            "Research Tags",
            "Notes",
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

    if selected_abdc_ratings:
        filtered = filtered[filtered["ABDC Rating"].isin(selected_abdc_ratings)]

    if selected_jcr_quartiles:
        filtered = filtered[filtered["JCR Quartile"].isin(selected_jcr_quartiles)]

    if selected_sjr_quartiles:
        filtered = filtered[filtered["SJR Quartile"].isin(selected_sjr_quartiles)]

    if selected_cssci:
        filtered = filtered[filtered["CSSCI"].isin(selected_cssci)]

    if selected_ssci:
        filtered = filtered[filtered["SSCI"].isin(selected_ssci)]

    if selected_chinese_core:
        filtered = filtered[filtered["Chinese Core"].isin(selected_chinese_core)]

    if selected_school_tiers:
        filtered = filtered[filtered["School Tier"].isin(selected_school_tiers)]

    if selected_custom_ratings:
        filtered = filtered[filtered["Custom Rating"].isin(selected_custom_ratings)]

    if selected_match_status:
        filtered = filtered[filtered["Ranking Match Status"].isin(selected_match_status)]

    if only_ajg_3_plus:
        filtered = filtered[
            filtered["AJG Rating"].apply(rating_value) >= rating_value("3")
        ]

    if only_ft50:
        filtered = filtered[filtered["FT50"] == "Yes"]

    if only_abdc_a_plus:
        filtered = filtered[filtered["ABDC Rating"].apply(abdc_rating_value) >= abdc_rating_value("A*")]

    if only_abdc_a_or_above:
        filtered = filtered[filtered["ABDC Rating"].apply(abdc_rating_value) >= abdc_rating_value("A")]

    if only_jcr_q1:
        filtered = filtered[filtered["JCR Quartile"] == "Q1"]

    if only_sjr_q1:
        filtered = filtered[filtered["SJR Quartile"] == "Q1"]

    if only_cssci:
        filtered = filtered[filtered["CSSCI"].fillna("").astype(str).str.strip().ne("")]

    if only_ssci:
        filtered = filtered[filtered["SSCI"].fillna("").astype(str).str.strip().ne("")]

    if only_chinese_core:
        filtered = filtered[filtered["Chinese Core"].fillna("").astype(str).str.strip().ne("")]

    if selected_reading_status:
        filtered = filtered[filtered["Reading Status"].isin(selected_reading_status)]

    if selected_priorities:
        filtered = filtered[filtered["Priority"].isin(selected_priorities)]

    if selected_paper_types:
        filtered = filtered[filtered["Paper Type"].isin(selected_paper_types)]

    if only_citation_candidates:
        filtered = filtered[filtered["Citation Candidate"].astype(bool)]

    if only_important:
        filtered = filtered[filtered["Important"].astype(bool)]

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
    Summarize multi-ranking matching results.
    """
    total = len(df)

    matched = 0
    unmatched = 0
    ajg_3_plus = 0
    ajg_4_plus = 0
    ft50_count = 0
    abdc_a_plus = 0
    abdc_a_or_above = 0
    jcr_q1 = 0
    sjr_q1 = 0
    cssci_count = 0
    ssci_count = 0
    chinese_core_count = 0

    if total > 0:
        matched = (df["Ranking Match Status"] == "Matched").sum()
        unmatched = (df["Ranking Match Status"] == "Unmatched").sum()
        ajg_3_plus = df["AJG Rating"].apply(rating_value).ge(3).sum()
        ajg_4_plus = df["AJG Rating"].apply(rating_value).ge(4).sum()
        ft50_count = (df["FT50"] == "Yes").sum()
        abdc_a_plus = df["ABDC Rating"].apply(abdc_rating_value).ge(abdc_rating_value("A*")).sum()
        abdc_a_or_above = df["ABDC Rating"].apply(abdc_rating_value).ge(abdc_rating_value("A")).sum()
        jcr_q1 = (df["JCR Quartile"] == "Q1").sum()
        sjr_q1 = (df["SJR Quartile"] == "Q1").sum()
        cssci_count = df["CSSCI"].fillna("").astype(str).str.strip().ne("").sum()
        ssci_count = df["SSCI"].fillna("").astype(str).str.strip().ne("").sum()
        chinese_core_count = df["Chinese Core"].fillna("").astype(str).str.strip().ne("").sum()

    return {
        "matched": int(matched),
        "unmatched": int(unmatched),
        "ajg_3_plus": int(ajg_3_plus),
        "ajg_4_plus": int(ajg_4_plus),
        "ft50_count": int(ft50_count),
        "abdc_a_plus": int(abdc_a_plus),
        "abdc_a_or_above": int(abdc_a_or_above),
        "jcr_q1": int(jcr_q1),
        "sjr_q1": int(sjr_q1),
        "cssci_count": int(cssci_count),
        "ssci_count": int(ssci_count),
        "chinese_core_count": int(chinese_core_count),
    }

# ============================================================
# Research annotation helper functions
# ============================================================

READING_STATUS_OPTIONS = [
    "Unread",
    "Reading",
    "Read",
    "To revisit",
    "Skimmed",
]

PRIORITY_OPTIONS = [
    "Low",
    "Medium",
    "High",
    "Core paper",
]

PAPER_TYPE_OPTIONS = [
    "",
    "Methodology paper",
    "Theory paper",
    "Empirical paper",
    "Literature review",
    "Dataset paper",
    "Application paper",
    "Background reading",
]

ANNOTATION_COLUMNS = [
    "Reading Status",
    "Paper Type",
    "Priority",
    "Research Tags",
    "Citation Candidate",
    "Important",
    "Notes",
]


def build_annotation_id(row: pd.Series) -> str:
    """
    Build a stable ID for storing annotations during the Streamlit session.

    Citation Key is preferred. If missing, use title + year + journal.
    """
    citation_key = str(row.get("Citation Key", "")).strip()

    if citation_key:
        base = citation_key
    else:
        base = "|".join(
            [
                str(row.get("Title", "")).strip(),
                str(row.get("Year", "")).strip(),
                str(row.get("Journal / Venue", "")).strip(),
            ]
        )

    base = base.lower()
    base = re.sub(r"[^a-z0-9]+", "_", base)
    base = re.sub(r"_+", "_", base).strip("_")

    return base


def add_annotation_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add editable annotation columns to the research library dataframe.
    """
    annotated = df.copy()

    if "Annotation ID" not in annotated.columns:
        annotated["Annotation ID"] = annotated.apply(build_annotation_id, axis=1)

    default_values = {
        "Reading Status": "Unread",
        "Paper Type": "",
        "Priority": "Medium",
        "Research Tags": "",
        "Citation Candidate": False,
        "Important": False,
        "Notes": "",
    }

    for col, default_value in default_values.items():
        if col not in annotated.columns:
            annotated[col] = default_value

    return annotated


def initialize_annotation_store() -> None:
    """
    Initialize Streamlit session-state storage for annotations.
    """
    if "research_library_annotations" not in st.session_state:
        st.session_state["research_library_annotations"] = {}


def apply_annotation_store(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply saved session annotations to the current dataframe.
    """
    initialize_annotation_store()

    annotated = df.copy()
    store = st.session_state["research_library_annotations"]

    for idx, row in annotated.iterrows():
        annotation_id = row.get("Annotation ID", "")

        if annotation_id in store:
            for col in ANNOTATION_COLUMNS:
                if col in store[annotation_id]:
                    annotated.at[idx, col] = store[annotation_id][col]

    return annotated


def update_annotation_store(edited_df: pd.DataFrame) -> None:
    """
    Save edited annotations back to Streamlit session state.
    """
    initialize_annotation_store()

    store = st.session_state["research_library_annotations"]

    for _, row in edited_df.iterrows():
        annotation_id = row.get("Annotation ID", "")

        if not annotation_id:
            annotation_id = build_annotation_id(row)

        if not annotation_id:
            continue

        store[annotation_id] = {
            col: row.get(col, "")
            for col in ANNOTATION_COLUMNS
            if col in edited_df.columns
        }

    st.session_state["research_library_annotations"] = store


def summarize_annotations(df: pd.DataFrame) -> dict:
    """
    Summarize reading and annotation progress.
    """
    if df.empty:
        return {
            "read": 0,
            "reading": 0,
            "important": 0,
            "citation_candidates": 0,
            "core_papers": 0,
        }

    read_count = (df["Reading Status"] == "Read").sum()
    reading_count = (df["Reading Status"] == "Reading").sum()
    important_count = df["Important"].astype(bool).sum()
    citation_candidates = df["Citation Candidate"].astype(bool).sum()
    core_papers = (df["Priority"] == "Core paper").sum()

    return {
        "read": int(read_count),
        "reading": int(reading_count),
        "important": int(important_count),
        "citation_candidates": int(citation_candidates),
        "core_papers": int(core_papers),
    }



# ============================================================
# Research dashboard and report helper functions
# ============================================================

def make_count_table(
    df: pd.DataFrame,
    column: str,
    empty_label: str = "Unspecified",
    order: list = None,
) -> pd.DataFrame:
    """
    Build a count table for dashboard summaries.
    """
    if df.empty or column not in df.columns:
        return pd.DataFrame(columns=[column, "Count", "Share (%)"])

    values = df[column].fillna("").astype(str).str.strip()
    values = values.replace("", empty_label)

    count_df = values.value_counts(dropna=False).reset_index()
    count_df.columns = [column, "Count"]

    total = int(count_df["Count"].sum())
    if total > 0:
        count_df["Share (%)"] = (count_df["Count"] / total * 100).round(1)
    else:
        count_df["Share (%)"] = 0.0

    if order:
        order_map = {value: idx for idx, value in enumerate(order)}
        count_df["_order"] = count_df[column].map(order_map).fillna(len(order) + 1)
        count_df = count_df.sort_values(["_order", "Count"], ascending=[True, False])
        count_df = count_df.drop(columns=["_order"])

    return count_df.reset_index(drop=True)


def make_tag_frequency_table(
    df: pd.DataFrame,
    tag_col: str = "Research Tags",
    top_n: int = 20,
) -> pd.DataFrame:
    """
    Split comma/semicolon-separated research tags and build a frequency table.
    """
    if df.empty or tag_col not in df.columns:
        return pd.DataFrame(columns=["Research Tag", "Count"])

    tag_counts = {}

    for raw_tags in df[tag_col].fillna("").astype(str):
        raw_tags = raw_tags.replace(";", ",")
        tags = [tag.strip().lower() for tag in raw_tags.split(",") if tag.strip()]

        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    if not tag_counts:
        return pd.DataFrame(columns=["Research Tag", "Count"])

    tag_df = pd.DataFrame(
        sorted(tag_counts.items(), key=lambda item: item[1], reverse=True),
        columns=["Research Tag", "Count"],
    )

    return tag_df.head(top_n).reset_index(drop=True)



def first_non_empty(df: pd.DataFrame, col_name: str) -> str:
    """
    Return the first non-empty value from a dataframe column.
    """
    if col_name not in df.columns:
        return ""

    values = df[col_name].fillna("").astype(str).str.strip()
    values = values[values != ""]

    if values.empty:
        return ""

    return values.iloc[0]


def make_top_journal_table(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """
    Build a top-journals table with multi-ranking context.
    """
    required_col = "Journal / Venue"

    output_columns = [
        "Journal / Venue",
        "Count",
        "Best AJG Rating",
        "FT50",
        "Best ABDC Rating",
        "Best JCR Quartile",
        "Best SJR Quartile",
        "SSCI",
    ]

    if df.empty or required_col not in df.columns:
        return pd.DataFrame(columns=output_columns)

    working = df.copy()
    working[required_col] = working[required_col].fillna("").astype(str).str.strip()
    working = working[working[required_col] != ""]

    if working.empty:
        return pd.DataFrame(columns=output_columns)

    rows = []

    for journal, group in working.groupby(required_col):
        ratings = group.get("AJG Rating", pd.Series(dtype=str)).fillna("").astype(str).tolist()
        best_rating = ""
        best_value = -1

        for rating in ratings:
            value = rating_value(rating)
            if value > best_value:
                best_value = value
                best_rating = rating

        abdc_ratings = group.get("ABDC Rating", pd.Series(dtype=str)).fillna("").astype(str).tolist()
        best_abdc = ""
        best_abdc_value = -1

        for rating in abdc_ratings:
            value = abdc_rating_value(rating)
            if value > best_abdc_value:
                best_abdc_value = value
                best_abdc = rating

        def best_quartile(col_name: str) -> str:
            quartiles = group.get(col_name, pd.Series(dtype=str)).fillna("").astype(str).tolist()
            best_q = ""
            best_q_value = -1

            for q in quartiles:
                value = quartile_value(q)
                if value > best_q_value:
                    best_q_value = value
                    best_q = q

            return best_q

        ft50_flag = "Yes" if "FT50" in group.columns and (group["FT50"] == "Yes").any() else ""
        ssci_flag = "Yes" if "SSCI" in group.columns and group["SSCI"].fillna("").astype(str).str.strip().ne("").any() else ""

        rows.append(
            {
                "Journal / Venue": journal,
                "Count": len(group),
                "Best AJG Rating": best_rating,
                "FT50": ft50_flag,
                "Best ABDC Rating": best_abdc,
                "Best JCR Quartile": best_quartile("JCR Quartile"),
                "Best SJR Quartile": best_quartile("SJR Quartile"),
                "SSCI": ssci_flag,
            }
        )

    top_df = pd.DataFrame(rows)
    top_df = top_df.sort_values(["Count", "Journal / Venue"], ascending=[False, True])

    return top_df.head(top_n).reset_index(drop=True)


def make_focus_paper_table(
    df: pd.DataFrame,
    condition_col: str = None,
    condition_value=True,
    max_rows: int = 20,
) -> pd.DataFrame:
    """
    Build a compact table for important/core/citation-candidate papers.
    """
    if df.empty:
        return pd.DataFrame()

    working = df.copy()

    if condition_col and condition_col in working.columns:
        if isinstance(condition_value, bool):
            working = working[working[condition_col].astype(bool) == condition_value]
        else:
            working = working[working[condition_col] == condition_value]

    columns = [
        "Citation Key",
        "Title",
        "Year",
        "Journal / Venue",
        "AJG Rating",
        "FT50",
        "ABDC Rating",
        "JCR Quartile",
        "SJR Quartile",
        "SSCI",
        "Reading Status",
        "Priority",
        "Paper Type",
        "Research Tags",
        "Notes",
    ]

    columns = [col for col in columns if col in working.columns]

    if working.empty:
        return pd.DataFrame(columns=columns)

    if "Year" in working.columns:
        working = working.sort_values("Year", ascending=False)

    return working[columns].head(max_rows).reset_index(drop=True)

def dataframe_to_simple_markdown(df: pd.DataFrame, max_rows: int = 20) -> str:
    """
    Convert a small dataframe into a simple markdown table without requiring tabulate.
    """
    if df is None or df.empty:
        return "_No records._"

    display_df = df.head(max_rows).fillna("").astype(str)

    def clean_cell(value: str) -> str:
        value = str(value).replace("|", "\\|")
        value = re.sub(r"\s+", " ", value).strip()
        return value

    columns = list(display_df.columns)
    header = "| " + " | ".join(clean_cell(col) for col in columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"

    rows = []
    for _, row in display_df.iterrows():
        rows.append("| " + " | ".join(clean_cell(row[col]) for col in columns) + " |")

    return "\n".join([header, separator] + rows)



def build_literature_review_report(df: pd.DataFrame, scope_label: str = "Filtered library") -> str:
    """
    Build a downloadable markdown report for the current research library view.
    """
    working = df.copy()

    summary = summarize_research_library(working)
    ranking_summary = summarize_ranking_matches(working)
    annotation_summary = summarize_annotations(working)

    ajg_table = make_count_table(
        working,
        "AJG Rating",
        empty_label="Unmatched / No AJG rating",
        order=["4*", "4", "3", "2", "1", "Unmatched / No AJG rating"],
    )
    abdc_table = make_count_table(
        working,
        "ABDC Rating",
        empty_label="No ABDC rating",
        order=["A*", "A", "B", "C", "No ABDC rating"],
    )
    jcr_table = make_count_table(
        working,
        "JCR Quartile",
        empty_label="No JCR quartile",
        order=["Q1", "Q2", "Q3", "Q4", "No JCR quartile"],
    )
    sjr_table = make_count_table(
        working,
        "SJR Quartile",
        empty_label="No SJR quartile",
        order=["Q1", "Q2", "Q3", "Q4", "No SJR quartile"],
    )
    reading_table = make_count_table(working, "Reading Status", empty_label="Unspecified")
    priority_table = make_count_table(working, "Priority", empty_label="Unspecified")
    paper_type_table = make_count_table(working, "Paper Type", empty_label="Unspecified")
    field_table = make_count_table(working, "AJG Field", empty_label="Unspecified field")
    tag_table = make_tag_frequency_table(working, top_n=20)
    top_journals = make_top_journal_table(working, top_n=15)
    citation_candidates = make_focus_paper_table(
        working,
        condition_col="Citation Candidate",
        condition_value=True,
        max_rows=20,
    )
    core_papers = make_focus_paper_table(
        working,
        condition_col="Priority",
        condition_value="Core paper",
        max_rows=20,
    )
    important_papers = make_focus_paper_table(
        working,
        condition_col="Important",
        condition_value=True,
        max_rows=20,
    )

    report = f"""# BibFlow Literature Review Report

**Scope:** {scope_label}  
**Generated by:** BibFlow Version {APP_VERSION}

## 1. Library Overview

- Total references: {summary['total_references']}
- References with DOI: {summary['doi_count']}
- References missing DOI: {summary['missing_doi_count']}
- Unique journals / venues: {summary['journal_count']}
- Year range: {summary['year_range']}

## 2. Journal Ranking Overview

- Matched journals: {ranking_summary['matched']}
- Unmatched journals: {ranking_summary['unmatched']}
- AJG 3+ references: {ranking_summary['ajg_3_plus']}
- AJG 4 / 4* references: {ranking_summary['ajg_4_plus']}
- FT50 references: {ranking_summary['ft50_count']}
- ABDC A* references: {ranking_summary['abdc_a_plus']}
- ABDC A / A* references: {ranking_summary['abdc_a_or_above']}
- JCR Q1 references: {ranking_summary['jcr_q1']}
- SJR Q1 references: {ranking_summary['sjr_q1']}
- SSCI references: {ranking_summary['ssci_count']}

### AJG Rating Distribution

{dataframe_to_simple_markdown(ajg_table)}

### ABDC Rating Distribution

{dataframe_to_simple_markdown(abdc_table)}

### JCR Quartile Distribution

{dataframe_to_simple_markdown(jcr_table)}

### SJR Quartile Distribution

{dataframe_to_simple_markdown(sjr_table)}

### AJG Field Distribution

{dataframe_to_simple_markdown(field_table)}

### Top Journals / Venues

{dataframe_to_simple_markdown(top_journals)}

## 3. Reading Progress

- Read: {annotation_summary['read']}
- Reading: {annotation_summary['reading']}
- Important: {annotation_summary['important']}
- Citation candidates: {annotation_summary['citation_candidates']}
- Core papers: {annotation_summary['core_papers']}

### Reading Status Distribution

{dataframe_to_simple_markdown(reading_table)}

### Priority Distribution

{dataframe_to_simple_markdown(priority_table)}

### Paper Type Distribution

{dataframe_to_simple_markdown(paper_type_table)}

### Research Tag Frequency

{dataframe_to_simple_markdown(tag_table)}

## 4. Citation Pipeline

### Core Papers

{dataframe_to_simple_markdown(core_papers)}

### Citation Candidates

{dataframe_to_simple_markdown(citation_candidates)}

### Important Papers

{dataframe_to_simple_markdown(important_papers)}

## 5. Interpretation Notes

- Journal rankings classify journals or journal-list membership, not individual paper quality.
- AJG/ABS, ABDC, FT50, SSCI, and JCR/SJR indicators have different purposes and should not be mechanically compared.
- Fuzzy journal matches should be manually checked.
- Use this report as a literature-review management summary, not as a mechanical quality judgement.
"""

    return report

def build_export_filename(stem: str, extension: str = "csv") -> str:
    """
    Build a dated export filename for cleaner file management.
    """
    clean_stem = re.sub(r"[^A-Za-z0-9_\-]+", "_", stem).strip("_")
    clean_extension = extension.lstrip(".")
    date_label = datetime.now().strftime("%Y%m%d")

    return f"{clean_stem}_{date_label}.{clean_extension}"


def build_version_testing_checklist() -> str:
    """
    Build a compact manual testing checklist for Version 2.0F.
    """
    return """
### Version 2.2 manual testing checklist

Use this checklist before pushing or deploying the app.

```text
1. Run: streamlit run app.py
2. Test Single DOI with a known DOI.
3. Test Batch + Merge with 2-3 DOI values.
4. Test Zotero HTML Import with a bibliography HTML export.
5. Test BibTeX Cleaner with a messy .bib file.
5. Test Quality Report with a problematic .bib file.
6. Open Research Library and upload a .bib file.
7. Confirm ranking match works with demo/private/uploaded ranking data, including multi-ranking columns.
8. Edit Reading Status, Priority, Tags, Citation Candidate, Important, and Notes.
9. Download the full annotated CSV.
10. Refresh the app and restore the annotated CSV.
11. Confirm annotations come back correctly.
12. Download the literature-review report and dashboard summary tables.
13. Check unmatched journals and fuzzy matches manually.
```

Recommended sample files:

```text
examples/sample_references.bib
examples/problematic_references.bib
examples/sample_journal_rankings_demo.csv
```
""".strip()


def build_library_health_messages(
    library_df: pd.DataFrame,
    summary: dict,
    ranking_summary: dict,
    annotation_summary: dict,
    ranking_loaded: bool = False,
) -> list:
    """
    Build practical UI messages for quick quality checks.
    """
    messages = []
    total = max(int(summary.get("total_references", 0)), 1)

    missing_doi_count = int(summary.get("missing_doi_count", 0))
    missing_doi_share = missing_doi_count / total

    if missing_doi_share >= 0.30:
        messages.append(
            (
                "warning",
                f"{missing_doi_count} references are missing DOI values. "
                "This can weaken duplicate detection and metadata tracking."
            )
        )
    elif missing_doi_count > 0:
        messages.append(
            (
                "info",
                f"{missing_doi_count} references are missing DOI values. "
                "This is acceptable, but you may want to improve key references first."
            )
        )

    if ranking_loaded:
        unmatched = int(ranking_summary.get("unmatched", 0))
        unmatched_share = unmatched / total

        if unmatched_share >= 0.30:
            messages.append(
                (
                    "warning",
                    f"{unmatched} references are unmatched against the ranking file. "
                    "Download the unmatched journals CSV and check journal names or aliases."
                )
            )
        elif unmatched > 0:
            messages.append(
                (
                    "info",
                    f"{unmatched} references are unmatched against the ranking file. "
                    "This is normal for books, working papers, conferences, or naming differences."
                )
            )

        if "Match Method" in library_df.columns:
            fuzzy_count = library_df["Match Method"].fillna("").astype(str).eq("Journal fuzzy").sum()
            if fuzzy_count > 0:
                messages.append(
                    (
                        "info",
                        f"{int(fuzzy_count)} references were matched using fuzzy journal-name matching. "
                        "Manually review these rows before relying on the ranking labels."
                    )
                )

    unread = total - int(annotation_summary.get("read", 0))
    if unread == total and total > 0:
        messages.append(
            (
                "info",
                "No references are marked as Read yet. Use the editable table to start tracking reading progress."
            )
        )

    if int(annotation_summary.get("citation_candidates", 0)) == 0 and total > 0:
        messages.append(
            (
                "info",
                "No citation candidates are marked yet. Mark likely thesis/paper references to build a citation pipeline."
            )
        )

    if not messages:
        messages.append(("success", "The current library view looks clean. Continue with filtering, annotation, and export."))

    return messages


# ============================================================
# Annotation import / restore helper functions
# ============================================================

def parse_bool_for_annotation(value) -> bool:
    """
    Convert common CSV boolean values to True/False for annotation columns.
    """
    if isinstance(value, bool):
        return value

    if value is None or pd.isna(value):
        return False

    value = str(value).strip().lower()

    return value in {"true", "yes", "y", "1", "checked", "important"}


def load_annotated_library_file(uploaded_file) -> pd.DataFrame:
    """
    Load a previously exported annotated research library file.

    Supported formats:
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

    raise ValueError("Unsupported annotation file format. Please upload CSV, XLSX, or XLS.")


def prepare_imported_annotations(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize a previously exported annotated library file before restoring annotations.
    """
    imported = raw_df.copy()

    # Build Annotation ID if an older export does not contain it.
    if "Annotation ID" not in imported.columns:
        imported["Annotation ID"] = imported.apply(build_annotation_id, axis=1)
    else:
        missing_id_mask = imported["Annotation ID"].fillna("").astype(str).str.strip().eq("")
        if missing_id_mask.any():
            imported.loc[missing_id_mask, "Annotation ID"] = imported.loc[
                missing_id_mask
            ].apply(build_annotation_id, axis=1)

    # Add missing annotation columns with safe defaults.
    defaults = {
        "Reading Status": "Unread",
        "Paper Type": "",
        "Priority": "Medium",
        "Research Tags": "",
        "Citation Candidate": False,
        "Important": False,
        "Notes": "",
    }

    for col, default_value in defaults.items():
        if col not in imported.columns:
            imported[col] = default_value

    # Normalize dropdown values so Streamlit selectbox columns do not fail.
    imported["Reading Status"] = imported["Reading Status"].fillna("Unread").astype(str)
    imported.loc[~imported["Reading Status"].isin(READING_STATUS_OPTIONS), "Reading Status"] = "Unread"

    imported["Priority"] = imported["Priority"].fillna("Medium").astype(str)
    imported.loc[~imported["Priority"].isin(PRIORITY_OPTIONS), "Priority"] = "Medium"

    imported["Paper Type"] = imported["Paper Type"].fillna("").astype(str)
    imported.loc[~imported["Paper Type"].isin(PAPER_TYPE_OPTIONS), "Paper Type"] = ""

    imported["Research Tags"] = imported["Research Tags"].fillna("").astype(str)
    imported["Notes"] = imported["Notes"].fillna("").astype(str)

    imported["Citation Candidate"] = imported["Citation Candidate"].apply(parse_bool_for_annotation)
    imported["Important"] = imported["Important"].apply(parse_bool_for_annotation)

    return imported


def import_annotations_into_store(imported_df: pd.DataFrame, overwrite_existing: bool = True) -> dict:
    """
    Restore annotations from an imported annotated CSV/XLSX into session state.

    Returns a small summary dictionary for the UI.
    """
    initialize_annotation_store()

    prepared = prepare_imported_annotations(imported_df)
    store = st.session_state["research_library_annotations"]

    imported_count = 0
    skipped_count = 0

    for _, row in prepared.iterrows():
        annotation_id = str(row.get("Annotation ID", "")).strip()

        if not annotation_id:
            skipped_count += 1
            continue

        if annotation_id in store and not overwrite_existing:
            skipped_count += 1
            continue

        store[annotation_id] = {
            col: row.get(col, "")
            for col in ANNOTATION_COLUMNS
            if col in prepared.columns
        }

        imported_count += 1

    st.session_state["research_library_annotations"] = store

    return {
        "imported": imported_count,
        "skipped": skipped_count,
        "total_rows": len(prepared),
    }


def clear_annotation_store() -> None:
    """
    Clear all current session annotations.
    """
    st.session_state["research_library_annotations"] = {}



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

remove_url_when_doi_exists = st.sidebar.checkbox(
    "Remove URL when DOI exists",
    value=True,
    help=(
        "Recommended for journal articles. If an entry has a DOI, BibFlow will "
        "omit the URL field to keep the LaTeX bibliography cleaner."
    ),
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




single_tab, batch_tab, html_tab, title_tab, cleaner_tab, quality_tab, library_tab = st.tabs(
    [
        "🔎 Single DOI",
        "📦 Batch + Merge",
        "🌐 Zotero HTML Import",
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
            remove_url_when_doi_exists=remove_url_when_doi_exists,
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
                        "Status": f"{type(e).__name__}: {e}",
                    }
                )

                with st.expander(f"Debug traceback for failed DOI: {doi}", expanded=False):
                    st.code(traceback.format_exc(), language="python")

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
                remove_url_when_doi_exists=remove_url_when_doi_exists,
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
# Zotero HTML Bibliography Import workflow
# ============================================================

with html_tab:

    st.markdown("## Zotero HTML Bibliography Import")

    st.markdown(
        """
        Upload a Zotero-exported **bibliography HTML** file and BibFlow will extract DOI values,
        fetch clean BibTeX metadata, and generate Overleaf-ready `.bib` output.

        Recommended Zotero export setting:

        ```text
        Output Mode: Bibliography
        Output Method: Save as HTML
        ```

        This works best for full bibliography HTML exports containing DOI links or Zotero `Z3988` metadata.
        Citation-only HTML, such as only `(Author et al., Year)`, usually does not contain enough metadata.
        """
    )

    html_files = st.file_uploader(
        "Upload Zotero bibliography HTML file(s)",
        type=["html", "htm"],
        accept_multiple_files=True,
        key="zotero_html_import_files",
    )

    pasted_html = st.text_area(
        "Optional: paste bibliography HTML text",
        height=160,
        placeholder="Paste Zotero bibliography HTML here if you do not want to upload a file...",
        key="zotero_html_paste_area",
    )

    html_sources = []

    if html_files:
        for uploaded_html in html_files:
            html_content = uploaded_html.getvalue().decode("utf-8", errors="ignore")
            html_sources.append(
                {
                    "Source": uploaded_html.name,
                    "Content": html_content,
                }
            )

    if pasted_html.strip():
        html_sources.append(
            {
                "Source": "Pasted HTML text",
                "Content": pasted_html,
            }
        )

    if not html_sources:
        st.info("Upload a Zotero bibliography `.html` file, or paste HTML text, to begin.")
    else:
        combined_dois = []
        source_rows = []
        preview_rows = []

        for source in html_sources:
            extraction = extract_dois_from_zotero_html(source["Content"])
            source_dois = extraction["unique_dois"]
            combined_dois.extend(source_dois)

            source_rows.append(
                {
                    "Source": source["Source"],
                    "CSL entries": extraction["csl_entry_count"],
                    "Z3988 metadata spans": extraction["z3988_count"],
                    "DOI links": extraction["doi_link_count"],
                    "Unique DOIs extracted": len(source_dois),
                }
            )

            for row in extract_csl_entry_preview(source["Content"], max_entries=8):
                row["Source"] = source["Source"]
                preview_rows.append(row)

        unique_dois = []
        seen_dois = set()
        for doi in combined_dois:
            doi_lower = normalize_doi(doi).lower()
            if doi_lower and doi_lower not in seen_dois:
                seen_dois.add(doi_lower)
                unique_dois.append(normalize_doi(doi))

        st.markdown("### HTML Extraction Summary")
        st.dataframe(pd.DataFrame(source_rows), use_container_width=True, hide_index=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("HTML sources", len(html_sources))
        with col2:
            st.metric("Unique DOIs", len(unique_dois))
        with col3:
            duplicate_count = max(0, len(combined_dois) - len(unique_dois))
            st.metric("Duplicate DOI mentions", duplicate_count)

        if preview_rows:
            with st.expander("Preview visible bibliography entries", expanded=False):
                preview_df = pd.DataFrame(preview_rows)
                preview_df = preview_df[["Source", "#", "Bibliography Entry Preview"]]
                st.dataframe(preview_df, use_container_width=True, hide_index=True)

        st.markdown("### Extracted DOI List")

        if unique_dois:
            extracted_doi_text = "\n".join(unique_dois)
            st.text_area(
                "Detected DOI values",
                value=extracted_doi_text,
                height=180,
                key="zotero_html_detected_doi_text",
            )

            st.download_button(
                label="Download extracted DOI list",
                data=extracted_doi_text,
                file_name="bibflow_extracted_dois_from_zotero_html.txt",
                mime="text/plain",
                key="zotero_html_download_doi_list",
            )
        else:
            st.warning(
                "No DOI values were found. This may be a citation-only export or a bibliography without DOI links/Z3988 metadata."
            )

        generate_from_html_button = st.button(
            "Generate BibTeX from extracted DOIs",
            type="primary",
            key="zotero_html_generate_bibtex_button",
            disabled=not bool(unique_dois),
        )

        if generate_from_html_button:

            generated_entries = []
            result_rows = []
            used_keys = set(existing_keys)

            progress_bar = st.progress(0)
            skipped_count = 0
            failed_count = 0

            for i, doi in enumerate(unique_dois, start=1):
                doi_lower = doi.lower()

                if uploaded_bib is not None and skip_existing_doi and doi_lower in existing_dois:
                    skipped_count += 1
                    result_rows.append(
                        {
                            "DOI": doi,
                            "Citation Key": "",
                            "Action": "Skipped",
                            "Status": "Skipped because DOI already exists in uploaded .bib",
                        }
                    )
                    progress_bar.progress(i / len(unique_dois))
                    continue

                try:
                    raw_bibtex = fetch_bibtex_from_doi(doi)
                    entry = parse_bibtex(raw_bibtex)

                    if entry is None:
                        raise ValueError("Could not parse BibTeX entry returned by DOI resolver.")

                    entry_doi = normalize_doi(entry.get("doi", "")).lower()
                    duplicate_by_returned_doi = uploaded_bib is not None and entry_doi in existing_dois

                    if skip_existing_doi and duplicate_by_returned_doi:
                        skipped_count += 1
                        result_rows.append(
                            {
                                "DOI": doi,
                                "Citation Key": "",
                                "Action": "Skipped",
                                "Status": "Skipped because returned DOI already exists in uploaded .bib",
                            }
                        )
                        progress_bar.progress(i / len(unique_dois))
                        continue

                    suggested_key = generate_citation_key(entry, citation_key_style=citation_key_style)
                    final_key = make_unique_key(suggested_key, used_keys)
                    entry["ID"] = final_key
                    used_keys.add(final_key)
                    generated_entries.append(entry)

                    result_rows.append(
                        {
                            "DOI": doi,
                            "Citation Key": final_key,
                            "Action": "Generated",
                            "Status": "Clean BibTeX entry generated from DOI.",
                        }
                    )

                except Exception as e:
                    failed_count += 1
                    result_rows.append(
                        {
                            "DOI": doi,
                            "Citation Key": "",
                            "Action": "Failed",
                            "Status": f"{type(e).__name__}: {e}",
                        }
                    )

                    with st.expander(f"Debug traceback for failed DOI: {doi}", expanded=False):
                        st.code(traceback.format_exc(), language="python")

                progress_bar.progress(i / len(unique_dois))

            st.divider()
            st.markdown("### DOI-to-BibTeX Processing Summary")

            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            with metric_col1:
                st.metric("Extracted DOIs", len(unique_dois))
            with metric_col2:
                st.metric("New entries", len(generated_entries))
            with metric_col3:
                st.metric("Skipped duplicates", skipped_count)
            with metric_col4:
                st.metric("Failed", failed_count)

            st.dataframe(pd.DataFrame(result_rows), use_container_width=True, hide_index=True)

            if generated_entries:
                html_import_bibtex = entries_to_bibtex(
                    generated_entries,
                    export_preset=export_preset,
                    sort_entries=sort_bib_entries,
                    include_header=include_export_header,
                    remove_url_when_doi_exists=remove_url_when_doi_exists,
                )

                st.markdown("### Clean BibTeX Generated from Zotero HTML")
                st.code(html_import_bibtex, language="bibtex")

                st.download_button(
                    label="Download BibTeX generated from HTML",
                    data=html_import_bibtex,
                    file_name="bibflow_from_zotero_html.bib",
                    mime="text/plain",
                    key="zotero_html_bibtex_download_button",
                )

                if uploaded_bib is not None:
                    merged_html_bibtex = build_merged_bib(existing_bib_content, html_import_bibtex)

                    st.markdown("### Clean Merged BibTeX")
                    st.caption("Your uploaded `.bib` content is preserved. New HTML-derived entries are appended.")
                    st.code(merged_html_bibtex, language="bibtex")

                    st.download_button(
                        label="Download merged .bib file",
                        data=merged_html_bibtex,
                        file_name="merged_references_from_zotero_html.bib",
                        mime="text/plain",
                        key="zotero_html_merged_bibtex_download_button",
                    )
                else:
                    st.info("Upload an existing references.bib file in the sidebar to enable clean merge output.")
            else:
                st.warning("No new BibTeX entries were generated from the extracted DOI list.")

    st.markdown("### Notes")
    st.markdown(
        """
        - Best input: Zotero **Bibliography** exported as **HTML**.
        - Different citation styles are okay if the HTML still contains DOI links or Z3988 metadata.
        - Citation-only exports are not reliable because they usually lack full metadata.
        - RTF import is not supported in this version; HTML is more structured and safer to parse.
        """
    )


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
                remove_url_when_doi_exists=remove_url_when_doi_exists,
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
                remove_url_when_doi_exists=remove_url_when_doi_exists,
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
        Upload a `.bib` file and turn your references into a searchable, editable, and exportable research library.

        **Version 2.2** adds multi-ranking support. It keeps the Version 2.0F research-library workflow,
        and extends ranking enrichment beyond AJG/ABS + FT50 to ABDC, JCR/SJR quartiles,
        SSCI indexing, JCR/SJR quartiles, and optional advanced/private ranking columns.

        Ranking data is optional:
        - If a private full ranking file exists, BibFlow loads it automatically.
        - If no private file exists, BibFlow can use a small demo ranking file.
        - Users can also upload their own ranking file in the advanced section.
        """
    )

    st.info(
        "For public deployment, keep the full ranking file private in `data/private/` and exclude this folder from GitHub. "
        "Use the annotated CSV export/restore workflow to continue literature-review work across sessions."
    )

    with st.expander("Version 2.2 sample files and testing checklist", expanded=False):
        st.markdown(build_version_testing_checklist())

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

            st.markdown("### 2. Optional: Restore Previous Annotations")

            st.markdown(
                """
                If you previously downloaded an annotated research library CSV from BibFlow,
                upload it here to continue editing your reading status, tags, priority, citation flags, and notes.
                """
            )

            restore_col1, restore_col2 = st.columns([2, 1])

            with restore_col1:
                annotated_library_file = st.file_uploader(
                    "Upload previously exported annotated library CSV/XLSX",
                    type=["csv", "xlsx", "xls"],
                    key="restore_annotated_library_file"
                )

            with restore_col2:
                overwrite_restored_annotations = st.checkbox(
                    "Overwrite current session annotations",
                    value=True,
                    key="overwrite_restored_annotations"
                )

                clear_current_annotations = st.button(
                    "Clear session annotations",
                    key="clear_current_annotations_button"
                )

            if clear_current_annotations:
                clear_annotation_store()
                st.success("Current session annotations have been cleared.")

            restored_annotation_summary = None

            if annotated_library_file is not None:
                try:
                    raw_annotated_df = load_annotated_library_file(annotated_library_file)
                    restored_annotation_summary = import_annotations_into_store(
                        raw_annotated_df,
                        overwrite_existing=overwrite_restored_annotations,
                    )

                    st.success(
                        f"Restored {restored_annotation_summary['imported']} annotation row(s) "
                        f"from {restored_annotation_summary['total_rows']} uploaded row(s). "
                        f"Skipped {restored_annotation_summary['skipped']} row(s)."
                    )

                    with st.expander("Preview restored annotation file", expanded=False):
                        st.dataframe(
                            prepare_imported_annotations(raw_annotated_df).head(30),
                            use_container_width=True,
                            hide_index=True,
                        )

                except Exception as e:
                    st.error(f"Failed to restore annotations: {e}")

            st.markdown("### 3. Optional Journal Ranking Match")

            st.markdown(
                """
                Journal ranking data is optional.  
                BibFlow can still build your editable research library even when no ranking file is available.
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

                    Use this when you want to match your references with AJG/ABS, FT50, ABDC,
                    JCR/SJR quartiles, SSCI indexing, and optional advanced/private ranking columns,
                    or your own custom ranking categories.

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
                    abdc_rating
                    abdc_field
                    jcr_quartile
                    sjr_quartile
                    cssci
                    chinese_core
                    school_tier
                    custom_rating
                    ranking_tags
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

            # Version 2.0D: add editable annotation columns and apply restored/current session annotations.
            library_df = add_annotation_columns(library_df)
            library_df = apply_annotation_store(library_df)

            summary = summarize_research_library(library_df)
            ranking_summary = summarize_ranking_matches(library_df)
            annotation_summary = summarize_annotations(library_df)

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

                multi_rank_col1, multi_rank_col2, multi_rank_col3, multi_rank_col4, multi_rank_col5 = st.columns(5)

                with multi_rank_col1:
                    st.metric("ABDC A*", ranking_summary["abdc_a_plus"])

                with multi_rank_col2:
                    st.metric("ABDC A/A*", ranking_summary["abdc_a_or_above"])

                with multi_rank_col3:
                    st.metric("JCR Q1", ranking_summary["jcr_q1"])

                with multi_rank_col4:
                    st.metric("SJR Q1", ranking_summary["sjr_q1"])

                with multi_rank_col5:
                    st.metric("SSCI", ranking_summary["ssci_count"])

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

                with st.expander("Additional ranking distributions", expanded=False):
                    extra_dist_col1, extra_dist_col2, extra_dist_col3 = st.columns(3)

                    with extra_dist_col1:
                        st.markdown("**ABDC Rating**")
                        st.dataframe(
                            make_count_table(library_df, "ABDC Rating", empty_label="No ABDC rating", order=["A*", "A", "B", "C", "No ABDC rating"]),
                            use_container_width=True,
                            hide_index=True,
                        )

                    with extra_dist_col2:
                        st.markdown("**JCR Quartile**")
                        st.dataframe(
                            make_count_table(library_df, "JCR Quartile", empty_label="No JCR quartile", order=["Q1", "Q2", "Q3", "Q4", "No JCR quartile"]),
                            use_container_width=True,
                            hide_index=True,
                        )

                    with extra_dist_col3:
                        st.markdown("**School / Custom Ratings**")
                        st.dataframe(
                            make_count_table(library_df, "Custom Rating", empty_label="No custom rating"),
                            use_container_width=True,
                            hide_index=True,
                        )

            st.markdown("### Research Progress Summary")

            ann_col1, ann_col2, ann_col3, ann_col4, ann_col5 = st.columns(5)

            with ann_col1:
                st.metric("Read", annotation_summary["read"])

            with ann_col2:
                st.metric("Reading", annotation_summary["reading"])

            with ann_col3:
                st.metric("Important", annotation_summary["important"])

            with ann_col4:
                st.metric("Citation Candidates", annotation_summary["citation_candidates"])

            with ann_col5:
                st.metric("Core Papers", annotation_summary["core_papers"])

            with st.expander("Version 2.0F quick health checks", expanded=True):
                for message_type, message_text in build_library_health_messages(
                    library_df=library_df,
                    summary=summary,
                    ranking_summary=ranking_summary,
                    annotation_summary=annotation_summary,
                    ranking_loaded=ranking_loaded,
                ):
                    if message_type == "warning":
                        st.warning(message_text)
                    elif message_type == "success":
                        st.success(message_text)
                    else:
                        st.info(message_text)

            st.divider()

            st.markdown("### Search and Filter")

            search_text = st.text_input(
                "Search references",
                placeholder="Search by title, author, journal, DOI, ISSN, AJG field, tags, notes, or citation key",
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

            multi_rank_filter_col1, multi_rank_filter_col2, multi_rank_filter_col3 = st.columns(3)

            with multi_rank_filter_col1:
                abdc_rating_options = sorted(
                    [
                        r for r in library_df["ABDC Rating"].dropna().astype(str).unique()
                        if r.strip()
                    ],
                    key=abdc_rating_value,
                    reverse=True,
                )

                selected_abdc_ratings = st.multiselect(
                    "Filter by ABDC rating",
                    options=abdc_rating_options,
                    key="library_abdc_rating_filter"
                )

            with multi_rank_filter_col2:
                jcr_quartile_options = sorted(
                    [
                        q for q in library_df["JCR Quartile"].dropna().astype(str).unique()
                        if q.strip()
                    ],
                    key=quartile_value,
                    reverse=True,
                )

                selected_jcr_quartiles = st.multiselect(
                    "Filter by JCR quartile",
                    options=jcr_quartile_options,
                    key="library_jcr_quartile_filter"
                )

            with multi_rank_filter_col3:
                sjr_quartile_options = sorted(
                    [
                        q for q in library_df["SJR Quartile"].dropna().astype(str).unique()
                        if q.strip()
                    ],
                    key=quartile_value,
                    reverse=True,
                )

                selected_sjr_quartiles = st.multiselect(
                    "Filter by SJR quartile",
                    options=sjr_quartile_options,
                    key="library_sjr_quartile_filter"
                )

            selected_cssci = []
            selected_chinese_core = []
            selected_school_tiers = []
            selected_custom_ratings = []

            compact_filter_col1, compact_filter_col2 = st.columns(2)

            with compact_filter_col1:
                ssci_options = sorted(
                    [
                        x for x in library_df["SSCI"].dropna().astype(str).unique()
                        if x.strip()
                    ]
                )

                selected_ssci = st.multiselect(
                    "Filter by SSCI",
                    options=ssci_options,
                    key="library_ssci_filter"
                )

            with compact_filter_col2:
                st.caption(
                    "Main ranking view: AJG Rating, AJG Field, FT50, ABDC Rating, JCR Quartile, SJR Quartile, and SSCI. "
                    "Advanced details are kept only for source, custom-rating, and match-checking information."
                )

            with st.expander("Advanced ranking filters", expanded=False):
                adv_custom_col1, adv_custom_col2 = st.columns(2)

                with adv_custom_col1:
                    custom_rating_options = sorted(
                        [
                            x for x in library_df["Custom Rating"].dropna().astype(str).unique()
                            if x.strip()
                        ]
                    )

                    selected_custom_ratings = st.multiselect(
                        "Filter by custom rating",
                        options=custom_rating_options,
                        key="library_custom_rating_filter"
                    )

                with adv_custom_col2:
                    st.caption(
                        "Custom rating is optional and designed for future private or school-specific ranking systems. "
                        "CSSCI, Chinese Core, and School Tier are not shown in the current compact workflow."
                    )

            quick_filter_col1, quick_filter_col2, quick_filter_col3, quick_filter_col4 = st.columns(4)

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

            with quick_filter_col3:
                only_abdc_a_or_above = st.checkbox(
                    "Show only ABDC A/A*",
                    value=False,
                    key="only_abdc_a_or_above_filter"
                )

            with quick_filter_col4:
                only_jcr_q1 = st.checkbox(
                    "Show only JCR Q1",
                    value=False,
                    key="only_jcr_q1_filter"
                )

            extra_quick_col1, extra_quick_col2, extra_quick_col3, extra_quick_col4 = st.columns(4)

            with extra_quick_col1:
                only_abdc_a_plus = st.checkbox(
                    "Show only ABDC A*",
                    value=False,
                    key="only_abdc_a_plus_filter"
                )

            with extra_quick_col2:
                only_sjr_q1 = st.checkbox(
                    "Show only SJR Q1",
                    value=False,
                    key="only_sjr_q1_filter"
                )

            with extra_quick_col3:
                only_ssci = st.checkbox(
                    "Show only SSCI",
                    value=False,
                    key="only_ssci_filter"
                )

            with extra_quick_col4:
                st.caption("Custom rating is available under Advanced ranking filters. CSSCI, Chinese Core, and School Tier are hidden for now.")

            only_cssci = False
            only_chinese_core = False

            annotation_filter_col1, annotation_filter_col2, annotation_filter_col3 = st.columns(3)

            with annotation_filter_col1:
                selected_reading_status = st.multiselect(
                    "Filter by reading status",
                    options=READING_STATUS_OPTIONS,
                    key="library_reading_status_filter"
                )

            with annotation_filter_col2:
                selected_priorities = st.multiselect(
                    "Filter by priority",
                    options=PRIORITY_OPTIONS,
                    key="library_priority_filter"
                )

            with annotation_filter_col3:
                selected_paper_types = st.multiselect(
                    "Filter by paper type",
                    options=[x for x in PAPER_TYPE_OPTIONS if x],
                    key="library_paper_type_filter"
                )

            annotation_flag_col1, annotation_flag_col2 = st.columns(2)

            with annotation_flag_col1:
                only_citation_candidates = st.checkbox(
                    "Show only citation candidates",
                    value=False,
                    key="only_citation_candidates_filter"
                )

            with annotation_flag_col2:
                only_important = st.checkbox(
                    "Show only important papers",
                    value=False,
                    key="only_important_filter"
                )

            filtered_library_df = filter_library_dataframe(
                df=library_df,
                search_text=search_text,
                selected_years=selected_years,
                selected_journals=selected_journals,
                selected_entry_types=selected_entry_types,
                selected_ajg_ratings=selected_ajg_ratings,
                selected_ft50=selected_ft50,
                selected_abdc_ratings=selected_abdc_ratings,
                selected_jcr_quartiles=selected_jcr_quartiles,
                selected_sjr_quartiles=selected_sjr_quartiles,
                selected_cssci=selected_cssci,
                selected_ssci=selected_ssci,
                selected_chinese_core=selected_chinese_core,
                selected_school_tiers=selected_school_tiers,
                selected_custom_ratings=selected_custom_ratings,
                selected_match_status=selected_match_status,
                only_ajg_3_plus=only_ajg_3_plus,
                only_ft50=only_ft50,
                only_abdc_a_plus=only_abdc_a_plus,
                only_abdc_a_or_above=only_abdc_a_or_above,
                only_jcr_q1=only_jcr_q1,
                only_sjr_q1=only_sjr_q1,
                only_cssci=only_cssci,
                only_ssci=only_ssci,
                only_chinese_core=only_chinese_core,
                selected_reading_status=selected_reading_status,
                selected_priorities=selected_priorities,
                selected_paper_types=selected_paper_types,
                only_citation_candidates=only_citation_candidates,
                only_important=only_important,
            )

            display_columns = [
                "Citation Key",
                "Title",
                "Authors",
                "Year",
                "Journal / Venue",
                "AJG Rating",
                "AJG Field",
                "FT50",
                "ABDC Rating",
                "JCR Quartile",
                "SJR Quartile",
                "SSCI",
                "Reading Status",
                "Paper Type",
                "Priority",
                "Research Tags",
                "Citation Candidate",
                "Important",
                "Notes",
                "DOI",
                "ISSN",
                "Ranking Match Status",
                "Entry Type",
                "Annotation ID",
            ]

            display_columns = [
                col for col in display_columns
                if col in filtered_library_df.columns
            ]

            st.markdown("### Editable Research Library Table")

            st.caption(
                f"Showing {len(filtered_library_df)} of {len(library_df)} references. "
                "Edit reading status, paper type, priority, tags, citation flags, importance, and notes directly in the table. "
                "Download the annotated CSV after editing if you want to keep the work permanently."
            )

            disabled_columns = [
                col for col in display_columns
                if col not in ANNOTATION_COLUMNS
            ]

            edited_library_df = st.data_editor(
                filtered_library_df[display_columns],
                use_container_width=True,
                hide_index=True,
                disabled=disabled_columns,
                column_config={
                    "Reading Status": st.column_config.SelectboxColumn(
                        "Reading Status",
                        options=READING_STATUS_OPTIONS,
                        required=True,
                    ),
                    "Paper Type": st.column_config.SelectboxColumn(
                        "Paper Type",
                        options=PAPER_TYPE_OPTIONS,
                    ),
                    "Priority": st.column_config.SelectboxColumn(
                        "Priority",
                        options=PRIORITY_OPTIONS,
                        required=True,
                    ),
                    "Research Tags": st.column_config.TextColumn(
                        "Research Tags",
                        help="Use comma-separated tags, e.g. option-implied density, VaR, GEV, tail risk",
                    ),
                    "Citation Candidate": st.column_config.CheckboxColumn(
                        "Citation Candidate",
                        help="Mark papers you may cite in your thesis or paper.",
                    ),
                    "Important": st.column_config.CheckboxColumn(
                        "Important",
                        help="Mark especially important papers.",
                    ),
                    "Notes": st.column_config.TextColumn(
                        "Notes",
                        help="Add short reading notes or literature review comments.",
                    ),
                    "Annotation ID": None,
                },
                key="research_library_annotation_editor",
            )

            update_annotation_store(edited_library_df)
            library_df = apply_annotation_store(library_df)
            filtered_library_df = apply_annotation_store(filtered_library_df)

            advanced_columns = [
                "Citation Key",
                "Journal / Venue",
                "AJG Source Year",
                "SSCI Categories",
                "Custom Rating",
                "Ranking Tags",
                "Matched Journal",
                "Match Method",
                "Match Score",
                "Ranking Source",
                "Ranking Match Note",
                "Annotation ID",
            ]
            advanced_columns = [col for col in advanced_columns if col in filtered_library_df.columns]

            with st.expander("Advanced ranking and matching details", expanded=False):
                st.caption(
                    "These columns are hidden from the main table to keep the default view focused. "
                    "Use them for source checking, debugging fuzzy matches, and optional custom/private rating information."
                )
                if advanced_columns:
                    st.dataframe(
                        filtered_library_df[advanced_columns],
                        use_container_width=True,
                        hide_index=True,
                    )

            st.divider()

            st.markdown("### Research Library Dashboard")

            dashboard_scope = st.radio(
                "Dashboard scope",
                options=["Filtered view", "Full library"],
                horizontal=True,
                key="dashboard_scope_selector",
            )

            dashboard_df = filtered_library_df.copy() if dashboard_scope == "Filtered view" else library_df.copy()
            report_scope_label = "Filtered library" if dashboard_scope == "Filtered view" else "Full library"

            dashboard_summary = summarize_research_library(dashboard_df)
            dashboard_ranking_summary = summarize_ranking_matches(dashboard_df)
            dashboard_annotation_summary = summarize_annotations(dashboard_df)

            dash_col1, dash_col2, dash_col3, dash_col4, dash_col5 = st.columns(5)

            with dash_col1:
                st.metric("Dashboard References", dashboard_summary["total_references"])

            with dash_col2:
                st.metric("AJG 3+", dashboard_ranking_summary["ajg_3_plus"])

            with dash_col3:
                st.metric("ABDC A/A*", dashboard_ranking_summary["abdc_a_or_above"])

            with dash_col4:
                st.metric("Citation Candidates", dashboard_annotation_summary["citation_candidates"])

            with dash_col5:
                st.metric("Core Papers", dashboard_annotation_summary["core_papers"])

            dashboard_tab1, dashboard_tab2, dashboard_tab3, dashboard_tab4 = st.tabs(
                [
                    "Ranking Overview",
                    "Reading Progress",
                    "Journals & Tags",
                    "Citation Pipeline",
                ]
            )

            with dashboard_tab1:
                ajg_distribution = make_count_table(
                    dashboard_df,
                    "AJG Rating",
                    empty_label="Unmatched / No AJG rating",
                    order=["4*", "4", "3", "2", "1", "Unmatched / No AJG rating"],
                )
                field_distribution = make_count_table(
                    dashboard_df,
                    "AJG Field",
                    empty_label="Unspecified field",
                )
                match_distribution = make_count_table(
                    dashboard_df,
                    "Ranking Match Status",
                    empty_label="Unspecified",
                )

                rank_left, rank_right = st.columns(2)

                with rank_left:
                    st.markdown("#### AJG Rating Distribution")
                    st.dataframe(ajg_distribution, use_container_width=True, hide_index=True)
                    if not ajg_distribution.empty:
                        st.bar_chart(ajg_distribution.set_index("AJG Rating")["Count"])

                with rank_right:
                    st.markdown("#### Ranking Match Status")
                    st.dataframe(match_distribution, use_container_width=True, hide_index=True)
                    if not match_distribution.empty:
                        st.bar_chart(match_distribution.set_index("Ranking Match Status")["Count"])

                st.markdown("#### AJG Field Distribution")
                st.dataframe(field_distribution.head(20), use_container_width=True, hide_index=True)

                st.markdown("#### Additional Ranking Systems")
                multi_dash_col1, multi_dash_col2, multi_dash_col3 = st.columns(3)

                with multi_dash_col1:
                    abdc_distribution = make_count_table(
                        dashboard_df,
                        "ABDC Rating",
                        empty_label="No ABDC rating",
                        order=["A*", "A", "B", "C", "No ABDC rating"],
                    )
                    st.dataframe(abdc_distribution, use_container_width=True, hide_index=True)

                with multi_dash_col2:
                    jcr_distribution = make_count_table(
                        dashboard_df,
                        "JCR Quartile",
                        empty_label="No JCR quartile",
                        order=["Q1", "Q2", "Q3", "Q4", "No JCR quartile"],
                    )
                    st.dataframe(jcr_distribution, use_container_width=True, hide_index=True)

                with multi_dash_col3:
                    list_distribution = make_count_table(
                        dashboard_df,
                        "Chinese Core",
                        empty_label="No Chinese-core flag",
                    )
                    st.dataframe(list_distribution, use_container_width=True, hide_index=True)

            with dashboard_tab2:
                reading_distribution = make_count_table(
                    dashboard_df,
                    "Reading Status",
                    empty_label="Unspecified",
                )
                priority_distribution = make_count_table(
                    dashboard_df,
                    "Priority",
                    empty_label="Unspecified",
                )
                paper_type_distribution = make_count_table(
                    dashboard_df,
                    "Paper Type",
                    empty_label="Unspecified",
                )

                progress_left, progress_right = st.columns(2)

                with progress_left:
                    st.markdown("#### Reading Status")
                    st.dataframe(reading_distribution, use_container_width=True, hide_index=True)
                    if not reading_distribution.empty:
                        st.bar_chart(reading_distribution.set_index("Reading Status")["Count"])

                with progress_right:
                    st.markdown("#### Priority")
                    st.dataframe(priority_distribution, use_container_width=True, hide_index=True)
                    if not priority_distribution.empty:
                        st.bar_chart(priority_distribution.set_index("Priority")["Count"])

                st.markdown("#### Paper Type")
                st.dataframe(paper_type_distribution, use_container_width=True, hide_index=True)

            with dashboard_tab3:
                top_journals = make_top_journal_table(dashboard_df, top_n=20)
                tag_frequency = make_tag_frequency_table(dashboard_df, top_n=25)

                journal_left, journal_right = st.columns(2)

                with journal_left:
                    st.markdown("#### Top Journals / Venues")
                    st.dataframe(top_journals, use_container_width=True, hide_index=True)

                with journal_right:
                    st.markdown("#### Research Tag Frequency")
                    st.dataframe(tag_frequency, use_container_width=True, hide_index=True)
                    if not tag_frequency.empty:
                        st.bar_chart(tag_frequency.set_index("Research Tag")["Count"])

            with dashboard_tab4:
                core_papers_df = make_focus_paper_table(
                    dashboard_df,
                    condition_col="Priority",
                    condition_value="Core paper",
                    max_rows=30,
                )
                citation_candidates_df = make_focus_paper_table(
                    dashboard_df,
                    condition_col="Citation Candidate",
                    condition_value=True,
                    max_rows=30,
                )
                important_papers_df = make_focus_paper_table(
                    dashboard_df,
                    condition_col="Important",
                    condition_value=True,
                    max_rows=30,
                )

                st.markdown("#### Core Papers")
                st.dataframe(core_papers_df, use_container_width=True, hide_index=True)

                st.markdown("#### Citation Candidates")
                st.dataframe(citation_candidates_df, use_container_width=True, hide_index=True)

                st.markdown("#### Important Papers")
                st.dataframe(important_papers_df, use_container_width=True, hide_index=True)

            literature_review_report = build_literature_review_report(
                dashboard_df,
                scope_label=report_scope_label,
            )

            st.download_button(
                label="Download literature-review report as Markdown",
                data=literature_review_report.encode("utf-8"),
                file_name=build_export_filename("bibflow_literature_review_report", "md"),
                mime="text/markdown",
                key="download_literature_review_report_md",
            )

            dashboard_summary_tables = []

            for table_name, table_df in [
                ("ajg_distribution", make_count_table(dashboard_df, "AJG Rating", empty_label="Unmatched / No AJG rating")),
                ("abdc_distribution", make_count_table(dashboard_df, "ABDC Rating", empty_label="No ABDC rating")),
                ("jcr_quartile", make_count_table(dashboard_df, "JCR Quartile", empty_label="No JCR quartile")),
                ("sjr_quartile", make_count_table(dashboard_df, "SJR Quartile", empty_label="No SJR quartile")),
                ("ssci", make_count_table(dashboard_df, "SSCI", empty_label="No SSCI flag")),
                ("reading_status", make_count_table(dashboard_df, "Reading Status", empty_label="Unspecified")),
                ("priority", make_count_table(dashboard_df, "Priority", empty_label="Unspecified")),
                ("paper_type", make_count_table(dashboard_df, "Paper Type", empty_label="Unspecified")),
                ("research_tags", make_tag_frequency_table(dashboard_df, top_n=50)),
                ("top_journals", make_top_journal_table(dashboard_df, top_n=50)),
            ]:
                temp_df = table_df.copy()
                temp_df.insert(0, "Summary Table", table_name)
                dashboard_summary_tables.append(temp_df)

            dashboard_summary_export = pd.concat(dashboard_summary_tables, ignore_index=True, sort=False)

            st.download_button(
                label="Download dashboard summary tables as CSV",
                data=dashboard_summary_export.to_csv(index=False).encode("utf-8"),
                file_name=build_export_filename("bibflow_dashboard_summary_tables", "csv"),
                mime="text/csv",
                key="download_dashboard_summary_tables_csv",
            )

            st.divider()

            st.markdown("### Export")

            csv_data = filtered_library_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="Download filtered annotated research library as CSV",
                data=csv_data,
                file_name=build_export_filename("bibflow_annotated_research_library_filtered", "csv"),
                mime="text/csv",
                key="download_annotated_research_library_csv"
            )

            full_csv_data = library_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="Download full annotated research library as CSV",
                data=full_csv_data,
                file_name=build_export_filename("bibflow_annotated_research_library_full", "csv"),
                mime="text/csv",
                key="download_full_annotated_research_library_csv"
            )

            annotation_export_columns = [
                "Annotation ID",
                "Citation Key",
                "Title",
                "Year",
                "Journal / Venue",
                "Reading Status",
                "Paper Type",
                "Priority",
                "Research Tags",
                "Citation Candidate",
                "Important",
                "Notes",
            ]

            annotation_export_columns = [
                col for col in annotation_export_columns
                if col in library_df.columns
            ]

            annotations_only_csv = library_df[annotation_export_columns].to_csv(index=False).encode("utf-8")

            st.download_button(
                label="Download annotations-only CSV for restore/import",
                data=annotations_only_csv,
                file_name=build_export_filename("bibflow_annotations_only", "csv"),
                mime="text/csv",
                key="download_annotations_only_csv"
            )

            unmatched_df = library_df[
                library_df["Ranking Match Status"] == "Unmatched"
            ].copy()

            if ranking_loaded and not unmatched_df.empty:
                unmatched_csv = unmatched_df.to_csv(index=False).encode("utf-8")

                st.download_button(
                    label="Download unmatched journals for manual checking",
                    data=unmatched_csv,
                    file_name=build_export_filename("bibflow_unmatched_journals", "csv"),
                    mime="text/csv",
                    key="download_unmatched_journals_csv"
                )

            st.markdown("### Interpretation Notes")

            st.markdown(
                """
                - AJG ranks **journals**, not individual papers.
                - The correct interpretation is: *this paper is published in an AJG 3 journal*.
                - FT50 also identifies journals, not paper quality directly.
                - Reading status, tags, priority, citation flags, importance flags, and notes can now be restored from a previously downloaded annotated CSV.
                - Version 2.0F adds polish, clearer testing guidance, quick health checks, and dated export filenames.
                - To continue your work later, download the annotated CSV and upload it again in the restore section.
                - Fuzzy matches should be manually checked, especially when the match score is below 1.00.
                - Keep the full ranking file private unless redistribution is clearly allowed.
                """
            )


render_footer()