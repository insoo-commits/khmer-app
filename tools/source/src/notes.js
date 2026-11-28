;/* ※ notes under example sentences: short meanings of the other words in the sentence */
const NDICT=__NDICT__,NRD=__NRD__,NFREQ=__NFREQ__,NSTOP=new Set(__NSTOP__);
const NMAX=(()=>{let m=0;for(const k in NDICT)if(k.length>m)m=k.length;for(const k of NSTOP)if(k.length>m)m=k.length;return m})();
function notesOf(lo,w){const hw=(w||"").replace(/…/g,"").trim();const seen=new Set(),out=[];
  const isW=t=>NDICT[t]!==undefined||NSTOP.has(t);const bad=/^[ា-៓៝]/;
  /* split each Khmer run into known words: fewest uncovered letters, then fewest pieces */
  for(const run of lo.match(/[ក-៓៝]+/g)||[]){const n=run.length,dp=[[0,0,-1,0]];
    for(let e=1;e<=n;e++){let best=[dp[e-1][0]+1,dp[e-1][1]+1,e-1,0];
      for(let b=Math.max(0,e-NMAX);b<e-1;b++){const t=run.slice(b,e);if(!isW(t)||bad.test(t)||(e<n&&bad.test(run[e]))||(b>0&&run[b-1]==="្"))continue;
        const c=[dp[b][0],dp[b][1]+1,b,1];if(c[0]<best[0]||(c[0]===best[0]&&c[1]<best[1]))best=c}
      dp[e]=best}
    const toks=[];for(let e=n;e>0;e=dp[e][2])if(dp[e][3])toks.unshift(run.slice(dp[e][2],e));
    for(const t of toks)if(NDICT[t]!==undefined&&t.length>=2&&!seen.has(t)&&!(hw&&(hw.includes(t)||t.includes(hw)))){seen.add(t);out.push(t)}}
  const wd=t=>t.length*0.62+[...((NRD[t]?" "+NRD[t]:"")+"("+NDICT[t]+")")].reduce((a,c)=>a+(/[가-힣]/.test(c)?1:0.55),0)+1.6;
  const cap=(typeof isBig==="function"&&isBig())?140:60;let tot=out.reduce((a,t)=>a+wd(t),0);
  if(tot>cap){const drop=out.slice().sort((a,b)=>(NFREQ[b]||0)-(NFREQ[a]||0)||a.length-b.length);const gone=new Set();for(const t of drop){if(tot<=cap||out.length-gone.size<=3)break;gone.add(t);tot-=wd(t)}return out.filter(t=>!gone.has(t))}return out}
