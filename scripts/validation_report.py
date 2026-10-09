"""Check physics invariants against exported OpenMC cases and references."""
import argparse,json,math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from shielding_dashboard.analytical import attenuation,hvl,tvl,stack_uncollided
from shielding_dashboard.schema import validate
p=argparse.ArgumentParser();p.add_argument('dataset');a=p.parse_args()
d=validate(json.loads(Path(a.dataset).read_text()));cases=d['cases'];slabs=[c for c in cases if c['spec']['kind']=='slab' and c['electron_treatment']=='ttb'];checks=[]
def add(name,good,detail):checks.append((name,bool(good),detail))
add('Zero anchor',attenuation(.5,0)==1,'T_N = T_E = B_N = B_E = 1 by exact postprocessing anchor')
add('Uncollided law',attenuation(.5,2)==math.exp(-1),'exp(-μx)')
add('HVL / TVL',abs(attenuation(.5,hvl(.5))-.5)<1e-12 and abs(attenuation(.5,tvl(.5))-.1)<1e-12,'0.5 and 0.1')
add('Layer-order invariant',stack_uncollided([(.5,2),(.2,3)])==stack_uncollided([(.2,3),(.5,2)]),'analytical product')
viol=[];energy=[];spectrum=[];number_spectrum=[];means=[]
for c in slabs:
    if c['T_N'] is None:continue
    unc=math.exp(-c['optical_thickness'])
    if c['T_N']+3*c['sigma_N']<unc:viol.append(c['case_id'])
    if c['T_E'] is not None and (c['T_E']>1+5*c['sigma_E'] or c['T_E']>c['T_N']+5*math.hypot(c['sigma_E'],c['sigma_N'])):energy.append(c['case_id'])
    edges=c['spectrum_edges_eV'];vals=c['spectrum']
    if abs(sum(vals)-c['T_N'])>max(.002,5*c['sigma_N']):number_spectrum.append(c['case_id'])
    if c['mean_energy_MeV'] is not None and abs(c['mean_energy_MeV']-c['energy_MeV']*c['T_E']/c['T_N'])>1e-10:means.append(c['case_id'])
    approx=sum(vals[i]*(edges[i]+edges[i+1])/2 for i in range(len(vals)))/(c['energy_MeV']*1e6)
    if c['T_E'] is not None and abs(approx-c['T_E'])>max(.002,.02*c['T_E']):spectrum.append(c['case_id'])
add('Current ≥ uncollided within 3σ',not viol,f'{len(viol)} / {len(slabs)} violations')
add('Energy current bounded within 5σ',not energy,f'{len(energy)} violations')
add('Number-current spectrum integral',not number_spectrum,f'{len(number_spectrum)} current discrepancies')
add('Mean-energy identity',not means,f'{len(means)} discrepancies')
add('Spectrum mean-energy agreement',not spectrum,f'{len(spectrum)} / {len(slabs)} midpoint integration discrepancies >2% or 0.002')
refs=[('water',.1,.1707),('water',1.,.07072),('lead',.1,5.549),('lead',1.,.07102)]
diffs=[(n,E,100*(d['coefficients'][n][str(E)]['mass_total']/ref-1)) for n,E,ref in refs]
add('NIST XCOM comparison',all(abs(diff)<3 for _,_,diff in diffs),'; '.join(f'{n} {E} MeV: {diff:+.2f}%' for n,E,diff in diffs))
validation=Path('docs/validation_direct.json')
if validation.exists():
    v=json.loads(validation.read_text());add('Direct mixed-source agreement',abs(v['combined_z'])<=3 and abs(v.get('combined_energy_z',float('inf')))<=3,f"number z = {v['combined_z']:.2f}; energy z = {v.get('combined_energy_z',float('nan')):.2f}")
else:add('Direct mixed-source agreement',False,'direct comparison has not been run')
stacks={c['spec'].get('name'):c for c in cases if c['spec']['kind']=='stack'}
if {'pb_sn_cu','cu_sn_pb','equal_mass_copper'}<=stacks.keys():
    graded=stacks['pb_sn_cu'];reversed=stacks['cu_sn_pb'];equal=stacks['equal_mass_copper']
    area=lambda c:sum(m['areal_density_g_cm2'] for m in c['materials'])
    add('Equal areal-density stack',abs(area(graded)-area(equal))<1e-9,f'graded {area(graded):.6f} versus Cu {area(equal):.6f} g/cm²')
    z=(graded['T_N']-reversed['T_N'])/math.hypot(graded['sigma_N'],reversed['sigma_N'])
    add('Measured layer-order effect',abs(z)>3,f'graded minus reversed number current: {z:.2f}σ; spectra are direct tallies')
add('Development/lecture separation',d['quality']=='development' or len(slabs)>=486,f"dataset quality = {d['quality']}")
counts=d.get('quality_counts',{});rel=[c['sigma_N']/c['T_N'] for c in slabs if c['T_N'] and c['sigma_N'] is not None]
lines=['# Validation report','',f"Dataset: **{d['quality']}**; schema {d['schema_version']}; library ID `{d['library_id']}`.",f"Stored cases: {len(cases)}; principal slab cases: {len(slabs)}; quality flags: {counts}.",f"Relative photon-number uncertainty: min {min(rel):.2%}, median {sorted(rel)[len(rel)//2]:.2%}, max {max(rel):.2%}.",'', '| Check | Result | Evidence |','|---|---|---|']
for name,good,detail in checks:lines.append(f'| {name} | {"PASS" if good else "FAIL"} | {detail} |')
lines+=['','The development data are not lecture-quality. Low-statistics cases remain visible. The complete lecture grid has 486 positive-thickness slab cases plus four curated stacks and one LED comparison case.','', 'The current surface tally is signed; a positive +x crossing of the downstream +x vacuum plane is outward. The positive measured currents and current ≥ uncollided checks support this orientation.','', 'NIST references: [water](https://pml.nist.gov/PhysRefData/XrayMassCoef/ComTab/water.html) and [lead](https://pml.nist.gov/PhysRefData/XrayMassCoef/ElemTab/z82.html).']
Path('docs/validation_report.md').write_text('\n'.join(lines)+'\n');print('docs/validation_report.md')
if not all(g for _,g,_ in checks):sys.exit(1)
