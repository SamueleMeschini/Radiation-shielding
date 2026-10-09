"""Parse locally saved NIST ESTAR/ASTAR text-only tables; no network calls."""
import datetime,hashlib,html,json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
raw=root/'data/reference/raw';out={'source':'NIST ESTAR/ASTAR text-only CGI tables','downloaded_date':'2026-10-08','materials':{}}
for path in sorted(raw.glob('*.html')):
    kind,name=path.stem.split('_',1)
    body=html.unescape(path.read_text())
    body=re.sub(r'<br\s*/?>','\n',body,flags=re.I)
    body=re.sub(r'<[^>]+>','',body)
    rows=[]
    for line in body.splitlines():
        v=line.split()
        if len(v)==7 and re.fullmatch(r'\d\.\d+E[+-]\d+',v[0]) and all(re.fullmatch(r'[+\-]?\d+(?:\.\d+)?(?:E[+\-]\d+)?',a) for a in v):
            rows.append([float(a) for a in v])
    if len(rows)<30:raise ValueError(f'{path}: only {len(rows)} rows')
    if any(rows[i][0]>=rows[i+1][0] for i in range(len(rows)-1)):raise ValueError(f'{path}: unordered energy')
    url='https://physics.nist.gov/cgi-bin/Star/'+('e_table-t.pl' if kind=='estar' else 'ap_table-t.pl')
    out['materials'].setdefault(name,{})[kind]={'rows':rows,'columns':['energy_MeV','collision','radiative','total','csda_g_cm2','radiation_yield','density_effect'] if kind=='estar' else ['energy_MeV','electronic','nuclear','total','csda_g_cm2','projected_g_cm2','detour'],'source_url':url,'raw_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
file=root/'data/reference/stopping_powers.json';file.write_text(json.dumps(out,separators=(',',':')));print(file,len(out['materials']),'materials')
