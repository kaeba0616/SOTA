# sota/scrape/fiber_js.py
"""Browser-side extraction scripts (validated against sephiria.wiki v0.12.0, 2026-06-01).

The wiki exposes no API and the data is not in static JS chunks; it lives in
in-memory React state. We start from a rendered palette button and walk up the
fiber tree to the array prop that holds the full data objects.
"""

ARTIFACTS = r"""
() => {
  const btns=[...document.querySelectorAll('button,[role="button"]')];
  const btn=btns.find(b=>/items\s/.test(b.getAttribute('aria-label')||'')||/강화 포션|돛대 모형/.test(b.textContent||''));
  if(!btn) return null;
  const key=Object.keys(btn).find(k=>k.startsWith('__reactFiber$'));
  let f=btn[key],depth=0,found=null;
  while(f&&depth<90){
    for(const bag of [f.memoizedProps,f.memoizedState]){
      if(bag&&typeof bag==='object') for(const k of Object.keys(bag)){
        try{const v=bag[k];if(Array.isArray(v)&&v.length>100&&v[0]&&v[0].label_eng){found=v;break;}}catch(e){}
      }
      if(found)break;
    }
    if(found)break; f=f.return; depth++;
  }
  return found;
}
"""

SLABS = r"""
() => {
  const btns=[...document.querySelectorAll('button,[role="button"]')];
  const btn=btns.find(b=>/기사도|건조|근사/.test(b.textContent||''));
  if(!btn) return null;
  const key=Object.keys(btn).find(k=>k.startsWith('__reactFiber$'));
  let f=btn[key],depth=0,found=null;
  while(f&&depth<90){
    for(const bag of [f.memoizedProps,f.memoizedState]){
      if(bag&&typeof bag==='object') for(const k of Object.keys(bag)){
        try{const v=bag[k];
          if(Array.isArray(v)&&v.length>=40&&v[0]&&v[0].props&&v[0].props.item&&v[0].props.item.type==='slabs'){found=v;break;}
        }catch(e){}
      }
      if(found)break;
    }
    if(found)break; f=f.return; depth++;
  }
  return found ? found.map(c=>({id:c.props.item.id, label:c.props.item.label})) : null;
}
"""

COMBOS = r"""
() => {
  let nf=(self.__next_f||[]).map(x=>Array.isArray(x)?x[1]:x).filter(s=>typeof s==='string').join('');
  const s=nf.split('\\"').join('"');
  const out=[];
  const re=/\{"key":"([a-z_]+)","label":"([^"]+)","image":"([^"]*)","minCount":(\d+),"maxCount":(\d+),"effects":(\[[^\]]*\])\}/g;
  let m;
  while((m=re.exec(s))){
    let effects=[]; try{effects=JSON.parse(m[6]);}catch(e){}
    out.push({key:m[1],label:m[2],image:m[3],minCount:+m[4],maxCount:+m[5],effects});
  }
  return out;
}
"""
