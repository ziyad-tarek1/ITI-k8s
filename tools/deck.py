#!/usr/bin/env python3
"""Slide builder for the ITI Kubernetes deck.

Emits exactly the markup the existing 56 slides use, so new content is
indistinguishable from hand-written slides. Content modules describe slides
with these helpers instead of raw HTML.

Design vocabulary (from the existing deck's CSS):
  tones   t-slate t-maroon t-amber t-blue t-green t-teal t-violet t-gold
  notes   n-info (i)  n-tip (pointing hand)  n-warn (!)  n-why (?)
  code    .k key/verb   .v value   .c comment
"""
import html
import re

# ------------------------------------------------------------------ constants
NOTE_ICO = {
    "n-info": "&#8505;",
    "n-tip": "&#9758;",
    "n-warn": "&#9888;",
    "n-why": "?",
}

# kubectl subcommands that should render as keywords
VERBS = (
    "get describe create apply delete logs exec run expose scale edit patch "
    "rollout set label annotate taint cordon drain top port-forward cp explain "
    "wait config version cluster-info api-resources auth diff replace"
).split()


# ------------------------------------------------------------------ utilities
def esc(t):
    """Escape text for HTML, leaving intentional entities alone."""
    return html.escape(t, quote=False).replace("&amp;#", "&#").replace("&amp;", "&")


def hl(code):
    """Syntax-highlight a shell/YAML block using the deck's .c/.k/.v spans."""
    out = []
    for line in code.split("\n"):
        raw = html.escape(line, quote=False)
        stripped = raw.lstrip()
        if stripped.startswith("#"):
            out.append(f'<span class="c">{raw}</span>')
            continue
        # YAML "key:" -> keyword (handles list items and nesting)
        m = re.match(r"^(\s*-?\s*)([A-Za-z_][\w.\-/]*)(:)(.*)$", raw)
        if m and not stripped.startswith("kubectl"):
            pre, key, colon, rest = m.groups()
            # numeric / boolean scalars get the value tone
            rest = re.sub(
                r"^(\s+)(\d+|true|false)(\s*)$",
                lambda x: f'{x.group(1)}<span class="v">{x.group(2)}</span>{x.group(3)}',
                rest,
            )
            out.append(f'{pre}<span class="k">{key}</span>{colon}{rest}')
            continue
        # kubectl <verb>
        m = re.match(r"^(\s*)(kubectl|helm|kind|docker)(\s+)([a-z-]+)(.*)$", raw)
        if m:
            pre, tool, sp, verb, rest = m.groups()
            if verb in VERBS or tool in ("helm", "kind", "docker"):
                out.append(f'{pre}{tool}{sp}<span class="k">{verb}</span>{rest}')
                continue
        out.append(raw)
    return "\n".join(out)


# --------------------------------------------------------------- components
def term(label, code, cls="sm"):
    """A terminal/editor panel with a Copy button."""
    return (
        f'<div class="term {cls} r"><div class="term-bar"><div class="dots">'
        f"<i></i><i></i><i></i></div>"
        f'<span class="term-label">{esc(label)}</span>'
        f'<button class="copy">Copy</button></div>'
        f"<pre><code>{hl(code)}</code></pre></div>"
    )


def note(kind, body, title=None, style=""):
    ico = NOTE_ICO[kind]
    t = f'<span class="note-title">{esc(title)}</span> &mdash; ' if title else ""
    st = f' style="{style}"' if style else ""
    return (
        f'<div class="note {kind}"{st}><span class="note-ico">{ico}</span>'
        f"<div>{t}{body}</div></div>"
    )


def cards(items, cols=3):
    """items: (icon_entity, title, body, tone)"""
    inner = "".join(
        f'<div class="card {tone} r"><div class="card-ico">{ico}</div>'
        f"<h3>{esc(title)}</h3><p>{body}</p></div>"
        for ico, title, body, tone in items
    )
    return f'<div class="cards cols-{cols}">{inner}</div>'


def table(headers, rows, note_after=None):
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows
    )
    t = f'<div class="tbl-wrap r"><table class="tbl"><tr>{head}</tr>{body}</table></div>'
    return t + (note_after or "")


def steps(items):
    li = "".join(
        f'<li><span class="step-n">{i}</span><div>{body}</div></li>'
        for i, body in enumerate(items, 1)
    )
    return f'<ul class="steps">{li}</ul>'


def two(left, right, ratio="1fr 1fr", gap=36):
    return (
        f'<div class="two" style="grid-template-columns:{ratio};gap:{gap}px;'
        f'align-items:start">{left}{right}</div>'
    )


def col(*parts):
    return '<div class="col r">' + "".join(parts) + "</div>"


# ------------------------------------------------------------------- slides
FOOT = (
    '<footer class="foot"><span class="foot-logo">'
    '<span class="iti-mark" role="img" aria-label="ITI"></span></span>'
    '<span class="foot-course">Kubernetes &middot; ITI DevOps 2026</span>'
    '<span class="foot-num"></span></footer>'
)


def _sec(cls, day, notes, inner):
    d = f' data-day="{day}"' if day else ""
    n = html.escape(notes, quote=True) if notes else ""
    return f'<section class="slide {cls}"{d} data-notes="{n}">{inner}{FOOT}</section>'


def slide(title, body, eyebrow=None, kicker=None, notes="", day=None, lab=False):
    head = ""
    if eyebrow:
        head += f'<div class="eyebrow r">{esc(eyebrow)}</div>'
    head += f'<h2 class="stitle r">{esc(title)}</h2>'
    if kicker:
        head += f'<p class="kicker r">{kicker}</p>'
    inner = (
        f'<div class="pad"><div class="shead">{head}</div>'
        f'<div class="body">{body}</div></div>'
    )
    return _sec("labslide" if lab else "", day, notes, inner)


def lab(title, body, eyebrow=None, kicker=None, notes="", day=None):
    return slide(title, body, eyebrow, kicker, notes, day, lab=True)


def divider(num, title, sub, items, notes="", day=None):
    li = "".join(f'<li class="r">{esc(i)}</li>' for i in items)
    inner = (
        f'<div class="div-pad"><div class="div-num r">{num}</div>'
        f'<div class="div-main"><h2 class="div-title r">{esc(title)}</h2>'
        f'<p class="div-sub r">{esc(sub)}</p>'
        f'<ul class="div-list">{li}</ul></div></div>'
    )
    return _sec("divider", day, notes, inner)


# --------------------------------------------------------- existing-deck I/O
SRC = "k8s-slides.html"


def load(path=SRC):
    """Return (head, [sections], tail) for the current deck."""
    s = open(path, encoding="utf-8").read()
    secs = re.findall(r'<section class="slide.*?</section>', s, flags=re.S)
    first, last = s.index(secs[0]), s.rindex(secs[-1]) + len(secs[-1])
    return s[:first], secs, s[last:]


def title_of(sec):
    m = re.search(r'class="(?:stitle|div-title|ts-title)[^"]*"[^>]*>(.*?)</', sec, re.S)
    t = re.sub(r"<[^>]+>", "", m.group(1)) if m else ""
    return html.unescape(t).strip()


def slug_of(sec):
    t = title_of(sec).lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "untitled"


def set_day(sec, day):
    """Stamp/replace data-day on an existing section."""
    sec = re.sub(r'\s*data-day="[^"]*"', "", sec, count=1)
    return sec.replace('<section class="slide', f'<section data-day="{day}" class="slide', 1)


def write(head, sections, tail, path=SRC):
    open(path, "w", encoding="utf-8").write(head + "".join(sections) + tail)
    return len(sections)
