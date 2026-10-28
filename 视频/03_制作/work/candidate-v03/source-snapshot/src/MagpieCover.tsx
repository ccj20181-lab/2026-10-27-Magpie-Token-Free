import React from 'react';
import {AbsoluteFill,Img,staticFile} from 'remotion';
import {AiCoachDemoData} from './types';
const ink='#153548',teal='#087E78';
export const MagpieCover:React.FC<{data:AiCoachDemoData}>=({data})=><AbsoluteFill style={{background:'#032442',fontFamily:'"Avenir Next", "PingFang SC", sans-serif'}}>
 <div style={{position:'absolute',top:252,left:64,display:'flex',alignItems:'center',gap:20}}><div style={{background:'#FFD84D',color:'#032442',borderRadius:45,padding:'22px 28px',fontSize:34,fontWeight:800}}>每天一条AI干货</div><div style={{background:'#FF4B3F',color:'white',borderRadius:60,padding:17,fontSize:28,fontWeight:800}}>#4</div></div>
 <div style={{position:'absolute',right:84,top:260,width:236,height:88,background:'white',padding:'4px 6px'}}><Img src={staticFile(data.meta.cornerLogoPath!)} style={{width:'100%',height:'100%',objectFit:'contain'}}/></div>
 <div style={{position:'absolute',left:28,top:470,width:1024,height:1100,background:'#FCFDFB',boxShadow:'0 18px 36px rgba(15,40,53,.09)'}}>
 <svg width={1024} height={1100} viewBox="0 0 1024 1100">
 <defs><linearGradient id="cg" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#F8EFCE"/><stop offset=".5" stopColor="#C9A15C"/><stop offset=".56" stopColor="#F0DBAB"/><stop offset="1" stopColor="#AE8137"/></linearGradient><filter id="cs"><feDropShadow dx="0" dy="12" stdDeviation="12" floodColor={ink} floodOpacity=".12"/></filter></defs>
 <path d="M56 54H94" stroke={teal} strokeWidth={5}/><text x={56} y={133} fontSize={44} fontWeight={600} fill={ink}>真神器 · Magpie</text>
 <text x={48} y={328} fontSize={151} fontWeight={800} fill={ink}>这次真的</text><text x={43} y={521} fontSize={166} fontWeight={800} fill={teal}>Token自由</text>
 <path d="M110 730H914" stroke="#D8E2E4" strokeWidth={5}/>
 <g filter="url(#cs)"><rect x={56} y={653} width={294} height={152} rx={4} fill="#F8F0DF" stroke="#DAC7A4" strokeWidth={2}/><text x={203} y={714} textAnchor="middle" fontSize={38} fill={ink} fontWeight={700}>免费模型</text><text x={203} y={764} textAnchor="middle" fontSize={29} fill="#6D7F89">WorkBuddy · Qoder</text>
 <rect x={674} y={653} width={294} height={152} rx={4} fill="#E5F2ED" stroke="#B9D4CA" strokeWidth={2}/><text x={821} y={714} textAnchor="middle" fontSize={38} fill={ink} fontWeight={700}>常用 Agent</text><text x={821} y={764} textAnchor="middle" fontSize={29} fill="#6D7F89">Harness · Codex</text>
 <circle cx={512} cy={729} r={95} fill="url(#cg)" stroke="#AE8137" strokeWidth={3}/><circle cx={512} cy={729} r={83} fill="none" stroke="#F8EBC4" strokeWidth={2}/><text x={512} y={757} textAnchor="middle" fontSize={83} fill={ink} fontWeight={700}>T</text></g>
 <text x={512} y={946} textAnchor="middle" fontSize={48} fill={ink} fontWeight={700}>一个总控台，打通模型和订阅</text>
 <path d="M56 1014H968" stroke="#D8E2E4" strokeWidth={2}/><text x={56} y={1060} fontSize={27} fill="#6D7F89">第 4 期 / 财叔 AI Lab</text>
 </svg></div>
 <div style={{position:'absolute',left:48,right:48,bottom:126,textAlign:'center',color:'white',fontSize:42,fontWeight:700}}>把好用的模型，接到你顺手的 Agent</div>
 </AbsoluteFill>;
