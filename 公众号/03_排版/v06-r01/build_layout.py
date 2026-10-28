from pathlib import Path
import re, json, html, hashlib

LAYOUT = Path(__file__).resolve().parent
ARTICLE = LAYOUT.parents[1]
ROOT = ARTICLE.parents[3]
ASSETS = ARTICLE / '02_素材'
ORIGINAL = ASSETS / '原始'
BODY = ASSETS / '正文图'
RELEASE = ARTICLE / '04_发布/当前'
THEME = Path('/Users/henry/.shared/global-skills/gzh-design-skill/references/theme-caishu-blue.md').read_text()
RENDERER = str(ROOT / '.agents/scripts/build_caishu_wechat_images.py')

def component(number):
    section = re.search(r'^### ' + re.escape(number) + r' .*?(?=^### |^## |\Z)', THEME, re.M | re.S).group()
    return re.search(r'```html\n(.*?)\n```', section, re.S).group(1)

def inline(text):
    parts = re.split(r'(\*\*.*?\*\*)', text)
    return ''.join('<strong style="font-weight:800;color:#0052FF;"><span leaf="">' + html.escape(p[2:-2]) + '</span></strong>' if p.startswith('**') else '<span leaf="">' + html.escape(p) + '</span>' for p in parts if p)

def paragraph(text):
    return component('3.4').replace('{{正文}}', inline(text)).replace('<span leaf="">' + inline(text) + '</span>', inline(text))

def image_block(src, caption):
    # Source files already contain the required gradient frame.
    out = component('3.7').replace('border:1px solid #C9D7E8;', '')
    return out.replace('{{图片路径}}', src).replace('{{图片说明}}', html.escape(caption))

specs = [
    ('01a','01a-Harness-多来源模型-v02.png','01-Harness-模型列表-v01.png',[1300,190,1905,950],'DeepSeek Harness 中的多来源模型列表'),
    ('01b','01b-Harness-WorkBuddy与Step-v02.png','01b-Harness-模型列表下半部-v01.png',[1300,740,1905,1510],'同一模型列表下半部：WorkBuddy、WorkBuddy AI 与 Step'),
    ('03','03-Magpie-Agents-v01.png','03-Magpie-Agents-v01.png',[0,0,2334,960],'Magpie 原生 Agent 主界面'),
    ('04','04-模型转接原理-v01.png','04-模型转接原理-AI原图-v01.png',None,'模型来源 → Magpie → 常用 Agent（原理示意图）'),
    ('05','05-Magpie-Providers-v01.png','05-Magpie-Providers-v01.png',[0,0,2334,1440],'Magpie 供应商页面，账号信息已打码'),
    ('06','06-Magpie-Routing-v01.png','06-Magpie-Routing-v01.png',[0,0,2334,1020],'Magpie 路由页面：真实请求的模型与账号去向'),
    ('07','07-Magpie-Plugins-v01.png','07-Magpie-Plugins-v01.png',[0,0,2334,960],'Magpie 已安装的插件，包括 Qoder 与 WorkBuddy'),
    ('08a','08a-WorkBuddy-多账号-v01.png','08a-WorkBuddy-多账号-v01.png',[560,130,1785,1180],'Magpie 中的 WorkBuddy 多账号，账号名已打码'),
    ('08b','08b-WorkBuddyAI-多账号-v01.png','08b-WorkBuddyAI-多账号-v01.png',[560,130,1785,1400],'Magpie 中的 WorkBuddy AI 多账号，邮箱已打码'),
    ('09','09-Harness-真实输出-v03.gif','09-Harness-WorkBuddy-真实输出-v01.mp4',[390,80,2130,1640],'WorkBuddy DeepSeek 真实输出，界面本次显示 111 tok/s'),
]

entries = []
for key, name, source, crop, caption in specs:
    item = dict(path=str(BODY/name),remote_src=f'https://wechat-official.local/materials/caishu-20261027-magpie-token/{key}'+('.gif' if name.endswith('.gif') else '.png'),source_images=[str(ORIGINAL/source)],caption=caption)
    if key == '04':
        item.update(kind='diagram',generated_by='codex-imagegen',transform='resize-and-frame')
    else:
        item.update(kind='screenshot',transform='crop-and-frame',crop=crop,renderer=RENDERER)
    if key == '09':
        item.update(media_type='gif',provenance=str(BODY/'09-Harness-真实输出-v03.provenance.json'))
    entries.append(item)

source_path = ARTICLE/'01_正文/正文-v05.md'
source = source_path.read_text()
production = source
coverpath = ASSETS/'封面/封面-v01.png'
production = production.replace('<!-- CAISHU_PROFILE_CARD -->', f'![当期封面]({coverpath})\n\n<!-- CAISHU_PROFILE_CARD -->',1)
groups = {'01':entries[:2],'02':[],'03':[entries[2]],'04':[entries[3]],'05':[entries[4]],'06':[entries[5]],'07':[entries[6]],'08':entries[7:9],'09':[entries[9]]}
for key, items in groups.items():
    production = re.sub(r'<!-- 配图'+key+r'：.*?-->', '\n\n'.join(f'![{x["caption"]}]({x["path"]})' for x in items), production,flags=re.S)
production = production.rstrip() + '\n\n<!-- CAISHU_FIXED_CTA -->\n\n<!-- CAISHU_PROFILE_CARD -->\n'
markdown_path = ARTICLE/'01_正文/正文-v06.md'
if markdown_path.exists() and markdown_path.read_text()!=production:
    raise RuntimeError('Refusing to overwrite a different production Markdown')
markdown_path.write_text(production)

# Validate that media insertion and the user-authorized deletion of image 02
# have not changed any of the supplied prose, headings or quoted prompt.
def prose(s):
    s=re.sub(r'<!--.*?-->','',s,flags=re.S)
    s=re.sub(r'!\[.*?\]\([^\n]*\)','',s)
    return re.sub(r'\s+','',s)
assert prose(source)==prose(production), 'Source prose changed'

coverremote='https://wechat-official.local/materials/caishu-20261027-magpie-token/cover.png'
remote_by_path={e['path']:e['remote_src'] for e in entries}
remote_by_path[str(coverpath)]=coverremote
blocks=[]
profiles=0
chapter=0
paragraph_lines=[]
quote_lines=[]
code_lines=[]
in_code=False

def flush_paragraph():
    if paragraph_lines:
        blocks.append(paragraph(' '.join(paragraph_lines)));paragraph_lines.clear()

def codeblock(lines, prompt=False):
    top=component('3.9a')
    row='<p style="margin:0;font-family:\'SF Mono\',Consolas,Monaco,monospace;font-size:13px;line-height:1.6;color:#E2E8F0;">{}</p>'
    content=''.join(row.format(inline(x) if x else '<span leaf="">&nbsp;</span>') for x in lines)
    top=re.sub(r'<p style="margin:0;font-family:.*?</p>',lambda _:content,top,count=1,flags=re.S)
    return top

def flush_quote():
    if quote_lines:
        blocks.append(codeblock(quote_lines,True));quote_lines.clear()

for line in production.splitlines():
    if line.startswith('```'):
        flush_paragraph();flush_quote()
        if in_code:
            blocks.append(codeblock(code_lines));code_lines.clear()
        in_code=not in_code
        continue
    if in_code:
        code_lines.append(line);continue
    if line.startswith('>'):
        flush_paragraph();quote_lines.append(re.sub(r'^> ?', '',line));continue
    flush_quote()
    if not line.strip():flush_paragraph();continue
    if line.startswith('# '):flush_paragraph();continue
    if line.startswith('## '):
        flush_paragraph();chapter+=1
        # Preserve the supplied chapter heading word for word.
        blocks.append(component('3.5').replace('{{章节编号}}',f'{chapter:02}').replace('{{中文章节标题}}',html.escape(line[3:])));continue
    if line=='<!-- CAISHU_PROFILE_CARD -->':
        flush_paragraph();profiles+=1
        blocks.append(component('3.3').replace('{{0或2}}','0' if profiles==1 else '2'));continue
    if line=='<!-- CAISHU_FIXED_CTA -->':
        flush_paragraph();blocks.append(component('3.10'));continue
    m=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',line)
    if m:
        flush_paragraph();caption,path=m.groups();remote=remote_by_path[path]
        if path==str(coverpath):blocks.append(component('3.2').replace('{{当期封面路径}}',remote))
        else:blocks.append(image_block(remote,caption))
        continue
    paragraph_lines.append(line)
flush_paragraph();flush_quote()
blocks.append(component('3.11'))
body=component('3.1').replace('<!-- 按完整文章骨架插入组件 -->','\n'.join(blocks))
html_path=LAYOUT/'正文_排版_财叔蓝(caishu-blue).html'
html_path.write_text(body)

manifest=dict(schema_version=1,brand_id='caishu-ai-lab',article_type='wechat-longform',theme_id='caishu-blue',title=source.splitlines()[0][2:],markdown=str(markdown_path),html=str(html_path),body_image_policy='required',cover=dict(path=str(coverpath),remote_src=coverremote,generated_by='codex-imagegen',transform='resize-only',style_profile='brand-editorial',source_images=[str(ORIGINAL/'封面-AI原图-v01.png')],reference_assets=[str(ROOT/'00_品牌与经营/品牌资产/卡通IP视觉系统/20260921-概念套图/12-财叔全新统一卡通IP-本人短碎发-v12.png'),str(ROOT/'00_品牌与经营/品牌资产/卡通IP视觉系统/20260921-公众号封面完整成图-v1/01-豆包Work四个自媒体工作流.png')]),body_images=entries,source_baseline=str(source_path),source_baseline_sha256=hashlib.sha256(source.encode()).hexdigest(),notes=['用户已明确取消配图02，发布HTML无该图及其替代图。','v06只插入配图引用和固定结构标记，v05原稿不变，原文全文一致性检查通过。','remote_src是官方上传适配器使用的逻辑映射，推送时直接上传本地文件并替换为微信CDN地址。'])
RELEASE.mkdir(parents=True,exist_ok=True)
(RELEASE/'release-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))

preview=body
for entry in [manifest['cover']]+entries:
    preview=preview.replace(entry['remote_src'],Path(entry['path']).as_uri())
preview='<!doctype html><html lang="zh-CN"><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(manifest['title'])+'</title><body style="margin:0;background:#edf2f7"><main style="max-width:693px;margin:auto;background:white">'+preview+'</main></body></html>'
(LAYOUT/'本地预览.html').write_text(preview)
(LAYOUT/'正文一致性检查.json').write_text(json.dumps(dict(ok=True,source=str(source_path),production=str(markdown_path),source_sha256=manifest['source_baseline_sha256'],prose_unchanged=True,cancelled_image='02',body_images=len(entries)),ensure_ascii=False,indent=2))
(ASSETS/'配图索引-v01.md').write_text('# Magpie 公众号配图索引\n\n基线：正文-v05.md；配图稿：正文-v06.md。用户明确取消配图02。\n\n'+ '\n'.join(f'- {e["caption"]}：[{Path(e["path"]).name}]({e["path"]})；来源：{e["source_images"][0]}' for e in entries)+'\n\n原始录像52.22秒；正文GIF截取12–35秒，原速，3fps，23秒。显示111 tok/s，不声称达到200–300。\n\n采集差异：本机WorkBuddy有4个账号，WorkBuddy AI有5个账号；Codex供应商页只显示1个账号。v05中“多个 WorkBuddy、WorkBuddy AI、Codex 账号”的原文保留，需作者核对其中Codex的表述。\n\n真实截图只做裁剪、缩放、品牌框；账号模糊来自Magpie内置账号打码。AI图明确为原理示意；封面为Codex内置生图。\n')
print(json.dumps(dict(markdown=str(markdown_path),html=str(html_path),preview=str(LAYOUT/'本地预览.html'),manifest=str(RELEASE/'release-manifest.json'),body_images=len(entries),prose_unchanged=True),ensure_ascii=False,indent=2))
