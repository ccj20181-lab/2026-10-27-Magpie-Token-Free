# -*- coding: utf-8 -*-
from pathlib import Path
import json,hashlib,subprocess,datetime
from PIL import Image
p=Path(__file__).resolve().parents[1]
root=p.parents[1]
old=root/'公众号/02_素材/原始'
new=p.parent/'02_素材/补采'
plan=json.loads((p/'visual_plan.json').read_text());assets=[]
def asset(aid,filename,folder,crop=None,highlights=None,kind='screenshot',support='',scene_ids=None):
 path=folder/filename
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))
 stream=next(s for s in probe['streams'] if s['codec_type']=='video')
 a={'asset_id':aid,'request_id':aid,'scene_ids':scene_ids or [],'type':kind,'path':str(path),'app':'原生应用 / 官方公开页面','task_title':filename,'captured_at':datetime.datetime.fromtimestamp(path.stat().st_mtime,datetime.timezone.utc).isoformat(),'width':stream['width'],'height':stream['height'],'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'semantic_support':support,'qa':{'status':'accepted','readability':'已查看原始截图；关键区域按完整菜单、结果区或面板取景，成片另验','stability':'截图静态；录像另有SAVED与选段检查','completeness':'保留真实对象、状态与语义上下文','notes':'源素材接受不等于完整成片听看或发布'},'provenance':{'method':'article_original_reuse' if folder==old else 'official_native_computer_use_and_screencapturekit' if aid.startswith('native') else 'ego_browser_public_page','source_project_id':'2026-10-27-Magpie-Token自由','source_manifest':str(root/'公众号/02_素材/配图索引-v02.md') if folder==old else None,'source_path':str(path)}}
 if crop:a['crop']=crop
 if highlights:a['highlights']=[{'rect':r,'color':'#D93232','strokeWidth':5} for r in highlights]
 if kind=='recording':a['duration_seconds']=float(probe['format']['duration']);a['events']=[]
 assets.append(a);return a
asset('article-models-a','01-Harness-模型列表-v01.png',old,[0,0,2560,1640],[[1300,170,630,810]],support='完整Harness窗口，实际模型列表显示多个来源')
asset('article-models-b','01b-Harness-模型列表下半部-v01.png',old,[1260,650,890,980],support='模型列表下半部，包含WorkBuddy、WorkBuddy AI、Step和当前所选模型')
asset('article-codex-config','02-Magpie-Codex模型配置-v01.png',old,[450,100,1850,1050],support='Magpie中Codex已接入状态和15模型来源分组；不是Codex本体截图')
asset('article-providers','05-Magpie-Providers-v01.png',old,[440,110,1870,1380],support='真实Providers列表显示Codex、Grok、WorkBuddy、WorkBuddy AI、Antigravity与订阅状态，账号已在源画面模糊')
asset('article-routing','06-Magpie-Routing-v01.png',old,[440,120,1870,1000],support='真实路由页面保留Codex→Magpie→模型与账号的关系及使用上下文')
asset('article-plugins','07-Magpie-Plugins-v01.png',old,[440,120,1870,850],support='实际已装插件列表，包括WorkBuddy与Qoder')
asset('article-accounts-wb','08a-WorkBuddy-多账号-v01.png',old,[540,120,1250,1160],support='真实WorkBuddy账号面板，4个账号与余额/状态；账号标识在源画面已模糊')
asset('article-accounts-wbai','08b-WorkBuddyAI-多账号-v01.png',old,[540,120,1250,1370],support='真实WorkBuddy AI账号面板，5个已授权账号、添加账号入口；账号标识已模糊')
asset('article-accounts-codex','08c-Codex-当前仅一账号-v01.png',old,[540,120,1250,1370],support='真实Codex账号面板，当前1个账号；不复制或伪造多账号数量')
asset('article-output','09-Harness-WorkBuddy-真实输出-v01.mp4',old,[390,80,2130,1510],kind='recording',support='已被用户通过的52.22秒原片，展示WorkBuddy DeepSeek实际长文输出与111 tok/s，引用原速片段')
asset('public-author','10-GitHub-作者与项目-v03.png',new,[0,65,650,550],[[15,15+65,245,40]],support='GitHub官方yetone/magpie真实项目页，作者、项目名和MIT许可')
asset('public-readme','11-GitHub-中文README-v03.png',new,[40,0,820,990],support='官方中文README的模型统一入口定位，保留Magpie图标、标题与平台支持，去除赞助商区')
asset('public-install','12-GitHub-中文安装-v03.png',new,[40,280,820,860],support='官方中文快速开始三步，展示安装、添加来源与给Agent选择模型')
asset('public-qoder','13-Qoder-限免规则-v01.png',new,[75,320,1120,900],[[90,990,1100,155]],support='Qoder官方限免文档，保留完整标题、活动模型、每日额度和10月31日截止说明')
asset('public-ccswitch','14-CCSwitch-真实项目页-v01.png',new,[0,130,1300,1200],support='CC Switch官方仓库身份；只证明工具对象，不用项目页伪造Bug证据')
asset('native-agents-still','15-Magpie-Agent-管理结果-v01.png',new,[410,40,1900,920],support='本次原生采集的Magpie Agent总览，多个Agent已连接及模型选项')
asset('native-agents-video','15-Magpie-Agent-管理演示-v01.mp4',new,[410,40,1900,920],kind='recording',support='本次真实收起Codex设置回到Agent总览的动作；不改接入配置')
asset('native-model-video','16-Harness-模型菜单演示-v01.mp4',new,[1260,600,1050,1030],kind='recording',support='本次Harness真实模型菜单，滚动展示模型来源，WorkBuddy DeepSeek保持选中，未更改默认模型')
asset('native-wb-models','17-WorkBuddy-模型与倍率-v01.png',new,[1030,760,730,860],support='WorkBuddy完整模型菜单与计费倍率，未改模型选择')
asset('native-wb-daily','18-WorkBuddy-每日100积分-v02.png',new,[15,1350,500,245],support='真实Buddy加油站完整福利卡，显示每日可领100积分、今日已领取；不截取单独数值')
asset('native-prompt','19-Harness-安装提示词-v01.png',new,[440,350,1680,1040],support='文章原有安装提示词实际粘贴到Harness输入框；仅展示，未发送和执行')
asset('native-profiles','21-Harness-真实Profile目录-v01.png',new,[340,0,1120,390],[[360,166,470,48],[360,288,470,48]],support='访达显示真实.dsh/profiles目录中的desktop与web，同时保留目录标题和相邻文件夹，不打开配置秘密')
asset('native-tools-start','22-Harness-工具调用-启动录像-v01.mp4',new,[430,90,1690,1480],kind='recording',support='新公开只读测试真实发送、开始运行、调用Python并返回83810205；当前选用WorkBuddy DeepSeek')
asset('native-tools-result','22-Harness-工具调用-结果录像-v01.mp4',new,[490,500,1550,1090],kind='recording',support='所选0–7.43秒展示完成的命令、输出、模型与步骤统计；另通过AX核对过实际bash调用，轨迹界面不入片')
mapping={2:'native-agents-still',3:'article-models-a',4:'native-model-video',5:'article-codex-config',7:'public-author',8:'public-readme',10:'native-wb-models',19:'public-ccswitch',20:'native-agents-video',21:'article-providers',22:'article-routing',24:'public-qoder',25:'article-plugins',26:'native-model-video',27:'native-tools-result',28:'article-accounts-wb',29:'article-accounts-wbai',30:'public-install',31:'native-prompt',32:'article-accounts-wbai',33:'native-profiles',34:'native-tools-start'}
byid={a['asset_id']:a for a in assets}
starts={4:7.8,20:10.8,26:0.1,27:0.0,34:20.0}
for s in plan['scenes']:
 i=int(s['id'][-2:])
 if i not in mapping:continue
 a=byid[mapping[i]];s['capture_asset_id']=a['asset_id'];s['capture_request_id']=a['request_id'];s['visual_type']='real_recording' if a['type']=='recording' else 'real_screenshot'
 s['content_description']=a['semantic_support'];s['framing']='固定电脑媒体框；原比例展示完整语义区，不拉伸；首个Harness镜头保留完整窗口，后续模型菜单为阅读名称而聚焦完整菜单。'
 a['scene_ids'].append(s['id'])
 if i in starts:s['source_start_seconds']=starts[i]
 if i==24:s['evidence_sequence']=[{'asset_id':'public-qoder','from_frame':0},{'asset_id':'native-wb-daily','from_frame':156}];byid['native-wb-daily']['scene_ids'].append(s['id'])
 if i==28:
  s['evidence_sequence']=[{'asset_id':'article-accounts-wb','from_frame':0},{'asset_id':'article-accounts-wbai','from_frame':102},{'asset_id':'article-accounts-codex','from_frame':186}]
  byid['article-accounts-wbai']['scene_ids'].append(s['id']);byid['article-accounts-codex']['scene_ids'].append(s['id'])
  s['content_description']='依次展示WorkBuddy 4账号、WorkBuddy AI 5账号、Codex当前1账号；不把同一账号复制成多个'
(p/'visual_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
(p/'capture_manifest.json').write_text(json.dumps({'schema_version':'1.0','project_id':plan['project_id'],'checked_after':'2026-10-27T21:40:33+08:00','source_article_index':str(root/'公众号/02_素材/配图索引-v02.md'),'assets':assets,'issues':[],'observations':['公众号原图/原片只读复用，未使用公众号AI原理图或封面替代视频动效','当前Codex账号面板为1个，按真实数量展示，不伪造多个','工具轨迹已确认bash实际返回83810205；含上下文的轨迹画面不进入成片','新任务只执行了python乘法，不修改文件和配置']},ensure_ascii=False,indent=2))
print('BOUND',len(mapping),'real scenes;',len(assets),'traceable assets')
