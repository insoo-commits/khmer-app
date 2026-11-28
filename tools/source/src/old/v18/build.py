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
for b in B.values():
    for w in b["w"]:
        if " " not in nk(w[0]): WD[nk(w[0])]=nk(w[2])
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
PMETA=[("P5","주제별","인사·학교·식당·시장 등 장면별 단어와 문장"),("P4","짝말","크다·작다처럼 짝으로 외우는 반대말"),("P1","말소리","크메르 글자의 소리와, 한글로 쓰면 같아서 헷갈리는 소리")]
DATA={"P":[{"id":p,"ko":k,"desc":d,"subs":[x for x in subs if x["id"].startswith(p)]} for p,k,d in PMETA],"B":B}
DATA["P"]=[p for p in DATA["P"] if p["subs"]]
# note dictionary: headwords (first meaning) + extra words
ND={};NR={}
for b in B.values():
    for w in b["w"]:
        k=w[0].replace("…","").replace("?","").strip()
        if " " in k: continue
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
code+=['let known=store.get("lao-known",{});const saved=store.get("lao-sel",{});']
code+=ln(47,83)+[repjs]+ln(90,212)
code+=["const BLAB="+J(BLAB)+";"]
code+=ln(214,274)+["const nmean=t=>NDICT[t];"]+ln(328,530)
s="\n".join(code)+"\n"
def rp(a,b,n=None):
    global s
    c=s.count(a)
    assert c>0 and (n is None or c==n),(a,c)
    s=s.replace(a,b)
rp('</span><span class="hint">${hintHtml(hint)}</span></span><span class="bk"','</span><span class="rd frd">${esc(rd)}</span><span class="hint">${hintHtml(hint)}</span></span><span class="bk"',1)
# RYU 2026-11-19: tapping the repeat button that is playing stops it
rp('if(t.matches(".speak.all"))P._bk=btnKey(t);','if(t.matches(".speak.all")){const k=btnKey(t);if(k&&P.active&&P._bk===k){stopPlay();P._bk=null;syncBtn();return}P._bk=k}',1)
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
h=h.replace('</head>','<style>.face .frd{margin:2px 0 4px}/* Khmer: stacked letters need more line height */.line .t1{font-size:18px;line-height:1.75}.entry-head .w{line-height:1.7}.cards .face .big{line-height:1.8!important}h1.lotitle{line-height:1.45!important;margin-top:-.2em}.bw.lo,.box .lo,.bintro .lo{line-height:1.8}.rel li{line-height:1.5!important;padding:0!important}.rel .rlo,.box.rel .lo{line-height:1.5!important}.rjump{padding-top:1px;padding-bottom:1px;line-height:1.5}/* RYU 2026-11-19: right-hand repeat buttons square on the right; 연속 재생 round left only, 묶음 재생 round right only */.speak.all[data-playsec],.speak.all[data-sayall]{border-radius:999px 0 0 999px!important}.speak.all[data-chain]{border-radius:999px 0 0 999px!important}.speak.all[data-playbundle]:not([data-chain]){border-radius:0 999px 999px 0!important}</style></head>',1)
assert not re.search('[຀-໿]',h),"Lao text left in html"
open(out+'/index.html','w',encoding='utf-8').write(h)
sw=open(here+'/base/sw.js').read();sw=re.sub(r'lao-shell-v[\d.]+',f'khm-shell-v{VER}',sw).replace('lao-','khm-');open(out+'/sw.js','w').write(sw)
mf=json.load(open(here+'/base/manifest.webmanifest'));mf["name"]=mf["short_name"]="KHMER Lang";json.dump(mf,open(out+'/manifest.webmanifest','w'),ensure_ascii=False)
for f in ('header.svg','header-day.svg','icon-180.png','icon-192.png','icon-512.png'):
    if os.path.exists(here+'/art/'+f): shutil.copyfile(here+'/art/'+f,out+'/'+f)
for f in ('_gap450.mp3','_gap900.mp3'): shutil.copyfile(here+'/base/'+f,out+'/audio/'+f)
open(out+'/.nojekyll','w').write('')
print('built',len(B),'bundles',nw,'words',ns,'sentences')
