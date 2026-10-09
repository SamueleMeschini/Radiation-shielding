"""Direct mixed-source and selected LED/TTB checks."""
import argparse,json,math,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from shielding_dashboard.runner import execute_case
from shielding_dashboard.photon_data import configure_library
from shielding_dashboard.analytical import superpose
p=argparse.ArgumentParser();p.add_argument('--cross-sections',default=os.getenv('OPENMC_CROSS_SECTIONS'));a=p.parse_args()
if not a.cross_sections:p.error('provide cross sections')
configure_library(a.cross_sections);profile={'particles':2000,'batches':10,'max_histories':20000,'adaptive':False};out='data/development/validation'
results={}
for E in (.1,1.):
 spec={'kind':'validation','energy_MeV':E,'layers':[['water',5.]],'electron':'ttb'}
 results[E]=execute_case(spec,a.cross_sections,out,profile)
spec={'kind':'validation_mixed','energy_MeV':1.,'layers':[['water',5.]],'electron':'ttb','mixed':[[.1,.5],[1.,.5]]}
direct=execute_case(spec,a.cross_sections,out,profile)
pred=superpose([(.1,.5),(1.,.5)],{E:(v['T_N'],v['sigma_N'],v['T_E'],v['sigma_E']) for E,v in results.items()})
z=(direct['T_N']-pred['T_N'])/math.hypot(direct['sigma_N'],pred['sigma_N'])
ze=(direct['T_E']-pred['T_E'])/math.hypot(direct['sigma_E'],pred['sigma_E'])
print('mixed direct',direct['T_N'],'predicted',pred['T_N'],'z',z,'energy z',ze)
base='data/development/cases'
spec={'kind':'slab','material':'water','energy_MeV':.661657,'optical_thickness':1.,'layers':[['water',11.66898545959127]],'electron':'led'}
led=execute_case(spec,a.cross_sections,base,profile);print('LED selected case',led['T_N'],led['sigma_N'])
Path('docs/validation_direct.json').write_text(json.dumps({'mixed_number_direct':direct['T_N'],'mixed_number_predicted':pred['T_N'],'combined_z':z,'combined_energy_z':ze,'mixed_energy_direct':direct['T_E'],'mixed_energy_predicted':pred['T_E'],'led_case_id':led['case_id']},indent=2))
