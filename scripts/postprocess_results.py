import argparse,os,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from shielding_dashboard.postprocess import build_dataset
p=argparse.ArgumentParser();p.add_argument('--cases',default='data/development/cases');p.add_argument('--cross-sections',default=os.getenv('OPENMC_CROSS_SECTIONS'));p.add_argument('--output',default='dashboard/data.json');p.add_argument('--quality',choices=['development','lecture'],default='development')
a=p.parse_args()
if not a.cross_sections:p.error('set --cross-sections or OPENMC_CROSS_SECTIONS')
d=build_dataset(a.cases,a.cross_sections,a.quality);Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(d,separators=(',',':')));print(a.output,len(d['cases']),'completed cases',d['quality'])
