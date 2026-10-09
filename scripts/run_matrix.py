import argparse,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from shielding_dashboard.runner import matrix
def main():
 p=argparse.ArgumentParser();p.add_argument('--profile',choices=['smoke','development','lecture'],default='smoke');p.add_argument('--cross-sections',default=os.getenv('OPENMC_CROSS_SECTIONS'));p.add_argument('--output');p.add_argument('--limit',type=int);p.add_argument('--workers',type=int,default=1);p.add_argument('--stacks',action='store_true')
 a=p.parse_args()
 if not a.cross_sections: p.error('set --cross-sections or OPENMC_CROSS_SECTIONS')
 out=a.output or f'data/{"lecture" if a.profile=="lecture" else "development"}/cases'
 for c in matrix(a.profile,a.cross_sections,out,a.limit,a.workers,a.stacks): print(c['case_id'],c['spec'],c.get('T_N'),c.get('sigma_N'),c['quality'],flush=True)

if __name__=="__main__": main()
