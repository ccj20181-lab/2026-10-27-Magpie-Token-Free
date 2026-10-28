"""Restore pre-update styles after WeChat filters encoded CSS quotes.

Retains the two restored model images and every existing article setting.
"""
from pathlib import Path
import json,re,html,hashlib,shlex,subprocess,sys
HERE=Path(__file__).resolve().parent
RELEASE=HERE.parents[1]/'04_发布/当前'
before=json.loads((RELEASE/'草稿更新前.json').read_text())['draft']['news_item'][0]
current_doc=json.loads((RELEASE/'草稿更新回执.json').read_text())
current=current_doc['draft']['news_item'][0]
img=re.compile(r'<img\b[^>]*>',re.I)
original_images=list(img.finditer(before['content']))
current_images=list(img.finditer(current['content']))
desired=before['content']
for index in (2,1):
    target=original_images[index]
    desired=desired[:target.start()]+current_images[index].group()+desired[target.end():]
style=re.compile(r'\bstyle\s*=\s*([\'\"])(.*?)\1',re.I|re.S)
def decode_css(m):
    value=html.unescape(m[2])
    if m[1] in value:
        value=value.replace(m[1],'&#34;' if m[1]=='"' else '&#39;')
    return 'style='+m[1]+value+m[1]
desired=style.sub(decode_css,desired)
(HERE/'后台修复内容.html').write_text(desired)
request={'media_id':'nzrpDfp75juLmURZ1bCkyWcLHq3ZIbzE9Q709YoTqC0rq-Nj_V5QTh7ZKndeC4NU','expected_current_hash':hashlib.sha256(current['content'].encode()).hexdigest(),'desired_content':desired,'original_article':before}
remote=r'''
import sys,json,hashlib,re,html,fcntl,os
from decimal import Decimal
sys.path.insert(0,'/Users/lixingpeng/CDI-Publisher/official')
import official as o
os.umask(0o077)
r=json.load(sys.stdin)
appid='wx0e8688f2a8b2994a';mid='nzrpDfp75juLmURZ1bCkyWcLHq3ZIbzE9Q709YoTqC0rq-Nj_V5QTh7ZKndeC4NU'
assert r['media_id']==mid
sha=lambda s:hashlib.sha256(s.encode()).hexdigest()
def normalize(s):
    tags=list(o.IMG.finditer(s))
    for index in (2,1):
        m=tags[index];s=s[:m.start()]+'<RESTORED_IMAGE>'+s[m.end():]
    return re.sub(r'\bstyle\s*=\s*([\'\"])(.*?)\1',lambda m:'style="'+html.unescape(m[2])+'"',s,flags=re.I|re.S)
token=o.token_for(appid)
with open(o.STATE/'gateway.lock','a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    draft=o.api('draft/get',token,body={'media_id':mid});article=draft['news_item'][0]
    assert article['title']==r['original_article']['title']
    assert sha(article['content'])==r['expected_current_hash'],'Draft changed during verification'
    assert normalize(r['desired_content'])==normalize(r['original_article']['content'])
    fields=('title','author','digest','content_source_url','thumb_media_id','show_cover_pic','need_open_comment','only_fans_can_comment','article_type')
    payload={k:article[k] for k in fields if k in article};payload['content']=r['desired_content']
    original_receipt=json.loads((o.STATE/'18213569c3db9facce614502605ddb787715d6ce11248631d8e518bb4501f6d6.json').read_text())
    assert original_receipt['appid']==appid and original_receipt['title']==article['title']
    payload['thumb_media_id']=original_receipt['thumb_media_id']
    assert payload['thumb_media_id']
    for crop in article.get('cover_info',{}).get('crop_percent_list',[]):
        names={'2.35_1':'pic_crop_235_1','1_1':'pic_crop_1_1'}
        if crop['ratio'] in names:payload[names[crop['ratio']]]='_'.join(format(Decimal(crop[k]),'f') for k in ('x1','y1','x2','y2'))
    receipt=o.STATE/('repair-'+sha(mid+r['desired_content'])+'.json')
    o.atomic(receipt,{'status':'submitting','media_id':mid,'before_content_sha256':sha(article['content']),'desired_content_sha256':sha(r['desired_content'])})
    response=o.api('draft/update',token,body={'media_id':mid,'index':0,'articles':payload})
    o.atomic(receipt,{'status':'updated','media_id':mid,'response':response})
    after=o.api('draft/get',token,body={'media_id':mid});actual=after['news_item'][0]
    unchanged=normalize(actual['content'])==normalize(r['original_article']['content'])
    metadata={k:actual.get(k)==(payload[k] if k=='thumb_media_id' else article.get(k)) for k in fields if k!='content'}
    oldcover=o.image_bytes(r['original_article']['thumb_url'].replace('http://','https://',1))[0]
    newcover=o.image_bytes(actual['thumb_url'].replace('http://','https://',1))[0]
    cover_equal=hashlib.sha256(oldcover).hexdigest()==hashlib.sha256(newcover).hexdigest()
    crop_equal=r['original_article'].get('cover_info')==actual.get('cover_info')
    result={'ok':unchanged and all(metadata.values()) and cover_equal and crop_equal,'media_id':mid,'response':response,'other_html_and_styles_unchanged':unchanged,'metadata_unchanged':metadata,'cover_bytes_unchanged':cover_equal,'cover_crop_unchanged':crop_equal,'draft':after}
    o.atomic(receipt,{'status':'verified' if result['ok'] else 'verification_failed',**result})
    print(json.dumps(result,ensure_ascii=False))
'''
result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','mac-mini','/usr/bin/python3','-c',shlex.quote(remote)],input=json.dumps(request),text=True,capture_output=True,timeout=600)
if result.returncode:
    (RELEASE/'样式还原错误.txt').write_text(result.stderr);print('Style restoration did not return a verified receipt; inspect state before retry.');sys.exit(result.returncode)
data=json.loads(result.stdout);(RELEASE/'草稿更新回执.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in data.items() if k!='draft'},ensure_ascii=False,indent=2))
sys.exit(0 if data.get('ok') else 1)
