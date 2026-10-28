"""Task-scoped restoration of two images in an existing WeChat draft.

Uses the deployed official transport's account, fixed egress and upload helpers.
Does not create drafts, change credentials, or alter shared publisher code.
"""
from pathlib import Path
import base64, hashlib, json, shlex, subprocess, sys
from PIL import Image

HERE=Path(__file__).resolve().parent
ARTICLE=HERE.parents[1]
RELEASE=ARTICLE/'04_发布/当前'
MEDIA='nzrpDfp75juLmURZ1bCkyWcLHq3ZIbzE9Q709YoTqC0rq-Nj_V5QTh7ZKndeC4NU'
REMOTE=r'''
import sys, json, hashlib, fcntl, re, html, os
sys.path.insert(0,'/Users/lixingpeng/CDI-Publisher/official')
import official as o
os.umask(0o077)
r=json.load(sys.stdin)
appid='wx0e8688f2a8b2994a'
assert r['appid']==appid and r['media_id']=='nzrpDfp75juLmURZ1bCkyWcLHq3ZIbzE9Q709YoTqC0rq-Nj_V5QTh7ZKndeC4NU'
digest=lambda s:hashlib.sha256(s.encode()).hexdigest()
token=o.token_for(appid)
if r['mode']=='locate':
    listing=o.api('draft/batchget',token,body={'offset':0,'count':20,'no_content':1})
    matches=[item for item in listing.get('item',[]) if any(a.get('title')=='真神器！有了 Magpie，我真的 Token 自由了！' for a in item.get('content',{}).get('news_item',[]))]
    print(json.dumps({'ok':True,'total_count':listing.get('total_count'),'matches':matches},ensure_ascii=False));sys.exit(0)
with open(o.STATE/'gateway.lock','a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    draft=o.api('draft/get',token,body={'media_id':r['media_id']})
    assert len(draft.get('news_item',[]))==1
    article=draft['news_item'][0]
    assert article['title']=='真神器！有了 Magpie，我真的 Token 自由了！'
    content=article['content']
    tags=list(o.IMG.finditer(content))
    assert len(tags)==11
    if r['mode']=='inspect':
        print(json.dumps({'ok':True,'draft':draft,'content_sha256':digest(content)},ensure_ascii=False))
        sys.exit(0)
    receipt=o.STATE/('update-'+r['update_key']+'.json')
    if receipt.exists():
        saved=json.loads(receipt.read_text())
        if digest(content)==saved.get('after_content_sha256'):
            saved['status']='verified';o.atomic(receipt,saved)
            print(json.dumps({'ok':True,'recovered':True,'receipt':saved,'draft':draft},ensure_ascii=False));sys.exit(0)
        if saved.get('status')=='submitting' and r.get('prior_wechat_rejection')==40007 and digest(content)==saved.get('before_content_sha256'):
            saved.update(status='rejected',wechat_error=40007);o.atomic(receipt,saved)
        if saved.get('status') in ('submitting','verified'):
            raise RuntimeError('update_result_uncertain_inspect_receipt_before_retry')
    assert digest(content)==r['before_content_sha256'],'Draft changed after inspection'
    newurls=saved['new_image_urls'] if receipt.exists() and saved.get('status')=='rejected' else [o.upload(i['data'],token) for i in r['images']]
    pattern=re.compile(r'(?<![\w:-])(?:data-)?src\s*=\s*([\'\"])(.*?)\1',re.I|re.S)
    parts=[];last=0
    for index,match in enumerate(tags):
        parts.append(content[last:match.start()]);tag=match.group()
        if index in (1,2):
            image=r['images'][index-1];url=html.escape(newurls[index-1],quote=True)
            tag=pattern.sub(lambda m:m.group().replace(m[2],url),tag)
            for name,value in [('data-w',image['width']),('data-h',image['height'])]:
                tag=re.sub(r'\b'+name+r'=([\'\"])(.*?)\1',lambda m:name+'='+m[1]+str(value)+m[1],tag)
        parts.append(tag);last=match.end()
    parts.append(content[last:]);updated=''.join(parts)
    def outside_images(s):
        matches=list(o.IMG.finditer(s))
        for i in (2,1):
            m=matches[i];s=s[:m.start()]+'<RESTORED_IMAGE>'+s[m.end():]
        return s
    assert outside_images(content)==outside_images(updated)
    fields=('title','author','digest','content_source_url','thumb_media_id','show_cover_pic','need_open_comment','only_fans_can_comment','pic_crop_235_1','pic_crop_1_1')
    payload={k:article[k] for k in fields if k in article}
    # Preserve the exact current cover pixels and crop. Backend-edited drafts
    # can expose a cover URL but no reusable permanent media identifier.
    cover_sha=None
    if not payload.get('thumb_media_id'):
        cover_source=article['thumb_url'].replace('http://','https://',1)
        cover_data,_,_=o.image_bytes(cover_source)
        cover_sha=hashlib.sha256(cover_data).hexdigest()
        if receipt.exists() and saved.get('cover_media_id') and saved.get('cover_source_sha256')==cover_sha:
            payload['thumb_media_id']=saved['cover_media_id']
        else:
            payload['thumb_media_id']=o.upload(cover_source,token,cover=True)
        from decimal import Decimal
        crop_names={'2.35_1':'pic_crop_235_1','1_1':'pic_crop_1_1'}
        for crop in article.get('cover_info',{}).get('crop_percent_list',[]):
            if crop['ratio'] in crop_names:
                payload[crop_names[crop['ratio']]]='_'.join(format(Decimal(crop[k]),'f') for k in ('x1','y1','x2','y2'))
    payload['content']=updated
    saved={'status':'submitting','appid':appid,'media_id':r['media_id'],'before_content_sha256':digest(content),'after_content_sha256':digest(updated),'replaced_image_indexes':[1,2],'new_image_urls':newurls,'before_draft':draft}
    if cover_sha:
        saved.update(cover_source_sha256=cover_sha,cover_media_id=payload['thumb_media_id'])
    o.atomic(receipt,saved)
    try:
        response=o.api('draft/update',token,body={'media_id':r['media_id'],'index':0,'articles':payload})
    except o.Failure as error:
        if str(error).startswith('wechat_error_'):
            saved.update(status='rejected',wechat_error=str(error));o.atomic(receipt,saved)
        raise
    saved['status']='updated';saved['response']=response;o.atomic(receipt,saved)
    after=o.api('draft/get',token,body={'media_id':r['media_id']})
    actual=after['news_item'][0]
    assert outside_images(actual['content'])==outside_images(content),'Non-target HTML changed'
    for k in fields:
        if k=='thumb_media_id' and cover_sha:
            assert actual[k]==payload[k]
            continue
        assert actual.get(k)==article.get(k),'Non-target field changed: '+k
    if cover_sha:
        actual_cover,_,_=o.image_bytes(actual['thumb_url'].replace('http://','https://',1))
        assert hashlib.sha256(actual_cover).hexdigest()==cover_sha,'Cover pixels changed'
        for before_crop,after_crop in zip(article['cover_info']['crop_percent_list'],actual['cover_info']['crop_percent_list']):
            assert before_crop['ratio']==after_crop['ratio']
            for k in ('x1','y1','x2','y2'):
                assert abs(float(before_crop[k])-float(after_crop[k]))<1e-6,'Cover crop changed'
        saved['cover_pixels_and_crop_unchanged']=True
    actualtags=list(o.IMG.finditer(actual['content']))
    for i in (1,2):
        assert html.unescape(newurls[i-1]) in html.unescape(actualtags[i].group())
    saved.update(status='verified',after_content_sha256=digest(actual['content']),other_html_unchanged=True,other_article_fields_unchanged=True)
    o.atomic(receipt,saved)
    print(json.dumps({'ok':True,'receipt':saved,'draft':after},ensure_ascii=False))
'''

mode=sys.argv[1]
manifest=json.loads((RELEASE/'release-manifest.json').read_text())
request={'mode':mode,'appid':'wx0e8688f2a8b2994a','media_id':MEDIA}
if mode=='update':
    before=json.loads((RELEASE/'草稿更新前.json').read_text())
    request['before_content_sha256']=before['content_sha256']
    request['images']=[]
    for item in manifest['body_images'][:2]:
        path=Path(item['path']);im=Image.open(path)
        request['images'].append({'data':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),'width':im.width,'height':im.height})
    request['update_key']=hashlib.sha256((MEDIA+before['content_sha256']+''.join(hashlib.sha256(Path(i['path']).read_bytes()).hexdigest() for i in manifest['body_images'][:2])).encode()).hexdigest()
    prior_error=RELEASE/'草稿update错误.txt'
    if prior_error.exists() and 'wechat_error_40007' in prior_error.read_text():
        request['prior_wechat_rejection']=40007
result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','mac-mini','/usr/bin/python3','-c',shlex.quote(REMOTE)],input=json.dumps(request),text=True,capture_output=True,timeout=600)
if result.returncode:
    (RELEASE/('草稿'+mode+'错误.txt')).write_text(result.stderr)
    print('Official operation failed; inspect the local error and remote receipt before retry.')
    sys.exit(result.returncode)
data=json.loads(result.stdout)
output=RELEASE/('当前草稿定位.json' if mode=='locate' else '草稿更新前.json' if mode=='inspect' and not (RELEASE/'草稿更新前.json').exists() else '草稿更新检查.json' if mode=='inspect' else '草稿更新回执.json')
output.write_text(json.dumps(data,ensure_ascii=False,indent=2))
print(json.dumps({'ok':data.get('ok'),'mode':mode,'media_id':MEDIA,'receipt':str(output),'content_sha256':data.get('content_sha256'),'status':data.get('receipt',{}).get('status'),'other_html_unchanged':data.get('receipt',{}).get('other_html_unchanged')},ensure_ascii=False,indent=2))
if mode=='locate':
    print(json.dumps({'total_count':data.get('total_count'),'matching_drafts':[{'media_id':x.get('media_id'),'update_time':x.get('update_time')} for x in data.get('matches',[])]},ensure_ascii=False))
