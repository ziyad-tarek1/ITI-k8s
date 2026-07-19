#!/usr/bin/env python3
"""Assemble the full 4-day deck from the existing slides + the day content modules.

The ordering below IS the curriculum: every topic appears only after its
prerequisites. Two deliberate moves from COURSE-REVIEW.md section 4:

  * Cluster architecture (old 21-25) now runs BEFORE distributions, so students
    can actually evaluate "who runs the control plane".
  * The deep kubeadm/k3s/EKS comparison (old 15-17) moves to Day 4.

Existing slides are referenced by their original 1-based number. Dropped:
  3   old one-day roadmap      -> replaced by the 4-day roadmap
  45  "Cluster DNS & Ingress"  -> split into Day 2 DNS and Day 4 Ingress
  47  old Ingress lab          -> rewritten to route the Voting App
"""
import importlib
import re
import sys

sys.path.insert(0, "tools")
import deck  # noqa: E402

head, EXIST, tail = deck.load()

d1 = importlib.import_module("content_day1").BLOCKS
d2 = importlib.import_module("content_day2").BLOCKS
d3 = importlib.import_module("content_day3").BLOCKS
d4 = importlib.import_module("content_day4").BLOCKS


def keep(*nums):
    """Existing slides by original 1-based number."""
    return [EXIST[n - 1] for n in nums]


# The old Ingress lab routed to an nginx Deployment called "web". By Day 4 the
# Voting App is the thing on the cluster, so the lab routes to it instead.
INGRESS_LAB = deck.lab(
    "Route the Voting App through one Ingress",
    deck.two(
        deck.term(
            "1 &middot; install the controller",
            """# kind-tuned ingress-nginx
kubectl apply -f https://raw.githubusercontent.com/\\
kubernetes/ingress-nginx/main/deploy/static/\\
provider/kind/deploy.yaml

# wait until the admission webhook is up
kubectl wait -n ingress-nginx \\
  --for=condition=ready pod \\
  -l app.kubernetes.io/component=controller \\
  --timeout=180s""",
        )
        + deck.term(
            "2 &middot; one front door, two apps",
            """kubectl apply -f - <<'EOF'
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: vote
  namespace: vote
spec:
  ingressClassName: nginx
  rules:
    - host: vote.localtest.me
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: vote
                port: {number: 80}
    - host: result.localtest.me
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: result
                port: {number: 80}
EOF

curl -s http://vote.localtest.me   | head -n3
curl -s http://result.localtest.me | head -n3""",
        ),
        ratio="1fr 1.15fr",
        gap=32,
    )
    + deck.note(
        "n-tip",
        "<code>*.localtest.me</code> resolves to <code>127.0.0.1</code> from any network, so "
        "no <code>/etc/hosts</code> editing. Port 80 was mapped into the node back in Lab 1 &mdash; "
        "that is why this reaches the cluster at all.",
        title="Why this works",
        style="margin-top:18px",
    )
    + deck.note(
        "n-warn",
        "One <b>external</b> entry point now fronts <b>two</b> Services. Compare that with the "
        "NodePort approach on Day 2, which burned a port on every node for a single Service.",
    ),
    eyebrow="Lab &middot; Ingress",
    kicker="Two apps, two hostnames, <b>one</b> load balancer &mdash; routed at L7 by the Host header.",
    notes="Students have used NodePort and, just now, a real LoadBalancer via MetalLB. Ingress is "
          "the third answer and the one they will actually meet in production: one controller, many "
          "Services, routed by host or path. Point out that the Ingress object is inert on its own "
          "&mdash; without a controller Pod watching for it, nothing happens. That trips up almost "
          "everyone the first time.",
    day=4,
)

# A lead-in for the Day 4 distributions deep-dive (old divider 13 stays on Day 1).
DIST_DIVIDER = deck.divider(
    "00",
    "Distributions, revisited",
    "You have run a cluster for three days. Now the question &lsquo;who operates the "
    "control plane?&rsquo; means something concrete.",
    ["kubeadm &mdash; you build it", "k3s &mdash; trimmed to one binary",
     "EKS &mdash; AWS runs the brain", "Choosing for real workloads"],
    notes="This section was deliberately held back from Day 1. On day one students had no "
          "vocabulary to judge a distribution; now they have run kubectl against a real "
          "cluster for three days and know what the control plane does. Ask them to guess "
          "the trade-offs before you reveal each one.",
    day=4,
)

ORDER = []

# ------------------------------------------------------------------- DAY 1
ORDER += keep(1, 2)                       # title + instructor (no day marker)
ORDER += d1["roadmap4"]                   # NEW 4-day roadmap
ORDER += keep(4, 5, 6, 7, 8, 9)           # 01 The Old Way
ORDER += keep(10, 11, 12)                 # 02 Why Kubernetes
ORDER += keep(21, 22, 23, 24, 25)         # 03 Cluster Architecture  <- MOVED UP
ORDER += d1["arch_extra"]                 # NEW object model / resource hierarchy
ORDER += keep(13, 14, 18)                 # 04 Distributions (trimmed)
ORDER += keep(19, 20, 26)                 # Labs: install, cluster, inspect
ORDER += keep(27, 28, 29, 30, 31, 32)     # 05 kubectl
ORDER += d1["namespaces"]                 # NEW
ORDER += d1["labels"]                     # NEW
ORDER += keep(33, 34, 35)                 # 06 Pods
ORDER += d1["podlife"]                    # NEW
ORDER += d1["envargs"]                    # NEW
ORDER += d1["vaimages"]                   # NEW build the Voting App images
ORDER += d1["vapods"]                     # NEW Voting App as bare Pods
ORDER += d1["debug1"]                     # NEW debugging toolkit
ORDER += d1["day1end"]                    # NEW recap + interview

# ------------------------------------------------------------------- DAY 2
ORDER += d2["day2open"]
ORDER += d2["replicaset"]
ORDER += keep(36, 37)                     # Deployment concept + YAML
ORDER += d2["deploy_extra"]               # selector immutability
ORDER += d2["vadeploy"]                   # Voting App -> Deployments
ORDER += keep(38)                         # scale / roll out / roll back
ORDER += d2["rollouts"]                   # status/history/restart, maxSurge
ORDER += keep(39)                         # workloads lab
ORDER += d2["varollout"]                  # rollout + rollback on vote
ORDER += keep(40, 41, 42, 43, 44)         # Networking + Services
ORDER += d2["svc_extra"]                  # headless, Endpoints, the four ports
ORDER += d2["dns"]                        # cluster DNS deep + lab
ORDER += keep(46)                         # NodePort lab
ORDER += d2["vasvc"]                      # Services for the whole app
ORDER += d2["multicontainer"]             # multi-container, init, sidecar
ORDER += d2["vainit"]                     # init container for worker
ORDER += d2["day2end"]

# ------------------------------------------------------------------- DAY 3
ORDER += d3["day3open"]
ORDER += d3["configmap"]
ORDER += d3["secret"]
ORDER += keep(48, 49, 50)                 # Storage: ephemeral fs, volumes
ORDER += d3["emptydir_lab"]               # watch redis lose data
ORDER += keep(51, 52)                     # PV/PVC, StorageClass
ORDER += d3["storage_extra"]              # accessModes, reclaim, Pending PVC
ORDER += keep(53)                         # PVC persistence lab
ORDER += d3["vapvc"]                      # Postgres PVC
ORDER += d3["statefulset"]
ORDER += d3["probes"]                     # incl. the zero-downtime payoff lab
ORDER += d3["day3end"]

# ------------------------------------------------------------------- DAY 4
ORDER += d4["day4open"]
ORDER += d4["resources"]                  # requests/limits/QoS
ORDER += d4["scheduling"]                 # nodeSelector, affinity, taints
ORDER += d4["metrics_hpa"]                # metrics-server, top, HPA
ORDER += d4["jobs"]                       # Jobs + CronJobs
ORDER += d4["ingress"]                    # Ingress theory
ORDER += [INGRESS_LAB]                    # replaces old slide 47 (routed to nginx)
ORDER += d4["lbmetal"]                    # MetalLB -> real LoadBalancer
ORDER += d4["netpol"]                     # CNI, pod networking, NetworkPolicy
ORDER += d4["helm"]
ORDER += [DIST_DIVIDER]
ORDER += keep(15, 16, 17)                 # kubeadm / k3s / EKS deep  <- MOVED HERE
ORDER += d4["awareness"]                  # DaemonSet, RBAC, quotas
ORDER += d4["troubleshoot"]
ORDER += d4["bestpractice"]
ORDER += d4["final"]                      # final challenge
ORDER += keep(54)                         # teardown
ORDER += keep(55)                         # course recap (retitled below)
ORDER += d4["interview4"]
ORDER += keep(56)                         # closing / questions

# ------------------------------------------------------- day stamps + fixes
# Title, instructor bio and the closing slide carry no day marker; everything
# between a day's opener and the next one belongs to that day.
IDX_D2 = ORDER.index(d2["day2open"][0])
IDX_D3 = ORDER.index(d3["day3open"][0])
IDX_D4 = ORDER.index(d4["day4open"][0])

final = []
for i, sec in enumerate(ORDER):
    if i < 2 or sec is ORDER[-1]:
        final.append(re.sub(r'\s*data-day="[^"]*"', "", sec, count=1))
    elif i < IDX_D2:
        final.append(deck.set_day(sec, 1))
    elif i < IDX_D3:
        final.append(deck.set_day(sec, 2))
    elif i < IDX_D4:
        final.append(deck.set_day(sec, 3))
    else:
        final.append(deck.set_day(sec, 4))

# The kept recap slide was written for a one-day course.
final = [s.replace("The whole day in one view", "The whole course in one view")
         for s in final]

# Renumber section dividers sequentially across the whole deck.
n = 0


def _renum(m):
    global n
    n += 1
    return f'{m.group(1)}{n:02d}{m.group(3)}'


out = []
for s in final:
    out.append(re.sub(r'(<div class="div-num r">)(\d+)(</div>)', _renum, s))

count = deck.write(head, out, tail)
print(f"assembled {count} slides")
print(f"  Day 1: slides 3-{IDX_D2}")
print(f"  Day 2: slides {IDX_D2+1}-{IDX_D3}")
print(f"  Day 3: slides {IDX_D3+1}-{IDX_D4}")
print(f"  Day 4: slides {IDX_D4+1}-{count}")
print(f"  dividers renumbered: {n}")
