"""Validate source-coordinate emphasis boxes; leave the original media untouched."""
import math

def validate_source_highlights(asset):
    boxes=asset.get('highlights',[])
    if not isinstance(boxes,list):raise ValueError('highlights must be a list')
    crop=asset.get('crop') or [0,0,asset.get('width',0),asset.get('height',0)]
    cx,cy,cw,ch=crop
    for box in boxes:
        r=box.get('rect') if isinstance(box,dict) else None
        if not isinstance(r,list) or len(r)!=4 or not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in r):
            raise ValueError('highlight rect requires four finite source-pixel coordinates')
        x,y,w,h=r
        if w<=0 or h<=0 or x<cx or y<cy or x+w>cx+cw or y+h>cy+ch:
            raise ValueError('highlight must fit within the displayed source crop')
        stroke=box.get('strokeWidth',5)
        if not isinstance(stroke,(int,float)) or not math.isfinite(stroke) or not 1<=stroke<=12:raise ValueError('highlight strokeWidth must be 1..12 canvas pixels')
    return boxes
