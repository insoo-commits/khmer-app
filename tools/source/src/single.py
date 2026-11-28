"""One-file preview (for a Claude artifact): app + audio inlined. python3 single.py <pwa_dir> <out.html>"""
import sys,os,base64,json,re,glob
d,out=sys.argv[1:3];h=open(d+'/index.html',encoding='utf-8').read()
uri=lambda f,t:'data:'+t+';base64,'+base64.b64encode(open(d+'/'+f,'rb').read()).decode()
for f in ('header.svg','header-day.svg'): h=h.replace('url('+f+')','url('+uri(f,'image/svg+xml')+')')
aud={os.path.basename(p)[:-4]:base64.b64encode(open(p,'rb').read()).decode() for p in glob.glob(d+'/audio/*.mp3')}
# artifact limit is 16 MB: when over budget, leave out the biggest Korean clips (the browser's own Korean voice reads those)
BUD=10.5e6;tot=sum(len(v) for v in aud.values())
for k in sorted([k for k in aud if k.startswith('k_')],key=lambda k:-len(aud[k])):
    if tot<=BUD: break
    tot-=len(aud[k]);del aud[k]
app=open(d+'/app.js',encoding='utf-8').read()
# clips come from the page itself instead of the network
app=app.replace('function blobUrl(k){','function blobUrl(k){if(!ABLOB[k]&&window.AUDIO_DATA&&AUDIO_DATA[k]){try{const s=atob(AUDIO_DATA[k]),u=new Uint8Array(s.length);for(let i=0;i<s.length;i++)u[i]=s.charCodeAt(i);ABLOB[k]=URL.createObjectURL(new Blob([u],{type:"audio/mpeg"}))}catch(e){ABLOB[k]="data:audio/mpeg;base64,"+AUDIO_DATA[k]}}',1)
assert 'AUDIO_DATA' in app
app=app.replace('if("serviceWorker" in navigator)navigator.serviceWorker.register("sw.js").catch(()=>{});','')
app=app.replace("p.innerHTML='<a href=\"#\" class=\"dla\">↓ 음성 mp3 내려받기 (오프라인용)</a><span class=\"dls\"></span>'","p.hidden=true;p.innerHTML='<a href=\"#\" class=\"dla\"></a><span class=\"dls\"></span>'")
idx='window.AUDIO_INDEX='+json.dumps({k:1 for k in sorted(aud) if not k.startswith('_')},separators=(',',':'))+';'
i=h.rindex('<script>/* load data only');j=h.index('</script>',i)+9
tail='<script>'+idx+'window.AUDIO_DATA='+json.dumps(aud,separators=(',',':'))+';</script>\n<script>'+app.replace('</script','<\\/script')+'</script>'
h=h[:i]+tail+h[j:]
h=re.sub(r'<link rel="manifest"[^>]*>','',h);h=re.sub(r'<link rel="apple-touch-icon"[^>]*>','',h)
h=h.replace('<title>KHMER Lang</title>','<title>KHMER Lang 미리보기</title>')
h=re.sub(r'(?i)<!doctype[^>]*>|</?html[^>]*>|</?head[^>]*>|</?body[^>]*>|<meta charset[^>]*>|<meta name="viewport"[^>]*>','',h)
open(out,'w',encoding='utf-8').write(h);print('single file',round(len(h)/1e6,2),'MB')
