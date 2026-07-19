#!/usr/bin/env python3
"""Inject a content auto-fit safety net into the deck controller.

The stage is a fixed 1920x1080. A slide whose content runs past the footer is
clipped on a projector, and no structural check can see it. This scales the
.body block down just enough to fit.

The floor is deliberate: below ~0.68 the type is too small to read from the
back of a room, so the slide is left overflowing rather than made illegible.
Those are found with tools/overflow-probe.js and fixed by splitting the
content, not by shrinking it further.
"""
import re
import sys

SRC = "k8s-slides.html"
s = open(SRC, encoding="utf-8").read()

if "fit(sl)" in s:
    sys.exit("autofit already installed")

FIT = """
  fit(sl){
    const body=sl.querySelector('.body'); if(!body) return;
    body.style.transform=''; body.style.width='';
    const foot=sl.querySelector('.foot');
    const footTop=foot?foot.getBoundingClientRect().top:sl.getBoundingClientRect().bottom;
    let bottom=0;
    body.querySelectorAll(':scope > *, :scope > * > *, :scope > * > * > *').forEach(el=>{
      const r=el.getBoundingClientRect();
      if(r.height>0 && r.bottom>bottom) bottom=r.bottom;
    });
    if(!bottom) return;
    const top=body.getBoundingClientRect().top;
    const avail=footTop-top-10, need=bottom-top;
    if(need>avail && avail>0){
      const k=Math.max(0.68, avail/need);
      body.style.transformOrigin='top left';
      body.style.transform='scale('+k+')';
      body.style.width=(100/k)+'%';
    }
  }
  fitAll(){
    this.slides.forEach(sl=>{
      const a=sl.classList.contains('active'), v=sl.classList.contains('visible');
      sl.classList.add('visible','active');
      this.fit(sl);
      if(!a) sl.classList.remove('active');
      if(!v) sl.classList.remove('visible');
    });
  }
"""

# 1. add the methods to the Deck class, just before next()/prev()
anchor = "  next(){this.go(this.i+1)} prev(){this.go(this.i-1)}"
assert anchor in s, "Deck.next anchor not found"
s = s.replace(anchor, FIT + anchor, 1)

# 2. fit the slide as it becomes active
go_anchor = "    if(!silent) history.replaceState(null,'','#'+(this.i+1));"
assert go_anchor in s, "go() anchor not found"
s = s.replace(go_anchor, "    this.fit(this.slides[this.i]);\n" + go_anchor, 1)

# 3. re-fit on resize (the stage scale changes, but so do measurements)
rs = "    this.scale(); addEventListener('resize',()=>this.scale());"
assert rs in s, "resize anchor not found"
s = s.replace(
    rs,
    "    this.scale(); addEventListener('resize',()=>{this.scale();"
    "this.fit(this.slides[this.i])});",
    1,
)

open(SRC, "w", encoding="utf-8").write(s)
print("autofit installed (floor 0.68)")
