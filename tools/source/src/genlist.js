// Clip lists for the Khmer app. node genlist.js <app.js> <outdir>  -> f.json (female), m.json (male), k.json (Korean)
const fs=require('fs');const src=fs.readFileSync(process.argv[2],'utf8');const od=process.argv[3];
const DATA=eval(src.split('\n')[0].replace('const DATA=','(').replace(/;$/,')'));
const NDICT=eval('('+/const NDICT=(\{.*?\}),NRD=/.exec(src)[1]+')');
eval(fs.readFileSync(__dirname+'/rep.js','utf8').replace('function rep','rep=function'));
function akey(t){t=rep(String(t)).replace(/\s+/g," ").trim();let h=0x811c9dc5;for(let i=0;i<t.length;i++){h^=t.charCodeAt(i);h=Math.imul(h,0x01000193)>>>0}return h.toString(36)}
const koSay=t=>String(t).replace(/[①-⑳]/g,"").replace(/\s*\([^)]*\)/g,"").replace(/[;·]/g,",").replace(/\s+/g," ").trim()||String(t);
// say_fix.json: text to speak when the voice misreads the written text (RYU 2026-11-18, ជំរាបលា before a space was read 라). After adding one: bump its key in aver.json.
const SAYFIX=JSON.parse(fs.readFileSync(__dirname+"/say_fix.json","utf8"));
// vowel cards (글자): "◌ា" is spoken on អ, the silent carrier: អា
const say=t=>{const s=rep(String(t)).replace(/◌/g,"អ").replace(/[…—]/g," ").replace(/\s+/g," ").trim();return SAYFIX[s]||s};
const F={},M={},K={};const f=t=>{if(t)F[akey(t)]=say(t)},m=t=>{if(t)M['m_'+akey(t)]=say(t)},k=t=>{if(t)K['k_'+akey(t)]=koSay(t).replace(/—/g,",")};
for(const b of Object.values(DATA.B)){
  b.w.forEach(w=>{f(w[0]);k(w[3]);w[4].forEach((e,i)=>{(i===1?m:f)(e[0]);k(e[2])})});
  b.pr.forEach(p=>p.forEach(x=>{f(x[0]);k(x[2])}));
  b.dl.forEach((x,i)=>{(i%2?m:f)(x[1]);k(x[3])});
  if(b.sm&&b.sm[0]){f(b.sm[0]);k(b.sm[2])}}
fs.mkdirSync(od,{recursive:true});for(const [n,o] of [['f',F],['m',M],['k',K]])fs.writeFileSync(od+'/'+n+'.json',JSON.stringify(o));
console.log('female',Object.keys(F).length,'male',Object.keys(M).length,'korean',Object.keys(K).length);
