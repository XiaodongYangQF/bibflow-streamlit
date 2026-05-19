"""
Build private BibFlow ranking files.

Expected input folder:

data/private/source_rankings/

Required files:
- ABS2024_clean_for_bibflow.csv
- ft50_clean_for_bibflow.csv
- ABDC-JQL-2025-v1-260326.xlsx
- SSCI-List_160424.csv

Output:
- data/private/source_rankings/abdc_2025_clean_for_bibflow.csv
- data/private/source_rankings/ssci_clean_for_bibflow.csv
- data/private/journal_rankings_combined_for_bibflow.csv

Run:
    python scripts/build_private_rankings.py
"""

from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "data" / "private"
SOURCE = PRIVATE / "source_rankings"

AJG_PATH = SOURCE / "ABS2024_clean_for_bibflow.csv"
FT50_PATH = SOURCE / "ft50_clean_for_bibflow.csv"
ABDC_PATH = SOURCE / "ABDC-JQL-2025-v1-260326.xlsx"
SSCI_PATH = SOURCE / "SSCI-List_160424.csv"

OUT_ABDC = SOURCE / "abdc_2025_clean_for_bibflow.csv"
OUT_SSCI = SOURCE / "ssci_clean_for_bibflow.csv"
OUT_COMBINED = PRIVATE / "journal_rankings_combined_for_bibflow.csv"


def clean_str(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    s = str(x)
    s = s.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    s = re.sub(r"\s+", " ", s).strip()
    if s.lower() in {"nan", "none"}:
        return ""
    return s


def normalize_journal_name(name):
    s = clean_str(name).lower()
    s = s.replace("&", " and ")
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"^the\s+", "", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_issn(x):
    s = clean_str(x).upper()
    s = re.sub(r"[^0-9X]", "", s)
    if len(s) == 8:
        return f"{s[:4]}-{s[4:]}"
    return s


def normalize_issn_plain(x):
    return re.sub(r"[^0-9X]", "", normalize_issn(x).upper())


def add_unique(existing, new):
    vals = []
    for v in str(existing).split(";"):
        v = clean_str(v)
        if v:
            vals.append(v)
    for v in str(new).split(";"):
        v = clean_str(v)
        if v and v not in vals:
            vals.append(v)
    return "; ".join(vals)


def merge_value(old, new):
    old = clean_str(old)
    new = clean_str(new)
    return old or new


def main():
    PRIVATE.mkdir(parents=True, exist_ok=True)
    SOURCE.mkdir(parents=True, exist_ok=True)

    ajg = pd.read_csv(AJG_PATH)
    ft50 = pd.read_csv(FT50_PATH)

    ajg_clean = pd.DataFrame()
    ajg_clean["journal"] = ajg.get("journal", "").apply(clean_str)
    ajg_clean["journal_normalized"] = ajg.get("journal_normalized", ajg_clean["journal"]).apply(normalize_journal_name)
    ajg_clean["journal_alias_normalized"] = ajg.get("journal_alias_normalized", ajg_clean["journal_normalized"]).apply(normalize_journal_name)
    ajg_clean["issn"] = ajg.get("issn", "").apply(normalize_issn)
    ajg_clean["ajg_rating"] = ajg.get("ajg_rating", "").apply(clean_str)
    ajg_clean["ajg_field"] = ajg.get("ajg_field", "").apply(clean_str)
    ajg_clean["ajg_source_year"] = ajg.get("source_year", ajg.get("ajg_source_year", "")).apply(clean_str)
    ajg_clean["ranking_source"] = ajg.get("ranking_source", "AJG 2024").apply(clean_str) if "ranking_source" in ajg.columns else "AJG 2024"
    ajg_clean["match_note"] = ""
    ajg_clean = ajg_clean[ajg_clean["journal_normalized"].ne("")].drop_duplicates(subset=["journal_normalized"], keep="first")

    ft50_clean = pd.DataFrame()
    ft50_clean["journal"] = ft50.get("journal", "").apply(clean_str)
    ft50_clean["journal_normalized"] = ft50.get("journal_normalized", ft50_clean["journal"]).apply(normalize_journal_name)
    ft50_clean["journal_alias_normalized"] = ft50.get("journal_alias_normalized", ft50_clean["journal_normalized"]).apply(normalize_journal_name)
    ft50_clean["issn"] = ft50.get("issn", "").apply(normalize_issn)
    ft50_clean["ft50"] = "Yes"
    ft50_clean["ft50_title"] = ft50_clean["journal"]
    ft50_clean["ft50_issn"] = ft50_clean["issn"]
    ft50_clean["ranking_source"] = ft50.get("ranking_source", "FT50").apply(clean_str) if "ranking_source" in ft50.columns else "FT50"
    ft50_clean["match_note"] = ""
    ft50_clean = ft50_clean[ft50_clean["journal_normalized"].ne("")].drop_duplicates(subset=["journal_normalized"], keep="first")

    abdc_raw = pd.read_excel(ABDC_PATH, sheet_name="2025 JQL", header=7)
    abdc_raw = abdc_raw.dropna(axis=1, how="all")
    abdc_raw = abdc_raw.loc[:, ~abdc_raw.columns.astype(str).str.startswith("Unnamed")]

    abdc_clean = pd.DataFrame()
    abdc_clean["journal"] = abdc_raw["Journal Title"].apply(clean_str)
    abdc_clean["journal_normalized"] = abdc_clean["journal"].apply(normalize_journal_name)
    abdc_clean["journal_alias_normalized"] = abdc_clean["journal_normalized"]
    abdc_clean["publisher"] = abdc_raw.get("Publisher", "").apply(clean_str)
    abdc_clean["issn"] = abdc_raw.get("ISSN", "").apply(normalize_issn)
    abdc_clean["online_issn"] = abdc_raw.get("ISSNOnline", "").apply(normalize_issn)
    abdc_clean["abdc_for"] = abdc_raw.get("FoR", "").apply(clean_str)
    abdc_clean["abdc_rating"] = abdc_raw.get("2025 rating", "").apply(lambda x: clean_str(x).replace(" ", "").upper())
    abdc_clean["abdc_source_year"] = "2025"
    abdc_clean["ranking_source"] = "ABDC JQL 2025"
    abdc_clean["match_note"] = ""
    abdc_clean = abdc_clean[
        abdc_clean["journal_normalized"].ne("") & abdc_clean["abdc_rating"].ne("")
    ].drop_duplicates(subset=["journal_normalized"], keep="first")
    abdc_clean.to_csv(OUT_ABDC, index=False, encoding="utf-8-sig")

    try:
        ssci = pd.read_csv(SSCI_PATH)
    except UnicodeDecodeError:
        ssci = pd.read_csv(SSCI_PATH, encoding="latin1")

    ssci_clean = pd.DataFrame()
    ssci_clean["journal"] = ssci["Journal title"].apply(clean_str)
    ssci_clean["journal_normalized"] = ssci_clean["journal"].apply(normalize_journal_name)
    ssci_clean["journal_alias_normalized"] = ssci_clean["journal_normalized"]
    ssci_clean["issn"] = ssci.get("ISSN", "").apply(normalize_issn)
    ssci_clean["online_issn"] = ssci.get("eISSN", "").apply(normalize_issn)
    ssci_clean["ssci"] = "Yes"
    ssci_clean["ssci_categories"] = ssci.get("Web of Science Categories", "").apply(clean_str)
    ssci_clean["ssci_publisher"] = ssci.get("Publisher name", "").apply(clean_str)
    ssci_clean["ranking_source"] = "SSCI List 2024-04-16"
    ssci_clean["match_note"] = ""
    ssci_clean = ssci_clean[ssci_clean["journal_normalized"].ne("")].drop_duplicates(subset=["journal_normalized"], keep="first")
    ssci_clean.to_csv(OUT_SSCI, index=False, encoding="utf-8-sig")

    columns = [
        "journal", "journal_normalized", "journal_alias_normalized", "issn", "online_issn",
        "ajg_rating", "ajg_field", "ajg_source_year",
        "ft50", "ft50_issn", "ft50_title",
        "abdc_rating", "abdc_source_year", "abdc_for",
        "ssci", "ssci_categories",
        "school_tier", "custom_rating", "ranking_tags",
        "ranking_source", "match_note",
    ]

    rows = []
    norm_to_idx = {}
    issn_to_idx = {}

    def register(row):
        idx = len(rows)
        rows.append(row)
        for col in ["journal_normalized", "journal_alias_normalized"]:
            norm = row.get(col, "")
            if norm:
                norm_to_idx[norm] = idx
        for col in ["issn", "online_issn"]:
            issn = normalize_issn_plain(row.get(col, ""))
            if issn:
                issn_to_idx.setdefault(issn, idx)

    def find(row, source):
        if source == "FT50":
            for col in ["journal_normalized", "journal_alias_normalized"]:
                norm = row.get(col, "")
                if norm and norm in norm_to_idx:
                    return norm_to_idx[norm], f"merged_by_{col}"
            return None, ""

        for col in ["issn", "online_issn"]:
            issn = normalize_issn_plain(row.get(col, ""))
            if issn and issn in issn_to_idx:
                return issn_to_idx[issn], f"merged_by_{col}"
        for col in ["journal_normalized", "journal_alias_normalized"]:
            norm = row.get(col, "")
            if norm and norm in norm_to_idx:
                return norm_to_idx[norm], f"merged_by_{col}"
        return None, ""

    def merge(idx, incoming, source, note):
        target = rows[idx]
        for col in columns:
            if col in ["ranking_source", "match_note"]:
                continue
            target[col] = merge_value(target.get(col, ""), incoming.get(col, ""))
        target["ranking_source"] = add_unique(target.get("ranking_source", ""), incoming.get("ranking_source", source))
        target["match_note"] = add_unique(add_unique(target.get("match_note", ""), incoming.get("match_note", "")), note)
        for col in ["journal_normalized", "journal_alias_normalized"]:
            norm = target.get(col, "")
            if norm:
                norm_to_idx[norm] = idx
        for col in ["issn", "online_issn"]:
            issn = normalize_issn_plain(target.get(col, ""))
            if issn:
                issn_to_idx.setdefault(issn, idx)

    def add_source(df, source):
        for _, r in df.iterrows():
            row = {c: "" for c in columns}
            row["journal"] = clean_str(r.get("journal", ""))
            row["journal_normalized"] = normalize_journal_name(r.get("journal_normalized", row["journal"]))
            row["journal_alias_normalized"] = normalize_journal_name(r.get("journal_alias_normalized", row["journal_normalized"]))
            row["issn"] = normalize_issn(r.get("issn", ""))
            row["online_issn"] = normalize_issn(r.get("online_issn", ""))
            row["ranking_source"] = clean_str(r.get("ranking_source", source))

            if source == "AJG 2024":
                row["ajg_rating"] = clean_str(r.get("ajg_rating", ""))
                row["ajg_field"] = clean_str(r.get("ajg_field", ""))
                row["ajg_source_year"] = clean_str(r.get("ajg_source_year", "")) or "2024"
            elif source == "FT50":
                row["ft50"] = "Yes"
                row["ft50_issn"] = normalize_issn(r.get("ft50_issn", r.get("issn", "")))
                row["ft50_title"] = clean_str(r.get("ft50_title", r.get("journal", "")))
            elif source == "ABDC JQL 2025":
                row["abdc_rating"] = clean_str(r.get("abdc_rating", ""))
                row["abdc_source_year"] = clean_str(r.get("abdc_source_year", "")) or "2025"
                row["abdc_for"] = clean_str(r.get("abdc_for", ""))
            elif source == "SSCI 2024":
                row["ssci"] = "Yes"
                row["ssci_categories"] = clean_str(r.get("ssci_categories", ""))

            idx, method = find(row, source)
            if idx is None:
                row["match_note"] = f"Base row from {source}"
                register(row)
            else:
                merge(idx, row, source, method)

    add_source(ajg_clean, "AJG 2024")
    add_source(abdc_clean, "ABDC JQL 2025")
    add_source(ssci_clean, "SSCI 2024")
    add_source(ft50_clean, "FT50")

    combined = pd.DataFrame(rows, columns=columns).sort_values("journal_normalized").reset_index(drop=True)
    combined.to_csv(OUT_COMBINED, index=False, encoding="utf-8-sig")

    print("Saved:", OUT_COMBINED)
    print("Combined rows:", len(combined))
    print("AJG rows:", combined["ajg_rating"].astype(str).str.strip().ne("").sum())
    print("FT50 rows:", combined["ft50"].eq("Yes").sum())
    print("ABDC rows:", combined["abdc_rating"].astype(str).str.strip().ne("").sum())
    print("SSCI rows:", combined["ssci"].eq("Yes").sum())


if __name__ == "__main__":
    main()
