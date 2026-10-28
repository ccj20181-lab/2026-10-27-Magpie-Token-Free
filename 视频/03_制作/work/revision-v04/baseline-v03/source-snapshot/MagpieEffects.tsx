import React from 'react';
import {Canvas,Text,Stroke,Reveal,Check,useMaterial} from './motion/caishu-editorial-v1/primitives';
import {color as C} from './motion/caishu-editorial-v1/tokens';
import {tween,clamp,cueFrame,pointOnPolyline} from './motion/caishu-editorial-v1/timing';
import {MotionEffectProps} from './types';

const Box=({x,y,w=270,h=116,label,sub,color=C.ink,dark=false}:{x:number;y:number;w?:number;h?:number;label:string;sub?:string;color?:string;dark?:boolean})=>{
 const m=useMaterial();const units=(s:string)=>[...s].reduce((v,c)=>v+(/[^\x00-\x7f]/.test(c)?1:.58),0);return <g transform={`translate(${x},${y})`}>
 <rect width={w} height={h} rx={4} fill={dark?color:m.paper} stroke={dark?color:C.line} strokeWidth={2} filter={m.shadow}/>
 <rect x={0} y={0} width={7} height={h} fill={color}/>
 <Text x={w/2} y={sub?h*.43:h*.59} size={Math.min(36,(w-38)/units(label))} color={dark?'white':C.ink} anchor="middle" weight={700}>{label}</Text>
 {sub&&<Text x={w/2} y={h*.75} size={Math.min(27,(w-32)/units(sub))} color={dark?'#D9ECE9':C.muted} anchor="middle" weight={500}>{sub}</Text>}
 </g>;
};
const Token=({x,y,r=42,label='T',p=1,color=C.gold}:{x:number;y:number;r?:number;label?:string;p?:number;color?:string})=>{
 const m=useMaterial();return <g opacity={p} transform={`translate(${x},${y}) scale(${.75+.25*p})`}>
 <circle r={r} fill={m.metal} stroke={color} strokeWidth={2} filter={m.shadow}/>
 <circle r={r-7} fill="none" stroke="#F8EBC4" strokeWidth={2}/><Text x={0} y={r*.3} anchor="middle" size={r*.8} weight={700} color={C.ink}>{label}</Text>
 </g>;
};
const Dot=({points,p,color=C.teal,label}:{points:[number,number][];p:number;color?:string;label?:string})=>{
 const [x,y]=pointOnPolyline(points,clamp(p));return <g opacity={p>0&&p<1?1:0}><circle cx={x} cy={y} r={14} fill={color}/>{label&&<Text x={x} y={y-30} size={29} anchor="middle" color={color}>{label}</Text>}</g>;
};
const Ray=({points,p=1,color=C.teal}:{points:[number,number][];p?:number;color?:string})=><Stroke d={points.map(([x,y],i)=>`${i?'L':'M'}${x} ${y}`).join(' ')} progress={p} color={color} width={4}/>;
const Console=({p=1,y=420}:{p?:number;y?:number})=><Reveal progress={p}><Box x={342} y={y} w={340} h={190} label="Magpie" sub="模型总控台" color={C.teal} dark/><g transform={`translate(377,${y+154})`}>{[0,1,2,3].map(i=><rect key={i} x={i*22} y={0} width={12} height={5} fill={i<3?'#87C5AD':C.gold}/>)}</g></Reveal>;

const Hook:React.FC<MotionEffectProps>=({local})=>{
 const p=tween(local,0,20),split=tween(local,20,26);
 return <Canvas><Text x={56} y={140} size={39} color={C.muted}>把模型，从客户端里解放出来</Text>
 <Text x={56} y={290} size={92} weight={800}>这次真的</Text><Reveal progress={p} y={36}><Text x={48} y={435} size={142} color={C.teal} weight={800}>Token 自由</Text></Reveal>
 <g opacity={1-split}><rect x={217} y={570} width={590} height={290} fill={C.light} stroke={C.line} strokeWidth={2}/><path d="M390 680v-50a55 55 0 0 1 110 0v50" fill="none" stroke={C.ink} strokeWidth={10}/><rect x={370} y={675} width={150} height={105} fill={C.ink}/></g>
 <Reveal progress={split}><Box x={65} y={635} w={260} label="DeepSeek" sub="Harness"/><Box x={699} y={635} w={260} label="Codex" sub="常用 Agent"/><Ray points={[[325,693],[425,693]]} p={split}/><Ray points={[[599,693],[699,693]]} p={split}/></Reveal>
 <Token x={512} y={695} r={92} p={p}/><Text x={512} y={957} size={34} anchor="middle" color={C.muted}>统一调度你已有的模型与额度</Text></Canvas>;
};
const Hub:React.FC<MotionEffectProps>=({local,scene})=>{
 const p=tween(local,0,20),q=tween(local,cueFrame(scene,'总控台',.28),24);
 return <Canvas title="Magpie 是什么？" foot="模型与订阅在左边，常用 Agent 在右边">
 <Text x={56} y={218} size={38} color={C.muted}>一个入口，连接两端</Text>
 {[['WorkBuddy','订阅 / 额度'],['Qoder','模型 / 额度'],['Codex','账号 / 订阅']].map(([label,sub],i)=><Reveal key={label} progress={tween(local,i*7,20)}><Box x={56} y={315+i*190} w={260} label={label} sub={sub} color={C.gold}/><Ray points={[[316,373+i*190],[340,373+i*190],[340,515]]} p={q} color={C.gold}/></Reveal>)}
 <Console p={p}/><Reveal progress={q}><Ray points={[[682,515],[710,515],[710,420],[730,420]]}/><Ray points={[[710,515],[710,630],[730,630]]}/><Box x={730} y={362} w={240} label="DeepSeek" sub="Harness"/><Box x={730} y={572} w={240} label="Codex" sub="日常工作台"/></Reveal></Canvas>;
};
const Silo:React.FC<MotionEffectProps>=({local,scene})=>{
 const p=tween(local,0,20),q=tween(local,cueFrame(scene,'只能',.5),24);
 return <Canvas title="原来：模型跟着客户端走" foot="示意：账号权益与客户端入口绑定">
 <Reveal progress={p}><rect x={120} y={250} width={784} height={605} rx={4} fill={C.light} stroke={C.line} strokeWidth={3}/><rect x={120} y={250} width={784} height={74} fill={C.ink}/><Text x={162} y={301} color="white" size={36}>Codex</Text><Box x={258} y={398} w={508} h={148} label="已登录的账号" sub="账号可用的模型" color={C.teal}/>
 {[0,1,2,3,4].map(i=><Token key={i} x={302+i*105} y={659} r={36} p={tween(local,12+i*5,18)}/>)}</Reveal>
 <Reveal progress={q}><path d="M163 895H861" stroke={C.red} strokeWidth={5}/><path d="M502 875v40m20-40v40" stroke={C.red} strokeWidth={5}/><Text x={512} y={963} size={40} anchor="middle" color={C.red}>用这批模型，就回这个客户端</Text></Reveal></Canvas>;
};
const Insert:React.FC<MotionEffectProps>=({local,scene})=>{
 const p=tween(local,cueFrame(scene,'总控台',.3),26);
 return <Canvas title="在中间，加一个总控台" foot="路由原理示意，不代表新增平台额度">
 <Box x={65} y={405} w={270} h={156} label="模型 / 订阅" sub="来自不同账号" color={C.gold}/><Box x={689} y={405} w={270} h={156} label="常用 Agent" sub="继续在熟悉的地方用"/>
 <Ray points={[[335,483],[689,483]]} color={C.line}/><g transform={`translate(0,${(1-p)*180})`} opacity={p}><Console y={390}/></g>
 <Ray points={[[335,483],[342,483]]} p={p} color={C.gold}/><Ray points={[[682,483],[689,483]]} p={p}/>
 <Reveal progress={p}><Text x={512} y={786} size={54} anchor="middle" weight={700}>两端不动，连接方式变了</Text></Reveal></Canvas>;
};
const Wiring:React.FC<MotionEffectProps>=({local,scene})=>{
 const left=tween(local,cueFrame(scene,'左边',.08),25),right=tween(local,cueFrame(scene,'右边',.5),25);
 return <Canvas title="左接模型，右接 Agent" foot="示意：按授权访问各账号可用模型">
 <Text x={60} y={225} size={33} color={C.gold}>你的模型与订阅</Text><Text x={720} y={225} size={33} color={C.teal}>你的工作入口</Text><Console/>
 {['WorkBuddy','Qoder','Codex'].map((s,i)=><g key={s}><Box x={56} y={310+i*190} w={260} label={s} color={C.gold}/><Ray points={[[316,368+i*190],[329,368+i*190],[329,515],[342,515]]} p={left} color={C.gold}/></g>)}
 {['DeepSeek','Codex'].map((s,i)=><g key={s}><Box x={716} y={380+i*240} w={260} label={s} sub={i===0?'Harness':undefined}/><Ray points={[[682,515],[700,515],[700,438+i*240],[716,438+i*240]]} p={right}/></g>)}
 </Canvas>;
};
const Discovery:React.FC<MotionEffectProps>=({local,scene})=>{
 const p=tween(local,cueFrame(scene,'认出来',.22),35),q=tween(local,cueFrame(scene,'统一',.53),26);
 return <Canvas title="先识别模型，再统一提供" foot="同名模型仍保留来源，额度由来源平台提供">
 {['WorkBuddy / DeepSeek','Qoder / DeepSeek','Codex / GPT'].map((s,i)=><g key={s}><Box x={80} y={250+i*155} w={630} h={105} label={s} color={i===2?C.teal:C.gold}/><Check x={775} y={305+i*155} progress={tween(p*100,i*20,20)}/></g>)}
 <Ray points={[[395,665],[395,738],[512,738],[512,788]]} p={q}/><Reveal progress={q}><Box x={230} y={788} w={564} h={134} label="Magpie 统一模型入口" sub="供其他 Agent 调用" color={C.teal} dark/></Reveal></Canvas>;
};
const Packet:React.FC<MotionEffectProps>=({local,scene})=>{
 const back=scene.id==='scene_15';
 const start=back?5:cueFrame(scene,'任务先到',.5);
 const middle=back?cueFrame(scene,'再原路',.2):cueFrame(scene,'再转给',.7);
 const finish=back?cueFrame(scene,'整个过程',.58):Math.min(scene.durationFrames-18,middle+30);
 const incoming:[number,number][]=[[214,430],[214,470],[512,470],[512,500]];
 const outgoing:[number,number][]=[[512,650],[512,690],[810,690],[810,750]];
 const first=back?[...outgoing].reverse():incoming,second=back?[...incoming].reverse():outgoing;
 const firstP=clamp((local-start)/Math.max(1,middle-start)),secondP=clamp((local-middle)/Math.max(1,finish-middle));
 return <Canvas title={back?'结果，沿原路回来':'一个任务，怎么走？'} foot="调用链路示意；原生界面与实跑结果见演示">
 <Box x={56} y={280} w={350} h={150} label="DeepSeek Harness" sub={back?'收到真实模型结果':'选择 WorkBuddy / DeepSeek'}/>
 <Box x={338} y={500} w={348} h={150} label="Magpie" sub={back?'接收并转发结果':'把请求路由到来源'} color={C.teal} dark/>
 <Box x={622} y={750} w={346} h={150} label="WorkBuddy" sub="DeepSeek" color={C.gold}/>
 <Ray points={incoming} color={C.line}/><Ray points={outgoing} color={C.line}/>
 <Ray points={first} p={firstP} color={back?C.teal:C.gold}/><Ray points={second} p={secondP} color={back?C.teal:C.gold}/>
 <Dot points={first} p={firstP} color={back?C.teal:C.gold}/><Dot points={second} p={secondP} color={back?C.teal:C.gold}/>
 <Reveal progress={tween(local,finish,12)}><Check x={back?214:810} y={back?459:718}/></Reveal></Canvas>;
};
const Passport:React.FC<MotionEffectProps>=({local,scene})=>{
 const p=tween(local,cueFrame(scene,'别的',.48),34);const x=244+536*p,y=550-100*Math.sin(p*Math.PI);
 return <Canvas title="订阅权益，有了新的使用入口" foot="使用已有账号权益；各平台额度规则继续适用">
 <rect x={56} y={280} width={370} height={480} fill={C.paper} stroke={C.line} strokeWidth={2}/><rect x={56} y={280} width={7} height={480} fill={C.gold}/><rect x={598} y={280} width={370} height={480} fill={C.paper} stroke={C.line} strokeWidth={2}/><rect x={598} y={280} width={7} height={480} fill={C.teal}/>
 <Text x={241} y={380} size={36} anchor="middle">原来的 Agent</Text><Text x={783} y={380} size={36} anchor="middle">其他 Agent</Text><Text x={241} y={434} size={29} anchor="middle" color={C.muted}>模型只在这里用</Text><Text x={783} y={434} size={29} anchor="middle" color={C.muted}>也能调用这批模型</Text>
 <Ray points={[[244,550],[780,550]]} p={p} color={C.teal}/><Token x={x} y={y} r={65}/><Reveal progress={p}><Text x={512} y={920} size={48} anchor="middle" color={C.teal}>模型来源不变，工作入口更自由</Text></Reveal></Canvas>;
};
const Core:React.FC<MotionEffectProps>=({local})=>{
 const p=tween(local,8,30);return <Canvas><Text x={56} y={180} size={43} color={C.muted}>它最核心的一件事</Text>
 <Text x={56} y={338} size={72} weight={750}>模型和订阅</Text><Text x={56} y={440} size={72} weight={750}>不必绑死在一个入口</Text>
 <Ray points={[[120,650],[904,650]]} p={p} color={C.teal}/><Box x={56} y={595} w={270} label="你的权益" color={C.gold}/><Box x={698} y={595} w={270} label="你的 Agent"/><g transform={`translate(512,650) rotate(${(1-p)*-40})`}><circle r={73} fill={C.teal}/><path d="M-35 0h70m-18-18 18 18-18 18" stroke="white" strokeWidth={6} fill="none"/></g>
 <Reveal progress={p}><Text x={512} y={899} size={56} anchor="middle" color={C.teal}>统一调度</Text></Reveal></Canvas>;
};
const Compare:React.FC<MotionEffectProps>=({local,scene})=>{
 const p=tween(local,cueFrame(scene,'体验',.35),35);return <Canvas title="同样是转接，体验差在管理" foot="个人使用体验，下一幕展示具体工具">
 <Text x={56} y={245} size={37} color={C.muted}>多处配置</Text><Ray points={[[100,330],[390,330],[390,480],[180,480],[180,620],[420,620],[420,750]]} color={C.red}/>
 {[330,480,620].map((y,i)=><g key={y}><circle cx={i===1?180:390} cy={y} r={24} fill={C.paper} stroke={C.red} strokeWidth={3}/><Text x={i===1?180:390} y={y+10} size={28} anchor="middle" color={C.red}>{i+1}</Text></g>)}
 <Text x={595} y={245} size={37} color={C.teal}>集中管理</Text><Ray points={[[740,330],[740,750]]} p={p}/><Reveal progress={p}><Box x={590} y={440} w={305} h={156} label="Magpie" sub="一个地方管理" color={C.teal} dark/><Check x={740} y={797}/></Reveal>
 <Text x={56} y={960} size={43}>少一些配置，工作更连贯</Text></Canvas>;
};
const Free:React.FC<MotionEffectProps>=({local,scene})=>{
 const p=tween(local,cueFrame(scene,'免费',.26),30);return <Canvas title="把分散的免费额度，用起来" foot="免费额度有活动期限和平台限制，以当日官方规则为准">
 <Text x={56} y={235} size={36} color={C.muted}>权益还在各个平台，入口统一到常用 Agent</Text>
 {['WorkBuddy','Qoder'].map((s,i)=><g key={s}><Box x={86+i*500} y={315} w={350} label={s} color={C.gold}/>{[0,1,2].map(j=><Token key={j} x={178+i*500+j*80} y={515} r={32} p={tween(local,i*6+j*5,20)}/>)}<Ray points={[[260+i*500,575],[260+i*500,645],[512,645],[512,735]]} p={p} color={C.gold}/></g>)}
 <Reveal progress={p}><Box x={230} y={735} w={564} h={150} label="Magpie" sub="让已有免费额度更好用" color={C.teal} dark/></Reveal></Canvas>;
};
const Outro:React.FC<MotionEffectProps>=({local})=>{
 const p=tween(local,0,22);return <Canvas><Text x={56} y={190} size={48} color={C.muted}>我是财叔</Text><Text x={56} y={340} size={80} weight={750}>真能省 Token 的工具</Text><Reveal progress={p}><Text x={56} y={455} size={80} weight={750} color={C.teal}>继续给大家挖</Text></Reveal>
 <g transform="translate(512,718)"><circle r={130} fill={C.mint}/><path d="M-75 0H75M25-50 75 0 25 50" stroke={C.teal} strokeWidth={12} fill="none" strokeLinecap="round"/><Token x={-57} y={-80} r={42} p={p}/></g>
 <Text x={512} y={970} size={42} anchor="middle">我们下期见</Text></Canvas>;
};
export const magpieEffects={magpie_hook:Hook,magpie_hub:Hub,magpie_silo:Silo,magpie_insert:Insert,magpie_wiring:Wiring,magpie_discovery:Discovery,magpie_packet:Packet,magpie_passport:Passport,magpie_core:Core,magpie_compare:Compare,magpie_free:Free,magpie_outro:Outro};
