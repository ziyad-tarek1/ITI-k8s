#!/usr/bin/env python3
"""Structural checks on the assembled deck.

Catches the failure modes that a browser screenshot of slide 1 would not:
unbalanced markup, slides missing a footer, empty bodies, stale day markers,
duplicated titles from copy-paste, and unescaped raw characters in prose.
"""
import html
import re
import sys
from collections import Counter

SRC = "k8s-slides.html"
s = open(SRC, encoding="utf-8").read()
secs = re.findall(r'<section [^>]*class="slide.*?</section>', s, flags=re.S)
if not secs:
    secs = re.findall(r'<section class="slide.*?</section>', s, flags=re.S)

fail = []
warn = []


def check(cond, msg, hard=True):
    if not cond:
        (fail if hard else warn).append(msg)


# ------------------------------------------------------------------ global
check(s.count("<section") == s.count("</section>"),
      f"section tags unbalanced: {s.count('<section')} open, {s.count('</section>')} close")
check(len(secs) > 150, f"expected >150 slides, found {len(secs)}")
check(s.count("<body") == 1 and s.count("</body>") == 1, "body tag count wrong")
check(s.count("</html>") == 1, "html not closed")
check("iti-mark{display:block" in s, "logo CSS rule missing")
check("Footer is generated" in s, "footer auto-numbering JS missing")

# base64 should appear exactly once (the single logo definition)
blobs = re.findall(r"[A-Za-z0-9+/]{5000,}={0,2}", s)
in_body = [b for b in blobs if s.find(b) > s.find("<body")]
check(len(in_body) == 0, f"{len(in_body)} large base64 blobs leaked back into the body")

# ------------------------------------------------------------------ per slide
titles = []
days = Counter()
for i, sec in enumerate(secs, 1):
    where = f"slide {i}"
    check("<footer class=\"foot\"" in sec, f"{where}: no footer")
    check('class="foot-num"' in sec, f"{where}: no slide-number element")
    check(sec.count("<div") == sec.count("</div>"),
          f"{where}: div tags unbalanced ({sec.count('<div')}/{sec.count('</div>')})")
    check(sec.count("<pre") == sec.count("</pre>"), f"{where}: pre unbalanced")
    check(sec.count("<table") == sec.count("</table>"), f"{where}: table unbalanced")

    m = re.search(r'data-day="(\d)"', sec)
    if m:
        days[m.group(1)] += 1
    else:
        days["none"] += 1

    t = re.search(r'class="(?:stitle|div-title|ts-title)[^"]*"[^>]*>(.*?)</', sec, re.S)
    if t:
        titles.append(html.unescape(re.sub(r"<[^>]+>", "", t.group(1))).strip())

    # body should not be empty
    b = re.search(r'<div class="body">(.*?)</div></div>', sec, re.S)
    if b:
        text = re.sub(r"<[^>]+>", "", b.group(1)).strip()
        check(len(text) > 20, f"{where}: body looks empty", hard=False)

    # raw smart punctuation should have been written as entities
    body_txt = re.sub(r"<[^>]+>", "", sec)
    for ch, name in (("—", "em dash"), ("’", "curly apostrophe"),
                     ("“", "curly quote")):
        if ch in body_txt:
            warn.append(f"{where}: raw {name} instead of an HTML entity")
            break

# duplicated titles usually mean a copy-paste slip
dupes = [t for t, n in Counter(titles).items() if n > 1 and t]
check(not dupes, f"duplicate slide titles: {dupes[:6]}", hard=False)

# ------------------------------------------------------------------ report
print(f"slides            {len(secs)}")
print(f"day distribution  {dict(sorted(days.items()))}")
print(f"unique titles     {len(set(titles))}/{len(titles)}")
print(f"file size         {len(s)/1024:.0f} KB")

if warn:
    print(f"\n{len(warn)} warning(s):")
    for w in warn[:25]:
        print("  ~", w)
if fail:
    print(f"\n{len(fail)} FAILURE(s):")
    for f_ in fail[:25]:
        print("  x", f_)
    sys.exit(1)
print("\nstructure OK")
