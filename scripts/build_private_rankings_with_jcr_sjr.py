import pandas as pd
import re, zipfile, shutil
from pathlib import Path
OUT=Path('/mnt/data')

def clean_str(x):
    if pd.isna(x): return ''
    return str(x).strip()

def normalize_journal_name(name):
    if pd.isna(name): return ''
    s=str(name).strip().lower().replace('&',' and ').replace('{','').replace('}','')
    s=re.sub(r'^the\s+','',s)
    s=re.sub(r'[^a-z0-9\s]',' ',s)
    return re.sub(r'\s+',' ',s).strip()

def normalize_issn_compact(x):
    if pd.isna(x): return ''
    s=re.sub(r'[^0-9X]','',str(x).upper().strip())
    return s if len(s)==8 else ''

def format_issn(compact):
    c=normalize_issn_compact(compact)
    return c[:4]+'-'+c[4:] if c else ''

def split_issns(x):
    if pd.isna(x): return []
    text=str(x).upper()
    out=[]
    # both hyphenated and compact ISSNs
    for m in re.findall(r'[0-9]{4}[- ]?[0-9X]{4}', text):
        c=normalize_issn_compact(m)
        if c and c not in out: out.append(c)
    return out

def append_unique(existing, add):
    existing=clean_str(existing); add=clean_str(add)
    if not add: return existing
    if not existing: return add
    parts=[p.strip() for p in existing.split(';') if p.strip()]
    if add not in parts: parts.append(add)
    return '; '.join(parts)

# JCR
jraw=pd.read_csv('/mnt/data/JCR_from_pdf.csv', header=None, dtype=str)
header_idx=None
for i,row in jraw.iterrows():
    vals=[clean_str(v).lower() for v in row.tolist()]
    if 'rank' in vals and any('journal name' in v for v in vals):
        header_idx=i; break
if header_idx is None: raise ValueError('JCR header not found')
header=[clean_str(x).replace('\n',' ').replace('  ',' ') for x in jraw.iloc[header_idx].tolist()]
jcr=jraw.iloc[header_idx+1:].copy(); jcr.columns=header
# robust columns by position
jcr_clean=pd.DataFrame({
    'journal': jcr.iloc[:,1].fillna('').astype(str).str.strip(),
    'issn': jcr.iloc[:,3].apply(lambda x: format_issn(normalize_issn_compact(x))),
    'jcr_impact_factor': jcr.iloc[:,4].fillna('').astype(str).str.replace(',','.', regex=False).str.strip(),
    'jcr_quartile': jcr.iloc[:,5].fillna('').astype(str).str.strip().str.upper(),
})
jcr_clean=jcr_clean[jcr_clean['journal'].ne('')].copy()
jcr_clean['journal_normalized']=jcr_clean['journal'].apply(normalize_journal_name)
jcr_clean['journal_alias_normalized']=jcr_clean['journal_normalized']
jcr_clean.loc[~jcr_clean['jcr_quartile'].isin(['Q1','Q2','Q3','Q4']),'jcr_quartile']=''
jcr_clean['jcr_source_year']='2025'
jcr_clean['ranking_source']='JCR 2025'
jcr_clean['match_note']='Cleaned from uploaded JCR_from_pdf.csv'
jcr_clean=jcr_clean[['journal','journal_normalized','journal_alias_normalized','issn','jcr_quartile','jcr_impact_factor','jcr_source_year','ranking_source','match_note']]
jcr_clean=jcr_clean[jcr_clean['journal_normalized'].ne('')].drop_duplicates('journal_normalized', keep='first')
jcr_clean.to_csv(OUT/'jcr_2025_clean_for_bibflow.csv', index=False)

# SJR
sraw=pd.read_csv('/mnt/data/scimagojr 2025.csv', sep=';', dtype=str, engine='c', on_bad_lines='skip')
if 'Type' in sraw.columns:
    sraw=sraw[sraw['Type'].fillna('').str.lower().eq('journal')].copy()
issns=sraw.get('Issn','').apply(split_issns)
sjr_clean=pd.DataFrame({
    'journal': sraw['Title'].fillna('').astype(str).str.strip(),
    'issn': issns.apply(lambda xs: format_issn(xs[0]) if xs else ''),
    'online_issn': issns.apply(lambda xs: format_issn(xs[1]) if len(xs)>1 else ''),
    'sjr_quartile': sraw.get('SJR Best Quartile','').fillna('').astype(str).str.strip().str.upper(),
    'sjr_score': sraw.get('SJR','').fillna('').astype(str).str.replace(',','.', regex=False).str.strip(),
    'sjr_categories': sraw.get('Categories','').fillna('').astype(str).str.strip(),
})
sjr_clean['journal_normalized']=sjr_clean['journal'].apply(normalize_journal_name)
sjr_clean['journal_alias_normalized']=sjr_clean['journal_normalized']
sjr_clean.loc[~sjr_clean['sjr_quartile'].isin(['Q1','Q2','Q3','Q4']),'sjr_quartile']=''
sjr_clean['sjr_source_year']='2025'
sjr_clean['ranking_source']='SJR 2025'
sjr_clean['match_note']='Cleaned from uploaded scimagojr 2025.csv'
sjr_clean=sjr_clean[['journal','journal_normalized','journal_alias_normalized','issn','online_issn','sjr_quartile','sjr_score','sjr_source_year','sjr_categories','ranking_source','match_note']]
sjr_clean=sjr_clean[sjr_clean['journal_normalized'].ne('')].drop_duplicates('journal_normalized', keep='first')
sjr_clean.to_csv(OUT/'sjr_2025_clean_for_bibflow.csv', index=False)

# Combine
base=pd.read_csv(OUT/'journal_rankings_combined_for_bibflow.csv', dtype=str).fillna('')
for col in ['journal','journal_normalized','journal_alias_normalized','issn','online_issn','ranking_source','match_note']:
    if col not in base.columns: base[col]=''
base['journal_normalized']=base.apply(lambda r: normalize_journal_name(r['journal_normalized'] or r['journal']), axis=1)
for col in ['jcr_quartile','jcr_impact_factor','jcr_source_year','sjr_quartile','sjr_score','sjr_source_year','sjr_categories']:
    if col not in base.columns: base[col]=''
base_records=base.to_dict('records')
journal_map={r['journal_normalized']:i for i,r in enumerate(base_records) if r['journal_normalized']}
issn_map={}
for i,r in enumerate(base_records):
    for col in ['issn','online_issn','ft50_issn']:
        c=normalize_issn_compact(r.get(col,''))
        if c and c not in issn_map: issn_map[c]=i

def find_or_new(row):
    jn=row.get('journal_normalized','')
    if jn in journal_map: return journal_map[jn], False
    for col in ['issn','online_issn']:
        c=normalize_issn_compact(row.get(col,''))
        if c and c in issn_map: return issn_map[c], False
    rec={col:'' for col in base.columns}
    rec['journal']=row.get('journal','')
    rec['journal_normalized']=jn
    rec['journal_alias_normalized']=jn
    rec['issn']=row.get('issn','')
    if 'online_issn' in rec: rec['online_issn']=row.get('online_issn','')
    rec['match_note']='Base row from external ranking source'
    idx=len(base_records)
    base_records.append(rec)
    if jn: journal_map[jn]=idx
    for col in ['issn','online_issn']:
        c=normalize_issn_compact(row.get(col,''))
        if c and c not in issn_map: issn_map[c]=idx
    return idx, True

for row in jcr_clean.to_dict('records'):
    idx,new=find_or_new(row); rec=base_records[idx]
    rec['jcr_quartile']=row.get('jcr_quartile','') or rec.get('jcr_quartile','')
    rec['jcr_impact_factor']=row.get('jcr_impact_factor','') or rec.get('jcr_impact_factor','')
    rec['jcr_source_year']=row.get('jcr_source_year','') or rec.get('jcr_source_year','')
    rec['ranking_source']=append_unique(rec.get('ranking_source',''), 'JCR 2025')
    rec['match_note']=append_unique(rec.get('match_note',''), 'merged_by_journal_or_issn_from_JCR')
for row in sjr_clean.to_dict('records'):
    idx,new=find_or_new(row); rec=base_records[idx]
    rec['sjr_quartile']=row.get('sjr_quartile','') or rec.get('sjr_quartile','')
    rec['sjr_score']=row.get('sjr_score','') or rec.get('sjr_score','')
    rec['sjr_source_year']=row.get('sjr_source_year','') or rec.get('sjr_source_year','')
    rec['sjr_categories']=row.get('sjr_categories','') or rec.get('sjr_categories','')
    rec['ranking_source']=append_unique(rec.get('ranking_source',''), 'SJR 2025')
    rec['match_note']=append_unique(rec.get('match_note',''), 'merged_by_journal_or_issn_from_SJR')

updated=pd.DataFrame(base_records).fillna('')
preferred=['journal','journal_normalized','journal_alias_normalized','issn','online_issn','ajg_rating','ajg_field','ajg_source_year','ft50','ft50_issn','ft50_title','abdc_rating','abdc_source_year','abdc_for','ssci','ssci_categories','jcr_quartile','jcr_impact_factor','jcr_source_year','sjr_quartile','sjr_score','sjr_source_year','sjr_categories','school_tier','custom_rating','ranking_tags','ranking_source','match_note']
cols=[c for c in preferred if c in updated.columns]+[c for c in updated.columns if c not in preferred]
updated=updated[cols].sort_values('journal_normalized', kind='stable').reset_index(drop=True)
updated.to_csv(OUT/'journal_rankings_combined_for_bibflow_updated.csv', index=False)
summary=pd.DataFrame([
    {'metric':'JCR raw rows','value':len(jcr)},
    {'metric':'JCR cleaned unique journals','value':len(jcr_clean)},
    {'metric':'JCR rows with quartile','value':int(jcr_clean['jcr_quartile'].ne('').sum())},
    {'metric':'SJR raw journal rows','value':len(sraw)},
    {'metric':'SJR cleaned unique journals','value':len(sjr_clean)},
    {'metric':'SJR rows with quartile','value':int(sjr_clean['sjr_quartile'].ne('').sum())},
    {'metric':'Previous combined rows','value':len(base)},
    {'metric':'Updated combined rows','value':len(updated)},
    {'metric':'Updated combined rows with JCR quartile','value':int(updated['jcr_quartile'].fillna('').ne('').sum())},
    {'metric':'Updated combined rows with SJR quartile','value':int(updated['sjr_quartile'].fillna('').ne('').sum())},
])
summary.to_csv(OUT/'jcr_sjr_combination_summary.csv', index=False)
(OUT/'JCR_SJR_PRIVATE_RANKING_GUIDE.md').write_text('''# BibFlow JCR + SJR Private Ranking Update\n\nGenerated files:\n\n- `jcr_2025_clean_for_bibflow.csv`\n- `sjr_2025_clean_for_bibflow.csv`\n- `journal_rankings_combined_for_bibflow_updated.csv`\n- `jcr_sjr_combination_summary.csv`\n\nRecommended local placement:\n\n```bash\ncd ~/GitHub/bibflow-streamlit\nmkdir -p data/private/source_rankings\ncp ~/Downloads/jcr_2025_clean_for_bibflow.csv data/private/source_rankings/\ncp ~/Downloads/sjr_2025_clean_for_bibflow.csv data/private/source_rankings/\ncp ~/Downloads/journal_rankings_combined_for_bibflow_updated.csv data/private/journal_rankings_combined_for_bibflow.csv\n```\n\nDo not commit `data/private/`.\n''', encoding='utf-8')
shutil.copy('/tmp/clean_jcr_sjr_fast.py', OUT/'build_private_rankings_with_jcr_sjr.py')
zip_path=OUT/'bibflow_jcr_sjr_cleaned_combined.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as zf:
    for fname in ['jcr_2025_clean_for_bibflow.csv','sjr_2025_clean_for_bibflow.csv','journal_rankings_combined_for_bibflow_updated.csv','jcr_sjr_combination_summary.csv','JCR_SJR_PRIVATE_RANKING_GUIDE.md','build_private_rankings_with_jcr_sjr.py']:
        zf.write(OUT/fname, fname)
print(summary.to_string(index=False))
print('ZIP', zip_path)
