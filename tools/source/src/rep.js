function rep(t){if(!t||t.indexOf("ៗ")<0)return t;
  /* ៗ repeats the word just before it: the shortest known word that ends right there */
  if(!rep.W){rep.W=new Set();try{for(const k in DATA.B)for(const w of DATA.B[k].w)if(!/\s/.test(w[0]))rep.W.add(w[0].replace(/ៗ/g,""));for(const k in NDICT)rep.W.add(k)}catch(e){}}
  return t.replace(/([ក-៓]+)\s*ៗ/g,(m,pre)=>{let b="";for(let n=2;n<=Math.min(pre.length,16);n++){const x=pre.slice(-n);if(rep.W.has(x)&&!/^[ា-៓]/.test(x)&&!/្$/.test(pre.slice(0,-n))){b=x;break}}return pre+" "+(b||pre)})}
