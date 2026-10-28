# -*- coding: utf-8 -*-
from pathlib import Path
import json,re,difflib,math
p=Path(__file__).resolve().parents[1]
chunks=[
['兄弟们','这次真的 Token 自由了'],
['最近我用上了一个真神器','叫 Magpie，越用越上头'],
['它直接把 WorkBuddy、Qoder','这些大厂的免费模型','接进了我常用的 DeepSeek 桌面端'],
['现在我打开模型列表','DeepSeek、Step、GPT','Grok、Gemini，全都在里面','想用哪个就用哪个'],
['而且不止 DeepSeek Harness','我日常主力用的 Codex','也被我接进了一大堆其他模型'],
['那 Magpie 到底是个啥','你把它理解成一个模型总控台就行'],
['Magpie 是 GitHub 上','一个叫 yetone 的大神做的开源项目'],
['它干的事儿其实特别好懂','我给你举个最简单的例子'],
['比如你在 Codex 里登了一个账号','这个账号能用的一批模型','正常就只能在 Codex 里面用'],
['WorkBuddy 也一样','它有它自己的模型和额度','平时你就得回 WorkBuddy 里面用'],
['Magpie 做的事','就是在中间加一个总控台'],
['左边接你的模型和订阅','右边接你真正想用的 Agent'],
['它先把不同账号里的可用模型认出来','再统一通过 Magpie','提供给其他 Agent'],
['比如你在 DeepSeek Harness 里','选 WorkBuddy 的 DeepSeek','任务先到 Magpie','再转给 WorkBuddy 里的 DeepSeek 去跑'],
['结果回来以后','再原路送回 DeepSeek Harness','整个过程你几乎感觉不到'],
['所以以前只能待在一个 Agent 里的订阅模型','现在可以拿去给别的 Agent 用'],
['这就是它最核心的一件事'],
['这件事以前也有工具干过','但说实话，体验都不算特别好'],
['像 CC Switch 我也折腾过','Bug 挺多，还要手动填不少东西','用起来其实挺麻烦'],
['Magpie 就完全不一样','它把这件事干得极其丝滑'],
['模型、账号、订阅、Agent','基本都在一个地方管','很多操作点几下就完事'],
['而且功能非常完善','路由、模型分组、自动切换','额度、用量统计都有','我现在其实只用了一小部分'],
['最爽的用法是','Magpie 还能帮你薅免费 Token','它真是个薅免费 Token 的神器'],
['现在 WorkBuddy 海外版、Qoder','都有免费的 DeepSeek V4.1 Flash','活动到十月底','WorkBuddy 国内版','每天签到还送一百积分'],
['问题是，这些免费的 DeepSeek','都散在 WorkBuddy、Qoder 这些客户端里','我又不想来回切客户端用'],
['我就想把它们统一接进','DeepSeek Harness','可不可以？可以','Magpie 就能直接帮我接过去'],
['而且 DeepSeek 配官方 DeepSeek Harness','真的很爽，响应快','工具调用顺','基本就是原生的感觉'],
['最最关键的是','Magpie 还支持你同时接多个账号','我现在就同时挂了多个','WorkBuddy、WorkBuddy AI、Codex 账号'],
['每个账号登录验证一次就行','后面交给 Magpie 管','相当于可以多倍白嫖'],
['安装也不用自己一条条敲命令','直接让 Agent 帮你装'],
['把我准备好的提示词','丢给 WorkBuddy 或 DeepSeek Harness','让它自己安装 Magpie','接账号、检查模型'],
['中间需要登录授权的时候','你自己点一下','剩下的继续让 Agent 干'],
['唯一特别注意一点','DeepSeek Harness','有 web 和 desktop 两套 Profile'],
['一定让 Agent 改对 desktop','重启以后看模型列表','再拿一个真实任务跑通','就算搞定'],
['我是财叔','类似这种真能省 Token 的神器','我继续给大家挖','我们下期见']]
def norm(s):return ''.join(c.lower() for c in s if c.isalnum())
rows={r['id']:r for r in json.loads((p/'work/tts-asr-review.json').read_text())}
n=json.loads((p/'narration.confirmed.json').read_text())
audio=json.loads((p/'audio_manifest.json').read_text())
output={}
for s,parts in zip(n['scenes'],chunks):
 sid=s['id'];expected=norm(s['narration']);assert norm(''.join(parts))==expected,sid
 recognized='';times=[]
 for seg in rows[sid]['segments']:
  for word in seg.get('words',[]):
   text=norm(word['word']);t0=word['start'];t1=word['end']
   for i,c in enumerate(text):recognized+=c;times.append(t0+(t1-t0)*i/max(1,len(text)))
 anchors={}
 for block in difflib.SequenceMatcher(None,expected,recognized,autojunk=False).get_matching_blocks():
  for j in range(block.size):anchors[block.a+j]=times[block.b+j]
 dur=math.ceil(audio['scenes'][sid]['duration_ms']*.03)
 def gettime(k):
  if k in anchors:return anchors[k]
  before=[i for i in anchors if i<k];after=[i for i in anchors if i>k]
  lo=max(before) if before else 0;hi=min(after) if after else len(expected)
  t0=anchors.get(lo,0);t1=anchors.get(hi,dur/30)
  return t0+(t1-t0)*(k-lo)/max(1,hi-lo)
 cuts=[0];k=0
 for part in parts[:-1]:
  k+=len(norm(part));cuts.append(max(cuts[-1]+1,min(dur-1,round((gettime(k)-.035)*30))))
 cuts.append(dur)
 output[sid]=[{'text':part,'startFrame':cuts[i],'endFrame':cuts[i+1]} for i,part in enumerate(parts)]
(p/'work/caption-overrides.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
for sid,segs in output.items():
 print(sid,[(s['text'],round((s['endFrame']-s['startFrame'])/30,2)) for s in segs])
props=p/'work/motion-preview-props.json';data=json.loads(props.read_text())
for s in data['data']['scenes']:s['captionSegments']=output[s['id']]
props.write_text(json.dumps(data,ensure_ascii=False,indent=2))
