"""Keep the complete original app screenshot and mark its real model menu.

The user explicitly requested whole-window screenshots with a red rectangle.
No UI text, menus, account information, or model results are synthesized.
"""
from pathlib import Path
import importlib.util, tempfile, json, hashlib
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ARTICLE = HERE.parents[1]
ROOT = ARTICLE.parents[3]
spec = importlib.util.spec_from_file_location('brand_frame', ROOT/'.agents/scripts/build_caishu_wechat_images.py')
brand = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brand)
raw = ARTICLE/'02_素材/原始'
out = ARTICLE/'02_素材/正文图'
jobs = [
    ('01-Harness-模型列表-v01.png','01a-Harness-整窗红框-v03.png',(1300,190,1905,950)),
    ('01b-Harness-模型列表下半部-v01.png','01b-Harness-整窗红框-v03.png',(1300,740,1905,1510)),
]
evidence=[]
for source_name, output_name, bounds in jobs:
    source, output = raw/source_name, out/output_name
    if output.exists():
        raise RuntimeError('Refusing to replace an existing image')
    im=Image.open(source).convert('RGB')
    ImageDraw.Draw(im).rectangle(bounds,outline='#E62626',width=9)
    with tempfile.TemporaryDirectory() as directory:
        marked=Path(directory)/'marked.png'
        im.save(marked)
        brand.screenshot_frame(marked,output,brand.load_policy()['visual'])
    evidence.append(dict(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),output=str(output),output_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),original_size=list(im.size),whole_window=True,annotation=dict(type='rectangle',bounds=bounds,color='#E62626',width=9),authorization='用户2026-10-27明确要求整窗截图并用红框圈出模型列表'))
(HERE/'模型截图修订证据.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
print(json.dumps(evidence,ensure_ascii=False,indent=2))
