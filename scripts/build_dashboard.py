import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from shielding_dashboard.build_dashboard import build
p=argparse.ArgumentParser();p.add_argument('--dataset',default='dashboard/data.json');p.add_argument('--output',default='dist/shielding_dashboard.html')
a=p.parse_args();print(build(a.dataset,a.output))
