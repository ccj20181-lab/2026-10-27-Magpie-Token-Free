import React,{createContext,useContext,useId,type ReactNode} from 'react';
import {color as C,fontFamily,type as T,stage,material} from './tokens';
import {clamp} from './timing';

export const Text=({x,y,children,size=T.body,color=C.ink,anchor='start',weight=T.weight}: {
  x:number;y:number;children:ReactNode;size?:number;color?:string;anchor?:'start'|'middle'|'end';weight?:number;
})=><text x={x} y={y} fill={color} fontFamily={fontFamily} fontSize={size} fontWeight={weight}
  textAnchor={anchor} style={{fontVariantNumeric:'tabular-nums',letterSpacing:T.tracking}}>{children}</text>;

export const Stroke=({d,progress=1,color=C.line,width=2}: {d:string;progress?:number;color?:string;width?:number})=>
  <path d={d} fill="none" stroke={color} strokeWidth={width} strokeLinecap="round" strokeLinejoin="round"
    pathLength={1} strokeDasharray={1} strokeDashoffset={1-clamp(progress)}/>;
export const Reveal=({progress,children,x=0,y=24}: {progress:number;children:ReactNode;x?:number;y?:number})=>{
  const p=clamp(progress);return <g opacity={p} transform={`translate(${(1-p)*x},${(1-p)*y})`}>{children}</g>;
};
export const Check=({x,y,progress=1,color=C.teal}: {x:number;y:number;progress?:number;color?:string})=>
  <Stroke d={`M${x-13} ${y}l9 10 21 -25`} progress={progress} color={color} width={4}/>;

const DefsContext=createContext<string|null>(null);
/** Fixed content area. The brand/header/captions are owned by DirectorComposition. */
export const Canvas=({title,foot,children}: {title?:string;foot?:string;children:ReactNode})=>{
  const id='caishu-'+useId().replace(/:/g,'');
  return <div style={{position:'absolute',left:stage.left,top:stage.top,width:stage.width,height:stage.height,
    boxShadow:material.shadow,background:C.paper}}>
    <svg width={stage.width} height={stage.height} viewBox="0 0 1024 1100" style={{fontFamily}}>
      <defs>
        <linearGradient id={id+'-paper'} x1="0" y1="0" x2="1" y2="1"><stop stopColor="white"/><stop offset="1" stopColor={material.paperShade}/></linearGradient>
        <linearGradient id={id+'-metal'} x1="0" y1="0" x2="1" y2="1">{material.metal.map((c,i)=><stop key={c} offset={[0,.46,.52,1][i]} stopColor={c}/>)}</linearGradient>
        <pattern id={id+'-grid'} width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke={C.line} strokeWidth=".6"/></pattern>
        <filter id={id+'-shadow'} x="-25%" y="-25%" width="160%" height="180%"><feDropShadow dx="0" dy="9" stdDeviation="9" floodColor={C.ink} floodOpacity=".10"/></filter>
      </defs>
      <rect width="1024" height="1100" fill={C.paper}/>
      {title&&<><path d="M56 36H84" stroke={C.teal} strokeWidth="4"/><Text x={56} y={112} size={T.title} weight={T.titleWeight}>{title}</Text></>}
      <DefsContext.Provider value={id}>{children}</DefsContext.Provider>
      {foot&&<><Stroke d="M56 1014H968"/><Text x={56} y={1060} size={T.note} color={C.muted} weight={500}>{foot}</Text></>}
    </svg>
  </div>;
};
export function useMaterial() {
  const id=useContext(DefsContext);
  if(!id)throw new Error('Material objects must be inside the Caishu Canvas');
  return {paper:`url(#${id}-paper)`,metal:`url(#${id}-metal)`,grid:`url(#${id}-grid)`,shadow:`url(#${id}-shadow)`};
}

/** Use only when a document is the subject. No built-in sample chart masquerades as real data. */
export const Paper=({x=0,y=0,width=300,height=350,page,children}: {
  x?:number;y?:number;width?:number;height?:number;page?:string;children?:ReactNode;
})=>{
  const m=useMaterial();return <g transform={`translate(${x},${y})`}>
    <rect width={width} height={height} rx="4" fill={m.paper} stroke={C.line} strokeWidth="2" filter={m.shadow}/>
    <rect x={width*.09} y={height*.1} width={width*.1} height={height*.035} fill={C.teal}/>
    <Stroke d={`M${width*.09} ${height*.22}H${width*.74}`} color={C.ink} width={Math.max(2,width*.015)}/>
    <Stroke d={`M${width*.09} ${height*.29}H${width*.58}`} width={Math.max(2,width*.009)}/>
    {children}
    {page&&<Text x={width*.9} y={height*.94} size={width*.085} anchor="end" color={C.muted} weight={500}>{page}</Text>}
  </g>;
};
