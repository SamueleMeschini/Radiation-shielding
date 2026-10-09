import json,re
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
def test_built_offline_structure():
    html=(ROOT/'dist/shielding_dashboard.html').read_text()
    m=re.search(r'<script id="embedded-data" type="application/json">(.*?)</script>',html,re.S)
    assert m,'missing embedded dataset'
    d=json.loads(m.group(1))
    assert d['schema_version']==1 and d['quality'] in ('development','lecture')
    assert len(d['cases'])>=1
    assert 'src="http' not in html and 'href="http' not in html
    assert '<script src="app.js">' not in html and '<link rel="stylesheet" href="styles.css">' not in html
    for id in ('explore','compare','interaction','hardening','builder','charged'):
        assert f'id="{id}"' in html
    assert '<section id="challenge"' not in html
    assert 'href="#challenge"' not in html

def test_student_facing_labels_and_figures():
    html=(ROOT/'dist/shielding_dashboard.html').read_text()
    visible=re.sub(r'<script.*?</script>','',html,flags=re.S|re.I)
    for forbidden in ('>01<','>02<','>03<','>04<','>05<','>06<','>07<','anchor','direct OpenMC point','Current curve data','Equal cm','Equal g/cm²','photon-number'):
        assert forbidden not in visible
    assert 'Transmitted photon spectrum' in html
    assert 'rotate(-90' in html
    assert 'katex' in html.lower()

def test_differential_spectrum_integrates_to_binned_transmission():
    for path in list((ROOT/'data/development/cases').glob('*.json'))[:20]:
        case=json.loads(path.read_text())
        if case['status']!='completed':
            continue
        edges=[v/1e6 for v in case['spectrum_edges_eV']]
        differential=[v/(edges[i+1]-edges[i]) for i,v in enumerate(case['spectrum'])]
        assert sum(y*(edges[i+1]-edges[i]) for i,y in enumerate(differential))==pytest.approx(sum(case['spectrum']),abs=1e-12)
