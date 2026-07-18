# Kubernetes Course — Curriculum Review & 4-Day Rebuild Plan

**Reviewed:** `k8s-slides.html` — 56 slides, 8 sections, 8 labs
**Target:** 4 full training days, absolute beginners → solid intermediate
**Status:** Analysis only. No slides modified.

---

## 1. Verdict

The existing deck is **a genuinely good one-day introduction** — strong diagrams, real
runnable labs, an honest narrative arc (bare metal → VM → container → Compose ceiling →
orchestrator). The writing is tight and the instructor notes are excellent. Nothing here
needs to be thrown away.

But measured against a 4-day beginner-to-intermediate syllabus it is **roughly 30% of the
required content**, and three entire required domains are missing outright:

| Domain | State |
|---|---|
| **Configuration** (ConfigMaps, Secrets) | **Absent — 0 slides** |
| **Scheduling** (requests, limits, QoS, affinity, taints) | **Absent — 0 slides** |
| **Health** (liveness, readiness, startup probes) | **Absent — 0 slides** |
| Jobs / CronJobs | Absent |
| NetworkPolicy | Absent |
| HPA / metrics-server | Absent |
| Troubleshooting toolkit (`top`, `port-forward`, `cp`) | Absent |
| **Voting App as the course project** | **Never referenced — 0 mentions** |

Every lab today uses `nginx`, `busybox` or `curlimages/curl`. The Voting App at
`voting-app/` — which is an almost perfect teaching vehicle — is entirely unused.

**Bottom line:** keep the spine, fix two sequencing inversions, add ~120 slides and ~26
labs, and re-anchor every lab onto the Voting App.

---

## 2. Coverage Matrix

Verified by extracting the rendered slide text (base64 assets stripped) and reading all 56
slides — not by title matching.

Legend: ✅ solid · 🟡 shallow / mentioned only · ❌ absent

### Kubernetes Fundamentals

| Topic | State | Evidence |
|---|---|---|
| Kubernetes architecture | ✅ | Slides 21–25, strong diagram |
| Control Plane components | ✅ | Slide 23 — all four, well explained |
| Worker Node components | ✅ | Slide 24 — kubelet / kube-proxy / runtime |
| kubectl basics | ✅ | Slides 27–32 — grammar, verbs, kubeconfig |
| Namespaces | 🟡 | One info-box aside on slide 31; used in Lab 3. **No dedicated slide.** No namespaced-vs-cluster-scoped, no quotas |
| Labels | 🟡 | Used in YAML 5×, **never taught**. No `-l` filtering, no `kubectl label` |
| Selectors | 🟡 | `matchLabels` appears in manifests; equality vs set-based never explained |
| Annotations | ❌ | Zero occurrences |
| Resource hierarchy | 🟡 | Deployment→RS→Pod shown (slide 36); no overall object model |

### Pods

| Topic | State | Evidence |
|---|---|---|
| Pod lifecycle | ❌ | No phases, no `restartPolicy`, no container states. **CrashLoopBackOff / ImagePullBackOff never explained** — this cripples troubleshooting |
| Multi-container Pods | 🟡 | One diagram box "sidecar (optional)" + one sentence (slide 34). No YAML, no lab |
| Init Containers | ❌ | Zero occurrences |
| Sidecars | 🟡 | Word appears in a diagram; pattern never taught |
| Commands vs Args | ❌ | A `command:` appears inside the Lab 7 busybox YAML, unexplained. No `args`, no ENTRYPOINT/CMD mapping |
| Environment variables | ❌ | **No `env:` anywhere in the deck.** Compose's `environment:` is shown (slide 8) but the K8s equivalent never is |

### Workloads

| Topic | State | Evidence |
|---|---|---|
| ReplicaSets | 🟡 | In the slide-36 diagram and named in prose; no dedicated slide, no YAML |
| Deployments | ✅ | Slides 36–39 — the strongest section in the deck |
| Rolling Updates | ✅ | Slide 38; `maxSurge`/`maxUnavailable` named but not tuned or demonstrated |
| Rollback | ✅ | `rollout undo`, slides 38–39 |
| `rollout history` | 🟡 | Mentioned twice in prose, never run; no `--revision`, no CHANGE-CAUSE |
| `rollout status` | ✅ | Used in labs |
| `rollout restart` | ❌ | Absent |

### Services

| Topic | State | Evidence |
|---|---|---|
| ClusterIP | ✅ | Slides 43–44 |
| NodePort | ✅ | Slide 43 + Lab 5 |
| LoadBalancer | 🟡 | Explained (43); **never done hands-on** — deck notes kind has no LB and stops there |
| Headless Services | ❌ | Absent |
| Service discovery | ✅ | Slide 45 — FQDN pattern is correct and clear |
| DNS in Kubernetes | 🟡 | CoreDNS named, FQDN shown; no `nslookup` lab, no search-domain/ndots, no Endpoints object |

### Configuration — **entire domain absent**

| Topic | State |
|---|---|
| ConfigMaps | ❌ |
| Secrets | ❌ |
| ConfigMap as env vars | ❌ |
| ConfigMap as mounted files | ❌ |
| Secret as env vars | ❌ |
| Secret as mounted volume | ❌ |

### Storage — best-covered area

| Topic | State | Evidence |
|---|---|---|
| Volumes | ✅ | Slide 50 |
| emptyDir | ✅ | Slide 50 conceptually; no lab |
| hostPath | ✅ | Slide 50 conceptually; no lab |
| PersistentVolumes | ✅ | Slide 51, good supply/demand framing |
| PVCs | ✅ | Slide 51 + Lab 7 (a genuinely good lab) |
| StorageClasses | ✅ | Slide 52 + Lab 7 |
| *Gaps* | 🟡 | accessModes (RWO/ROX/RWX) never expanded, no reclaim policy, StatefulSet mentioned once in passing |

### Networking

| Topic | State | Evidence |
|---|---|---|
| CNI overview | 🟡 | Named twice (kubeadm lab, EKS slide). **Never explained what a CNI does** |
| Pod-to-Pod communication | 🟡 | Implied by "every Pod gets an IP"; flat-network/no-NAT model never stated |
| Service networking | ✅ | Slides 42–43 |
| kube-proxy | ✅ | Slides 24, 42 — right level for beginners |
| Network Policies | ❌ | Absent |
| DNS | 🟡 | See Services |

### Scheduling — **entire domain absent**

| Topic | State |
|---|---|
| Requests | ❌ (`requests:` appears only as PVC *storage*, not CPU/memory) |
| Limits | ❌ |
| QoS classes | ❌ |
| Node Selectors | ❌ |
| Node Affinity | ❌ |
| Taints | ❌ |
| Tolerations | ❌ |

Only the scheduler's *existence* is mentioned (slide 23).

### Scaling

| Topic | State |
|---|---|
| Manual scaling | ✅ Slides 38–39 |
| HPA | ❌ One prose phrase "autoscale on CPU" (slide 11). No HPA object, no metrics-server |

### Debugging

| Topic | State | Evidence |
|---|---|---|
| `logs` | ✅ | Slides 29, 32 |
| `exec` | ✅ | Slides 29, 32 |
| `describe` | ✅ | Good emphasis: "Events tail is where 90% of failures explain themselves" |
| `events` | 🟡 | Only via `describe`; no `get events --sort-by`, no dedicated slide |
| `top` | ❌ | Absent (needs metrics-server) |
| `port-forward` | ❌ | Absent |
| `cp` | ❌ | Absent |

**No troubleshooting section and no failure-scenario labs exist at all.**

### Jobs

| Topic | State |
|---|---|
| Jobs | ❌ |
| CronJobs | ❌ |

### Production Concepts

| Topic | State | Evidence |
|---|---|---|
| Ingress | ✅ | Slide 45 + Lab 6 |
| Ingress Controller | ✅ | Lab 6 installs ingress-nginx properly |
| Helm | ❌ | Absent |
| Metrics Server | ❌ | Absent |
| Readiness Probe | ❌ | Absent |
| Liveness Probe | ❌ | Absent |
| Startup Probe | ❌ | Absent |

### Beyond the checklist — worth adding

| Topic | State | Recommendation |
|---|---|---|
| StatefulSets | 🟡 one passing mention | Day 3, intro only (justifies why `db` differs) |
| DaemonSets | ❌ | Day 4, one slide (kube-proxy is one — nice callback) |
| RBAC / ServiceAccounts | ❌ | Day 4, one slide, awareness only |
| ResourceQuota / LimitRange | ❌ | Day 4, pairs with requests/limits |

---

## 3. Critical Gaps, Ranked

1. **ConfigMaps & Secrets (whole domain).** Students cannot deploy any real app without
   these. The Voting App's `POSTGRES_PASSWORD` makes this concrete and non-contrived.
2. **Probes (whole domain).** See §5 — their absence makes an existing slide factually wrong.
3. **Requests / limits / QoS.** The #1 real-world production failure cause, and the most
   common interview question after "what is a Pod".
4. **Pod lifecycle & failure states.** Without `CrashLoopBackOff`/`ImagePullBackOff`,
   students cannot debug their own labs — they will be stuck and you will be firefighting.
5. **The Voting App is unused.** The single biggest pedagogical win available: 5 components
   that each naturally demand a different Kubernetes concept.
6. **No troubleshooting practice.** Day 4 needs planted-failure labs.
7. **Scheduling (affinity/taints), HPA, NetworkPolicy, Jobs.** Required by the syllabus,
   all absent.

---

## 4. Sequencing Problems in the Current Deck

### 4.1 Distributions taught before architecture — **the clearest inversion**
Slides 13–18 compare kubeadm / k3s / EKS on the basis of *"who runs the control plane"* —
but the control plane isn't explained until slide 22. Students are asked to choose between
installers for a thing they cannot yet describe.

Worse: the labs that follow use **kind**, which is not one of the three discussed. So the
section doesn't even serve the lab it precedes.

**Fix:** Architecture first. Keep ~2 distribution slides on Day 1 ("kind is what we use, here's
the landscape in one table"), move the deep kubeadm/k3s/EKS comparison to **Day 4**, where
students have the vocabulary to actually evaluate the trade-off.

### 4.2 Namespaces taught as a footnote to kubeconfig
Slide 31 is about contexts; namespaces appear as an info-box aside. Students then use
`kubectl create namespace` in Lab 3 having never been taught what a namespace *is*.
**Fix:** dedicated Namespace slide + lab on Day 1, *before* the kubeconfig/context slide.

### 4.3 Labels & selectors used five times before being taught
`labels: app: web` (slide 35), `selector.matchLabels` (37), Service `selector` (44). The
label→selector match is *the* core coupling mechanism in Kubernetes and it is currently
absorbed by osmosis.
**Fix:** dedicated Labels/Selectors/Annotations block on Day 1, before Pods. Then every
later manifest reinforces something already named.

### 4.4 Ingress on day one
Lab 6 (Ingress + controller install) is good, but it's a production-concern topic landing
before students have seen ConfigMaps or probes. **Fix:** move to Day 4.

### 4.5 Prerequisite chain to enforce
```
containers → why orchestration → architecture → kubectl
  → namespaces → labels/selectors
    → Pods → lifecycle → env/command/args
      → ReplicaSet → Deployment → rollouts
        → Services → DNS
          → ConfigMaps/Secrets
            → Volumes → PV/PVC/SC
              → probes
                → requests/limits → QoS → scheduling
                  → HPA (needs metrics-server + requests)
                    → Ingress → NetworkPolicy → Helm
```
Two hard dependencies students trip on: **HPA requires resource *requests*** (it computes
against them), and **NetworkPolicy requires a CNI that enforces it** (kind's default kindnet
does **not** — see §12).

---

## 5. Two Technical Defects Found

**(a) The "zero downtime" claim is currently false.**
Slides 38 and 39 both promise rolling updates give "no downtime" / "Zero downtime". Without
a **readiness probe**, Kubernetes adds a Pod to the Service the moment its container starts —
before the app can serve — so a rolling update *does* drop requests. The claim only becomes
true once probes exist. Since probes aren't in the deck, the deck currently teaches a myth.

**Fix:** either soften the claim on Day 2, or (better) keep it and pay it off on Day 3 with a
lab that demonstrates dropped requests without readiness, then fixes it. That's a memorable
teaching moment rather than an erratum.

**(b) Lab 4's self-heal command deletes every Pod, not one.**
```
kubectl delete pod -l app=web --field-selector status.phase=Running --grace-period=0 | head -1
```
`head -1` truncates the *output*, not the deletion — this deletes all 6 replicas while the
comment says "kill a pod". Self-healing still demonstrates, but it misrepresents what the
student just did.
**Fix:** `kubectl delete pod "$(kubectl get pod -l app=web -o name | head -1)"`

---

## 6. The Voting App as the Course Spine

`voting-app/` is a 5-component app — and each component naturally demands a *different*
Kubernetes concept. This is why it beats nginx examples: nothing is contrived.

```
       vote (Python/Flask :80)          result (Node.js :80)
              │                                  ▲
              ▼                                  │
          redis (queue)  ──►  worker (Java)  ──► db (Postgres)
```

| Component | Teaches | Why it's the natural fit |
|---|---|---|
| **vote** | Deployment, Service, HPA, ConfigMap, Ingress | Stateless HTTP frontend; CPU load is generatable → real HPA demo |
| **result** | Deployment, Service, readiness probe, Ingress path routing | Second frontend → forces path-based Ingress rules |
| **worker** | Deployment **without** a Service, resource limits, liveness probe, init container | Has no inbound traffic → teaches "not everything needs a Service". Crashes if db is absent → *authentic* init-container use case |
| **redis** | ClusterIP, emptyDir → PVC | Show data loss with emptyDir, then fix it. Ephemeral-vs-durable made visceral |
| **db** (Postgres) | **Secret** (`POSTGRES_PASSWORD`), ConfigMap (`POSTGRES_USER`), PVC + StorageClass, headless Service, StatefulSet intro, exec probe (`pg_isready`) | Every stateful concern in one component. The password is a *real* secret, not a toy |
| **whole app** | NetworkPolicy, Jobs/CronJobs, troubleshooting, final challenge | Policy: only vote+worker→redis, only worker+result→db. A genuine 4-tier policy |

**The evolution narrative** — the same app, deepened daily:

- **Day 1:** run `vote` + `redis` as **bare Pods**. It half-works. Kill a Pod — nothing comes back. *Feel the problem.*
- **Day 2:** convert to Deployments, add Services. **The app works end-to-end for the first time.** Roll out a new vote version, roll it back.
- **Day 3:** hardcoded password → Secret. Vote options → ConfigMap. Postgres gets a PVC (votes now survive a restart). Probes added — and the Day-2 "zero downtime" claim finally becomes true.
- **Day 4:** requests/limits on everything, HPA on `vote`, Ingress routing `/` → vote and `/result` → result, NetworkPolicy locking down the data tier, then a broken-cluster troubleshooting gauntlet and a from-scratch final challenge.

Each day ends with a **"you are here"** architecture diagram showing the app with that day's
new Kubernetes objects highlighted. That recurring visual is the strongest single addition
this course can make.

---

## 7. The 4-Day Restructure

Assumes ~6h/day with breaks ≈ 5h instruction. Target ~185 slides, ~34 labs, ~55% hands-on.

### DAY 1 — Foundations & First Contact (~46 slides, 8 labs)
| Block | Content | Source |
|---|---|---|
| 01 Why orchestration | Bare metal → VM → container → Compose → the ceiling | **Keep 4–9**, trim 1 |
| 02 What Kubernetes is | Control loop, desired state, Compose vs K8s | **Keep 10–12** |
| 03 Architecture | Control plane, workers, `kubectl apply` request flow | **Keep 21–25 — MOVED UP** |
| 04 Landscape | kind (ours) + one comparison table | **Trim 13–18 → 2 slides** |
| 🔬 Lab 1 | Install Docker/kubectl/kind | Keep 19 |
| 🔬 Lab 2 | 3-node cluster | Keep 20 |
| 🔬 Lab 3 | Inspect the cluster you built | Keep 26 |
| 05 kubectl | Grammar, verbs, imperative vs declarative, kubeconfig | Keep 27–31 |
| 06 Namespaces | **NEW** — what/why, namespaced vs cluster-scoped, DNS impact | NEW ×3 |
| 🔬 Lab 4 | **NEW** — namespaces, `-n`, default context |
| 07 Labels & Selectors | **NEW** — labels, `-l` filtering, selectors, annotations vs labels | NEW ×4 |
| 🔬 Lab 5 | **NEW** — label, filter, relabel; watch a selector follow |
| 08 Pods | The atom, YAML, **lifecycle & phases NEW**, restartPolicy, **CrashLoopBackOff/ImagePullBackOff NEW** | Keep 34–35 + NEW ×4 |
| 09 Container config | **NEW** — env vars, command vs args, ENTRYPOINT/CMD mapping | NEW ×3 |
| 🔬 Lab 6 | **NEW — Voting App as bare Pods** (vote + redis). Half-works. Kill one → gone |
| 10 Debugging I | **NEW** — describe/logs/exec/events/**port-forward**/**cp** | NEW ×4 |
| 🔬 Lab 7 | **NEW** — port-forward to `vote`, see the UI; break it, read the Events |
| 🔬 Lab 8 | **NEW** — planted failure #1: bad image tag → diagnose ImagePullBackOff |
| Wrap | Day-1 recap + "you are here" + **8 interview questions** | NEW ×2 |

### DAY 2 — Workloads & Networking (~45 slides, 8 labs)
| Block | Content | Source |
|---|---|---|
| Recap | Why bare Pods failed yesterday | NEW ×1 |
| 11 ReplicaSet | **NEW** — dedicated slide + YAML + why you don't create them directly | NEW ×2 |
| 12 Deployments | Controller, YAML, selector immutability ⚠ | Keep 36–37 + NEW ×1 |
| 🔬 Lab 9 | **Voting App: Pods → Deployments** (all 5 components) |
| 13 Rollouts | Rolling update mechanics, maxSurge/maxUnavailable, **status/history/restart/undo NEW**, CHANGE-CAUSE | Keep 38 + NEW ×3 |
| 🔬 Lab 10 | **Rolling update + rollback on `vote`**, read `rollout history` |
| 🔬 Lab 11 | Self-heal (fixed command, §5b) + `rollout restart` |
| 14 The Service problem | Pods are moving targets | Keep 41 |
| 15 Services | ClusterIP / NodePort / LoadBalancer, **Headless NEW**, **Endpoints object NEW** | Keep 42–44 + NEW ×2 |
| 16 DNS | CoreDNS, FQDN, search domains, cross-namespace | Keep 45a + NEW ×2 |
| 🔬 Lab 12 | **Services for all 5 components — app works end-to-end** 🎉 |
| 🔬 Lab 13 | **NEW** — `nslookup` from a Pod; resolve cross-namespace; inspect Endpoints |
| 17 Multi-container Pods | **NEW** — shared IP/volume, **init containers**, **sidecar pattern** | NEW ×4 |
| 🔬 Lab 14 | **NEW** — init container makes `worker` wait for `db` (real fix for a real crash) |
| 🔬 Lab 15 | **NEW** — planted failure #2: selector/label mismatch → Service with no Endpoints |
| Wrap | Recap + "you are here" + **8 interview questions** | NEW ×2 |

### DAY 3 — Configuration, Storage & Health (~48 slides, 9 labs)
| Block | Content | Source |
|---|---|---|
| 18 ConfigMaps | **NEW** — creation (literal/file/YAML), as **env**, as **mounted files**, hot-reload caveat ⚠ | NEW ×5 |
| 🔬 Lab 16 | **NEW** — vote options + `POSTGRES_USER` → ConfigMap, both injection styles |
| 19 Secrets | **NEW** — types, **base64 ≠ encryption** ⚠, as env, as volume, etcd-at-rest note | NEW ×5 |
| 🔬 Lab 17 | **NEW** — `POSTGRES_PASSWORD` → Secret; then `base64 -d` it to prove it's not encrypted |
| 20 Ephemeral storage | Pod filesystem dies; emptyDir, hostPath | Keep 49–50 |
| 🔬 Lab 18 | **NEW** — redis on emptyDir: cast votes, kill Pod, **watch data vanish** |
| 21 PV / PVC / SC | Supply vs demand, accessModes, reclaim policy, WaitForFirstConsumer ⚠ | Keep 51–52 + NEW ×2 |
| 🔬 Lab 19 | **Postgres gets a PVC — votes now survive a Pod kill** (adapt Lab 7) |
| 22 StatefulSets | **NEW** — intro only: why `db` differs, stable identity, volumeClaimTemplates | NEW ×2 |
| 23 Probes | **NEW** — liveness vs readiness vs startup, what each *fixes*, probe types, tuning ⚠ | NEW ×6 |
| 🔬 Lab 20 | **NEW** — readiness on `vote`/`result`, `pg_isready` exec probe on `db` |
| 🔬 Lab 21 | **NEW ⭐ — pay off the Day-2 promise:** roll out under `curl` load *without* readiness → see dropped requests; add readiness → zero downtime |
| 🔬 Lab 22 | **NEW** — planted failure #3: over-aggressive liveness → restart loop |
| 🔬 Lab 23 | **NEW** — planted failure #4: PVC Pending (no matching SC) |
| Wrap | Recap + "you are here" + **8 interview questions** | NEW ×2 |

### DAY 4 — Scheduling, Scaling, Production & Troubleshooting (~46 slides, 9 labs)
| Block | Content | Source |
|---|---|---|
| 24 Requests & Limits | **NEW** — scheduling vs runtime, CPU throttle vs memory OOMKill ⚠ | NEW ×4 |
| 25 QoS | **NEW** — Guaranteed/Burstable/BestEffort, eviction order | NEW ×2 |
| 🔬 Lab 24 | **NEW** — requests/limits across the Voting App; trigger an OOMKill deliberately |
| 26 Scheduling | **NEW** — nodeSelector, node affinity, taints & tolerations | NEW ×5 |
| 🔬 Lab 25 | **NEW** — pin `db` to a node; taint a node and watch scheduling change |
| 27 metrics-server + top | **NEW** — install, `kubectl top nodes/pods` | NEW ×2 |
| 28 HPA | **NEW** — control loop, why it needs *requests* ⚠ | NEW ×3 |
| 🔬 Lab 26 | **NEW** — HPA on `vote` + load generator; watch replicas climb and settle |
| 29 Jobs & CronJobs | **NEW** — run-to-completion, parallelism, schedules | NEW ×4 |
| 🔬 Lab 27 | **NEW** — DB-init Job; CronJob that snapshots the vote tally |
| 30 Ingress | Controller, host/path routing, TLS note | Keep 45b + Lab 6 → **adapt to `/`→vote, `/result`→result** |
| 🔬 Lab 28 | **Ingress for the Voting App** (adapted from existing Lab 6) |
| 31 CNI & pod networking | **NEW** — flat network model, no NAT, what a CNI plugin does | NEW ×3 |
| 32 NetworkPolicy | **NEW** — default-deny, ingress/egress rules, namespaces ≠ isolation ⚠ | NEW ×4 |
| 🔬 Lab 29 | **NEW** — lock down `db`/`redis` (⚠ needs Calico — see §12) |
| 33 Helm | **NEW** — intro only: why templating, chart anatomy, `helm install` | NEW ×3 |
| 34 Distributions revisited | kubeadm / k3s / EKS deep comparison | **MOVED from Day 1** (13–18) |
| 35 Awareness | **NEW** — DaemonSet, RBAC/ServiceAccount, ResourceQuota | NEW ×3 |
| 36 Troubleshooting | **NEW** — decision tree, the 6-step playbook | NEW ×4 |
| 🔬 Lab 30 | **NEW** — troubleshooting gauntlet: 5 planted failures, timed |
| 37 Best practices | **NEW** — production checklist + top-10 mistakes | NEW ×4 |
| 🔬 Lab 31 | **⭐ Final challenge** — deploy the whole Voting App from scratch to a written spec |
| Close | Recap, **interview questions**, next steps, contact | Keep 55–56 |

**Totals:** ~185 slides (56 kept/adapted, ~129 new), 31 labs + 3 optional stretch labs.

---

## 8. Diagram Gaps

The existing diagrams (VM/container comparison, control loop, architecture, Deployment→RS→Pod,
Service selector, PV/PVC) are strong — the new content must match that bar. Highest value first:

1. **⭐ Voting App "you are here" map** — one per day, new objects highlighted. The single most valuable visual in the course.
2. **⭐ The four ports** — `containerPort` / `targetPort` / `port` / `nodePort` on one traffic path. This is the most confused topic in all of Kubernetes.
3. **⭐ Probe timeline** — startup → readiness → liveness, showing what each failure *does* (removed from Service vs restarted).
4. **Pod lifecycle state machine** — Pending → Running → Succeeded/Failed, with the CrashLoopBackOff cycle.
5. **Label → selector matching** — how a selector "finds" Pods.
6. **ConfigMap/Secret injection** — two-column: as env vs as mounted volume.
7. **Rolling update timeline** — Pod-by-Pod with maxSurge/maxUnavailable.
8. **Service → Endpoints → Pod chain** — the missing link students never see.
9. **QoS decision tree** — requests/limits combination → class.
10. **Taints & tolerations** — lock-and-key metaphor.
11. **HPA control loop** — metrics-server → HPA → replica count.
12. **NetworkPolicy before/after** — allowed-traffic matrix for the 4 tiers.
13. **DNS resolution walkthrough** — Pod → CoreDNS → Service IP → Endpoints.
14. **Storage durability comparison** — emptyDir vs hostPath vs PVC, what survives what.
15. **Init container vs sidecar timeline** — sequential vs parallel.
16. **Namespace partitioning** — one cluster, virtual sub-clusters.
17. **Troubleshooting decision tree** — symptom → command → likely cause.

---

## 9. Where Students Will Get Confused (address explicitly)

| # | Confusion | Mitigation |
|---|---|---|
| 1 | `port` vs `targetPort` vs `nodePort` vs `containerPort` | Dedicated diagram (§8.2) + a "name the port" exercise |
| 2 | Labels vs selectors vs annotations | Side-by-side contrast slide |
| 3 | **Secrets are base64, not encrypted** | Lab 17 makes them decode it themselves |
| 4 | Liveness vs readiness | "Liveness restarts, readiness removes from traffic" — plus Lab 22's restart loop |
| 5 | Requests vs limits | "Requests schedule, limits constrain"; CPU throttles, memory OOMKills |
| 6 | ConfigMap changes don't restart Pods (env) but do update mounted files | Explicit ⚠ + `rollout restart` as the answer |
| 7 | **Namespaces are not network isolation** | State it in the Namespace slide, prove it in Lab 29 |
| 8 | Pod IP vs Service IP vs Node IP | Three-column table |
| 9 | Deployment selector is immutable | ⚠ box; they *will* hit this |
| 10 | PVC stuck Pending / WaitForFirstConsumer | Lab 23 makes it happen on purpose |
| 11 | "Zero downtime" without readiness | Lab 21 — the payoff lab |
| 12 | `emptyDir` lifetime = Pod, not container | Diagram §8.14 |
| 13 | `apply` vs `create` vs `replace` | One slide, extends existing imperative/declarative (30) |
| 14 | READY `1/1` — what the numbers mean | Call out during Day-1 debugging |
| 15 | HPA silently does nothing without requests | ⚠ on the HPA slide |

---

## 10. Best Practices, Mistakes & Interview Questions

**Per-day interview slides** (~8 questions each, 32 total), scoped to that day's material —
Day 1 architecture/kubectl/Pods, Day 2 workloads/Services, Day 3 config/storage/probes,
Day 4 scheduling/scaling/networking.

**Top-10 mistakes slide (Day 4):** no resource requests · `:latest` tags · Secrets in git ·
missing readiness probe · over-aggressive liveness · bare Pods in production · everything in
`default` namespace · no CHANGE-CAUSE on rollouts · `hostPath` for app data · no
NetworkPolicy on the data tier.

**Production checklist slide (Day 4):** pinned image tags, requests+limits set, all three probes
considered, PVCs for state, Secrets externalized, NetworkPolicy on data tier, HPA where load
varies, resource quotas per namespace, manifests in git.

---

## 11. Recommendation on Scope Tension

You listed probes under **"Production Concepts (intro only)"** but also as **Day 3 hands-on**.

**My recommendation: give probes full hands-on treatment on Day 3** (6 slides + 2 labs), not
intro-only. Reason: probes are not a "nice to know" — the deck's existing zero-downtime claim
is *false* without them (§5a), and they're the fix for the most common beginner failure mode.
Keep **Helm, metrics-server, StatefulSets, RBAC and DaemonSets** as genuine intro-only.

---

## 12. Decisions I Need From You Before Building

| # | Decision | Recommendation |
|---|---|---|
| 1 | **Container images** — Voting App builds from source (Python/Node/Java). Building 4 images per student is slow. | Use the prebuilt `dockersamples/examplevotingapp_*` images for labs; add **one optional Day-1 exercise** building `vote` locally + `kind load docker-image` as a bridge from the Docker course. |
| 2 | **NetworkPolicy needs an enforcing CNI.** kind's default *kindnet ignores NetworkPolicy* — Lab 29 would silently "pass" while enforcing nothing, teaching the wrong lesson. | Create the Day-4 cluster with `--disable-default-cni` + **Calico**, or run Day 4 on **k3s**. Must be decided before Lab 29 is written. |
| 3 | **LoadBalancer is never demonstrated** (kind has no LB). | Add **MetalLB** on Day 4, or switch to k3s (ServiceLB built in). Otherwise `type: LoadBalancer` stays theory for 4 days. |
| 4 | **Deliverable shape** — one 185-slide deck, or four day-decks? | **Four files** (`day1.html`…`day4.html`) + an index page. A 185-slide single file is unwieldy to teach from and slow to load. Pages index links all four. |
| 5 | **Voting App manifests** — students type YAML or clone it? | Ship a `k8s-manifests/day1..day4/` directory in the repo as the answer key; students type the small ones, clone the long ones. |
| 6 | Keep the existing kind-based lab track, or move to k3s? | Keep kind (labs 1–2 are solid); patch it with Calico + MetalLB for Day 4. |

---

## 13. Proposed Build Order (once approved)

Each phase = one commit, per your git-per-step preference.

| Phase | Work | Est. |
|---|---|---|
| 0 | Fix the two defects (§5) in the current deck | 1 commit |
| 1 | Split into 4 day-decks + shared CSS/JS + index page | 1 commit |
| 2 | Day 1: reorder (architecture before distributions), add namespaces/labels/pod-lifecycle/env/debugging + Voting App Lab 6 | 2–3 commits |
| 3 | Day 2: ReplicaSet, rollout subcommands, headless/Endpoints, DNS lab, multi-container/init/sidecar, Voting App Deployments+Services | 2–3 commits |
| 4 | Day 3: ConfigMaps, Secrets, storage labs, StatefulSet intro, probes + the payoff lab | 3 commits |
| 5 | Day 4: requests/limits/QoS, scheduling, metrics-server/HPA, Jobs, Ingress, CNI/NetworkPolicy, Helm, troubleshooting, final challenge | 3–4 commits |
| 6 | `k8s-manifests/` answer key for all 4 days | 1 commit |
| 7 | Diagrams pass (§8) + interview/best-practice slides | 2 commits |
| 8 | Full lab dry-run on a clean kind cluster, publish to Pages | 1 commit |

---

## 14. Summary

- The existing 56 slides are good and ~90% reusable — **keep them**.
- Three required domains are entirely absent: **Configuration, Scheduling, Health/Probes**.
- Two sequencing inversions to fix: **distributions before architecture**, **namespaces/labels taught by osmosis**.
- Two real defects: a **false zero-downtime claim** and a **lab command that deletes all Pods**.
- The **Voting App is unused** — wiring it in as the spine is the highest-value change available.
- Plan: ~129 new slides, 23 new labs, 17 new diagrams, 4 day-decks.
- **Six decisions needed from you (§12)** — items 2 and 3 (Calico, MetalLB) change the lab
  infrastructure and must be settled before Day 4 labs are written.

*No slides have been modified. Awaiting approval.*
