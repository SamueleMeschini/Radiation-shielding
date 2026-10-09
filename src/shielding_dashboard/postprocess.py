import datetime,json,math,hashlib
from pathlib import Path
from .materials import ROOT,load_materials,composition_id
from .photon_data import configure_library,coefficients,library_id,absorption_edges
from .schema import validate

def build_dataset(case_dir,library,quality='development'):
    configure_library(library)
    mats=load_materials();cases=[]
    for path in sorted(Path(case_dir).glob('*.json')):
        c=json.loads(path.read_text())
        if c['status']=='completed':
            if c['T_N'] is not None and c['T_N']<=0: c['quality']='unresolved';c['T_N']=None;c['T_E']=None;c['mean_energy_MeV']=None
            if c['T_E'] is not None and c['T_E']>1+5*c['sigma_E']: c['quality']='physical_check_failed'
            if c['T_N'] is not None and c['T_E'] is not None and c['T_E']>c['T_N']+5*math.hypot(c['sigma_E'],c['sigma_N']): c['quality']='physical_check_failed'
            cases.append(c)
    energies=[.100,.300,.500,.661657,1.000,1.173228,1.332492,2.614511,3.000]
    coeffs={name:{str(E):coefficients(name,m,E) for E in energies} for name,m in mats.items()}
    anchors={name:{str(E):{'thickness_cm':0,'areal_density_g_cm2':0,'optical_thickness':0,'T_N':1,'T_E':1,'B_N':1,'B_E':1,'sigma_N':0,'sigma_E':0,'status':'exact analytical'} for E in energies} for name in mats}
    materials={name:{'density':m['density'],'composition':m['composition'],'composition_id':composition_id(name,m)} for name,m in mats.items()}
    from collections import Counter
    counts=dict(Counter(c['quality'] for c in cases))
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'configs').glob('*.yaml'))}
    for c in cases:c['spec_sha256']=hashlib.sha256(json.dumps(c['spec'],sort_keys=True).encode()).hexdigest()
    dataset={'quality_counts':counts,'configuration_hashes':hashes,'schema_version':1,'quality':quality,'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'library_id':library_id(library),'materials':materials,'anchors':anchors,'energies_MeV':energies,'coefficients':coeffs,'absorption_edges':{name:absorption_edges(m) for name,m in mats.items()},'sources':json.loads((ROOT/'configs/sources.yaml').read_text()),'stacks':json.loads((ROOT/'configs/stacks.yaml').read_text()),'charged_data':json.loads((ROOT/'data/reference/stopping_powers.json').read_text()),'cases':cases}
    return validate(dataset)
