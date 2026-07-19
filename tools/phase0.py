#!/usr/bin/env python3
"""Phase 0 — deck infrastructure.

1. Deduplicate the ITI logo: 59 identical inline copies (908 KB) -> one CSS rule.
2. Auto-number slide footers in JS so adding slides never means renumbering.
3. Render a "Day N" marker in the footer from section[data-day].
4. Fix the two defects found in the curriculum review.
"""
import re
import sys

SRC = "k8s-slides.html"

s = open(SRC, encoding="utf-8").read()
before = len(s)

# ---------------------------------------------------------------- 1. logo dedup
blobs = re.findall(r"[A-Za-z0-9+/]{15000,}={0,2}", s)
body_blobs = [b for b in blobs if s.find(b) > s.find("<body")]
assert len(set(body_blobs)) == 1, "expected one distinct logo blob"
LOGO = body_blobs[0]

img_tag = f'<img src="data:image/png;base64,{LOGO}" alt="ITI">'
n_imgs = s.count(img_tag)
assert n_imgs == 59, f"expected 59 logo imgs, found {n_imgs}"
s = s.replace(img_tag, '<span class="iti-mark" role="img" aria-label="ITI"></span>')

# One background definition + the sizes the old `img` rules gave each context.
EXTRA_CSS = ".cols-1{grid-template-columns:1fr}"

logo_css = (
    ".iti-mark{display:block;background-image:url(data:image/png;base64,"
    + LOGO
    + ");background-position:center;background-size:contain;background-repeat:no-repeat}"
    ".lg .iti-mark,.ts-brand .lg .iti-mark{width:54px;height:54px}"
    ".foot-logo .iti-mark{width:32px;height:32px}"
    ".bio-badge .iti-mark{width:200px;height:200px}"
    ".close-lg .iti-mark{width:104px;height:104px}"
)
close_style = s.rindex("</style>")
logo_css += EXTRA_CSS
s = s[:close_style] + logo_css + s[close_style:]

# ------------------------------------------------- 2 & 3. footer numbers + day
# Footer text is currently hardcoded per slide ("4 / 56"). Let the controller own
# it so slide count and day labels stay correct no matter how many we add.
anchor = "    this.scale(); addEventListener('resize',()=>this.scale());"
assert anchor in s, "controller anchor not found"
footer_js = """    // Footer is generated: numbering and the Day marker never need hand-editing.
    this.slides.forEach((sl,k)=>{
      const num=sl.querySelector('.foot-num');
      if(num) num.innerHTML=(k+1)+' <i>/</i> '+this.slides.length;
      const course=sl.querySelector('.foot-course');
      if(course){
        const d=sl.dataset.day;
        course.textContent=(d?'Day '+d+' \\u00b7 ':'')+'Kubernetes \\u00b7 ITI DevOps 2026';
      }
    });
"""
s = s.replace(anchor, footer_js + anchor, 1)

# ------------------------------------------------------------- 4. defect fixes
# (a) Lab 4's self-heal command deleted every replica: `| head -1` truncates the
#     printed output, not the deletion. Target exactly one Pod instead.
bad = (
    'kubectl <span class="k">delete</span> pod -l app=web --field-selector \\\n'
    "  status.phase=Running --grace-period=0 | head -1"
)
good = (
    'kubectl <span class="k">delete</span> pod "$(kubectl <span class="k">get</span> pod \\\n'
    "  -l app=web -o name | head -1)\""
)
assert bad in s, "buggy delete command not found"
s = s.replace(bad, good, 1)

# (b) "Zero downtime" is false without a readiness probe — a Pod joins the
#     Service when its container starts, not when it can serve. Flag it forward
#     to the Day 3 probes section rather than asserting something untrue.
fixes = [
    (
        "&#8646; <b>Rolling update</b> &mdash; a new ReplicaSet is created; Pods shift over a "
        "few at a time ( <code>maxUnavailable</code> / <code>maxSurge</code> ) so there is no "
        "<b>downtime</b> .",
        None,  # located by fuzzy match below
    ),
]
# The exact markup differs; patch the two "zero downtime" assertions textually.
s = s.replace(
    "so there is <b>no downtime</b>",
    "so capacity never drops. <b>Add a readiness probe (Day 3) to make that truly zero-downtime</b>",
)
s = s.replace(
    "Zero downtime</b> .",
    "Capacity holds</b> &mdash; but only a readiness probe makes it truly zero-downtime; we add one on Day 3.",
)
s = s.replace(
    "become Ready. <b>Zero downtime</b> .",
    "become Ready. <b>Capacity holds</b> &mdash; a readiness probe (Day 3) is what makes it truly zero-downtime.",
)

open(SRC, "w", encoding="utf-8").write(s)
print(f"size {before:,} -> {len(s):,} chars  ({(before-len(s))/1024:.0f} KB saved)")
print(f"logo copies collapsed: {n_imgs} -> 1")
