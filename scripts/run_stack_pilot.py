"""Raise selected precomputed stack spectra to 100,000 histories."""
import json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from shielding_dashboard.runner import execute_case
from shielding_dashboard.photon_data import configure_library
from shielding_dashboard.materials import ROOT
lib=sys.argv[1] if len(sys.argv)>1 else os.getenv('OPENMC_CROSS_SECTIONS')
if not lib:raise SystemExit('pass the cross_sections.xml path')
configure_library(lib)
p={'particles':10000,'batches':10,'max_histories':100000,'adaptive':False}
for name,c in json.loads((ROOT/'configs/stacks.yaml').read_text()).items():
 spec={'kind':'stack','name':name,'energy_MeV':c['energy_MeV'],'layers':c['layers'],'electron':'ttb'}
 out=execute_case(spec,lib,'data/development/cases',p,force=True)
 print(name,out['histories'],out['T_N'],out['sigma_N'],flush=True)
