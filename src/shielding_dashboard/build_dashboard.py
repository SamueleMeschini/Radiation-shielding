import base64
import json
from pathlib import Path
from .schema import validate
from .materials import ROOT

def build(dataset_path,output_path):
    data=validate(json.loads(Path(dataset_path).read_text()))
    html=(ROOT/'dashboard/index.html').read_text();css=(ROOT/'dashboard/styles.css').read_text();js=(ROOT/'dashboard/app.js').read_text();katex_css=(ROOT/'dashboard/katex.min.css').read_text();katex_js=(ROOT/'dashboard/katex.min.js').read_text()
    for font in (ROOT/'dashboard/katex-fonts').glob('*.woff2'):
        encoded=base64.b64encode(font.read_bytes()).decode('ascii')
        katex_css=katex_css.replace(f'url(fonts/{font.name})',f'url(data:font/woff2;base64,{encoded})')
    blob=json.dumps(data,separators=(',',':')).replace('</','<\\/')
    html=html.replace('<link rel="stylesheet" href="katex.min.css">','<style>'+katex_css+'</style>').replace('<link rel="stylesheet" href="styles.css">','<style>'+css+'</style>')
    html=html.replace('<script src="katex.min.js"></script><script src="app.js"></script>','<script>'+katex_js+'</script><script id="embedded-data" type="application/json">'+blob+'</script><script>'+js+'</script>')
    out=Path(output_path);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(html)
    return out
