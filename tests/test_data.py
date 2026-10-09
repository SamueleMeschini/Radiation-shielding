import json,math
from pathlib import Path
import pytest
from shielding_dashboard.schema import validate
from shielding_dashboard.materials import load_materials
from shielding_dashboard.photon_data import configure_library,coefficients
ROOT=Path(__file__).resolve().parents[1]

def test_materials():
    m=load_materials();assert len(m)==6
    assert m['water']['density']==1 and m['lead']['density']==11.34

def test_schema_quality():
    d={'schema_version':1,'quality':'development','cases':[],'anchors':{'water':{'0.1':{'T_N':1,'T_E':1,'B_N':1,'B_E':1,'thickness_cm':0}}}}
    assert validate(d)==d
    with pytest.raises(ValueError):validate({**d,'schema_version':2})
    with pytest.raises(ValueError):validate({**d,'quality':'lecture','cases':[{'status':'completed','T_N':1,'spectrum_edges_eV':[0,1],'spectrum':[1],'spectrum_sigma':[0],'quality':'below_target'}]})

def test_nist_attenuation_reference():
    pytest.importorskip('openmc')
    configure_library(ROOT/'endfb-viii.1-hdf5/cross_sections.xml')
    mats=load_materials()
    for name,E,nist in [('water',.1,.1707),('water',1,.07072),('lead',.1,5.549),('lead',1,.07102)]:
        c=coefficients(name,mats[name],E)
        assert c['mass_total']==pytest.approx(nist,rel=.03)
        assert sum(c[k] for k in ('coherent','incoherent','photoelectric','pair_triplet'))==pytest.approx(c['total'])

def test_real_spectrum_integration_if_present():
    paths=list((ROOT/'data/development/cases').glob('*.json'))
    if not paths:pytest.skip('no OpenMC case yet')
    for path in paths[:5]:
        c=json.loads(path.read_text())
        if c['status']!='completed':continue
        edges=c['spectrum_edges_eV'];v=c['spectrum']
        assert sum(v)==pytest.approx(c['T_N'],abs=max(.005,5*c['sigma_N']))
        midpoint=sum(v[i]*(edges[i]+edges[i+1])/2 for i in range(len(v)))/(c['energy_MeV']*1e6)
        assert midpoint==pytest.approx(c['T_E'],rel=.02,abs=.002)
        assert c['mean_energy_MeV']==pytest.approx(c['energy_MeV']*c['T_E']/c['T_N'])

def test_local_nist_tables_and_equal_mass_stack():
    refs=json.loads((ROOT/'data/reference/stopping_powers.json').read_text())
    water=refs['materials']['water']
    estar=next(row for row in water['estar']['rows'] if row[0]==1.0)
    astar=next(row for row in water['astar']['rows'] if row[0]==1.0)
    assert estar[4]==pytest.approx(.4367,rel=.002)
    assert astar[4]==pytest.approx(.0005931,rel=.002)
    cfg=json.loads((ROOT/'configs/stacks.yaml').read_text())
    densities={n:m['density'] for n,m in load_materials().items()}
    def area(name):return sum(densities[n]*x for n,x in cfg[name]['layers'])
    assert area('pb_sn_cu')==pytest.approx(area('equal_mass_copper'),rel=1e-12)
