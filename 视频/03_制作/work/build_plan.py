# -*- coding: utf-8 -*-
from pathlib import Path
import sys,json,hashlib
p=Path(__file__).resolve().parents[1]
skill=Path('/Users/henry/Desktop/财叔 AI Lab/.agents/skills/ai-coach-daily-demo')
sys.path.insert(0,str(skill/'scripts'))
import director
import render_ai_coach_demo as renderer
renderer.PUBLIC_ROOT=p/'remotion/public/ai-coach-daily-demo'
npath=p/'narration.confirmed.json';n=json.loads(npath.read_text())
motion={1:('magpie_hook','Token从受限客户端中释放并连接两个Agent','开场直接展示权益可以换入口使用'),
6:('magpie_hub','左侧三个模型来源接入中央Magpie，右侧连接两个Agent','把模型总控台的两端说清楚'),
9:('magpie_silo','Codex窗口围住账号与模型，底部阻隔线说明原来使用入口受限','同一个模型权益原本跟随客户端'),
11:('magpie_insert','两个端点不动，中央插入Magpie','总控台改变连接关系'),
12:('magpie_wiring','左侧金色来源线路、右侧青绿Agent线路分段接通','左右两端与口播同步建立'),
13:('magpie_discovery','识别不同来源模型逐个打勾，再汇入一个模型入口','先发现可用模型再提供给Agent'),
14:('magpie_packet','请求沿Harness→Magpie→WorkBuddy路线移动','用运动说明真实任务的转发路径'),
15:('magpie_packet','结果沿WorkBuddy→Magpie→Harness反向回传','同一条链路解释返回过程'),
16:('magpie_passport','同一权益Token从原Agent跨到其他Agent','模型来源保留，使用入口可变'),
17:('magpie_core','权益与Agent间一个稳定调度关系落定','核心结论有清晰视觉落点'),
18:('magpie_compare','左侧多次配置的折返线与右侧集中管理的直线对照','仅图解个人体验，下一幕展示工具'),
23:('magpie_free','两处免费模型Token通过汇流线进入Magpie','把分散免费权益集中调度'),
35:('magpie_outro','Token与继续前进的箭头构成收尾','财叔持续挖工具的CTA')}
real={
2:('Magpie','overview','Magpie真实主界面与连接状态'),
3:('DeepSeek Harness','models-a','Harness真实模型菜单，保留来源provider'),
4:('DeepSeek Harness','models-b','模型菜单展开与滚动，显示多个厂商'),
5:('Codex','codex-models','Codex真实模型选择器或Magpie Codex Agent模型设置'),
7:('GitHub','github-author','yetone/magpie项目页，作者、仓库名、开源信息'),
8:('GitHub','github-example','Magpie README中连接Agent的功能说明'),
10:('WorkBuddy','workbuddy-models','WorkBuddy实际模型选择界面与客户端标题'),
19:('CC Switch','ccswitch','CC Switch真实项目页或配置页面，只作为工具身份，不伪造Bug'),
20:('Magpie','agents-recording','Magpie Agents界面真实操作，展示集中管理'),
21:('Magpie','providers','Providers列表中的来源与可用模型'),
22:('Magpie','routing','Routing页面中的组和路由设置，保留标题'),
24:('官方文档','free-policy','Qoder与WorkBuddy官方免费活动、截至日期和签到积分规则'),
25:('Magpie','plugins','真实插件页同时展示WorkBuddy与Qoder来源'),
26:('DeepSeek Harness','models-select','Harness中实际选择WorkBuddy DeepSeek的模型列表'),
27:('DeepSeek Harness','task-result','真实任务输出录像，模型与完整结果上下文同时出现'),
28:('Magpie','accounts-wb','WorkBuddy多账号页面，遮挡真实账号标识'),
29:('Magpie','accounts-wbai','WorkBuddy AI多账号已授权状态，遮挡账号标识'),
30:('GitHub','installation','Magpie官方安装入口与支持平台文档'),
31:('DeepSeek Harness','setup-prompt','准备好的安装提示词完整可读，不执行系统安装'),
32:('Magpie','authorization','真实账号授权入口，展示需要用户完成的步骤，不替用户登录'),
33:('DeepSeek Harness','profiles','真实web/desktop Profile选择或真实配置文件路径'),
34:('DeepSeek Harness','verify','重启后模型列表和已运行的真实任务结果录像')}
scenes=[]
for i,s in enumerate(n['scenes'],1):
 base={'id':s['id'],'narration':s['narration'],'audience_takeaway':s['intent'],'framing':'固定1080×1920财叔版式；内容画布1024×1100；无额外英文标签','timing':'以本幕真实TTS自然时长校准，关键结果在对应字幕片段附近落定并留阅读时间。'}
 if i in motion:
  eid,desc,reason=motion[i];base.update(visual_type='motion_effect',selection_reason=reason,content_description=desc,effect={'id':eid,'renderer':'custom','params':{}})
 else:
  app,rid,desc=real[i];rec=i in {4,20,26,27,32,34}
  base.update(visual_type='real_recording' if rec else 'real_screenshot',media_surface='desktop',selection_reason='真实界面或官方材料支持本幕实际对象与操作；原图不替换原生控件',content_description=desc,capture_request_id=rid,capture_request={'purpose':desc,'app':app,'task_context':'财叔第4期Magpie视频；优先复用同主题公众号原始素材，只补对应缺口','required_events':[desc],'framing':'保留应用标题、对象、模型来源和结果上下文；固定电脑媒体框，原始比例contain','readability_requirements':'手机画幅可识别关键标签；不显示邮箱、账号标识、密钥、令牌或未授权聊天'})
 scenes.append(base)
plan={'schema_version':'1.0','project_id':n['project_id'],'narration_path':str(npath),'narration_sha256':director.sha(npath),'source_article_path':str(p.parents[1]/'公众号/01_正文/正文-v05.md'),'brand_profile':'caishu_ai_lab','episode':'4','motion_style':'caishu-editorial-v1','scenes':scenes,'bgm':{'volume':.12,'fadeInSeconds':.8,'fadeOutSeconds':1.6}}
director.write(p/'visual_plan.json',plan)
director.export_requests(p/'visual_plan.json',p/'requests')
audio=json.loads((p/'audio_manifest.json').read_text())
slug='magpie-04-motion-preview'
data={'meta':director.brand_metadata(plan,slug,renderer.copy_public),'scenes':[]}
data['meta'].update(workflowVersion=2,episode='4',demoTitle=n['title'],fps=30,width=1080,height=1920)
import math
for s in scenes:
 if s['visual_type']!='motion_effect':continue
 a=audio['scenes'][s['id']];dur=math.ceil(a['duration_ms']*.03)
 data['scenes'].append({'id':s['id'],'kind':'effect','visualType':'motion_effect','headline':s['audience_takeaway'],'caption':s['narration'],'effect':s['effect'],'durationFrames':dur,'assetPath':'','audioPath':renderer.copy_public(Path(a['path']),slug,'audio/'+s['id']+'.mp3'),'captionSegments':renderer.caption_segments(s['narration'],audio_duration_ms=a['duration_ms'],duration_frames=dur)})
director.write(p/'work/motion-preview-props.json',{'data':data})
start=0;frames=[]
for s in data['scenes']:
 frames.append({'id':s['id'],'start':start,'duration':s['durationFrames'],'samples':[start+min(5,s['durationFrames']-1),start+int(s['durationFrames']*.5),start+int(s['durationFrames']*.85)]});start+=s['durationFrames']
director.write(p/'work/motion-preview-frames.json',frames)
print('13 motion, 22 real; preview',round(start/30,2),'s')
