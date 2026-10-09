"""Deterministic, cached OpenMC case execution."""
import datetime
import hashlib
import json
import math
import multiprocessing
import os
import sys
from pathlib import Path
import traceback
from .materials import ROOT,load_materials,composition_id,make_openmc
from .photon_data import configure_library,coefficients,library_id
from .model import build

def case_seed(key): return 1+int(hashlib.sha256(key.encode()).hexdigest()[:8],16)%2000000000
def config_hash(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]
def target_relative(t):
    if t>=.01: return .02
    if t>=.001: return .05
    return None

def execute_case(spec,library,outdir,profile,force=False):
    import openmc
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    key=json.dumps(spec,sort_keys=True)
    ident=hashlib.sha256((key+library_id(library)).encode()).hexdigest()[:20]
    path=outdir/(ident+'.json')
    mats=load_materials()
    if path.exists() and not force:
        old=json.loads(path.read_text())
        ids={n:composition_id(n,mats[n]) for n,_ in spec['layers']}
        unchanged=all(m.get('composition_id')==ids.get(m.get('name')) for m in old.get('materials',[]))
        if old.get('status')=='completed' and old.get('histories',0)>=profile['particles']*profile['batches'] and old.get('openmc_version')==openmc.__version__ and unchanged: return old
    E=spec['energy_MeV'];electron=spec.get('electron','ttb')
    incident_E=sum(e*w for e,w in spec['mixed']) if spec.get('mixed') else E
    layers=[(name,float(x)) for name,x in spec['layers']]
    mat_objects=[(make_openmc(name,mats[name]),x) for name,x in layers]
    max_hist=profile['max_histories']; particles=profile['particles'];batches=profile['batches']
    seed=case_seed(key);max_rounds=max(1,math.ceil(max_hist/(particles*batches)))
    result={'schema_version':1,'case_id':ident,'spec':spec,'materials':[{ 'name':n,'composition_id':composition_id(n,mats[n]),'density_g_cm3':mats[n]['density'],'thickness_cm':x,'areal_density_g_cm2':x*mats[n]['density']} for n,x in layers],
            'energy_MeV':E,'electron_treatment':electron,'random_seed':seed,'openmc_version':openmc.__version__,'library_id':library_id(library),'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'running','rounds':[]}
    if len(layers)==1:
        n,x=layers[0]; coeff=coefficients(n,mats[n],E)
        result.update(coefficients=coeff,mu_cm_inverse=coeff['total'],mass_mu_cm2_g=coeff['mass_total'],optical_thickness=x*coeff['total'],thickness_cm=x,areal_density_g_cm2=x*mats[n]['density'])
    work=outdir/'work'/ident;work.mkdir(parents=True,exist_ok=True)
    try:
        for j in range(max_rounds):
            run_dir=work/f'round_{j:02d}';run_dir.mkdir(exist_ok=True)
            model,edges=build(mat_objects,E,particles,batches,seed+j,electron,spec.get('mixed'))
            sp=model.run(cwd=run_dir,output=False,openmc_exec=str(Path(sys.executable).resolve().parent/"openmc"))
            with openmc.StatePoint(sp) as state:
                n=state.get_tally(name='photon_number');e=state.get_tally(name='photon_energy_eV');s=state.get_tally(name='photon_spectrum')
                round_result={'histories':particles*batches,'batches':batches,'seed':seed+j,'number':float(n.mean.ravel()[0]),'number_sigma':float(n.std_dev.ravel()[0]),'energy_eV':float(e.mean.ravel()[0]),'energy_sigma_eV':float(e.std_dev.ravel()[0]),'spectrum':s.mean.ravel().tolist(),'spectrum_sigma':s.std_dev.ravel().tolist()}
            result['rounds'].append(round_result)
            # Independent rounds have equal histories; combine with sample variance
            vals=result['rounds']; k=len(vals)
            def combine(field,sfield):
                avg=sum(v[field] for v in vals)/k
                if k>1: sig=math.sqrt(sum((v[field]-avg)**2 for v in vals)/(k*(k-1)))
                else: sig=vals[0][sfield]
                return avg,sig
            t,st=combine('number','number_sigma');energy,se=combine('energy_eV','energy_sigma_eV')
            result.update(T_N=t,sigma_N=st,T_E=energy/(incident_E*1e6),sigma_E=se/(incident_E*1e6),histories=k*particles*batches,batches=k*batches,spectrum_edges_eV=edges.tolist())
            result['spectrum']=[sum(v['spectrum'][i] for v in vals)/k for i in range(len(vals[0]['spectrum']))]
            result['spectrum_sigma']=[(math.sqrt(sum((v['spectrum'][i]-result['spectrum'][i])**2 for v in vals)/(k*(k-1))) if k>1 else vals[0]['spectrum_sigma'][i]) for i in range(len(result['spectrum']))]
            result['mean_energy_MeV']=incident_E*result['T_E']/t if t>0 else None
            target=target_relative(t)
            result['quality']='unresolved' if t<=0 else ('low_transmission' if target is None else ('target_met' if st/t<=target else 'below_target'))
            path.write_text(json.dumps(result))
            if profile.get('adaptive') and result['quality']=='target_met': break
        if result['quality']=='unresolved':
            result['upper_limit_95_N']=3.0/result['histories']
            result['T_N']=None;result['T_E']=None;result['mean_energy_MeV']=None
        result['status']='completed';path.write_text(json.dumps(result))
        (work/'case.log').write_text(f"status={result['status']} histories={result['histories']} quality={result['quality']} T_N={result['T_N']} sigma_N={result['sigma_N']}\n")
    except Exception as exc:
        result.update(status='failed',error=str(exc),traceback=traceback.format_exc());path.write_text(json.dumps(result));(work/'case.log').write_text(result['traceback']);raise
    return result

def _worker(args):
    spec,library,outdir,p=args
    configure_library(library)
    return execute_case(spec,library,outdir,p)

def matrix(profile_name,library,outdir,limit=None,workers=1,stacks=False):
    import concurrent.futures
    configure_library(library)
    grid=json.loads((ROOT/'configs/simulation_grid.yaml').read_text());p=dict(grid[profile_name]);p['adaptive']=profile_name=='lecture'
    mats=p.get('materials',list(load_materials()))
    energies=p.get('energies_MeV',grid['energies_MeV']);taus=p.get('optical_thickness',grid['optical_thickness'])
    specs=[];allm=load_materials()
    for name in mats:
        for E in energies:
            mu=coefficients(name,allm[name],E)['total']
            for tau in taus:
                if tau>0: specs.append({'kind':'slab','material':name,'energy_MeV':E,'optical_thickness':tau,'layers':[[name,tau/mu]],'electron':'ttb'})
    if profile_name=='lecture':
        mu=coefficients('water',allm['water'],.661657)['total']
        specs.append({'kind':'slab','material':'water','energy_MeV':.661657,'optical_thickness':1,'layers':[['water',1/mu]],'electron':'led'})
    if stacks:
        for name,entry in json.loads((ROOT/'configs/stacks.yaml').read_text()).items():
            specs.append({'kind':'stack','name':name,'energy_MeV':entry['energy_MeV'],'layers':entry['layers'],'electron':'ttb'})
    if limit: specs=specs[:limit]
    args=[(s,library,outdir,p) for s in specs]
    if workers==1: return [_worker(a) for a in args]
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context("spawn")) as pool: return list(pool.map(_worker,args))
