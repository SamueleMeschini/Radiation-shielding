import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_built_offline_structure():
    html=(ROOT/'dist/shielding_dashboard.html').read_text()
    m=re.search(r'<script id="embedded-data" type="application/json">(.*?)</script>',html,re.S)
    assert m,'missing embedded dataset'
    d=json.loads(m.group(1))
    assert d['schema_version']==1 and d['quality']=='development'
    assert len(d['cases'])>=1
    assert 'src="http' not in html and 'href="http' not in html
    assert '<script src="app.js">' not in html and '<link rel="stylesheet" href="styles.css">' not in html
    for id in ('explore','compare','interaction','hardening','builder','charged','challenge'):
        assert f'id="{id}"' in html
