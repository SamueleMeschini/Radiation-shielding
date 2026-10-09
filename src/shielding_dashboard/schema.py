"""Versioned dashboard data validation."""
import math
import json
from .materials import ROOT
SCHEMA_VERSION=1
def validate(data):
    if data.get('schema_version')!=SCHEMA_VERSION: raise ValueError('unsupported schema')
    if data.get('quality') not in ('development','lecture'): raise ValueError('dataset quality missing')
    if not isinstance(data.get('cases'),list): raise ValueError('cases missing')
    if not data.get('anchors'): raise ValueError('zero-thickness anchors missing')
    for by_energy in data['anchors'].values():
        for a in by_energy.values():
            if any(a[k]!=1 for k in ('T_N','T_E','B_N','B_E')) or a['thickness_cm']!=0:raise ValueError('invalid exact anchor')
    for c in data['cases']:
        if c['status']!='completed': raise ValueError('incomplete case')
        if c['T_N'] is not None and (not math.isfinite(c['T_N']) or c['T_N']<0): raise ValueError('invalid current')
        if len(c['spectrum_edges_eV'])!=len(c['spectrum'])+1: raise ValueError('spectrum size')
        if len(c['spectrum_sigma'])!=len(c['spectrum']): raise ValueError('spectrum sigma')
    if data['quality']=='lecture':
        grid=json.loads((ROOT/'configs/simulation_grid.yaml').read_text())
        expected={(m,float(E),float(t)) for m in grid['lecture']['materials'] for E in grid['energies_MeV'] for t in grid['optical_thickness'] if t>0}
        actual={(c['spec'].get('material'),float(c['energy_MeV']),float(c['spec'].get('optical_thickness',-1))) for c in data['cases'] if c.get('spec',{}).get('kind')=='slab' and c.get('electron_treatment')=='ttb'}
        if not expected<=actual: raise ValueError(f'lecture matrix missing {len(expected-actual)} cases')
        stacks=set(json.loads((ROOT/'configs/stacks.yaml').read_text()))
        observed={c['spec'].get('name') for c in data['cases'] if c.get('spec',{}).get('kind')=='stack'}
        if not stacks<=observed: raise ValueError('lecture stacks incomplete')
        if not any(c['electron_treatment']=='led' for c in data['cases']): raise ValueError('lecture LED comparison missing')
        if any(c['histories']<200000 for c in data['cases']): raise ValueError('lecture case has development history count')
    return data
