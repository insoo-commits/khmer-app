"""Header art (Angkor Wat instead of That Luang) + icons. python3 art/make_art.py"""
import re,os,subprocess,base64
here=os.path.dirname(os.path.abspath(__file__));base=here+'/../base/'
ANGKOR='''<!-- Angkor Wat on the bank -->
  <g transform="translate(700 228)" fill="url(#gold)">
    <rect x="-190" y="-10" width="380" height="10" fill="#7a4e2a"/>
    <rect x="-175" y="-26" width="350" height="16" rx="2"/>
    <rect x="-120" y="-44" width="240" height="18" rx="2"/>
    <rect x="-70" y="-60" width="140" height="16" rx="2"/>
    <g id="twr"><path d="M-13 0 C-15 -16 -12 -30 -8 -42 C-6 -52 -3 -60 0 -72 C3 -60 6 -52 8 -42 C12 -30 15 -16 13 0Z"/><path d="M-12 -14 H12 M-10 -28 H10 M-7 -42 H7" stroke="#8a5f17" stroke-width="1.6" fill="none" opacity=".6"/></g>
    <use href="#twr" transform="translate(0 -60) scale(1.45)"/>
    <use href="#twr" transform="translate(-58 -44) scale(1.05)"/>
    <use href="#twr" transform="translate(58 -44) scale(1.05)"/>
    <use href="#twr" transform="translate(-150 -26) scale(.85)"/>
    <use href="#twr" transform="translate(150 -26) scale(.85)"/>
    <g fill="#7a4e2a" opacity=".55"><rect x="-6" y="-24" width="12" height="14"/><rect x="-100" y="-22" width="6" height="10"/><rect x="-80" y="-22" width="6" height="10"/><rect x="-40" y="-22" width="6" height="10"/><rect x="34" y="-22" width="6" height="10"/><rect x="74" y="-22" width="6" height="10"/><rect x="94" y="-22" width="6" height="10"/></g>
  </g>
  <!-- reflection -->
  <g transform="translate(700 230) scale(1 -.35)" opacity=".22" fill="#ffd36b">
    <rect x="-175" y="-44" width="350" height="44"/>
    <path d="M-19 -60 C-22 -85 -10 -120 0 -165 C10 -120 22 -85 19 -60Z"/>
    <path d="M-72 -44 C-73 -70 -64 -95 -58 -120 C-52 -95 -43 -70 -44 -44Z"/><path d="M44 -44 C43 -70 52 -95 58 -120 C64 -95 73 -70 72 -44Z"/>
  </g>

  '''
for f in ('header.svg','header-day.svg'):
    s=open(base+f,encoding='utf-8').read()
    s,n=re.subn(r'<!-- That Luang.*?(?=<!-- palms -->)',lambda m:ANGKOR,s,flags=re.S);assert n==1
    s=s.replace('<!-- Mekong -->','<!-- water -->').replace('<!-- dok champa, national flower -->','<!-- flowers -->')
    open(here+'/'+f,'w',encoding='utf-8').write(s)
font=base64.b64encode(open(base+'km.woff2','rb').read()).decode()
html='<html><head><style>@font-face{font-family:K;src:url(data:font/woff2;base64,'+font+')}html,body{margin:0}div{width:512px;height:512px;background:#1F5F8F;color:#fff8ea;font:600 190px K;display:flex;align-items:center;justify-content:center;padding-bottom:10px;box-sizing:border-box}</style></head><body><div>ខ្មែរ</div></body></html>'
open(here+'/icon.html','w',encoding='utf-8').write(html)
js='''const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();for(const n of [180,192,512]){const p=await b.newPage({viewport:{width:512,height:512},deviceScaleFactor:n/512});await p.goto('file://%s/icon.html');await p.evaluate(()=>document.fonts.ready);await p.screenshot({path:'%s/icon-'+n+'.png'});await p.close()}await b.close()})()'''%(here,here)
subprocess.run(['node','-e',js],check=True)
