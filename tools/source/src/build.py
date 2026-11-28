"""Build the Khmer beginner PWA from the Lao app's code (src/base = copy of insoo-commits/lao-app v2.50) + content modules c*.py.
Usage: python3 build.py <out_dir> [version]"""
import json,sys,os,glob,importlib.util,base64,re,shutil,datetime
here=os.path.dirname(os.path.abspath(__file__)); out=sys.argv[1]; VER=sys.argv[2] if len(sys.argv)>2 else "0.1"
DATE=datetime.date.today().isoformat()
subs=[];B={};BLAB={};EXTRA={};NAMES=[]
class TM: pass
def load_txt(f):
    """compact text format, one sub per file: '# subid | name', '@ id | title | khmer label | intro', 'w km | hint | reading | meaning' (hint '=' = same as meaning),
    'e km | reading | ko' (examples of the last w), 'tp text', 'pr a|r|k || b|r|k', 'dl who | km | r | ko', 'sm km | r | ko', 'qz q | a', 'x km | reading | meaning' (note word)"""
    m=TM();m.BUNDLES=[];m.EXTRA={};m.NAMES=[];cur=None
    for n,line in enumerate(open(f,encoding='utf-8'),1):
        line=line.strip()
        if not line or line.startswith('//'): continue
        tag,_,rest=line.partition(' ');P=[x.strip() for x in rest.split(' | ')]
        try:
            if tag=='#': m.SUB={"id":P[0],"name":P[1]}
            elif tag=='@': cur={"id":P[0],"t":P[1],"lab":[P[1],P[2]],"i":P[3],"w":[],"tp":[],"pr":[],"dl":[],"qz":[]};m.BUNDLES.append(cur)
            elif tag=='w': assert len(P)==4;cur["w"].append([P[0],P[3] if P[1]=='=' else P[1],P[2],P[3],[]])
            elif tag=='e': assert len(P)==3;cur["w"][-1][4].append(P)
            elif tag=='tp': cur["tp"].append('• '+rest.strip())
            elif tag=='pr': a,b2=[[y.strip() for y in x.split('|')] for x in rest.split(' || ')];assert len(a)==3 and len(b2)==3;cur["pr"].append([a,b2])
            elif tag=='dl': assert len(P)==4;cur["dl"].append(P)
            elif tag=='sm': assert len(P)==3;cur["sm"]=P
            elif tag=='qz': assert len(P)==2;cur["qz"].append(P)
            elif tag=='x': assert len(P)==3;m.EXTRA[P[0]]=(P[1],P[2])
            else: raise ValueError(tag)
        except Exception as ex: raise SystemExit(f'{f}:{n}: {line} ({ex!r})')
    for b in m.BUNDLES:
        for w in b["w"]: assert len(w[4])>=2,(b["id"],w[0])
    return m
for f in sorted(glob.glob(here+'/c[0-9]*.py')+glob.glob(here+'/c[0-9]*.txt'),key=os.path.basename):
    if f.endswith('.txt'): m=load_txt(f)
    else: sp=importlib.util.spec_from_file_location('m',f);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
    ex=[x for x in subs if x["id"]==m.SUB["id"]]
    if ex: ex[0]["b"]+=[b["id"] for b in m.BUNDLES]
    else: subs.append({"id":m.SUB["id"],"name":m.SUB["name"],"b":[b["id"] for b in m.BUNDLES]})
    for b in m.BUNDLES:
        B[b["id"]]={"t":b["t"],"h":" · ".join(w[0] for w in b["w"]),"i":b["i"],"w":b["w"],"tp":b.get("tp",[]),"nx":b.get("nx",[]),"pr":b.get("pr",[]),"dl":b.get("dl",[]),"sm":b.get("sm",["","",""]),"qz":b.get("qz",[])}
        BLAB[b["id"]]=b["lab"]
    EXTRA.update(m.EXTRA);NAMES+=m.NAMES
sp=importlib.util.spec_from_file_location('titles',here+'/titles.py');TT=importlib.util.module_from_spec(sp);sp.loader.exec_module(TT)
for k,v in TT.BT.items(): B[k]["t"]=v;BLAB[k][0]=v
for x in subs: x["name"]=TT.SUBN.get(x["id"],x["name"])
assert all(k in [x["id"] for x in subs] for k in TT.SUBN)
for x in subs: x["b"].sort();x["name"]=x["name"].replace(" ","")  # RYU 2026-11-19: menu labels without spaces
# --- readings follow RYU's textbook (2026-11-18): final stop written ㅅ (엇, 쩟, 싸앗), except 받
def fin(t):
    o=[]
    for ch in t:
        c=ord(ch)-0xAC00
        if 0<=c<11172 and c%28==7 and ch!='받': ch=chr(0xAC00+c-7+19)
        o.append(ch)
    return ''.join(o)
OLD=set()
def R(t):
    for tok in re.findall('[가-힣]+',t):
        if fin(tok)!=tok: OLD.add(tok)
    return fin(t)
for b in B.values():
    for w in b["w"]:
        w[2]=R(w[2])
        for e in w[4]: e[1]=R(e[1])
    for pr in b["pr"]:
        for x in pr: x[1]=R(x[1])
    for x in b["dl"]: x[2]=R(x[2])
    if b["sm"][0]: b["sm"][1]=R(b["sm"][1])
EXTRA={k:(R(r),mn) for k,(r,mn) in EXTRA.items()}
free=lambda t:re.sub('(?<![가-힣])[가-힣]+(?![가-힣])',lambda m:fin(m.group()) if m.group() in OLD else m.group(),t)
for b in B.values():
    b["i"]=free(b["i"]);b["tp"]=[free(t) for t in b["tp"]];b["qz"]=[[free(q),free(a)] for q,a in b["qz"]]
    for w in b["w"]: w[1]=free(w[1])
# --- front text (intro + tips): Korean reading in parentheses after every Khmer phrase (RYU 2026-11-18)
PM={}
nk=lambda t:re.sub('[?…!,.]','',t).strip()
for b in B.values():
    for w in b["w"]:
        PM[nk(w[0])]=w[2]
        for e in w[4]: PM[nk(e[0])]=e[1]
    for pr in b["pr"]:
        for x in pr: PM[nk(x[0])]=x[1]
    for x in b["dl"]: PM[nk(x[1])]=x[2]
WD={k:r for k,(r,mn) in EXTRA.items()}
NOND={"ខ្ញុំញ៉ាំបាយ","ផ្ទះធំ","សៀវភៅខ្ញុំ","សៀវភៅនេះ","ផ្ទះនេះធំ","សៀវភៅពីរ"}  # 문법 pattern sentences, not words
for bid,b in B.items():
    for w in b["w"]:
        if bid[:4] in ("2-01","2-02") or "…" in w[0] or w[0] in NOND: continue
        if " " not in nk(w[0]):
            if bid[0] in "23": WD.setdefault(nk(w[0]),nk(w[2]))
            else: WD[nk(w[0])]=nk(w[2])
BADK=re.compile('^[ា-៓៝]')
def segrd(run):
    n=len(run);dp=[None]*(n+1);dp[0]=(0,[])
    for e in range(1,n+1):
        for st in range(max(0,e-24),e):
            t=run[st:e]
            if dp[st] is None or t not in WD or BADK.match(t) or (e<n and BADK.match(run[e])) or (st>0 and run[st-1]=='្'): continue
            c=(dp[st][0]+1,dp[st][1]+[WD[t]])
            if dp[e] is None or c[0]<dp[e][0]: dp[e]=c
    return ' '.join(dp[n][1]) if dp[n] else None
def rdof(ph):
    ph=nk(ph)
    if ph in PM: return re.sub('[?,.…]','',PM[ph]).strip()
    out=[]
    for piece in ph.split():
        if piece in PM: out.append(re.sub('[?,.…]','',PM[piece]).strip());continue
        dbl=piece.endswith('ៗ');base=piece.rstrip('ៗ')
        if not base: return None
        r=PM.get(base) or segrd(base)
        if r is None: return None
        if dbl: ws=r.split(' ');ws[-1]=ws[-1]*2;r=' '.join(ws)
        out.append(r)
    return ' '.join(out)
MISS=set()
def addrd(t):
    def f(m):
        run,q,par=m.group(1),m.group(2) or '',m.group(4)
        if not re.search('[ក-អ]',run): return m.group(0)
        r=rdof(run)
        if r is None: MISS.add(run);return m.group(0)
        if par is None: return f'{run}({r}){q}'
        sq=lambda x:re.sub(r'[\s,?]','',x)
        if sq(par)==sq(r) or sq(par).startswith(sq(r)): return m.group(0)
        return f'{run}{q}({r} · {par})'
    return re.sub(r'([ក-៿]+(?: [ក-៿]+)*)(\?)?(\(([^()]*)\))?',f,t)
for b in B.values():
    b["i"]=addrd(b["i"]);b["tp"]=[addrd(t) for t in b["tp"]]
if MISS: print('NO READING for',sorted(MISS))
def mark(km,ko):
    for k,t in (("លោកគ្រូ","선생님(남)"),("អ្នកគ្រូ","선생님(여)")):
        if k in km and "선생님" in ko and "선생님(" not in ko: ko=ko.replace("선생님",t,1)
    return ko
for b in B.values():
    for w in b["w"]:
        for e in w[4]: e[2]=mark(e[0],e[2])
    for pr in b["pr"]:
        for x in pr: x[2]=mark(x[0],x[2])
    for x in b["dl"]: x[3]=mark(x[1],x[3])
    if b["sm"][0]: b["sm"][2]=mark(b["sm"][0],b["sm"][2])
    alld=" ".join(x[1] for x in b["dl"])
    for x in b["dl"]:
        if x[0]=="선생님": x[0]="선생님(남)" if "លោកគ្រូ" in alld else "선생님(여)" if "អ្នកគ្រូ" in alld else x[0]
PMETA=[("P5","기초회화","인사·학교·식당·시장 등 장면별 단어와 문장"),("P6","문자학습","크메르 글자: 자음 두 줄, 모음, 받침과 기호"),("P7","문장규칙","말의 순서·부정·묻기·때·세는 말 등 문장을 만드는 틀"),("P4","짝말비교","크다·작다처럼 짝으로 외우는 반대말"),("P1","발음구별","크메르 글자의 소리와, 한글로 쓰면 같아서 헷갈리는 소리")]
DATA={"P":[{"id":p,"ko":k,"desc":d,"subs":[x for x in subs if x["id"].startswith(p)]} for p,k,d in PMETA],"B":B}
DATA["P"]=[p for p in DATA["P"] if p["subs"]]
# note dictionary: headwords (first meaning) + extra words
ND={};NR={}
for bid,b in B.items():
    for w in b["w"]:
        if bid[:4] in ("2-01","2-02") or (bid[0] in "23" and ("…" in w[0] or w[0] in NOND)): continue
        k=w[0].replace("…","").replace("?","").strip()
        if " " in k: continue
        if bid[0] in "23" and k in ND: continue
        ND[k]=re.split(r"[;(]",w[3])[0].strip();NR[k]=w[2]
for k,(r,mn) in EXTRA.items(): ND[k]=mn;NR[k]=r
alltxt=" ".join(e[0] for b in B.values() for w in b["w"] for e in w[4])
NF={k:alltxt.count(k) for k in ND}
J=lambda o:json.dumps(o,ensure_ascii=False,separators=(",",":"))
L=open(here+'/base/app.js',encoding='utf-8').read().split('\n')
ln=lambda a,b:L[a-1:b]   # 1-based inclusive
notes=open(here+'/notes.js',encoding='utf-8').read().replace('__NDICT__',J(ND)).replace('__NRD__',J(NR)).replace('__NFREQ__',J(NF)).replace('__NSTOP__',J(sorted(set(NAMES))))
repjs=open(here+'/rep.js',encoding='utf-8').read().rstrip('\n')
code=["const DATA=JSON.parse("+json.dumps(J(DATA),ensure_ascii=False)+");",notes]
code+=ln(31,35)
# v2.0: 글자·문법 came in as tabs 2 and 3, so 짝말 ids moved 2-xx → 4-xx and 말소리 3-xx → 5-xx (saved selection follows once)
code+=['let known=store.get("lao-known",{});const saved=store.get("lao-sel",{});if(store.get("lao-idv",0)<2){const mp={P4:["2-","4-"],P1:["3-","5-"]};if(saved.bun)for(const k in saved.bun){const m=mp[k.slice(0,2)],v=String(saved.bun[k]);if(m&&v.indexOf(m[0])===0)saved.bun[k]=m[1]+v.slice(2)}store.set("lao-idv",2)}']
code+=ln(47,83)+[repjs]+ln(90,212)
code+=["const BLAB="+J(BLAB)+";"]
code+=ln(214,274)+["const nmean=t=>NDICT[t];"]+ln(328,530)
s="\n".join(code)+"\n"
def rp(a,b,n=None):
    global s
    c=s.count(a)
    assert c>0 and (n is None or c==n),(a,c)
    s=s.replace(a,b)
# v2.9 RYU 2026-11-21: Lao v2.79–v2.85: scroll only when the playing item leaves the middle 25–75%, speed 0.7–2.0 by 0.1, tighter 횟수·배속 lists
rp('function mark(id){document.querySelectorAll(".playing").forEach(e=>e.classList.remove("playing"));if(id){const el=document.getElementById(id);if(el){el.classList.add("playing");if(P.follow){const r=el.getBoundingClientRect();if(r.top<70||r.bottom>innerHeight-90)el.scrollIntoView({block:"center",behavior:"smooth"})}}}}','function mark(id){document.querySelectorAll(".playing").forEach(e=>e.classList.remove("playing"));if(id){const el=document.getElementById(id);if(el){el.classList.add("playing");if(P.follow){/* v2.53 RYU: keep the playing item at the vertical centre (above the player bar) */const r=el.getBoundingClientRect(),pl=document.getElementById("player"),ph=pl&&!pl.hidden?pl.getBoundingClientRect().height+16:0,H=innerHeight-ph,c=r.top+r.height/2,d=c-H/2;/* v2.79 RYU: move only when the item leaves the middle area (25%..75%) or is cut off */if(c<H*.25||c>H*.75||(r.top<0&&r.height<H)||(r.bottom>H&&r.height<H))window.scrollBy({top:d,behavior:"smooth"})}}}}',1)
# v2.14 RYU 2026-11-22: when the playing item leaves 25–75%, scroll it to about 25% from the top (not the middle)
rp('c=r.top+r.height/2,d=c-H/2;','c=r.top+r.height/2,d=c-H*.25;',1)
rp('let RATE=store.get("lao-rate",1);if(![0.8,1,1.2,1.5,2].includes(RATE))RATE=1;','let RATE=store.get("lao-rate",1);if(!(RATE>=0.7&&RATE<=2))RATE=1;RATE=Math.round(RATE*10)/10;',1)
rp("'.ddl button.ctr{justify-content:center","'.ddl button:not(.ctr){padding:.22em 1em;line-height:1.25}'+'.ddl button.ctr{justify-content:center",1)
# v2.6 RYU 2026-11-21: Lao app v2.75–v2.78: key badges, key info line, K = Korean voice on/off, short pause between repeats of one sentence, no Khmer-only review pass after word cards
rp('let REP=store.get("lao-rep",2);','let REP=store.get("lao-rep",2);let SAYKO=store.get("lao-sayko",true)!==false;',1)
rp('<span class="nbl">← 이전 묶음</span>','<span class="nbl"><kbd class="kc">&lt;</kbd>← 이전 묶음</span>',1)
rp('<span class="nbl">다음 묶음 →</span>','<span class="nbl">다음 묶음 →<kbd class="kc">&gt;</kbd></span>',1)
rp('if(!single&&items.every(it=>it&&/^cd-/.test(it.id||""))){const r0=q.length;items.forEach((it,ri)=>{const n=q.length;q.push({...it,rv:1,rv0:r0,ri:ri,rn:items.length,rvl:ri===items.length-1,gi:groups.length+ri,gs:n,ge:n,rs:n,kg:false})})}','',1)
rp('setTimeout(()=>{if(AUD){blobUrl("_gap450")','setTimeout(()=>{if(AUD){blobUrl("_gap150").catch(()=>{});blobUrl("_gap450")',1)
rp('const it=P.queue[P.i];cardSync(it);mark(it.id);showPlayer();','const it=P.queue[P.i];if(it.ko&&!SAYKO){advQ();nextPlay(tok);return}cardSync(it);mark(it.id);showPlayer();',1)
rp('advQ();gapThen(tok,P.i>=P.queue.length||(P.queue[P.i].rv&&P.queue[P.i].rv0===P.i)?900:450)','advQ();gapThen(tok,gapMs(it))',1)
rp('advQ();setTimeout(()=>nextPlay(tok),P.i>=P.queue.length||(P.queue[P.i].rv&&P.queue[P.i].rv0===P.i)?900:450)','advQ();setTimeout(()=>nextPlay(tok),gapMs(it))',1)
rp('function gapThen(tok,ms){','function gapMs(it){const q=P.queue;if(P.i>=q.length||(q[P.i].rv&&q[P.i].rv0===P.i))return 900;let j=P.i;if(!SAYKO)while(j<q.length&&q[j].ko)j++;const n=q[j];return n&&!it.ko&&!n.ko&&n.text===it.text?150:450}\nfunction setSayKo(v){SAYKO=!!v;store.set("lao-sayko",SAYKO);const c=document.getElementById("koChk");if(c)c.checked=SAYKO}\n{const c=document.getElementById("koChk");if(c){c.checked=SAYKO;c.addEventListener("change",()=>{setSayKo(c.checked);try{c.blur()}catch(e){}})}}\nfunction gapThen(tok,ms){',1)
rp('${RPT}<span>연속 재생</span></button><button class="speak all" data-playbundle="${b}">${RPT}<span>묶음 재생</span></button>','${RPT}<span>연속 재생</span><kbd class="kc">C</kbd></button><button class="speak all" data-playbundle="${b}">${RPT}<span>묶음 재생</span><kbd class="kc">G</kbd></button>',1)
rp('Promise.all([blobUrl("_gap450"),blobUrl("_gap900")]','Promise.all([blobUrl("_gap150"),blobUrl("_gap450"),blobUrl("_gap900")]',1)
# v2.5 RYU 2026-11-20: keyboard shortcuts (kbd.js = Lao app v2.74 handler)
rp('function stopPlay(){P.token++;','function stopPlay(){P.rel=0;P.token++;',1)
rp('const it=P.queue[P.i];if(!it){P.i++;return}if(P.i<it.ge){P.i++;return}','const it=P.queue[P.i];if(!it){P.i++;return}if(P.rel){P.rel=0;P.k=0;P.i=it.ge+1;return}if(P.i<it.ge){P.i++;return}',1)
s+=open(here+'/kbd.js',encoding='utf-8').read()
s+='\n'+open(here+'/swipe.js',encoding='utf-8').read()  # v2.21 RYU: phone swipe = next/previous bundle (Lao v3.23)
rp('</span><span class="hint">${hintHtml(hint)}</span></span><span class="bk"','</span><span class="rd frd">${esc(rd)}</span><span class="hint">${hintHtml(hint)}</span></span><span class="bk"',1)
# RYU 2026-11-19: tapping the repeat button that is playing stops it
rp('if(t.matches(".speak.all"))P._bk=btnKey(t);','if(t.matches(".speak.all")){const k=btnKey(t);if(k&&P.active&&P._bk===k){stopPlay();P._bk=null;syncBtn();return}P._bk=k}',1)
# v2.1 RYU 2026-11-20: 캄보디아 tab (P8) = info pages from khinfo.py, no words, no audio, not counted (same shape as Lao app v2.64)
sp=importlib.util.spec_from_file_location('khinfo',here+'/khinfo.py');KI=importlib.util.module_from_spec(sp);sp.loader.exec_module(KI)
CR=json.load(open(here+'/img/credits.json')) if os.path.exists(here+'/img/credits.json') else {}
FLAG=re.sub(r'^.*?<svg[^>]*>','<svg class="flag" viewBox="0 0 1000 640" role="img" aria-label="캄보디아 국기" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">',open(here+'/img/flag.svg',encoding='utf-8').read(),count=1,flags=re.S).replace('\n','')
def _ph(m):
    c=CR.get(m.group(1))
    return f'<figure class="ph"><img src="img/{m.group(1)}.jpg" width="{c["w"]}" height="{c["h"]}" loading="lazy" alt=""><figcaption>{m.group(2)}<small>사진: {c["a"]} · {c["lic"]} · Wikimedia Commons</small></figcaption></figure>' if c else ''
IB={};IL={}
for bid,(t,km,html) in KI.B.items():
    html=re.sub(r'@@PHOTO:([a-z0-9]+):(.*?)@@',_ph,html).replace('@@FLAG@@',FLAG).replace('<div class="top2"><div></div><div>','<div class="top1"><div>')
    IB[bid]=dict(t=t,h=km,i="",w=[],tp=[],nx=[],pr=[],dl=[],sm=None,qz=[],info=f'<h2>{t}</h2><div class="sub2 lo">{km}</div>'+html);IL[bid]=[t,km]
IP=dict(id='P8',ko='캄보디아',desc='캄보디아를 이해하기 위한 자료',subs=[dict(id=sid,name=nm.replace(' ',''),b=[k for k in KI.B if k.startswith('6-%02d-'%(n+1))]) for n,(sid,nm) in enumerate(KI.SUBS)])
sp=importlib.util.spec_from_file_location('khhelp',here+'/khhelp.py');KH=importlib.util.module_from_spec(sp);sp.loader.exec_module(KH)
INFOLINE='const HELPINFO='+J(dict(part=KH.PART,B=KH.B,blab=KH.BLAB))+';'+'const KHINFO='+J(dict(part=IP,B=IB,blab=IL))+';DATA.P.push(KHINFO.part);Object.assign(DATA.B,KHINFO.B);DATA.P.push(HELPINFO.part);Object.assign(DATA.B,HELPINFO.B);\n'
rp('const PARTEN={P1:"SOUND",P2:"ROOT",P3:"MEANING",P4:"PAIR",P5:"SCENE"};',INFOLINE+'const PARTEN={P1:"SOUND",P2:"ROOT",P3:"MEANING",P4:"PAIR",P5:"SCENE",P6:"LETTER",P7:"GRAMMAR",P8:"CAMBODIA",PH:"HELP"};',1)
rp('const L=PARTS.flatMap(p=>p.subs.flatMap(x=>x.b)),cur=S.bun[S.sub]||sb.b[0];','const L=PARTS.flatMap(p=>p.subs.flatMap(x=>x.b)).filter(x=>!B[x].info),cur=S.bun[S.sub]||sb.b[0];',1)
rp('const all=Object.values(B),nw=all.reduce','const all=Object.values(B).filter(b=>!b.info),nw=all.reduce',1)
rp('${cs.b.length}묶음 ${nwd.toLocaleString()}단어 ${nsb.toLocaleString()}문장`}','${cs.b.length}묶음`+(B[cs.b[0]].info?"":` ${nwd.toLocaleString()}단어 ${nsb.toLocaleString()}문장`)}',1)
rp('if(S.q.trim()){renderSearch();return}','if(S.q.trim()){renderSearch();return}\n  if(!BLAB["6-01-01"])Object.assign(BLAB,KHINFO.blab);if(!BLAB["7-01-01"])Object.assign(BLAB,HELPINFO.blab);{const ib=B[curBun()];if(ib&&ib.info){$("#controls").hidden=true;renderBand();$("#view").innerHTML=`<article class="info">${ib.info}</article>`+nextRow(curBun());snapLater();return}}\n  $("#controls").hidden=false;',1)
rp('<span class="w tn">${toneHtml(lo)}</span>','<span class="w">${esc(lo)}</span>',1)
rp('const TONE_IDS={has:()=>true};','const TONE_IDS={has:()=>false};',1)
rp('([຀-໿][຀-໿\\s◌]*)','([\\u1780-\\u17FF][\\u1780-\\u17FF\\s◌]*)',1)
rp('/^lo([-_]|$)/i','/^km([-_]|$)/i',1); rp('"lo-LA"','"km-KH"'); rp('Intl.Segmenter("lo"','Intl.Segmenter("km"',1)
rp('라오스어','크메르어'); rp('LAO Lang','KHMER Lang'); rp('lao-','khm-')
print('code lines still holding Lao letters (tone/swatch code, unused):',len([l for l in s.split(chr(10))[1:] if re.search('[\u0E80-\u0EFF]',l)]))
os.makedirs(out+'/audio',exist_ok=True)
open(out+'/app.js','w',encoding='utf-8').write(s)
# index.html
h=open(here+'/base/index.html',encoding='utf-8').read()
font=base64.b64encode(open(here+'/base/km.woff2','rb').read()).decode()
h,n=re.subn(r'@font-face\{font-family:"Lao Local";.*?\}','@font-face{font-family:"Khmer Local";src:url(data:font/woff2;base64,'+font+') format("woff2");font-weight:100 900;font-display:swap;unicode-range:U+1780-17FF,U+19E0-19FF,U+200C-200D,U+25CC}',h,count=1,flags=re.S);assert n==1
def hp(a,b):
    global h
    assert a in h,a
    h=h.replace(a,b)
hp('"Lao Local","Noto Sans Lao Looped","Phetsarath OT","Saysettha OT","Lao UI"','"Khmer Local","Noto Sans Khmer","Khmer Sangam MN","Khmer OS"')
hp('"Lao Local"','"Khmer Local"')
hp('라오스어, 주제별로 공부하기','캄보디아어(크메르어) 첫걸음')
hp('ຮຽນ ພາສາລາວ','រៀនភាសាខ្មែរ')
hp('라오스어, 독음, 뜻으로 검색 (예: ໝາກ, 막, 과일)','크메르어, 독음, 뜻으로 검색 (예: ទឹក, 뜩, 물)')
nw=sum(len(b["w"]) for b in B.values());ns=sum(sum(len(w[4]) for w in b["w"])+len(b["pr"])*2+len(b["dl"])+(1 if b["sm"][0] else 0) for b in B.values())
h,n=re.subn(r'<span><b>[\d,]+</b>묶음</span><span><b>[\d,]+</b>단어</span><span><b>[\d,]+</b>문장</span>',f'<span><b>{len(B)}</b>묶음</span><span><b>{nw:,}</b>단어</span><span><b>{ns:,}</b>문장</span>',h);assert n==1
h,n=re.subn(r'\d{4}-\d\d-\d\d v[\d.]+ · Claude',f'{DATE} v{VER} · Claude',h);assert n>=1
h,n=re.subn(r'app\.js\?v=[\d.]+"',f'app.js?v={VER}"',h);assert n>=1
h=h.replace('LAO Lang','KHMER Lang').replace('lao-','khm-')
h=h.replace('h1.lotitle{font-size:clamp(28px,calc((100vw - 96px)/8.1),66px)','h1.lotitle{font-size:clamp(26px,calc((100vw - 96px)/7.4),62px)')
for a_,b_ in (('<span class="ll">예문보기</span></button>','<span class="ll">예문보기</span><kbd class="kc">Q</kbd></button>'),('<span class="ll">단어공부</span></button>','<span class="ll">단어공부</span><kbd class="kc">W</kbd></button>'),('<span class="ll">확인퀴즈</span></button>','<span class="ll">확인퀴즈</span><kbd class="kc">E</kbd></button>'),('<span class="ll olab">반복</span>','<span class="ll olab">반복<kbd class="kc">1~5</kbd></span>'),('<span class="ll olab">배속</span>','<span class="ll olab">배속<kbd class="kc">±</kbd></span>'),
  ('x 2.0</option></select></span>','x 2.0</option></select></span>\n      <div class="kbinfo" id="kbinfo"><span><kbd class="kc">Esc</kbd>재생 정지</span><span><kbd class="kc">Enter</kbd>무한 반복/취소</span><span><kbd class="kc">←</kbd>이전 문장</span><span><kbd class="kc">→</kbd>다음 문장</span><label class="kok"><input type="checkbox" id="koChk" checked><kbd class="kc">K</kbd>한국어 말하기</label></div>')):
    assert h.count(a_)==1,a_
    h=h.replace(a_,b_)
RATEOPT=''.join(f'<option value="{v/10:g}">x {v/10:.1f}</option>' for v in range(7,21))
a_='<option value="0.8">x 0.8</option><option value="1">x 1.0</option><option value="1.2">x 1.2</option><option value="1.5">x 1.5</option><option value="2">x 2.0</option>';assert h.count(a_)==1;h=h.replace(a_,RATEOPT)
h=h.replace('<div class="kbinfo" id="kbinfo"><span>','<div class="kbinfo" id="kbinfo"><span><kbd class="kc">Space</kbd>일시정지/재개</span><span>',1)
# v2.10 RYU 2026-11-22: menu box like the Lao app v2.98–v2.99
a_='  <nav class="groups" id="groups" aria-label="대분류"></nav>\n  <nav class="subs" id="subs" role="tablist" aria-label="소분류"></nav>\n  <div class="sinfo" id="sinfo"></div>\n';assert h.count(a_)==1;h=h.replace(a_,'  <div class="menubox">\n'+a_+'  </div>\n')
KCSS=open(here+'/kbd.css',encoding='utf-8').read()
h=h.replace('</head>','<style>'+KCSS+'</style></head>',1)
h=h.replace('</head>','<style>:root{--p8:#1F4E8C;--p8-soft:#E2EAF5}@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--p8:#8DB4E8;--p8-soft:#172538}}:root[data-theme="dark"]{--p8:#8DB4E8;--p8-soft:#172538}[data-g="P8"]{--accent:var(--p8);--accent-soft:var(--p8-soft)}.info .lo{line-height:1.7}.info .terms .lo{font-size:18px}/* v2.1 캄보디아 탭 info pages */.info{padding:6px 4px 12px;font-size:15.5px;line-height:1.65;color:var(--ink)}.info h2{font-size:21px;margin:4px 0 0;line-height:1.3}.info .sub2{color:var(--muted);font-size:14px;margin-bottom:14px}.info figure{margin:0 0 14px;text-align:center}.info figure svg.flag,.info figure img{display:block;width:100%;max-width:420px;height:auto;margin:0 auto;border-radius:8px;box-shadow:0 1px 6px rgba(0,0,0,.18)}.info figure img{background:var(--line)}.info figcaption{font-size:13px;color:var(--muted);margin-top:6px;line-height:1.5}.info figcaption small{display:block;font-size:11px;opacity:.85}.info .facts{width:100%;border-collapse:collapse;margin:2px 0 14px;font-size:14.5px}.info .facts th{width:31%;text-align:left;font-weight:700;color:var(--accent);padding:7px 6px;vertical-align:top;border-bottom:1px solid var(--line)}.info .facts td{padding:7px 6px;border-bottom:1px solid var(--line)}.info h3{font-size:16.5px;margin:18px 0 6px;padding-left:9px;border-left:4px solid var(--accent);line-height:1.35}.info p{margin:0 0 8px}.info .lo{font-family:var(--lao)}.info .r{color:var(--accent)}.info .clr{display:flex;flex-direction:column;gap:7px;margin:6px 0 10px}.info .clr div{display:flex;gap:10px;align-items:flex-start}.info .clr i{flex:none;width:22px;height:22px;border-radius:5px;margin-top:2px;border:1px solid var(--line)}.info .terms{background:var(--accent-soft);border-radius:12px;padding:8px 14px;margin:8px 0 14px}.info .terms div{padding:5px 0;border-bottom:1px dashed var(--line)}.info .terms div:last-child{border:0}.info .terms .lo{font-size:17px;font-weight:700}.info .terms .r{margin:0 8px 0 6px}.info .rel{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}.info .rel button{border:1.5px solid var(--accent);color:var(--accent);background:none;border-radius:999px;padding:3px 13px;font:inherit;font-size:13.5px;cursor:pointer}@media (min-width:860px){.info{padding:8px 14px 14px}.info .top2{display:grid;grid-template-columns:44% 1fr;gap:28px;align-items:start}.info .two{display:grid;grid-template-columns:1fr 1fr;gap:32px}.info .facts th{width:28%}}/* v2.0 글자(P6)·문법(P7) colours */:root{--p6:#1E7470;--p6-soft:#E0F1F0;--p7:#A24F28;--p7-soft:#F7E8DF}@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--p6:#6FCFC9;--p6-soft:#17302F;--p7:#F0A27A;--p7-soft:#3A241A}}:root[data-theme="dark"]{--p6:#6FCFC9;--p6-soft:#17302F;--p7:#F0A27A;--p7-soft:#3A241A}[data-g="P6"]{--accent:var(--p6);--accent-soft:var(--p6-soft)}[data-g="P7"]{--accent:var(--p7);--accent-soft:var(--p7-soft)}.face .frd{margin:2px 0 4px}/* Khmer: stacked letters need more line height */.line .t1{font-size:18px;line-height:1.75}.entry-head .w{line-height:1.7}.cards .face .big{line-height:1.8!important}h1.lotitle{line-height:1.45!important;margin-top:-.2em}.bw.lo,.box .lo,.bintro .lo{line-height:1.8}.rel li{line-height:1.5!important;padding:0!important}.rel .rlo,.box.rel .lo{line-height:1.5!important}.rjump{padding-top:1px;padding-bottom:1px;line-height:1.5}/* RYU 2026-11-19: right-hand repeat buttons square on the right; 연속 재생 round left only, 묶음 재생 round right only */.speak.all[data-playsec],.speak.all[data-sayall]{border-radius:999px 0 0 999px!important}.speak.all[data-chain]{border-radius:999px 0 0 999px!important}.speak.all[data-playbundle]:not([data-chain]){border-radius:0 999px 999px 0!important}</style></head>',1)
assert not re.search('[຀-໿]',h),"Lao text left in html"
open(out+'/index.html','w',encoding='utf-8').write(h)
sw=open(here+'/base/sw.js').read();assert '["_gap450","_gap900"].map' in sw;sw=sw.replace('["_gap450","_gap900"].map','["_gap150","_gap450","_gap900"].map');sw=re.sub(r'lao-shell-v[\d.]+',f'khm-shell-v{VER}',sw).replace('lao-','khm-');open(out+'/sw.js','w').write(sw)
mf=json.load(open(here+'/base/manifest.webmanifest'));mf["name"]=mf["short_name"]="KHMER Lang";json.dump(mf,open(out+'/manifest.webmanifest','w'),ensure_ascii=False)
for f in ('header.svg','header-day.svg','icon-180.png','icon-192.png','icon-512.png'):
    if os.path.exists(here+'/art/'+f): shutil.copyfile(here+'/art/'+f,out+'/'+f)
for f in ('_gap150.mp3','_gap450.mp3','_gap900.mp3'): shutil.copyfile(here+'/base/'+f,out+'/audio/'+f)
open(out+'/.nojekyll','w').write('')
if CR:
    os.makedirs(out+'/img',exist_ok=True)
    for k in CR: shutil.copyfile(here+'/img/'+k+'.jpg',out+'/img/'+k+'.jpg')
print('built',len(B),'bundles',nw,'words',ns,'sentences')
