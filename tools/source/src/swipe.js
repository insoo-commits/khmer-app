/* v3.23 RYU: phone swipe left/right = next/previous bundle (same as the 다음 묶음/이전 묶음 buttons) */
/* v2.22 RYU: swipe also over info tables (.facts). v2.23 RYU: decide during touchmove (60px, 1 s, |dx|>1.5|dy|), vertical move >40px = scroll, one bundle per swipe, switch at once then slide in; a swipe never counts as a tap (sticky bundle-name bar no longer opens the list) */
(function(){let sx=0,sy=0,st=0,ok=false,moved=false,swT=0;
 const hscroll=el=>{for(;el&&el!==document.body;el=el.parentElement){if(el.scrollWidth>el.clientWidth+4){const o=getComputedStyle(el).overflowX;if(o==="auto"||o==="scroll")return true}}return false};
 const go=dx=>{try{const s=getSelection();if(s&&String(s).length)return}catch(_){}
  const b=document.querySelector(dx<0?".nextbun:not(.prevbun)":".nextbun.prevbun");if(!b)return;swT=Date.now();b.click();
  const s2=document.getElementById("sheet");if(s2){s2.style.transition="none";s2.style.transform="translateX("+(dx<0?36:-36)+"px)";s2.style.opacity=".4";requestAnimationFrame(()=>requestAnimationFrame(()=>{s2.style.transition="transform .16s ease-out,opacity .16s";s2.style.transform="";s2.style.opacity=""}))}};
 /* a finger that moved (swipe or scroll) is not a tap: swallow the click the browser may send afterwards */
 document.addEventListener("click",e=>{if(e.isTrusted&&(moved||Date.now()-swT<500)){moved=false;e.preventDefault();e.stopPropagation()}},true);
 document.addEventListener("touchstart",e=>{ok=false;moved=false;if(e.touches.length!==1)return;const t=e.touches[0],w=innerWidth;sx=t.clientX;sy=t.clientY;st=Date.now();if(t.clientX<24||t.clientX>w-24)return;/* leave screen edges to the browser back/forward gesture */
  const el=e.target;if(el.closest&&el.closest("input,select,textarea,#player,.gal,table:not(.facts),.bsel,#groups,#subs,.subs,.tabs"))return;if(hscroll(el))return;ok=true},{passive:true});
 const chk=t=>{if(!ok)return;const dx=t.clientX-sx,dy=t.clientY-sy;
  if(Math.abs(dy)>40||Date.now()-st>1000){ok=false;return}
  if(Math.abs(dx)>=60&&Math.abs(dx)>Math.abs(dy)*1.5){ok=false;go(dx)}};
 document.addEventListener("touchmove",e=>{if(e.touches.length!==1)return;const t=e.touches[0];if(Math.abs(t.clientX-sx)>12||Math.abs(t.clientY-sy)>12)moved=true;if(ok)chk(t)},{passive:true});
 document.addEventListener("touchend",e=>{if(ok)chk(e.changedTouches[0]);ok=false;setTimeout(()=>{moved=false},400)},{passive:true});
 document.addEventListener("touchcancel",()=>{ok=false},{passive:true})})();
