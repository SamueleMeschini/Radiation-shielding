import argparse,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
p=argparse.ArgumentParser();p.add_argument('--cross-sections',default=os.getenv('OPENMC_CROSS_SECTIONS'))
a=p.parse_args();print('Python',sys.version.split()[0]);print('OPENMC_CROSS_SECTIONS',os.getenv('OPENMC_CROSS_SECTIONS'))
try:
 import openmc
 print('OpenMC',openmc.__version__)
 from shielding_dashboard.photon_data import configure_library,coefficients,library_id
 from shielding_dashboard.materials import load_materials
 if not a.cross_sections: raise ValueError('set --cross-sections or OPENMC_CROSS_SECTIONS')
 path=configure_library(a.cross_sections);print('Library ID',library_id(path),'photon data:',len([x for x in openmc.data.DataLibrary.from_xml().libraries if x['type']=='photon']))
 for name in ('water','lead'):
  print(name,'mu(1 MeV)',coefficients(name,load_materials()[name],1.0)['total'])
except Exception as e:
 print(type(e).__name__+':',e);sys.exit(1)
