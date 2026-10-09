import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load_materials(path=None):
    data=json.loads(Path(path or ROOT/'configs/materials.yaml').read_text())
    for name,m in data.items():
        if m['density']<=0 or abs(sum(m['composition'].values())-1)>1e-5: raise ValueError(name)
    return data
def composition_id(name,m):
    blob=json.dumps([name,m['density'],m['composition']],sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:16]
def make_openmc(name,m):
    import openmc
    mat=openmc.Material(name=name);mat.set_density('g/cm3',m['density'])
    for el,w in m['composition'].items():
        if el in ('Cu','Sn'):
            from openmc.data import NATURAL_ABUNDANCE, atomic_mass
            isotopes={n:a for n,a in NATURAL_ABUNDANCE.items() if n.startswith(el) and n[len(el):].isdigit()}
            total=sum(a*atomic_mass(n) for n,a in isotopes.items())
            for n,a in isotopes.items(): mat.add_nuclide(n,w*a*atomic_mass(n)/total,'wo')
        else: mat.add_element(el,w,'wo')
    return mat
