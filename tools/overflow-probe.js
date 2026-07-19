// Paste into the browser console against the served deck.
// Baseline on the original 56 hand-tuned slides: 0 overflowing.
// Any slide reported here has content colliding with / running past the footer
// on the fixed 1920x1080 stage -- invisible to every structural check.
window.probeOverflow = function(){
  const slides=[...document.querySelectorAll('.slide')];
  const prev=slides.findIndex(s=>s.classList.contains('active'));
  const bad=[];
  slides.forEach((s,i)=>{
    const wasA=s.classList.contains('active'), wasV=s.classList.contains('visible');
    s.classList.add('visible','active');
    const foot=s.querySelector('.foot');
    const footTop = foot ? foot.getBoundingClientRect().top : 1080;
    let worstBottom=0;
    s.querySelectorAll('.pad > *, .pad > * > *, .pad > * > * > *, .div-pad > *').forEach(el=>{
      if(el.closest('.foot')) return;
      const r=el.getBoundingClientRect();
      if(r.height>0 && r.bottom>worstBottom) worstBottom=r.bottom;
    });
    const overlap=Math.round(worstBottom-footTop);
    if(overlap>0) bad.push([i+1,overlap]);
    if(!wasA) s.classList.remove('active');
    if(!wasV) s.classList.remove('visible');
  });
  if(prev>=0) slides[prev].classList.add('active','visible');
  return {total:slides.length, over:bad.length, worst:bad.sort((a,b)=>b[1]-a[1]).slice(0,20)};
};
probeOverflow();
