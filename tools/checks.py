#!/usr/bin/env python3
"""Content checks the structural verifier cannot make.

1. Every Kubernetes manifest embedded in a lab's code block is extracted and
   run through `kubectl apply --dry-run=client`. The labs ARE the deliverable;
   a typo'd apiVersion should fail here, not in front of a class.
2. Every CSS class used in the deck is checked against the classes the
   stylesheet actually defines. An invented class renders unstyled but passes
   every structural check.
3. Known-bad strings (e.g. flags that do not exist) are grepped out.
"""
import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path("k8s-slides.html")
s = SRC.read_text(encoding="utf-8")

# ------------------------------------------------------- 1. embedded manifests
code_blocks = re.findall(r"<pre><code>(.*?)</code></pre>", s, flags=re.S)
manifests, skipped = [], 0
for cb in code_blocks:
    text = html.unescape(re.sub(r"<[^>]+>", "", cb))
    # A manifest starts at whichever of kind:/apiVersion: comes first and runs
    # to the heredoc terminator, a blank line followed by prose, or block end.
    for m in re.finditer(r"^((?:kind|apiVersion)\s*:.*?)(?=^EOF$|^\s*$\n^[a-z#]|\Z)",
                         text, flags=re.S | re.M):
        body = m.group(1).strip()
        if "kind" not in body or "apiVersion" not in body:
            continue
        # kind's own Cluster config is not a Kubernetes API object.
        if "kind.x-k8s.io" in body:
            skipped += 1
            continue
        # Shell line-continuations and $VARS are not valid YAML; skip those.
        if "\\\n" in body or re.search(r"\$\{?\w+", body):
            skipped += 1
            continue
        manifests.append(body)

print(f"embedded manifests found: {len(manifests)} (skipped {skipped} with shell syntax)")
bad = []
for i, man in enumerate(manifests):
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(man)
        path = f.name
    r = subprocess.run(
        ["kubectl", "apply", "--dry-run=client", "--validate=false", "-f", path],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        first = man.split("\n")[:4]
        bad.append((i, r.stderr.strip().split("\n")[0], first))
    Path(path).unlink()

if bad:
    print(f"\n{len(bad)} embedded manifest(s) FAILED kubectl validation:")
    for i, err, head in bad[:12]:
        print(f"  x #{i}: {err}")
        for line in head:
            print(f"      | {line}")
else:
    print("all embedded manifests validate")

# ------------------------------------------------------------ 2. CSS classes
head_css = s[: s.find("<body")]
defined = set(re.findall(r"\.([a-zA-Z][\w-]*)", head_css))
defined |= {"slide", "active", "visible", "r", "pad", "body", "col", "two"}

used = set()
for attr in re.findall(r'class="([^"]+)"', s[s.find("<body"):]):
    used |= set(attr.split())

unknown = sorted(u for u in used - defined if not u.startswith("t-"))
print(f"\ncss classes used: {len(used)}  undefined: {len(unknown)}")
if unknown:
    print("  undefined (renders unstyled):", ", ".join(unknown[:30]))

# ------------------------------------------------------------ 3. known-bad
BAD_STRINGS = {
    "--disable-default-cni": "not a real kind flag; it is networking.disableDefaultCNI in the config file",
    "apiversion:": "lowercase apiVersion",
    "kubectl create -f": "prefer kubectl apply -f",
}
text_only = html.unescape(re.sub(r"<[^>]+>", " ", s[s.find("<body"):]))
hits = []
for needle, why in BAD_STRINGS.items():
    n = text_only.lower().count(needle.lower())
    if n:
        hits.append(f"{needle!r} x{n} -- {why}")
if hits:
    print("\nknown-bad strings present:")
    for h in hits:
        print("  x", h)
else:
    print("\nno known-bad strings")

sys.exit(1 if (bad or hits) else 0)
