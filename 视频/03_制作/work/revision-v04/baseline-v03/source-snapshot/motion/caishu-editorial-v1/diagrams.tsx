import React,{type ReactNode} from 'react';
import {color as C} from './tokens';
import {Text,Stroke} from './primitives';
import {clamp,lerp,pointOnPolyline} from './timing';

export const UnitGrid=({x,y,total=100,columns=20,from,to,progress,width=870,height=330}: {
  x:number;y:number;total?:number;columns?:number;from:number;to:number;progress:number;width?:number;height?:number;
})=>{
  if(!Number.isInteger(total)||total<1||columns<1||!Number.isInteger(columns)||
    ![from,to].every(n=>Number.isInteger(n)&&n>=0&&n<=total))throw new Error('UnitGrid requires valid integer counts');
  const rows=Math.ceil(total/columns),cw=width/columns,ch=height/rows;
  return <g>{Array.from({length:total},(_,i)=>{
    const a=lerp(i<from?1:0,i<to?1:0,clamp(progress));
    return <g key={i}><rect x={x+i%columns*cw} y={y+Math.floor(i/columns)*ch} width={cw*.7} height={ch*.72} rx="3" fill={C.line} opacity=".3"/>
      <rect x={x+i%columns*cw} y={y+Math.floor(i/columns)*ch} width={cw*.7} height={ch*.72} rx="3" fill={C.teal} opacity={a}/></g>;
  })}</g>;
};

export const WeightRing=({cx,cy,r=214,width=74,segments,progress=1}: {
  cx:number;cy:number;r?:number;width?:number;segments:{label:string;value:number;color:string;progress?:number}[];progress?:number;
})=>{
  if(segments.some(s=>!Number.isFinite(s.value)||s.value<=0)||Math.abs(segments.reduce((n,s)=>n+s.value,0)-100)>.00001)
    throw new Error('WeightRing percentages must be positive and sum to 100');
  let offset=0;return <g><circle cx={cx} cy={cy} r={r} fill="none" stroke={C.light} strokeWidth={width}/>
    {segments.map(s=>{
      const start=offset;offset+=s.value;const n=s.value*clamp(s.progress??progress);
      if(n<=0)return null;
      if(n>=100-1e-9)return <circle key={s.label} cx={cx} cy={cy} r={r} fill="none" stroke={s.color} strokeWidth={width}/>;
      const point=(a:number)=>[cx+r*Math.cos((a-90)*Math.PI/180),cy+r*Math.sin((a-90)*Math.PI/180)];
      const a=point(start*3.6),b=point((start+n)*3.6);
      return <path key={s.label} d={`M${a[0]} ${a[1]} A${r} ${r} 0 ${n>50?1:0} 1 ${b[0]} ${b[1]}`}
        fill="none" stroke={s.color} strokeWidth={width} strokeLinecap="butt"/>;
    })}
  </g>;
};

export const FlowPath=({points,progress,color=C.teal,marker}: {
  points:readonly (readonly [number,number])[];progress:number;color?:string;marker?:(x:number,y:number)=>ReactNode;
})=>{
  const d=points.map((p,i)=>`${i?'L':'M'}${p[0]} ${p[1]}`).join(' '),[x,y]=pointOnPolyline(points,progress);
  return <g><Stroke d={d} color={C.line} width={7}/><Stroke d={d} color={color} width={5} progress={progress}/>
    {marker?marker(x,y):<circle cx={x} cy={y} r="8" fill={color} stroke="white" strokeWidth="3"/>}</g>;
};

/** One stable page. Pagination is an editorial decision in the episode, never automatic scrolling. */
export const DataTable=({x=44,y=216,width=936,columns,rows,rowHeight=116,highlight=[]}: {
  x?:number;y?:number;width?:number;columns:{label:string;share:number;align?:'start'|'end'}[];
  rows:({text:string;detail?:string}[])[];rowHeight?:number;highlight?:number[];
})=>{
  const total=columns.reduce((n,c)=>n+c.share,0);
  if(total<=0||columns.some(c=>c.share<=0)||rows.some(r=>r.length!==columns.length))throw new Error('Invalid table geometry');
  if(y+68+rows.length*rowHeight>1004)throw new Error('Table exceeds reading area; paginate instead of shrinking text');
  const bounds=columns.map((c,i)=>({left:x+width*columns.slice(0,i).reduce((n,a)=>n+a.share,0)/total,width:width*c.share/total}));
  return <g><rect x={x} y={y} width={width} height="59" fill={C.ink}/>
    {columns.map((c,i)=><Text key={i} x={c.align==='end'?bounds[i].left+bounds[i].width-22:bounds[i].left+22} y={y+39}
      size={31} color="white" anchor={c.align==='end'?'end':'start'}>{c.label}</Text>)}
    {rows.map((row,i)=>{const top=y+68+i*rowHeight,active=highlight.includes(i);return <g key={i}>
      <rect x={x} y={top} width={width} height={rowHeight-5} fill={active?C.mint:i%2===0?C.light:'white'}/>
      {active&&<rect x={x} y={top} width="4" height={rowHeight-5} fill={C.teal}/>}
      {row.map((cell,j)=>{const right=columns[j].align==='end',xx=right?bounds[j].left+bounds[j].width-22:bounds[j].left+22;
        return <g key={j}><Text x={xx} y={top+rowHeight/2+(cell.detail?-13:10)} size={j?43:36} color={active?C.teal:C.ink} anchor={right?'end':'start'}>{cell.text}</Text>
          {cell.detail&&<Text x={xx} y={top+rowHeight/2+28} size={30} color={C.muted} weight={500} anchor={right?'end':'start'}>{cell.detail}</Text>}</g>;
      })}
    </g>;})}
  </g>;
};
