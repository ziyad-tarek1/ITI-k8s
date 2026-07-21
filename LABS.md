# LABS.md — ITI Kubernetes 2026, runnable lab guide

Companion to `k8s-slides.html` (209 slides). Every hands-on lab in the deck,
rewritten as a **runnable, checkable procedure** for the target machine:

```
Host visora   →   89.116.25.8   (user: ziyad)
```

**Status: none of this has ever been run on a real cluster.** That is the point
of this document. We walk it lab by lab; you run, I check.

---

## How we work through this

1. You: `ssh visora`, run **one lab** top to bottom.
2. You: write `result-lab-<NN>.md` (template at the bottom of this file) and share it.
3. Me: check it against the **Pass when** block, fix `LABS.md` **and the slides**
   if anything is wrong, and tell you whether to move on.

Do not batch labs. One lab, one result file. A silent failure in Lab 06 shows up
as a mystery in Lab 15.

### Conventions used in every lab

| Marker | Meaning |
|---|---|
| **Goal** | why this lab exists — one line |
| **Slide** | which slide(s) in the deck this covers |
| **Needs** | state that must already exist. If it doesn't, stop |
| **Pass when** | the exact condition that means it worked |
| **If it fails** | the two or three things that actually go wrong |
| ❓ **Confirm** | I am predicting output I cannot verify. Your run settles it |
| ⚠️ | destructive, or a known trap |

### Shell conventions

- Every command runs as `ziyad` on visora, **not** as root, unless it says `sudo`.
- The repo lives at `~/ITI-k8s`. The app source is `~/ITI-k8s/voting-app`.
- The cluster is called `iti`. Nodes: `iti-control-plane`, `iti-worker`, `iti-worker2`.
- The app namespace is `vote`. Throwaway experiments live in `demo`.

### Seeing a web page in your browser

`kubectl port-forward` binds to **visora's** localhost, not yours. It is invisible
from your laptop. Two ways to actually look at the app:

```bash
# A · SSH tunnel (preferred — no firewall change, works for everything)
#    run this on YOUR LAPTOP, in its own terminal, and leave it running:
ssh -L 8080:localhost:30080 visora
#    then open http://localhost:8080 in your browser

# B · straight at the VPS (only if port 30080 is open in the firewall)
#    open http://89.116.25.8:30080
```

Where a lab says *"open the app"*, it means one of those. Where a lab needs
port-forward to a Service with no NodePort (e.g. `result`), tunnel that port too:

```bash
# laptop:
ssh -L 5001:localhost:5001 visora
# visora:
kubectl port-forward svc/result 5001:80 -n vote
```

---

## Lab map

The eyebrows in the slides ("Lab 1", "Lab 9", …) are **not reliable** — several
numbers repeat and some are leftovers from the deck's original 8-lab version.
**This table is the source of truth.** `result-lab-<NN>.md` uses the NN in
column 1.

| NN | Day | Slide(s) | Goal | Destructive |
|---|---|---|---|---|
| 00 | — | — | Preflight: is visora able to host this at all? | |
| 01 | 1 | 23–24 | Install Docker, kubectl, kind; create the 3-node cluster | |
| 02 | 1 | 25 | Look inside the cluster you just built | |
| 03 | 1 | 31 | Drive the cluster: run → get → describe → logs → exec → delete | |
| 04 | 1 | 35 | Namespaces: create `vote`, make it your default | |
| 05 | 1 | 40 | Labels and selectors, live | |
| 06 | 1 | 52–54 | Build the three app images, load them into kind | |
| 07 | 1 | 55–56 | Run the app as bare Pods — then kill one | |
| 08 | 1 | 61 | See the app in a browser; prove the vote reached redis | |
| 09 | 1 | 62 | Planted failure #1 — ImagePullBackOff | |
| 10 | 2 | 72–73 | Bare Pods → five Deployments | |
| 11 | 2 | 79 | Deploy, scale, roll out, self-heal (throwaway nginx) | |
| 12 | 2 | 80–81 | Roll out `vote:v2`, read the history, undo it | |
| 13 | 2 | 92 | Cluster DNS from inside a Pod | |
| 14 | 2 | 93 | NodePort, and curl it from the VPS | |
| 15 | 2 | 94–95 | Services for all five components — **the app works end to end** | |
| 16 | 2 | 100–101 | Init container: make `worker` wait for `db` | |
| 17 | 2 | 102 | Planted failure — a Service with no Endpoints | |
| 18 | 3 | 111 | ConfigMap as env vars — and watch it go stale | |
| 19 | 3 | 112 | ConfigMap as a volume — and watch it self-update | |
| 20 | 3 | 118 | Move the Postgres password into a Secret | |
| 21 | 3 | 119 | Prove base64 is not encryption | |
| 22 | 3 | 123 | emptyDir — cast votes, kill the Pod, lose them | |
| 23 | 3 | 129 | PVC survives a Pod restart (throwaway) | |
| 24 | 3 | 130–131 | Give Postgres a PVC; kill the Pod, keep the votes | |
| 25 | 3 | 140 | Readiness probes — then break one on purpose | |
| 26 | 3 | 141 | ⭐ Zero-downtime rollout, measured | |
| 27 | 3 | 142 | Planted failure — a PVC that will never bind | |
| 28 | 4 | 151 | Requests, limits and QoS across the whole app | |
| 29 | 4 | 152 | OOMKilled, on purpose | |
| 30 | 4 | 158 | nodeSelector and taints/tolerations | |
| 31 | 4 | 163 | metrics-server on kind | |
| 32 | 4 | 164 | HPA — autoscale `vote` under load | |
| 33 | 4 | 169 | A Job and a CronJob | |
| 34 | 4 | 173 | Ingress — two hostnames, one front door | |
| 35 | 4 | 174–175 | MetalLB — a real `EXTERNAL-IP` | |
| 36 | 4 | 182 | Rebuild the cluster on Calico, restore the app | ⚠️ **wipes everything** |
| 37 | 4 | 183 | NetworkPolicy — lock down the data tier | |
| 38 | 4 | 198 | The troubleshooting gauntlet — five planted faults | |
| 39 | 4 | 203 | Final challenge — rebuild the app from scratch | |
| 40 | 4 | 205 | Tear it all down | ⚠️ |

**Not labs.** These slides are `labslide`-styled but are reference material — read
them, don't run them: 28 (kubectl verbs), 30 (contexts), 43 / 70 / 86 (manifest
anatomy), 74 (scale/rollout summary), 126 (StorageClass on AWS), 188 (kubeadm),
189 (k3s), 190 (EKS).

⚠️ **Do not run slides 188/189 on visora.** `kubeadm init` and the k3s installer
both install a system-level Kubernetes that will fight with kind for ports and
`~/.kube/config`. They are whiteboard slides.

---

## Bugs already found (before running anything)

Found by reading the slide source against the app source. Fixed in this document;
the slide fixes are tracked in the handover section.

| # | Where | Problem | Fix |
|---|---|---|---|
| B1 | Slide 80 (Lab 12) | `sed 's/Cats vs Dogs/…/' vote/templates/index.html` matches **nothing** — the template says `{{option_a}} vs {{option_b}}!`. The v2 image would be byte-identical to v1 and the whole rollout lab shows no visible change. | Lab 12 uses a sed that matches the real template |
| B2 | Slides 52 / 80 | `cd voting-app` vs `cd ~/voting-app` — two different paths, neither of which exists until the repo is cloned. | Standardised on `~/ITI-k8s/voting-app`; clone step added to Lab 01 |
| B3 | Slides 93 → 94 | Slide 93 takes `nodePort: 30080` for a throwaway `web-np` Service. Slide 94 then asks for the *same* port for `vote` → `provided port is already allocated`. The app never comes up. | Lab 11 and Lab 14 run in the `demo` namespace and clean up after themselves |
| B4 | Slide 182 (Lab 36) | Rebuilding on Calico deletes the cluster — and with it every image, Deployment, Secret, PVC and the whole of Labs 01–35. The slide does not say to restore any of it, but Lab 37 immediately probes `redis` and `db`. | Lab 36 includes a full restore procedure |

---

# Lab 00 · Preflight

**Goal** Find out, before installing anything, whether visora can host a 3-node
kind cluster plus a five-service app — and whether the ports the deck needs are free.

**Needs** SSH access to visora.

### Steps

```bash
ssh visora

# 1 · size of the box
nproc                      # CPU cores
free -h                    # RAM
df -h /                    # free disk
cat /etc/os-release | head -2

# 2 · is anything already installed?
docker --version   2>/dev/null || echo 'no docker'
kubectl version --client 2>/dev/null || echo 'no kubectl'
kind version       2>/dev/null || echo 'no kind'

# 3 · are the ports the cluster wants free?
sudo ss -tlnp | grep -E ':(80|443|30080)\s' || echo 'PORTS 80/443/30080 ARE FREE'

# 4 · is anything already listening that we might break?
sudo ss -tlnp | head -20

# 5 · can we reach the registries?
curl -sI https://registry-1.docker.io/v2/ | head -1
curl -sI https://dl.k8s.io/release/stable.txt | head -1
```

### Pass when

- `nproc` ≥ **4** and `free -h` total ≥ **8 GB**. Below that, expect trouble at
  Lab 31 (metrics-server) and Lab 36 (Calico). ⚠️ Below 4 GB, stop and tell me.
- `df -h /` shows ≥ **25 GB** free. The three images plus the Maven build cache
  plus three node containers are not small.
- Step 3 prints `PORTS 80/443/30080 ARE FREE`.
- Both `curl -sI` lines return an HTTP status (`200`, `401` for the registry is fine).

### If it fails

**Port 80 or 443 is already in use** — very likely on a live VPS running nginx,
Apache or Caddy. Do **not** stop the existing service. Tell me what is on it,
and use this alternate cluster config in Lab 01 instead:

```yaml
  extraPortMappings:
  - {containerPort: 80,    hostPort: 8080}
  - {containerPort: 443,   hostPort: 8443}
  - {containerPort: 30080, hostPort: 30080}
```

Everything then shifts: `curl localhost:8080` instead of `curl localhost:80` in
Lab 34. I will regenerate the affected labs — just tell me which ports were taken.

**Port 30080 is in use** — that one is ours to move. Tell me and I will pick another.

### Report back

`nproc`, `free -h`, `df -h /`, the OS line, and the full output of step 3.

---

# DAY 1 — from zero to a running Pod

---

## Lab 01 · Install the tooling and build the cluster

**Slides** 23, 24
**Goal** A working 3-node Kubernetes cluster on visora, plus the app source on disk.
**Needs** Lab 00 passed.

### Steps

**1 · Docker**

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

⚠️ `newgrp docker` only fixes the *current* shell. Cleanest is to log out and
back in:

```bash
exit          # back to your laptop
ssh visora    # new session, new group membership
docker ps     # must work WITHOUT sudo
```

**2 · kubectl**

```bash
curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -m0755 kubectl /usr/local/bin/kubectl
rm -f kubectl
```

**3 · kind**

```bash
curl -Lo kind https://kind.sigs.k8s.io/dl/v0.24.0/kind-linux-amd64
sudo install -m0755 kind /usr/local/bin/kind
rm -f kind

kind version && kubectl version --client
```

**4 · the course repo** *(not in the deck — see bug B2)*

```bash
cd ~
git clone https://github.com/ziyad-tarek1/ITI-k8s.git
cd ~/ITI-k8s/voting-app
ls          # vote/ result/ worker/ docker-compose.yml architecture.png
```

**5 · the cluster**

The port mappings are baked in now because you cannot add them later — changing
`extraPortMappings` means deleting and recreating the cluster.

```bash
cd ~
cat > kind.yaml <<'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs: {node-labels: "ingress-ready=true"}
  extraPortMappings:
  - {containerPort: 80,    hostPort: 80}
  - {containerPort: 443,   hostPort: 443}
  - {containerPort: 30080, hostPort: 30080}
- role: worker
- role: worker
EOF

kind create cluster --name iti --config kind.yaml
kubectl get nodes
```

### Pass when

```
NAME                 STATUS   ROLES           AGE   VERSION
iti-control-plane    Ready    control-plane   1m    v1.31.x
iti-worker           Ready    <none>          1m    v1.31.x
iti-worker2          Ready    <none>          1m    v1.31.x
```

All three **Ready**. Takes 1–3 minutes; nodes are `NotReady` for the first ~30s
while kindnet starts — that is normal.

Also: `docker ps` shows 3 containers named `iti-*`.

### If it fails

- `Cannot connect to the Docker daemon` → step 1's group change did not take. Re-`ssh`.
- `port is already allocated` → Lab 00's port check was wrong or something started
  since. Run `sudo ss -tlnp | grep -E ':(80|443|30080)'`, then
  `kind delete cluster --name iti` and use the alternate mapping from Lab 00.
- Nodes stuck `NotReady` past 3 minutes → `kubectl -n kube-system get pods` and
  send me the output.
- `too many open files` / inotify errors → known kind issue on small VPSes:
  ```bash
  sudo sysctl -w fs.inotify.max_user_watches=524288
  sudo sysctl -w fs.inotify.max_user_instances=512
  ```
  Then delete and recreate the cluster.

### Report back

`kind version`, `kubectl version --client`, `kubectl get nodes`, `docker ps`.

---

## Lab 02 · Look inside the cluster you built

**Slide** 25
**Goal** Connect every box in the architecture diagram to a real process.
**Needs** Lab 01.

### Steps

```bash
# the control plane runs as Pods here
kubectl get pods -n kube-system

# the "nodes" are Docker containers on this VPS
docker ps --format 'table {{.Names}}\t{{.Image}}'

# the containers inside one node
docker exec iti-control-plane crictl ps | head

# which node is each system Pod on?
kubectl get pods -n kube-system -o wide
```

### Pass when

`kubectl get pods -n kube-system` lists all of:
`etcd-iti-control-plane`, `kube-apiserver-iti-control-plane`,
`kube-controller-manager-iti-control-plane`, `kube-scheduler-iti-control-plane`,
two `coredns-*`, three `kube-proxy-*`, three `kindnet-*` — every one `Running`.

The `-o wide` output shows the four control-plane components **only** on
`iti-control-plane`, and `kube-proxy`/`kindnet` on **all three** nodes. That
contrast is the teaching point.

### Teaching note

Ask the students: *why are there three `kube-proxy` Pods but only one `etcd`?*
Answer: kube-proxy is a DaemonSet — one per node, because every node needs to
program its own iptables. etcd is the single source of truth.

### Report back

Both `kubectl get pods -n kube-system` outputs and `docker ps`.

---

## Lab 03 · Drive the cluster

**Slide** 31
**Goal** The everyday loop: run → get → describe → logs → exec → delete.
**Needs** Lab 01.

### Steps

```bash
kubectl create namespace demo
kubectl config set-context --current --namespace=demo

kubectl run tmp --image=nginx:1.27
kubectl get pods -o wide

# the debugging trio
kubectl describe pod tmp | sed -n '/Events/,$p'
kubectl logs tmp
kubectl exec -it tmp -- curl -s localhost | head -3
```

❓ **Confirm** — `nginx:1.27` is Debian-based and *should* have `curl`. If
`exec ... curl` says `command not found`, use this instead and tell me:

```bash
kubectl exec -it tmp -- sh -c 'apt-get update -qq && apt-get install -y -qq curl >/dev/null && curl -s localhost | head -3'
```

```bash
kubectl delete pod tmp
```

### Pass when

- `kubectl get pods -o wide` → `tmp  1/1  Running`, with a Pod IP and a node name.
- `describe` Events show `Scheduled → Pulling → Pulled → Created → Started`.
- `logs` shows nginx's startup lines (`/docker-entrypoint.sh: Configuration complete`).
- `exec ... curl` prints `<!DOCTYPE html>` / `<title>Welcome to nginx!</title>`.

### Teaching note

`kubectl run` creates a **bare Pod** — no controller. That is deliberate here and
is the setup for Lab 07's punchline.

### Report back

All six command outputs.

---

## Lab 04 · Namespaces

**Slide** 35
**Goal** Build the namespace the Voting App lives in for four days, and stop typing `-n`.
**Needs** Lab 03.

### Steps

```bash
kubectl create namespace vote
kubectl get namespace
kubectl describe namespace vote

# run something in it explicitly
kubectl run tmp --image=nginx:1.27 -n vote
kubectl get pods                 # your default is still `demo` — tmp is NOT here
kubectl get pods -n vote         # there it is
kubectl get pods -A              # every namespace at once

# make vote the default for THIS context
kubectl config set-context --current --namespace=vote
kubectl config view --minify | grep namespace

kubectl get pods                 # now it just works
kubectl delete pod tmp
```

### Pass when

- `kubectl get namespace` lists `default`, `demo`, `kube-node-lease`,
  `kube-public`, `kube-system`, `vote`.
- The pair of `get pods` calls is the whole lesson: `No resources found in demo
  namespace.` then `tmp 1/1 Running`.
- After `set-context`, `kubectl config view --minify | grep namespace` prints
  `namespace: vote`, and the bare `kubectl get pods` now finds `tmp`.

### If it fails

`kubectl get pods` in step 2 shows `tmp` → your default was never `demo`. Re-run
Lab 03's `set-context`, then start this lab over.

### ⚠️ Carry-forward

**Your default namespace is now `vote` and stays that way through Lab 35.** Every
later lab assumes it. If you open a fresh shell it is still `vote` — the setting
lives in `~/.kube/config`, not in the shell.

### Report back

Both `get pods` outputs (the contrast), and `kubectl config view --minify | grep namespace`.

---

## Lab 05 · Labels and selectors

**Slide** 40
**Goal** Watch a selector follow a Pod in and out of a set, live. **Two terminals.**
**Needs** Lab 04 (default namespace = `vote`).

### Steps

**Terminal 1:**

```bash
kubectl run web-1 --image=nginx:1.27 -l app=web,env=dev
kubectl run web-2 --image=nginx:1.27 -l app=web,env=prod
kubectl run cache --image=redis:alpine -l app=cache

kubectl get pods --show-labels
kubectl get pods -l app=web
kubectl get pods -l app=web,env=prod
kubectl get pods -l 'env in (dev, prod)'
kubectl get pods -L app,env        # labels as COLUMNS, not a filter

# now WATCH the selector — leave this running
kubectl get pods -l app=web -w
```

**Terminal 2** (`ssh visora` again):

```bash
kubectl label pod cache app=web --overwrite   # watch terminal 1
kubectl label pod cache app=cache --overwrite # and back out
kubectl label pod web-1 env-                  # remove a label
```

**Terminal 1:** `Ctrl-C`, then clean up:

```bash
kubectl delete pod web-1 web-2 cache
```

### Pass when

- `-l app=web` → 2 Pods. `-l app=web,env=prod` → 1 Pod (`web-2`).
  `-l 'env in (dev, prod)'` → 2 Pods.
- `-L app,env` shows **all three** Pods with APP and ENV columns — `cache` has an
  empty ENV. This is the difference between `-l` (filter) and `-L` (display).
- **The moment that matters:** when terminal 2 relabels `cache` to `app=web`,
  terminal 1's watch prints a `cache` line. When it is relabelled back, the watch
  shows it leave. *Nothing about the Pod changed — only its label.*

### If it fails

`kubectl label pod web-1 tier-` removes a label named `tier`, which `web-1` never
had → `label "tier" not found`. That was bug B5; the slide now says `env-`, which
`web-1` actually has. If your copy of the deck still says `tier-`, you are on an
old build.

### Teaching note

This is the mechanism behind Services (Lab 15), Deployments (Lab 10) and
NetworkPolicy (Lab 37). Every one of them is *just a label selector*. Spend the
time here.

### Report back

`kubectl get pods -L app,env`, and what terminal 1's watch printed while terminal
2 relabelled `cache`.

---

## Lab 06 · Build the three images and load them into kind

**Slides** 52, 53, 54
**Goal** Three local images the cluster can actually see.
**Needs** Lab 01 (repo cloned), Lab 04.

⏱ **The Java worker build is 5–15 minutes on a cold Maven cache.** It starts
first, in the background, and you teach the other two while it runs. Do not
reorder this lab.

### Steps

**1 · start the slow one first**

```bash
cd ~/ITI-k8s/voting-app
ls          # vote/ result/ worker/ docker-compose.yml

docker build -t iti/worker:v1 ./worker > /tmp/worker.log 2>&1 &

jobs                        # [1]+ Running
tail -f /tmp/worker.log     # peek; Ctrl-C stops watching, NOT the build
```

**2 · vote — Python/Flask, fast**

```bash
docker build -t iti/vote:v1 ./vote
```

`python:3.11-slim` + `pip install`. Note the Dockerfile's `CMD`: gunicorn binds
**:80**, not :5000. That is why every manifest later says `containerPort: 80`.

**3 · result — Node, multi-stage**

```bash
docker build -t iti/result:v1 ./result
```

The Dockerfile is `base → dev → prod`. A plain build stops at the **last** stage,
`prod`. ⚠️ Do **not** pass `--target dev` — that stage is for `docker compose`
(nodemon, dev dependencies) and it is the single most common mistake here.

**4 · collect all three**

```bash
wait                        # blocks until the worker build finishes
tail -20 /tmp/worker.log
docker images | grep iti/
```

**5 · load them into the cluster** — mandatory, and the step everyone forgets

```bash
kind load docker-image iti/vote:v1   --name iti
kind load docker-image iti/result:v1 --name iti
kind load docker-image iti/worker:v1 --name iti

# prove they landed on the node itself
docker exec iti-control-plane crictl images | grep iti/
docker exec iti-worker        crictl images | grep iti/
```

### Pass when

- `docker images | grep iti/` shows exactly three: `iti/vote:v1`,
  `iti/result:v1`, `iti/worker:v1`.
- `tail -20 /tmp/worker.log` ends in `BUILD SUCCESS` and
  `naming to docker.io/iti/worker:v1`.
- `crictl images` on **both** nodes lists all three. If a node is missing them,
  a Pod scheduled there will `ErrImageNeverPull` and you will lose 20 minutes.

### If it fails

- Worker build dies with a Maven network error → re-run just that build:
  `docker build -t iti/worker:v1 ./worker`. The layer cache means the retry is fast.
- `docker build` `permission denied` → the docker group again; re-`ssh`.
- Disk full mid-build → `docker system prune -af` and check `df -h /`.

### Teaching note

`kind load` exists because the kind nodes have their **own** container runtime
(containerd). Your `docker images` list is on the host and is invisible to them.
Ask the class where they think the image lives — it is the cleanest way to teach
that a node is a real machine with its own disk.

### Report back

`docker images | grep iti/`, the last 20 lines of `/tmp/worker.log`, both
`crictl images` outputs, and **how long the worker build took**.

---

## Lab 07 · Run the app as bare Pods, then kill one

**Slides** 55, 56
**Goal** Feel the problem that Deployments exist to solve.
**Needs** Lab 06.

### Steps

**1 · two Pods and a Service**

```bash
cd ~
cat > day1-pods.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata: {name: redis, labels: {app: redis}}
spec:
  containers:
    - name: redis
      image: redis:alpine
      ports: [{containerPort: 6379}]
---
apiVersion: v1
kind: Service          # so the DNS name "redis" exists
metadata: {name: redis}
spec:
  selector: {app: redis}
  ports: [{port: 6379, targetPort: 6379}]
---
apiVersion: v1
kind: Pod
metadata: {name: vote, labels: {app: vote}}
spec:
  containers:
    - name: vote
      image: iti/vote:v1
      imagePullPolicy: IfNotPresent   # MANDATORY for kind-loaded images
      ports: [{containerPort: 80}]
EOF

kubectl apply -f day1-pods.yaml -n vote
kubectl get pods -n vote -o wide
kubectl get svc,endpoints -n vote

kubectl logs vote -n vote
kubectl exec redis -n vote -- redis-cli ping
```

**2 · now break it**

```bash
kubectl get pods -n vote
kubectl delete pod redis -n vote

kubectl get pods -n vote               # only "vote" is left
kubectl get endpoints redis -n vote    # ENDPOINTS: <none>

kubectl get pods -n vote -w            # wait as long as you like. Ctrl-C.
```

**3 · the only repair you have today**

```bash
kubectl apply -f day1-pods.yaml -n vote
kubectl get pods -n vote
```

### Pass when

- Step 1: both Pods `1/1 Running`. `kubectl logs vote` shows gunicorn
  `Listening at: http://0.0.0.0:80`. `redis-cli ping` → `PONG`.
- `kubectl get endpoints redis` shows a real Pod IP, e.g. `10.244.1.5:6379`.
- **Step 2 is the lesson:** after deleting `redis`, `get pods` shows only `vote`,
  `get endpoints redis` shows `<none>`, and the watch prints **nothing, forever**.
  No controller owns a bare Pod, so nothing replaces it.
- Step 3 brings it back — by hand. At 3am. That is the point.

### If it fails

`ErrImageNeverPull` or `ImagePullBackOff` on `vote` → Lab 06 step 5 did not reach
the node that Pod landed on. Check `kubectl get pod vote -o wide` for the node,
then `docker exec <that-node> crictl images | grep iti/`.

### Teaching note

Ask before deleting: *"how long until Kubernetes brings redis back?"* Most
students say "a few seconds". Let the watch run for a full minute in silence.
That silence is worth more than a slide.

### Report back

`get pods` + `get endpoints redis` **before and after** the delete, and confirm
the watch stayed empty.

---

## Lab 08 · See the app in a browser

**Slide** 61
**Goal** First sight of the app you built, running in Kubernetes — then prove the
vote really reached redis.
**Needs** Lab 07 step 3 (both Pods back).

### Steps

**On your laptop**, in its own terminal — leave it running:

```bash
ssh -L 8080:localhost:8080 visora
```

**In that SSH session** (this is terminal 1 on visora):

```bash
kubectl get pods -n vote      # both Running
kubectl port-forward pod/vote 8080:80 -n vote
# Forwarding from 127.0.0.1:8080 -> 80   <- leave running
```

**Open `http://localhost:8080` in your laptop's browser.** Vote a few times.

**Terminal 2** (`ssh visora` again):

```bash
curl -s localhost:8080 | grep -i -E 'cats|dogs'

# count what redis actually received
kubectl exec redis -n vote -- redis-cli llen votes
kubectl exec redis -n vote -- redis-cli lrange votes 0 -1

kubectl logs vote -n vote -f      # watch requests arrive; Ctrl-C
```

### Pass when

- The browser shows the **Cats vs Dogs** page and clicking a button highlights it.
- `curl ... | grep -i -E 'cats|dogs'` prints the two button lines.
- `redis-cli llen votes` equals the number of times you voted.
- `lrange votes 0 -1` shows JSON like
  `{"voter_id": "3f8c…", "vote": "a"}` — one per vote.
- `kubectl logs vote -f` prints a gunicorn access line per click.

### If it fails

- Browser shows nothing → the tunnel and the port-forward are two separate hops.
  Both must be running. Test the inner hop first with `curl -s localhost:8080`
  **on visora**.
- Page loads but voting shows an error → redis is gone. `kubectl get pods -n vote`.
- `llen votes` → `(integer) 0` but the page worked → you voted via GET, not POST.
  Click the buttons, don't just reload.

### Teaching note

Nothing writes to Postgres yet — `worker` is not deployed until Day 2. Votes pile
up in a redis list. Show `llen` growing; it makes the queue real, and it sets up
Lab 22 (where those queued votes get destroyed).

### Report back

`llen votes`, `lrange votes 0 -1`, and confirm the browser worked through the tunnel.

---

## Lab 09 · Planted failure #1

**Slide** 62
**Goal** Diagnose a broken Pod with the toolkit, in order, without being told the answer.
**Needs** Lab 08.

⚠️ **Students: do not read past step 1 until you have run step 2 yourself.**

### Steps

**1 · plant it**

```bash
kubectl run broken -n vote \
  --image=iti/vote:v99 \
  --image-pull-policy=IfNotPresent

kubectl get pod broken -n vote
```

**2 · your turn — diagnose it**

```bash
kubectl logs broken -n vote
kubectl describe pod broken -n vote | sed -n '/Events/,$p'
kubectl get events -n vote --sort-by=.lastTimestamp | tail -5

docker images | grep iti/vote
docker exec iti-control-plane crictl images | grep iti/vote
```

**3 · clean up**

```bash
kubectl delete pod broken -n vote
```

### Pass when

- `get pod broken` → `0/1  ErrImageNeverPull` or `ImagePullBackOff`.
  ❓ **Confirm which one you get.** With `IfNotPresent` and a tag that exists in
  no registry, I expect the kubelet to *try* the registry and land on
  `ImagePullBackOff`. If you see `ErrImageNeverPull` instead, tell me — the slide
  says `ImagePullBackOff` and I will correct it.
- `kubectl logs broken` → `Error from server (BadRequest): container "broken" in
  pod "broken" is waiting to start: trying and failing to pull image`.
  **The logs are empty because the container never started.** That is the lesson:
  logs are the *second* place to look, not the first.
- `describe … Events` names the cause outright: `Failed to pull image
  "iti/vote:v99"` / `manifest unknown`.
- `docker images | grep iti/vote` → `v1` only. `crictl images` → `v1` only.
  The tag simply does not exist.

### Teaching note

The order is the whole lab: **describe first, logs second.** A Pod that never
started has no logs to give you. Make them run `logs` first and fail, so the
lesson lands.

### Report back

`kubectl get pod broken`, the exact `logs` error, and the Events block.
---

# DAY 2 — controllers, and making the app actually work

---

## Lab 10 · Bare Pods → five Deployments

**Slides** 72, 73
**Goal** Same containers, same namespace — now with an owner.
**Needs** Lab 09 cleaned up, images loaded (Lab 06).

⚠️ **Order matters.** Delete the bare Pods *first*. Day 1 left Pods labelled
`app=vote` and `app=redis` plus a `redis` Service. If you apply the Deployments
first, the `redis` Service selector matches **both** the leftover bare Pod and
the new Deployment's Pods — half your traffic goes to a Pod nothing manages.

### Steps

**1 · clear yesterday's bare Pods**

```bash
kubectl config set-context --current --namespace=vote
kubectl get pods

kubectl delete pod --all
kubectl get pods            # No resources found in vote namespace.
```

**2 · vote, now as a Deployment**

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata: {name: vote, namespace: vote}
spec:
  replicas: 2
  selector:
    matchLabels: {app: vote}      # which Pods are mine
  template:
    metadata:
      labels: {app: vote}         # MUST match the selector
    spec:
      containers:
        - name: vote
          image: iti/vote:v1
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 80
EOF

kubectl get deploy,rs,pods -l app=vote
```

**3 · the two images you built**

Note: no `ports:` on `worker`. Nothing ever calls it, so it will never get a
Service either.

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata: {name: result}
spec:
  selector: {matchLabels: {app: result}}
  template:
    metadata: {labels: {app: result}}
    spec: {containers: [{name: result, image: "iti/result:v1",
      imagePullPolicy: IfNotPresent, ports: [{containerPort: 80}]}]}
---
apiVersion: apps/v1
kind: Deployment
metadata: {name: worker}
spec:
  selector: {matchLabels: {app: worker}}
  template:
    metadata: {labels: {app: worker}}
    spec: {containers: [{name: worker, image: "iti/worker:v1",
      imagePullPolicy: IfNotPresent}]}
EOF
```

**4 · the two off-the-shelf images**

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata: {name: redis}
spec:
  selector: {matchLabels: {app: redis}}
  template:
    metadata: {labels: {app: redis}}
    spec: {containers: [{name: redis, image: "redis:alpine",
      ports: [{containerPort: 6379}]}]}
---
apiVersion: apps/v1
kind: Deployment
metadata: {name: db}
spec:
  selector: {matchLabels: {app: db}}
  template:
    metadata: {labels: {app: db}}
    spec: {containers: [{name: db, image: "postgres:14",
      env: [{name: POSTGRES_PASSWORD, value: postgres}]}]}
EOF

kubectl get deploy
kubectl get pods -o wide
```

**5 · now kill one and watch the difference**

```bash
kubectl delete pod -l app=redis
kubectl get pods -l app=redis
```

### Pass when

- `kubectl get deploy` → five rows, every one `READY 1/1` except `vote` at `2/2`.
- `kubectl get pods` → six Pods `Running` (2× vote, 1 each of result, worker,
  redis, db).
- **Step 5 is the payoff:** a replacement redis Pod, with a *new name*, appears
  within seconds. Contrast this out loud with Lab 07.

### If it fails

- `worker` is `CrashLoopBackOff` or restarting → **expected and fine right now.**
  There is no `db` *Service* yet, so it cannot resolve the hostname. Lab 15 fixes
  it. Do not chase this.
- `db` `CrashLoopBackOff` → check `kubectl logs deploy/db`. Postgres refuses to
  start without `POSTGRES_PASSWORD`; make sure step 4 applied cleanly.
- `vote` `ErrImageNeverPull` → Lab 06 step 5.

### ❓ Confirm

What state is `worker` in at the end of this lab — `Running`, `Error`, or
`CrashLoopBackOff`? `Worker.java` loops waiting for the DB rather than exiting,
so I expect **`1/1 Running` while doing nothing at all** — which is exactly the
dishonest-health-signal that Lab 16 fixes. Send me `kubectl get pods -l
app=worker` and `kubectl logs deploy/worker --tail=20`.

### Report back

`kubectl get deploy`, `kubectl get pods -o wide`, and the before/after of step 5.

---

## Lab 11 · Deploy, scale, roll out, self-heal

**Slide** 79
**Goal** The full lifecycle of a workload, on a throwaway app, in eight commands.
**Needs** Lab 03 (the `demo` namespace).

⚠️ **This lab runs in `demo`, not `vote`** — see bug B3. Everything here is
disposable and must not touch the Voting App.

### Steps

```bash
kubectl create deployment web --image=nginx:1.27 --replicas=3 -n demo
kubectl get pods -l app=web -n demo -o wide

# scale out
kubectl scale deploy/web --replicas=6 -n demo
kubectl get pods -l app=web -n demo

# rolling update, then watch it
kubectl set image deploy/web nginx=nginx:1.29 -n demo
kubectl rollout status deploy/web -n demo

# bad release? one command back
kubectl rollout undo deploy/web -n demo
kubectl rollout status deploy/web -n demo

# self-heal: kill a Pod, watch it return
kubectl delete pod "$(kubectl get pod -l app=web -n demo -o name | head -1)" -n demo
kubectl get pods -l app=web -n demo -w      # Ctrl-C when the replacement is Running
```

### Pass when

- 3 Pods → 6 Pods after the scale.
- `rollout status` → `deployment "web" successfully rolled out`, and
  `kubectl get pods -l app=web -n demo -o jsonpath='{.items[0].spec.containers[0].image}'`
  → `nginx:1.29`, then `nginx:1.27` after the undo.
- The watch shows the deleted Pod go `Terminating` and a **new Pod name** appear
  and reach `Running` — count stays at 6 the whole time.

### Teaching note

`kubectl create deployment` is imperative and fine for demos. Everything the
Voting App uses is `apply -f`. Say why: the YAML is reviewable, diffable and
lives in git; the imperative command lives in one person's shell history.

### Report back

Pod counts at each stage, both image values, and the self-heal watch.

---

## Lab 12 · Roll out `vote:v2`, then undo it

**Slides** 80, 81
**Goal** A real image, a real rolling update, and one command back.
**Needs** Lab 10.

### Steps

**1 · build v2 with a visible change**

⚠️ The slide's `sed` is wrong (bug B1) — it looks for the literal text
`Cats vs Dogs`, but the template contains Jinja placeholders. Use this:

```bash
cd ~/ITI-k8s/voting-app

grep -n 'option_b' vote/templates/index.html      # see what you are editing

sed -i 's|{{option_b}}!|{{option_b}}! (v2)|g' vote/templates/index.html

grep -n 'v2' vote/templates/index.html            # must show 2 changed lines
```

```bash
docker build -t iti/vote:v2 ./vote
kind load docker-image iti/vote:v2 --name iti

docker exec iti-worker crictl images | grep vote
```

**2 · ship it, with a reason attached**

Two panes. **Pane B** first, so you can watch:

```bash
# PANE B
kubectl get pods -l app=vote -w
```

```bash
# PANE A
kubectl set image deploy/vote vote=iti/vote:v2

kubectl annotate deploy/vote --overwrite \
  kubernetes.io/change-cause="vote v2: heading change"

kubectl rollout status deploy/vote
kubectl get rs -l app=vote
```

**3 · read the history**

```bash
kubectl rollout history deploy/vote
kubectl rollout history deploy/vote --revision=1

kubectl get pods -l app=vote -o jsonpath='{.items[*].spec.containers[0].image}'; echo
```

**4 · undo**

```bash
kubectl rollout undo deploy/vote
kubectl rollout status deploy/vote

kubectl rollout history deploy/vote
kubectl get rs -l app=vote

kubectl rollout restart deploy/vote        # just to watch a clean restart
```

### Pass when

- `grep -n 'v2'` after the sed shows **2** lines (the `<title>` and the `<h3>`).
  If it shows 0, stop — the build will be pointless.
- `crictl images | grep vote` on `iti-worker` lists both `v1` and `v2`.
- Pane B shows the rolling update: new Pods `Pending → ContainerCreating →
  Running` **before** old ones go `Terminating`. Never all-down-then-all-up.
- `kubectl get rs -l app=vote` → **two** ReplicaSets, old one at `0  0  0`.
- `rollout history` →
  ```
  REVISION  CHANGE-CAUSE
  1         <none>
  2         vote v2: heading change
  ```
- The jsonpath prints `iti/vote:v2 iti/vote:v2` before the undo, `iti/vote:v1
  iti/vote:v1` after.
- After the undo, history shows revisions **2 and 3** — revision 1 is *renumbered*,
  not restored. Students always get this wrong; point at it.

### If it fails

- `rollout status` hangs → `kubectl get pods -l app=vote` and
  `kubectl describe pod <new-pod>`. Almost always the `kind load` was skipped.
- History shows `<none>` for revision 2 → you annotated after the rollout had
  already recorded. Harmless; the annotation only labels *future* revisions.

### Teaching note

The undo is instant because **nothing is rebuilt** — the old ReplicaSet was never
deleted, only scaled to zero. Show `get rs` before and after: the same ReplicaSet
name goes `0 → 2`. That is the entire mechanism.

### Report back

The `grep -n 'v2'` output, `get rs -l app=vote` before and after, both
`rollout history` outputs, and both jsonpath image lists.

---

## Lab 13 · Cluster DNS

**Slide** 92
**Goal** Names in, IPs out — then match those IPs to the Endpoints object by hand.
**Needs** Lab 10 (the `redis` Service from Day 1 still exists).

### Steps

**1 · from inside a Pod**

```bash
kubectl run dnsutils -n vote --rm -it --restart=Never \
  --image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.3 -- /bin/sh
```

Inside the Pod:

```sh
cat /etc/resolv.conf

nslookup redis
nslookup redis.vote.svc.cluster.local

nslookup kubernetes.default
nslookup kube-dns.kube-system.svc.cluster.local

dig +search +short redis
exit
```

**2 · from your terminal**

```bash
kubectl -n kube-system get pods -l k8s-app=kube-dns
kubectl -n kube-system get svc kube-dns
kubectl -n kube-system get cm coredns -o jsonpath='{.data.Corefile}'; echo

kubectl -n vote get endpoints redis
kubectl -n vote get svc redis -o wide
```

### Pass when

- `/etc/resolv.conf` inside the Pod shows
  `nameserver 10.96.0.10` and
  `search vote.svc.cluster.local svc.cluster.local cluster.local`.
  **That search list is why the short name works.**
- `nslookup redis` and `nslookup redis.vote.svc.cluster.local` return the **same**
  ClusterIP.
- The returned IP equals the `CLUSTER-IP` in `kubectl get svc redis` — *not* the
  Pod IP in `get endpoints redis`. The Service IP is stable; the endpoint IP is not.
- `nslookup kubernetes.default` works (2 of the 3 search suffixes complete it),
  and the fully-qualified `kube-dns.kube-system.svc.cluster.local` also works.

❓ **Confirm** — the `jessie-dnsutils:1.3` image is old. If it fails to pull, use:

```bash
kubectl run dnsutils -n vote --rm -it --restart=Never --image=busybox:1.28 -- sh
```

`busybox:1.28` is the version whose `nslookup` still behaves; newer busybox tags
have a broken one. Tell me which you had to use.

### Teaching note

Walk the chain out loud once: *name → CoreDNS → ClusterIP → kube-proxy → Endpoints
→ Pod IP.* Then show `get endpoints redis` and delete the redis Pod in another
pane — the endpoint IP changes, the ClusterIP does not. That is the whole value
of a Service in ten seconds.

### Report back

`/etc/resolv.conf`, both `nslookup redis*` results, and `get svc redis` +
`get endpoints redis` side by side.

---

## Lab 14 · NodePort, and curl it from the VPS

**Slide** 93
**Goal** Reach a Pod from outside the cluster.
**Needs** Lab 11 (`web` Deployment in `demo`).

⚠️ Runs in `demo`, and **must clean up** — it borrows nodePort 30080, which the
Voting App claims in Lab 15 (bug B3).

### Steps

```bash
cat <<'EOF' | kubectl apply -n demo -f -
apiVersion: v1
kind: Service
metadata: {name: web-np}
spec:
  type: NodePort
  selector: {app: web}
  ports:
  - {port: 80, targetPort: 80, nodePort: 30080}
EOF

kubectl get svc,endpoints -n demo

# from inside the cluster, by name
kubectl run c --rm -it --image=curlimages/curl --restart=Never -n demo \
  -- curl -s http://web-np | head -n1

# from the VPS host — kind mapped 30080 to the host
curl -s http://localhost:30080 | head -n1
```

**Clean up — do not skip:**

```bash
kubectl delete svc web-np -n demo
kubectl get svc -A | grep 30080 || echo 'port 30080 is free again'
```

### Pass when

- `get endpoints web-np -n demo` lists **6** Pod IPs (the 6 nginx replicas).
- Both curls print `<!DOCTYPE html>`.
- After cleanup, `kubectl get svc -A | grep 30080` finds nothing.

### If it fails

- `curl localhost:30080` refused, but the in-cluster curl worked → the host port
  mapping. `docker port iti-control-plane` must list `30080/tcp`. If it does not,
  your cluster was created without the `extraPortMappings` — recreate it (Lab 01).
- ⚠️ If you forget the cleanup, Lab 15 fails with `provided port is already
  allocated`. That error message is the receipt.

### Teaching note

NodePort opens the port on **every** node, not just the one running the Pod. Prove
it: `curl` the node that has no `web` Pod on it. kube-proxy forwards it. Students
assume NodePort means "the port is on that machine".

### Report back

`get endpoints web-np -n demo`, both curl outputs, and the cleanup confirmation.

---

## Lab 15 · The app comes alive

**Slides** 94, 95
**Goal** The first time the whole thing works end to end.
**Needs** Lab 10, and **Lab 14 cleaned up**.

### Steps

**1 · four Services — `worker` gets none**

```bash
kubectl get svc -A | grep 30080 || echo 'good, 30080 is free'

cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Service
metadata: {name: redis}      # NAME IS LOAD-BEARING
spec: {selector: {app: redis}, ports: [{port: 6379, targetPort: 6379}]}
---
apiVersion: v1
kind: Service
metadata: {name: db}         # NAME IS LOAD-BEARING
spec: {selector: {app: db}, ports: [{port: 5432, targetPort: 5432}]}
---
apiVersion: v1
kind: Service
metadata: {name: vote}       # NodePort so a browser can reach it
spec: {type: NodePort, selector: {app: vote},
  ports: [{port: 80, targetPort: 80, nodePort: 30080}]}
EOF

kubectl expose deploy/result --name=result --port=80 --target-port=80
```

**2 · verify the wiring before you use it**

```bash
kubectl get svc,endpoints
```

**Every Service must show real IPs under ENDPOINTS.** A Service with `<none>` is
a Service that does nothing — that is Lab 17's entire subject.

**3 · use it**

```bash
curl -s http://localhost:30080 | head -n 20

# the worker should now be doing its job
kubectl logs -l app=worker --tail=20
```

Open the app: `ssh -L 8080:localhost:30080 visora` on your laptop, then
`http://localhost:8080`. Vote a few times.

`result` has no NodePort, so forward it:

```bash
# laptop:   ssh -L 5001:localhost:5001 visora
# visora:
kubectl port-forward svc/result 5001:80
# then open http://localhost:5001
```

### Pass when

- `kubectl get endpoints` → **four** Services, every one with at least one
  `IP:port`. `vote` has two (2 replicas).
- `curl localhost:30080` returns the voting page HTML.
- `kubectl logs -l app=worker` shows `Processing vote for 'a' by '3f8c…'` — one
  line per vote you cast. **This is the moment the app is real:** browser →
  vote → redis → worker → postgres → result.
- The `result` page shows your votes, and the percentage bar moves as you vote.

### If it fails

- `provided port is already allocated` → Lab 14 cleanup. `kubectl get svc -A |
  grep 30080`, delete the offender, re-apply.
- `worker` logs show connection errors → check `kubectl get endpoints db`. If it
  is `<none>`, the `db` Deployment's Pod labels do not match the Service selector.
- `result` shows 0 votes but `worker` logged them → `kubectl logs deploy/result`.
  It connects to `db` with user/password `postgres`/`postgres` at this stage.
- Votes do not appear at all → `kubectl exec deploy/redis -- redis-cli llen votes`.
  If that number is growing, redis is fine and `worker` is the problem.

### Teaching note

Do the whole chain on the whiteboard *while* the logs stream. Five containers,
four Services, one DNS name each. The `worker` has no Service at all — ask them
why, and make them answer with "nothing ever calls it".

### Report back

`kubectl get svc,endpoints` (all of it), `kubectl logs -l app=worker --tail=20`,
and confirm both the vote page and the result page worked in your browser.

---

## Lab 16 · Init container: make `worker` wait for `db`

**Slides** 100, 101
**Goal** Move the dependency wait out of the app and into the platform, where it
is *visible*.
**Needs** Lab 15.

### Steps

**1 · patch the worker Deployment**

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata: {name: worker, namespace: vote}
spec:
  replicas: 1
  selector: {matchLabels: {app: worker}}
  template:
    metadata: {labels: {app: worker}}
    spec:
      initContainers:
        - name: wait-for-db
          image: postgres:14
          command: ['sh', '-c',
            'until pg_isready -h db -p 5432; do sleep 2; done']
      containers:
        - name: worker
          image: iti/worker:v1
          imagePullPolicy: IfNotPresent
EOF

kubectl rollout status deploy/worker
```

**2 · take the database away**

```bash
kubectl scale deploy/db --replicas=0
kubectl rollout restart deploy/worker

kubectl get pods -l app=worker -w        # Ctrl-C after ~30s
```

```bash
kubectl logs -l app=worker -c wait-for-db --tail=5
```

**3 · give it back**

```bash
kubectl scale deploy/db --replicas=1

kubectl get pods -l app=worker -w        # Ctrl-C once it is 1/1
kubectl describe pod -l app=worker | grep -A6 'Init Containers'
kubectl logs -l app=worker --tail=10
```

### Pass when

- Step 2: the worker Pod sits at `0/1  Init:0/1` and **stays there**. Not
  `CrashLoopBackOff`, not `Error` — a Pod that is honestly reporting *"I have not
  started, and here is why"*.
- `kubectl logs -l app=worker -c wait-for-db` → `db:5432 - no response`, repeating.
- Step 3: within ~10 seconds the watch shows
  `Init:0/1 → PodInitializing → 1/1 Running`.
- `describe … Init Containers` shows `wait-for-db` with
  `State: Terminated, Reason: Completed, Exit Code: 0`.

### Teaching note

Compare with Lab 10's ❓: **without** the init container the Pod reported
`1/1 Running` while being completely unable to do its job. `Worker.java` retries
its DB connection forever rather than crashing — so Kubernetes sees a healthy
process and every dashboard is green while nothing works. The init container
converts a lie into an honest `Init:0/1`. That is the lesson, not "how to wait".

### Report back

`kubectl get pods -l app=worker` while db is scaled to 0, the `wait-for-db` logs,
and the `describe … Init Containers` block after db returns.

---

## Lab 17 · Planted failure: a Service with no Endpoints

**Slide** 102
**Goal** Everything green, nothing works. Find it in under two minutes.
**Needs** Lab 15.

⚠️ Students: diagnose before reading the fix.

### Steps

**1 · plant it**

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Service
metadata: {name: result-broken, namespace: vote}
spec:
  selector: {app: results}      # the Pods are app=result
  ports: [{port: 80, targetPort: 80}]
EOF

kubectl run probe --rm -it --restart=Never \
  --image=curlimages/curl -- curl -sS --max-time 5 http://result-broken
```

**2 · diagnose**

```bash
kubectl get svc result-broken               # looks perfectly healthy
kubectl get endpoints result-broken         # <none>   <- there it is
kubectl describe svc result-broken | grep -i selector
kubectl get pods --show-labels | grep result
```

**3 · fix and clean up**

```bash
kubectl patch svc result-broken -p '{"spec":{"selector":{"app":"result"}}}'
kubectl get endpoints result-broken         # now has an IP

kubectl delete svc result-broken
```

### Pass when

- The probe fails with `curl: (28) Connection timed out` — **a timeout, not
  "connection refused"**. That distinction is the diagnostic: refused means
  something answered; timeout means the packet went into a Service with nowhere
  to send it.
- `kubectl get svc result-broken` looks entirely normal — ClusterIP assigned, port
  listed. Nothing is red.
- `kubectl get endpoints result-broken` → `<none>`.
- `describe svc | grep -i selector` → `Selector: app=results`, while
  `get pods --show-labels` shows `app=result`. One character.
- After the patch, endpoints appear immediately.

### Teaching note

Teach the rule: **`kubectl get endpoints` is the second command you run on any
"the Service doesn't work" report.** The first is `kubectl get pods`. Between them
they cover most of it.

### Report back

The exact curl error, `get svc` vs `get endpoints`, and the selector mismatch.
---

# DAY 3 — configuration, storage, and health

---

## Lab 18 · ConfigMap as environment variables

**Slide** 111
**Goal** Change two words in a ConfigMap and change what 25 students see on screen
— then discover the catch.
**Needs** Lab 15.

The app reads them: `vote/app.py` line 8 is
`option_a = os.getenv('OPTION_A', "Cats")`.

### Steps

**1 · create and wire**

```bash
kubectl create configmap vote-config -n vote \
  --from-literal=OPTION_A=Tea \
  --from-literal=OPTION_B=Coffee

kubectl set env deployment/vote -n vote --from=configmap/vote-config
kubectl rollout status deployment/vote -n vote

# see what that actually wrote into the Pod spec
kubectl get deployment vote -n vote \
  -o jsonpath='{.spec.template.spec.containers[0].env}' | tr ',' '\n'
```

Look at the app: `http://localhost:8080` through your tunnel (`ssh -L
8080:localhost:30080 visora`). It should say **Tea vs Coffee**.

**2 · change it, and be disappointed**

```bash
kubectl create configmap vote-config -n vote \
  --from-literal=OPTION_A=Vim \
  --from-literal=OPTION_B=Emacs \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl get configmap vote-config -n vote -o yaml | grep -A3 '^data'
```

The ConfigMap now says Vim / Emacs. **Refresh the browser. It still says Tea vs
Coffee.**

```bash
kubectl exec deploy/vote -n vote -- printenv OPTION_A
# Tea      <- the running Pod never heard about it
```

**3 · the only cure**

```bash
kubectl rollout restart deployment/vote -n vote
kubectl rollout status deployment/vote -n vote
kubectl exec deploy/vote -n vote -- printenv OPTION_A
```

Refresh → **Vim vs Emacs**.

### Pass when

- After step 1 the page says `Tea vs Coffee` and the jsonpath shows two entries
  with `valueFrom.configMapKeyRef`.
- After step 2 the ConfigMap `data` says `Vim`/`Emacs` but `printenv OPTION_A`
  still says `Tea`, and the browser is unchanged. **This gap is the lab.**
- After step 3, `printenv OPTION_A` → `Vim`, and the page follows.

### Teaching note

Environment variables are injected **once, at container start**. There is no
watch, no reload, no magic. Say it plainly: *if you change a ConfigMap consumed as
env, nothing happens until new Pods exist.* This is the single most common
"I changed the config and nothing happened" ticket in real life.

### Report back

`printenv OPTION_A` before and after the restart, and the ConfigMap `data` block
between them.

---

## Lab 19 · ConfigMap as a volume

**Slide** 112
**Goal** The other injection path — and the other half of the update story.
**Needs** Lab 18.

### Steps

**1 · create and mount**

```bash
cd ~
cat > banner.txt <<'EOF'
ITI DevOps 2026 -- vote responsibly
EOF

kubectl create configmap vote-banner -n vote --from-file=banner.txt
```

⚠️ Strategic-merge patches match containers **by name**. The container must be
called exactly `vote` or this silently patches nothing.

```bash
kubectl patch deployment vote -n vote --type=strategic -p "$(cat <<'EOF'
spec:
  template:
    spec:
      volumes:
      - name: banner
        configMap: {name: vote-banner}
      containers:
      - name: vote
        volumeMounts:
        - {name: banner, mountPath: /etc/vote, readOnly: true}
EOF
)"

kubectl rollout status deployment/vote -n vote
```

**2 · read it, change it, re-read it — no restart**

```bash
kubectl exec deploy/vote -n vote -- ls -l /etc/vote
kubectl exec deploy/vote -n vote -- cat /etc/vote/banner.txt

# change it. Do NOT restart anything.
kubectl edit configmap vote-banner -n vote
#   ... change the text, save, quit

# check immediately — probably unchanged
kubectl exec deploy/vote -n vote -- cat /etc/vote/banner.txt

# wait up to ~70s (the kubelet sync period), then again
sleep 70
kubectl exec deploy/vote -n vote -- cat /etc/vote/banner.txt
```

If `kubectl edit` opens an editor you dislike: `export EDITOR=nano` first.

### Pass when

- `ls -l /etc/vote` shows `banner.txt -> ..data/banner.txt` — a **symlink**. That
  symlink swap is the atomic-update mechanism; point at it.
- The first `cat` shows the original text.
- After editing and waiting, the *same Pod* (`kubectl get pods -l app=vote` — same
  names, `RESTARTS 0`, same AGE) serves the **new** text.

### Teaching note

Two paths, two behaviours, and the difference is not arbitrary:

| Injected as | Updates without restart? | Why |
|---|---|---|
| env var | **No** | copied into the process at exec time |
| volume | **Yes**, ~60s | kubelet re-projects the files and swaps a symlink |

But: the *file* updating does not mean the *app* noticed. An app must re-read the
file. Kubernetes updates the file; it cannot make your code care.

### Report back

`ls -l /etc/vote`, `cat` before, `cat` after, and `kubectl get pods -l app=vote`
showing `RESTARTS 0` and an unchanged AGE.

---

## Lab 20 · Move the Postgres password into a Secret

**Slide** 118
**Goal** One Secret, three consumers — and the whole app follows the change.
**Needs** Lab 15.

Confirmed against the source: `result/server.js` reads `DB_HOST/DB_USER/
DB_PASSWORD/DB_NAME` from the environment, and `Worker.java` does the same. Both
default to the old values, so this lab actually changes something.

### Steps

**1 · create it, feed the database**

```bash
kubectl create secret generic db-secret -n vote \
  --from-literal=POSTGRES_USER=postgres \
  --from-literal=POSTGRES_PASSWORD='S3cure-ITI-2026'

kubectl set env deployment/db -n vote --from=secret/db-secret
kubectl rollout status deployment/db -n vote

kubectl describe deployment db -n vote | grep -A4 Environment
```

❓ **Confirm** — the `db` Deployment already carries a literal
`POSTGRES_PASSWORD: postgres` from Lab 10. I expect `set env --from` to *replace*
it, leaving exactly one entry. Check with:

```bash
kubectl get deploy db -n vote \
  -o jsonpath='{.spec.template.spec.containers[0].env}' | tr ',' '\n'
```

If you see `POSTGRES_PASSWORD` **twice** — once as a literal and once as a
`secretKeyRef` — tell me. The literal wins in Postgres and the rest of the lab
will fail confusingly, and the slide needs a `kubectl set env deployment/db
POSTGRES_PASSWORD-` line before the `--from`.

**2 · feed the two clients (renamed keys)**

```bash
for d in result worker; do
kubectl patch deployment $d -n vote --type=strategic -p "$(cat <<EOF
spec:
  template:
    spec:
      containers:
      - name: $d
        env:
        - {name: DB_HOST, value: db}
        - name: DB_USER
          valueFrom:
            secretKeyRef: {name: db-secret, key: POSTGRES_USER}
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef: {name: db-secret, key: POSTGRES_PASSWORD}
EOF
)"
done

kubectl rollout status deployment/result -n vote
kubectl rollout status deployment/worker -n vote
```

**3 · prove the app still works**

```bash
kubectl logs deploy/worker -n vote --tail=10
```

Vote once through the tunnel, then check the `result` page still counts.

### Pass when

- `describe deployment db | grep -A4 Environment` shows
  `POSTGRES_PASSWORD:  <set to the key 'POSTGRES_PASSWORD' in secret 'db-secret'>`
  — **a reference, never the value.**
- `worker` logs show it connected and is processing votes.
- A new vote still lands on the `result` page.

### If it fails

- `db` `CrashLoopBackOff` → `kubectl logs deploy/db`. Duplicate/conflicting
  `POSTGRES_PASSWORD` (see the ❓ above) is the likely cause.
- `worker` logs `password authentication failed` → db restarted with a **fresh**
  data directory and the new password, but a client is still using the old one.
  `kubectl rollout restart deploy/worker deploy/result`.
- `result` shows 0 votes → **expected.** `db` had no PVC, so recreating the Pod
  wiped the old votes. Cast new ones. Lab 24 is where that stops happening.

### Report back

The `describe deployment db` Environment block, the env jsonpath from the ❓, and
`kubectl logs deploy/worker --tail=10`.

---

## Lab 21 · base64 is not encryption

**Slide** 119
**Goal** Two minutes that permanently fix the most common Kubernetes
misconception.
**Needs** Lab 20.

### Steps

**1 · three ways to read a "secret"**

```bash
kubectl get secret db-secret -n vote -o yaml

kubectl get secret db-secret -n vote \
  -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d; echo

kubectl get secret db-secret -n vote \
  -o go-template='{{ .data.POSTGRES_PASSWORD | base64decode }}'; echo

kubectl exec deploy/result -n vote -- printenv DB_PASSWORD
```

**2 · and the things that do help**

```bash
kubectl auth can-i get secrets -n vote
kubectl auth can-i get secrets -n vote --as=system:serviceaccount:vote:default

kubectl describe secret db-secret -n vote
```

### Pass when

- All three of the first block print `S3cure-ITI-2026` in clear text.
- `printenv DB_PASSWORD` in the running container prints it too.
- `kubectl auth can-i get secrets` → `yes` (you are cluster-admin).
- `--as=system:serviceaccount:vote:default` → **`no`**. RBAC is the actual control.
- `kubectl describe secret` shows only `POSTGRES_PASSWORD:  15 bytes` — **lengths,
  no values.** `describe` is safe to screen-share; `get -o yaml` is not.

### Teaching note

Say it in one sentence: *base64 is transport encoding, not protection.* What
actually protects a Secret is **RBAC** (who may read it), **encryption at rest**
(etcd `EncryptionConfiguration`), and **not putting it in git** (external secret
stores). Ask who has committed a `secret.yaml` to a repo. Hands will go up.

### Report back

All three decoded outputs, both `auth can-i` answers, and the `describe` output
showing bytes only.

---

## Lab 22 · emptyDir — cast votes, kill the Pod, lose them

**Slide** 123
**Goal** Six votes in, one `delete pod`, zero votes out.
**Needs** Lab 20.

### Steps

**1 · give redis a scratch volume, then stop the drain**

```bash
kubectl patch deployment redis -n vote --type=strategic -p "$(cat <<'EOF'
spec:
  template:
    spec:
      volumes:
      - name: data
        emptyDir: {}
      containers:
      - name: redis
        volumeMounts:
        - {name: data, mountPath: /data}
EOF
)"
kubectl rollout status deployment/redis -n vote

# stop the drain so votes PILE UP in redis instead of moving to postgres
kubectl scale deployment/worker -n vote --replicas=0
kubectl get pods -l app=worker -n vote     # should be empty
```

Now cast **5–6 votes** through your tunnel at `http://localhost:8080`.

**2 · watch them vanish**

```bash
kubectl exec deploy/redis -n vote -- redis-cli LLEN votes
# (integer) 6      <- queued, not yet in postgres

kubectl delete pod -l app=redis -n vote
kubectl rollout status deployment/redis -n vote

kubectl exec deploy/redis -n vote -- redis-cli LLEN votes
# (integer) 0      <- gone. every queued vote.
```

**3 · put the drain back**

```bash
kubectl scale deployment/worker -n vote --replicas=1
kubectl rollout status deployment/worker -n vote
```

### Pass when

- `LLEN votes` equals the number of votes you cast (5 or 6).
- After deleting the Pod, `LLEN votes` → `(integer) 0`.
- ⚠️ If the second `LLEN` errors with `Connection refused`, you asked too fast —
  wait for `rollout status` to finish and retry.

### Teaching note

`emptyDir` is tied to the **Pod**, not the container. A container *restart* keeps
it; a Pod *delete* destroys it. Worth demonstrating the difference if you have
time: `kubectl exec deploy/redis -- kill 1` restarts the container and the data
**survives**. Same volume, opposite outcome.

Also: you turned the worker off deliberately so the votes would sit in redis where
they were destroyable. In normal operation the worker drains the queue within
milliseconds — which is a real durability strategy, not an accident.

### Report back

`LLEN votes` before and after the Pod delete, and how many votes you cast.

---

## Lab 23 · A PVC that survives a Pod restart

**Slide** 129
**Goal** The mechanism, on a throwaway Pod, before applying it to the database.
**Needs** Lab 01.

⚠️ Runs in `demo` so it cannot collide with the app.

### Steps

```bash
kubectl get sc
# kind ships a default StorageClass: standard (rancher.io/local-path)

cat <<'EOF' > pvc-pod.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata: {name: data}
spec:
  accessModes: [ReadWriteOnce]
  resources: {requests: {storage: 1Gi}}
---
apiVersion: v1
kind: Pod
metadata: {name: writer}
spec:
  containers:
  - {name: app, image: busybox, command:
     ["sh","-c","echo hi-ITI >/data/msg; sleep 1d"],
     volumeMounts: [{name: v, mountPath: /data}]}
  volumes:
  - {name: v, persistentVolumeClaim: {claimName: data}}
EOF

kubectl apply -f pvc-pod.yaml -n demo
kubectl get pvc,pv -n demo

kubectl wait --for=condition=ready pod/writer -n demo --timeout=120s
kubectl exec writer -n demo -- cat /data/msg

# delete the POD, keep the PVC
kubectl delete pod writer -n demo
kubectl get pvc -n demo                 # still Bound
kubectl apply -f pvc-pod.yaml -n demo
kubectl wait --for=condition=ready pod/writer -n demo --timeout=120s

kubectl exec writer -n demo -- cat /data/msg
```

Clean up:

```bash
kubectl delete pod writer -n demo
kubectl delete pvc data -n demo
```

### Pass when

- `kubectl get sc` shows `standard (default)  rancher.io/local-path`.
- The PVC goes `Pending` → `Bound` **only once the Pod is scheduled** — kind's
  local-path provisioner is `WaitForFirstConsumer`. A `Pending` PVC with no
  consumer is correct, not broken. (Lab 27 leans on this.)
- Both `cat /data/msg` calls print `hi-ITI` — the second one after the Pod was
  destroyed and recreated.

### Teaching note

Three objects, three jobs: the **PVC** is the request, the **StorageClass**
fulfils it, the **PV** is the result. Show `kubectl get pv` and point out the
name is generated — you never write a PV by hand on a cloud or on kind.

### Report back

`kubectl get sc`, `kubectl get pvc,pv -n demo`, and both `cat /data/msg` outputs.

---

## Lab 24 · Give Postgres a PVC, then kill the Pod

**Slides** 130, 131
**Goal** New Pod, new IP, same data.
**Needs** Lab 20, Lab 23 understood.

### Steps

**1 · claim a disk**

```bash
kubectl apply -n vote -f - <<'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pgdata
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 1Gi
EOF

kubectl get pvc pgdata -n vote
# STATUS: Pending -- correct, nothing consumes it yet
```

**2 · mount it into `db`**

`strategy: Recreate` matters here: two Postgres Pods must never hold the same
`ReadWriteOnce` volume, and the default `RollingUpdate` would try exactly that.

```bash
kubectl patch deployment db -n vote --type=strategic -p "$(cat <<'EOF'
spec:
  strategy: {type: Recreate}
  template:
    spec:
      volumes:
      - name: pgdata
        persistentVolumeClaim: {claimName: pgdata}
      containers:
      - name: db
        env:
        - {name: PGDATA, value: /var/lib/postgresql/data/pgdata}
        volumeMounts:
        - {name: pgdata, mountPath: /var/lib/postgresql/data}
EOF
)"

kubectl rollout status deployment/db -n vote
kubectl get pvc pgdata -n vote      # now Bound
```

The `PGDATA` subdirectory is not decoration — `local-path` gives you a directory
that Postgres refuses to `initdb` into unless it is empty, and it will not be.

**3 · vote, then verify the tally**

The database just re-initialised on a fresh disk, so cast a handful of **new**
votes now through your tunnel.

```bash
kubectl rollout restart deploy/worker -n vote     # reconnect to the new db
kubectl exec deploy/db -n vote -- \
  psql -U postgres -c 'select vote, count(*) from votes group by vote;'
```

**4 · delete it and prove durability**

```bash
kubectl get pod -l app=db -n vote -o wide          # note the NAME and IP

kubectl delete pod -l app=db -n vote
kubectl wait --for=condition=ready pod -l app=db -n vote --timeout=180s

kubectl get pod -l app=db -n vote -o wide          # NEW name, NEW IP

kubectl exec deploy/db -n vote -- \
  psql -U postgres -c 'select vote, count(*) from votes group by vote;'

kubectl get pvc pgdata -n vote     # still Bound, same volume
```

### Pass when

- `pgdata` is `Pending` before the patch, `Bound` after.
- Step 3's `psql` returns your vote counts, e.g. `a | 4`, `b | 2`.
- Step 4's Pod has a **different name and a different IP** — and returns the
  **same counts**.
- `kubectl get pvc pgdata` shows the same `VOLUME` name throughout.

### If it fails

- `db` `CrashLoopBackOff` after the patch → `kubectl logs deploy/db`. If it says
  *"directory … exists but is not empty"*, the `PGDATA` env var did not apply.
  Check `kubectl get deploy db -o yaml | grep -A2 PGDATA`.
- `psql` → `relation "votes" does not exist` → the `worker` has not connected yet
  (it creates the table). `kubectl logs deploy/worker`, restart it, cast a vote.
- PVC stuck `Pending` after the patch → `kubectl describe pvc pgdata`, and check
  the local-path provisioner: `kubectl -n local-path-storage get pods`.

### Teaching note

Say the sentence: **the claim outlived the thing that mounted it.** That is the
entire idea of persistent storage in Kubernetes. Pods are cattle; the PVC is the
brand.

### Report back

`get pvc pgdata` before and after, both `psql` tallies, and `get pod -l app=db -o
wide` before and after the delete.

---

## Lab 25 · Readiness probes

**Slide** 140
**Goal** Add readiness, then break it deliberately and watch the endpoint list
empty out.
**Needs** Lab 24.

### Steps

**1 · httpGet readiness on the two web apps**

```bash
for d in vote result; do
kubectl patch deployment $d -n vote --type=strategic -p "$(cat <<EOF
spec:
  template:
    spec:
      containers:
      - name: $d
        readinessProbe:
          httpGet: {path: /, port: 80}
          initialDelaySeconds: 3
          periodSeconds: 5
          timeoutSeconds: 2
          failureThreshold: 3
EOF
)"
done

kubectl rollout status deployment/vote -n vote
kubectl rollout status deployment/result -n vote
```

**2 · exec readiness on the database**

`db` speaks Postgres, not HTTP. `httpGet` would be wrong here — use `exec`.

```bash
kubectl patch deployment db -n vote --type=strategic -p "$(cat <<'EOF'
spec:
  template:
    spec:
      containers:
      - name: db
        readinessProbe:
          exec:
            command: ["pg_isready","-U","postgres","-h","127.0.0.1"]
          initialDelaySeconds: 10
          periodSeconds: 10
EOF
)"
kubectl rollout status deployment/db -n vote

kubectl get endpoints vote -n vote
```

**3 · break one on purpose**

```bash
kubectl patch deployment vote -n vote --type=json -p \
  '[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/path","value":"/nope"}]'

sleep 40
kubectl get pod -l app=vote -n vote
kubectl get endpoints vote -n vote
kubectl describe pod -l app=vote -n vote | grep -A3 -i readiness
```

**4 · put it back**

```bash
kubectl patch deployment vote -n vote --type=json -p \
  '[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/path","value":"/"}]'
kubectl rollout status deployment/vote -n vote
kubectl get endpoints vote -n vote
```

### Pass when

- Step 2: `get endpoints vote` lists the ready Pod IPs.
- **Step 3 is the lab:**
  - `kubectl get pod -l app=vote` → `READY 0/1` with **`RESTARTS 0`**.
    Readiness does not kill anything — it only removes it from service. (A
    *liveness* probe would restart it. That is the difference, in one screen.)
  - `kubectl get endpoints vote` → `<none>`.
  - `curl -s http://localhost:30080` now fails or hangs — no backends.
  - `describe pod` Events show `Readiness probe failed: HTTP probe failed with
    statuscode: 404`.
- Step 4 restores endpoints within ~15 seconds.

❓ **Confirm** — during step 3 `kubectl rollout status deploy/vote` will hang,
because no new Pod ever becomes ready. That is correct behaviour, not a bug. Tell
me if you see anything else.

### Teaching note

The three probes, in one line each:
**startup** = "has it booted yet" (suspends the others);
**readiness** = "should it get traffic" (removes from Endpoints);
**liveness** = "should it be killed" (restarts the container).

The most expensive production mistake is putting a liveness probe on a slow
dependency: your database blips, and Kubernetes helpfully restarts every app Pod
you own.

### Report back

`get pod -l app=vote` and `get endpoints vote` at each of steps 2, 3 and 4, plus
the readiness failure Event.

---

## Lab 26 · ⭐ Zero-downtime rollout, measured

**Slide** 141
**Goal** The same rollout, twice. Once it drops ~50 requests. Once it drops none.
**Needs** Lab 25. **Two terminals.** Budget 15 minutes.

This is the payoff lab of the whole course. Do not rush it.

### Steps

**Round 1 — no readiness probe**

```bash
kubectl scale deployment/vote -n vote --replicas=1

kubectl patch deployment vote -n vote --type=json -p \
  '[{"op":"remove","path":"/spec/template/spec/containers/0/readinessProbe"}]'

# simulate a real app's warm-up: JVM start, migrations, cache fill
kubectl patch deployment vote -n vote --type=strategic -p "$(cat <<'EOF'
spec:
  template:
    spec:
      containers:
      - name: vote
        command: ["sh","-c","sleep 10 && python app.py"]
EOF
)"
kubectl rollout status deployment/vote -n vote
```

`app.py` ends with `app.run(host='0.0.0.0', port=80)`, so this still serves on
port 80 — just via Flask's dev server instead of gunicorn. Fine for the
experiment; step 3 puts it back.

**TERMINAL A — continuous load from inside the cluster. Leave it running.**

```bash
kubectl run load -n vote --rm -it --restart=Never \
  --image=curlimages/curl -- sh -c \
  'n=0; f=0; while true; do n=$((n+1));
     curl -sf -m 2 -o /dev/null http://vote/ || { f=$((f+1)); echo "FAIL $f  (request $n)"; };
     sleep 0.2; done'
```

**TERMINAL B — roll it:**

```bash
kubectl rollout restart deployment/vote -n vote
```

Watch terminal A. **Count the FAIL lines.**

**Round 2 — with a readiness probe**

Leave terminal A running. In terminal B:

```bash
kubectl patch deployment vote -n vote --type=strategic -p "$(cat <<'EOF'
spec:
  strategy:
    rollingUpdate: {maxUnavailable: 0, maxSurge: 1}
  template:
    spec:
      containers:
      - name: vote
        readinessProbe:
          httpGet: {path: /, port: 80}
          periodSeconds: 2
          failureThreshold: 3
EOF
)"
kubectl rollout status deployment/vote -n vote

# note the FAIL count in terminal A right now, then:
kubectl rollout restart deployment/vote -n vote
```

**Round 3 — put it back**

```bash
# drop the sleep-and-dev-server override; return to the image's gunicorn CMD
kubectl patch deployment vote -n vote --type=json -p \
  '[{"op":"remove","path":"/spec/template/spec/containers/0/command"}]'

kubectl scale deployment/vote -n vote --replicas=2
kubectl rollout status deployment/vote -n vote
kubectl get pods -l app=vote -n vote
```

Then `Ctrl-C` terminal A.

### Pass when

- **Round 1:** terminal A prints a burst of `FAIL` lines — I expect roughly
  10 s ÷ 0.2 s ≈ **50**. ❓ **Confirm the actual number.** Anything in the
  30–60 range proves the point.
- **Round 2:** the FAIL counter does **not increase**. Zero new lines through the
  entire rollout.
- Round 3: two Pods `1/1 Running`, and
  `kubectl get deploy vote -o jsonpath='{.spec.template.spec.containers[0].command}'`
  returns nothing.

### If it fails

- Round 2 still drops requests → check `maxUnavailable: 0` actually applied:
  `kubectl get deploy vote -o jsonpath='{.spec.strategy}'`. With
  `maxUnavailable: 1` and one replica, Kubernetes is allowed to take your only
  Pod down first, and no probe can save you.
- Terminal A fails from the very first request → the `vote` Service has no ready
  endpoints. `kubectl get endpoints vote`.

### Teaching note

The number on screen is the argument. `maxUnavailable: 0` + a readiness probe is
the difference between a deploy your users notice and one they do not — and it is
four lines of YAML. Ask them what those 50 requests would be at their company.

### Report back

The FAIL count after round 1, the FAIL count after round 2 (should be identical),
and `kubectl get pods -l app=vote` after round 3.

---

## Lab 27 · Planted failure: a PVC that will never bind

**Slide** 142
**Goal** Same symptom, two completely different causes — and only one is a bug.
**Needs** Lab 23.

### Steps

**1 · break it**

```bash
kubectl apply -n vote -f - <<'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: broken
spec:
  storageClassName: fast-ssd
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 5Gi
EOF

kubectl get pvc broken -n vote
```

**2 · diagnose**

```bash
kubectl describe pvc broken -n vote | tail -8
kubectl get sc
```

**3 · "fix" it — and meet the second cause**

`storageClassName` is **immutable**. You cannot edit it; you recreate.

```bash
kubectl delete pvc broken -n vote
kubectl apply -n vote -f - <<'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata: {name: broken}
spec:
  storageClassName: standard
  accessModes: [ReadWriteOnce]
  resources: {requests: {storage: 5Gi}}
EOF

kubectl get pvc broken -n vote
kubectl describe pvc broken -n vote | tail -5
kubectl delete pvc broken -n vote
```

### Pass when

- Step 1: `STATUS Pending`, `STORAGECLASS fast-ssd`.
- Step 2: `describe` Events say
  `storageclass.storage.k8s.io "fast-ssd" not found`, and `get sc` shows only
  `standard (default)`.
- **Step 3 is the twist:** the PVC is **still `Pending`** — but now for the right
  reason. `describe` says `waiting for first consumer to be created before
  binding`. kind's provisioner is `WaitForFirstConsumer`; no Pod, no volume.
- Trying to `kubectl edit` the storageClassName is rejected — worth doing once so
  they see the error.

### Teaching note

`Pending` is a symptom, never a diagnosis. Two causes here that look identical in
`get pvc` and are told apart only by `describe`:
1. the class does not exist → a real bug;
2. nothing consumes the claim yet → correct, working-as-designed behaviour.

`kubectl describe` is where Kubernetes stops being mysterious.

### Report back

Both `get pvc broken` outputs and both `describe … Events` blocks.
---

# DAY 4 — production concerns

---

## Lab 28 · Requests, limits and QoS

**Slide** 151
**Goal** Size the whole Voting App, and see what class each Pod earns.
**Needs** Lab 26 finished (vote back on 2 replicas, no `command` override).

### Steps

```bash
# frontends: small, burstable
kubectl set resources deploy/vote deploy/result \
  --requests=cpu=100m,memory=128Mi \
  --limits=cpu=500m,memory=256Mi

# worker: no inbound traffic, steady burn
kubectl set resources deploy/worker \
  --requests=cpu=100m,memory=256Mi \
  --limits=cpu=500m,memory=512Mi

# redis: tiny
kubectl set resources deploy/redis \
  --requests=cpu=50m,memory=64Mi \
  --limits=cpu=200m,memory=256Mi

# db: requests == limits, so it can never be evicted first
kubectl set resources deploy/db \
  --requests=cpu=250m,memory=512Mi \
  --limits=cpu=250m,memory=512Mi

kubectl get deploy
```

Read it back:

```bash
kubectl get pod -o custom-columns=NAME:.metadata.name,QOS:.status.qosClass

kubectl describe node iti-worker | grep -A8 'Allocated resources'

kubectl get pod -l app=db -o jsonpath='{.items[0].spec.containers[0].resources}'; echo
```

### Pass when

- All five Deployments roll and return to `READY`.
- The QoS column is the lesson:
  - `db` → **`Guaranteed`** (requests == limits, on every resource)
  - everything else → **`Burstable`** (requests < limits)
  - ❓ `worker`'s init container has no resources set — confirm whether `worker`
    still comes out `Burstable`. I believe init containers count toward the QoS
    calculation; if you see `BestEffort` on worker, tell me.
- `describe node … Allocated resources` shows CPU/memory **Requests** summing to
  well under 100%. Limits may exceed 100% — that is overcommit, and it is allowed.

### Teaching note

Two numbers, two completely different jobs:
- **requests** → used by the **scheduler**, at placement time. This is what
  "the node is full" means. Nothing enforces it at runtime.
- **limits** → used by the **kernel** (cgroups), continuously. CPU over the limit
  gets *throttled*; memory over the limit gets the process *killed*. Lab 29 shows
  the second one.

QoS decides who dies first when a node runs out of memory:
`BestEffort` → `Burstable` → `Guaranteed`. Your database should be last on that
list, which is why it is the only one with requests == limits.

### Report back

The QoS custom-columns table and the `Allocated resources` block.

---

## Lab 29 · OOMKilled, on purpose

**Slide** 152
**Goal** A 64 Mi limit and a container that wants 250 Mi. Watch the kernel win.
**Needs** Lab 28.

### Steps

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: oomer
spec:
  restartPolicy: Never
  containers:
  - name: stress
    image: polinux/stress
    args: ["stress","--vm","1","--vm-bytes","250M","--vm-hang","1"]
    resources:
      requests:
        memory: 32Mi
      limits:
        memory: 64Mi
EOF

kubectl get pod oomer -w        # Ctrl-C once the status settles
```

```bash
kubectl get pod oomer -o jsonpath='{.status.containerStatuses[0].state.terminated.reason}{" exit "}{.status.containerStatuses[0].state.terminated.exitCode}'; echo

kubectl describe pod oomer | grep -A8 'State'
kubectl logs oomer

kubectl delete pod oomer
```

### Pass when

- The watch shows `ContainerCreating → Running → Error` (or straight to `Error`)
  within a few seconds.
- The jsonpath prints exactly: **`OOMKilled exit 137`**.
- `describe` shows `Last State: Terminated`, `Reason: OOMKilled`, `Exit Code: 137`.
- ⚠️ `kubectl logs oomer` shows the stress tool's output, **not** an out-of-memory
  message. The application never learns it was killed — that is the whole
  difficulty of debugging OOM in production.

### Teaching note

**137 = 128 + 9 = SIGKILL.** Not a crash, not an exception, not something your
error handler will ever catch. The kernel's OOM killer sent SIGKILL and the
process ceased mid-instruction.

With `restartPolicy: Never` it stops at `Error`. Change it to `Always` and you get
`CrashLoopBackOff` — the same event, a different-looking symptom. If you have five
minutes, do it: it explains half the `CrashLoopBackOff` tickets they will ever see.

### Report back

The jsonpath output (must be `OOMKilled exit 137`) and the `describe … State` block.

---

## Lab 30 · nodeSelector and taints

**Slide** 158
**Goal** Pin the database to one node; repel everything from another until you
hand it the key.
**Needs** Lab 28.

### Steps

**1 · label a node and pin `db` to it**

```bash
kubectl label node iti-worker disktype=ssd
kubectl get nodes -L disktype

kubectl patch deploy db -p '{"spec":{"template":{"spec":{"nodeSelector":{"disktype":"ssd"}}}}}'

kubectl rollout status deploy/db
kubectl get pod -l app=db -o wide
```

**2 · taint the other node, then tolerate it**

```bash
kubectl taint node iti-worker2 tier=data:NoSchedule

kubectl scale deploy/vote --replicas=6
kubectl get pod -l app=vote -o wide
# nothing lands on iti-worker2
```

```bash
kubectl patch deploy vote -p '{"spec":{"template":{"spec":{"tolerations":[{"key":"tier","operator":"Equal","value":"data","effect":"NoSchedule"}]}}}}'

kubectl rollout status deploy/vote
kubectl get pod -l app=vote -o wide
# now some do
```

**3 · clean up — note the trailing dash**

```bash
kubectl taint node iti-worker2 tier=data:NoSchedule-
kubectl scale deploy/vote --replicas=2
kubectl patch deploy db -p '{"spec":{"template":{"spec":{"nodeSelector":null}}}}'
kubectl rollout status deploy/db
```

### Pass when

- `kubectl get nodes -L disktype` → `iti-worker` has `ssd`, the others blank.
- After the patch, `get pod -l app=db -o wide` shows the db Pod **on
  `iti-worker`** — and it moved there, so it is a new Pod.
- After the taint + scale to 6: **zero** vote Pods on `iti-worker2`. They pile
  onto `iti-control-plane` and `iti-worker`.
  ❓ **Confirm** — does `iti-control-plane` accept them? kind does *not* apply the
  usual `node-role.kubernetes.io/control-plane:NoSchedule` taint, so I expect yes.
  Send me the `-o wide` output.
- After the toleration patch, new vote Pods **do** land on `iti-worker2`.

### If it fails

`kubectl get pod -l app=vote` shows some `Pending` after the taint → normal if the
remaining nodes cannot fit 6 replicas at 100m CPU each.
`kubectl describe pod <pending>` will say either `node(s) had untolerated taint`
(the taint working) or `Insufficient cpu` (the node genuinely full). Both are
instructive; tell me which you got.

### Teaching note

The direction is what students confuse, so state it twice:
- **nodeSelector / affinity** = the *Pod* chooses the node. Pod-driven attraction.
- **taint / toleration** = the *node* rejects Pods. Node-driven repulsion.

A toleration does not *attract* — it only removes an objection. A Pod that
tolerates a taint may still land elsewhere. This is exactly how kind keeps your
workloads off dedicated nodes, and how cloud providers reserve GPU nodes.

### Report back

`get nodes -L disktype`, `get pod -l app=db -o wide` after pinning, and
`get pod -l app=vote -o wide` both before and after the toleration.

---

## Lab 31 · metrics-server

**Slide** 163
**Goal** Real CPU and memory numbers. Without this, Lab 32 cannot work at all.
**Needs** Lab 30.

### Steps

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# kind: the kubelet serves a self-signed cert. Accept it.
kubectl patch deploy metrics-server -n kube-system --type=json \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'

kubectl rollout status deploy/metrics-server -n kube-system --timeout=180s
```

Wait ~60 s for the first scrape, then:

```bash
kubectl top nodes
kubectl top pods
kubectl top pods --containers

# usage vs reserved — compare these two
kubectl top nodes
kubectl describe node iti-worker | grep -A8 'Allocated resources'
```

### Pass when

- `kubectl rollout status` succeeds and `kubectl -n kube-system get pods -l
  k8s-app=metrics-server` → `1/1 Running`.
- `kubectl top nodes` prints real numbers for all three nodes — **not** `error:
  Metrics API not available`.
- `kubectl top pods` lists your app Pods with CPU in `m` and memory in `Mi`.

### If it fails

- `Metrics API not available` immediately after install → you were too fast. Wait
  60 s. If it persists past 3 minutes:
  `kubectl -n kube-system logs deploy/metrics-server`. `x509: cannot validate
  certificate` means the `--kubelet-insecure-tls` patch did not apply — check
  `kubectl -n kube-system get deploy metrics-server -o jsonpath='{.spec.template.spec.containers[0].args}'`.
- Pod `0/1 Running` and never ready → its own readiness probe is failing on the
  same TLS problem. Same fix.

### Teaching note

The comparison at the end is the point, so put both on screen together:
`top nodes` shows what is **actually being used**; `describe node … Allocated
resources` shows what has been **promised away** by requests. In most real
clusters the second number is 3–5× the first. That gap is the money.

### Report back

`kubectl top nodes`, `kubectl top pods`, and the `Allocated resources` block.

---

## Lab 32 · HPA — autoscale `vote` under load

**Slide** 164
**Goal** A replica count that moves on its own.
**Needs** Lab 31 (`kubectl top pods` must work) and Lab 28 (a CPU **request** on
`vote` — without one the HPA has no denominator and reads `<unknown>`).

### Steps

```bash
kubectl get deploy vote -o jsonpath='{.spec.template.spec.containers[0].resources}'; echo

kubectl autoscale deploy/vote --cpu-percent=50 --min=2 --max=10
kubectl get hpa vote
```

⚠️ Check `TARGETS` before generating load. It must read `0%/50%` (or similar),
**never `<unknown>/50%`**. Wait up to 60 s for the first reading.

**Terminal 2 — generate load:**

```bash
kubectl run load --image=busybox:1.36 --restart=Never -- \
  /bin/sh -c "while true; do wget -q -O- http://vote; done"
```

**Terminal 1 — watch:**

```bash
kubectl get hpa vote -w          # leave for 3-5 minutes
```

Then, in another pane:

```bash
kubectl get pod -l app=vote
kubectl top pods -l app=vote
kubectl describe hpa vote | tail -20
```

**Stop the load, then be patient:**

```bash
kubectl delete pod load
kubectl get hpa vote -w          # scale-down takes ~5 minutes
```

### Pass when

- `get hpa vote` → `TARGETS 0%/50%`, `MINPODS 2`, `MAXPODS 10`, `REPLICAS 2`.
- Under load, `TARGETS` climbs past 50% and `REPLICAS` rises — 2 → 4 → 6 …
  ❓ **Confirm how high it actually goes.** One busybox `wget` loop is a single
  serial requester; it may only push `vote` to 3–4 replicas rather than 10. If it
  barely moves, run **three** load Pods (`load1`, `load2`, `load3`) and tell me.
- `describe hpa` Events show `New size: N; reason: cpu resource utilization
  (percentage of request) above target`.
- After deleting `load`, replicas fall back to 2 — **after about 5 minutes**, not
  immediately.

### Teaching note

Two things students always ask:

1. *Why does scale-down take five minutes?* The
   `--horizontal-pod-autoscaler-downscale-stabilization` window, 5 min by default.
   It exists so a brief dip in traffic does not throw away capacity you are about
   to need. Scaling **up** is immediate; scaling **down** is deliberately timid.
2. *50% of what?* Of the **request** (100m), not of the limit and not of the node.
   So the target is 50m of actual CPU per Pod. This is why Lab 28 had to come
   first — no request, no percentage, no HPA.

### Report back

`get hpa vote` before load, the peak `REPLICAS` and `TARGETS` under load,
`describe hpa vote | tail -20`, and the replica count 5 minutes after you stopped.

---

## Lab 33 · A Job and a CronJob

**Slide** 169
**Goal** One Job that must succeed once; one CronJob that reports forever.
**Needs** Lab 20 (`db-secret`), Lab 24 (a working `db`).

### Steps

**1 · initialise the schema, once**

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata: {name: db-init}
spec:
  backoffLimit: 4
  ttlSecondsAfterFinished: 600
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: psql
        image: postgres:14
        env:
        - name: PGPASSWORD
          valueFrom:
            secretKeyRef: {name: db-secret, key: POSTGRES_PASSWORD}
        command: ["sh","-c"]
        args:
        - |
          until pg_isready -h db -U postgres; do sleep 2; done
          psql -h db -U postgres -c "CREATE TABLE IF NOT EXISTS votes (id VARCHAR(255) NOT NULL UNIQUE, vote VARCHAR(255) NOT NULL);"
EOF

kubectl get job db-init
kubectl logs job/db-init
```

**2 · snapshot the tally every 2 minutes**

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: batch/v1
kind: CronJob
metadata: {name: tally}
spec:
  schedule: "*/2 * * * *"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: psql
            image: postgres:14
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef: {name: db-secret, key: POSTGRES_PASSWORD}
            command: ["sh","-c"]
            args: ["psql -h db -U postgres -t -c 'SELECT vote, count(*) FROM votes GROUP BY vote;'"]
EOF

kubectl get cronjob tally
kubectl get jobs -w              # wait up to 2 minutes for the first run. Ctrl-C.
```

```bash
kubectl logs "$(kubectl get pod -l batch.kubernetes.io/job-name \
  --sort-by=.metadata.creationTimestamp -o name | tail -1)"
```

Clean up when done:

```bash
kubectl delete cronjob tally
```

### Pass when

- `kubectl get job db-init` → `COMPLETIONS 1/1`.
- `kubectl logs job/db-init` → `CREATE TABLE` (or `NOTICE: relation "votes"
  already exists, skipping` — the worker may have created it first; both mean
  success, and that is why `IF NOT EXISTS` is there).
- After ~2 minutes, `kubectl get jobs` shows a second Job named `tally-<digits>`.
- The last Job's logs print the vote tally, e.g. ` a | 4` / ` b | 2`.
- Wait ~6 minutes: `kubectl get jobs` never holds more than **3** completed
  `tally-*` Jobs — `successfulJobsHistoryLimit` at work.
- After 10 minutes, `db-init` disappears entirely: `ttlSecondsAfterFinished: 600`.

### If it fails

- Job `BackoffLimitExceeded` → `kubectl logs job/db-init`.
  `password authentication failed` means the Secret and the running `db` disagree
  — cast an eye over Lab 20's ❓.
- No `tally` Job after 3 minutes → `kubectl describe cronjob tally`. Check the
  node clock: `date` on visora versus your laptop.

### Teaching note

Four fields worth naming out loud, because they are what separates a Job from a
Deployment: `backoffLimit` (how many retries before giving up),
`restartPolicy: OnFailure` (Jobs may **not** use `Always`),
`ttlSecondsAfterFinished` (self-cleanup — without it your cluster accumulates
completed Pods forever), and `concurrencyPolicy: Forbid` (if the last run is still
going, skip this one — the answer to "why did my cron job run twice").

### Report back

`kubectl get job db-init`, its logs, `kubectl get jobs` after ~5 minutes, and the
tally output.

---

## Lab 34 · Ingress — two hostnames, one front door

**Slide** 173
**Goal** Route both apps through one L7 entry point, by Host header.
**Needs** Lab 15 (Services `vote` and `result`), port 80 free on visora.

### Steps

**1 · install the controller**

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

kubectl wait -n ingress-nginx --for=condition=ready pod \
  -l app.kubernetes.io/component=controller --timeout=300s
```

This manifest is the **kind-specific** one — it schedules onto the node labelled
`ingress-ready=true` (Lab 01 set that) and binds host ports 80/443 directly.

**2 · one front door, two apps**

```bash
kubectl apply -f - <<'EOF'
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata: {name: vote, namespace: vote}
spec:
  ingressClassName: nginx
  rules:
  - host: vote.localtest.me
    http:
      paths:
      - {path: /, pathType: Prefix, backend:
         {service: {name: vote, port: {number: 80}}}}
  - host: result.localtest.me
    http:
      paths:
      - {path: /, pathType: Prefix, backend:
         {service: {name: result, port: {number: 80}}}}
EOF

kubectl get ingress
kubectl describe ingress vote | tail -15
```

**3 · use it — from visora**

```bash
curl -s http://vote.localtest.me   | head -n3
curl -s http://result.localtest.me | head -n3

# prove it is the Host header doing the work, not DNS:
curl -s -H 'Host: vote.localtest.me'   http://localhost | head -n3
curl -s -H 'Host: result.localtest.me' http://localhost | head -n3
curl -s -H 'Host: nope.localtest.me'   http://localhost | head -n3
```

**From your laptop's browser** — `*.localtest.me` resolves to `127.0.0.1`, which
is *your laptop*, not visora. Tunnel port 80 and it lines up:

```bash
# laptop, needs sudo for a port below 1024:
sudo ssh -L 80:localhost:80 visora
# then open http://vote.localtest.me and http://result.localtest.me
```

### Pass when

- `kubectl get ingress` shows both hosts and, after a minute, an `ADDRESS`.
- The two curls return the voting page and the results page respectively —
  **same IP, same port, different app.**
- The `Host: nope.localtest.me` curl returns nginx's **404** default backend. That
  is the proof that routing is by Host header.

### If it fails

- `curl: (7) Failed to connect to … port 80` → nothing is bound to host port 80.
  `docker port iti-control-plane` must show `80/tcp`. If Lab 00 made you use the
  alternate mapping, use `http://vote.localtest.me:8080` throughout this lab.
- `503 Service Temporarily Unavailable` → the Ingress resolved but the backend
  Service has no ready endpoints. `kubectl get endpoints vote result`.
- The admission webhook rejects the Ingress → the controller was not ready. Re-run
  the `kubectl wait`, then re-apply.

### Teaching note

Contrast the three, on one slide, in this order — it is the summary of the whole
networking day:

| | Layer | Cost | Routes by |
|---|---|---|---|
| NodePort | 4 | free, ugly port | node IP + port |
| LoadBalancer | 4 | **one cloud LB per Service** | its own IP |
| Ingress | 7 | one LB for *everything* | Host header and path |

Fifty microservices as LoadBalancer = fifty cloud load balancers on your bill.
As Ingress = one.

### Report back

`kubectl get ingress`, all three `-H 'Host: …'` curl results (including the 404).

---

## Lab 35 · MetalLB — a real `EXTERNAL-IP`

**Slides** 174, 175
**Goal** For four days `type: LoadBalancer` has been a slide. Make it real.
**Needs** Lab 34.

### Steps

**1 · install, then find a free range**

```bash
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.14.8/config/manifests/metallb-native.yaml

kubectl wait -n metallb-system --timeout=300s \
  --for=condition=ready pod -l app=metallb

# which subnet do the kind nodes live on?
docker network inspect kind -f '{{ (index .IPAM.Config 0).Subnet }}'

# which addresses are already taken?
kubectl get nodes -o wide
```

⚠️ The next step assumes the subnet is `172.18.0.0/16`. **If
`docker network inspect` printed something else, stop and tell me** — the pool
must live inside the real subnet and outside the range Docker hands out.

**2 · hand MetalLB a slice of it**

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: kind-pool
  namespace: metallb-system
spec:
  addresses:
  - 172.18.255.200-172.18.255.250
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: kind-l2
  namespace: metallb-system
spec:
  ipAddressPools:
  - kind-pool
EOF

kubectl get ipaddresspool -n metallb-system
```

**3 · flip the Service type**

```bash
kubectl patch svc vote -p '{"spec":{"type":"LoadBalancer"}}'

kubectl get svc vote -w        # EXTERNAL-IP: <pending> -> a real address. Ctrl-C.
```

**4 · use it**

```bash
IP=$(kubectl get svc vote -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "$IP"

curl -s "http://$IP" | head -n5

# the IP survives a scale event
kubectl scale deploy/vote --replicas=4
curl -s "http://$IP" | head -n1

kubectl describe svc vote | tail -8
```

### Pass when

- `kubectl get ipaddresspool -n metallb-system` lists `kind-pool`.
- `kubectl get svc vote` → `TYPE LoadBalancer`, `EXTERNAL-IP 172.18.255.200`,
  `PORT(S) 80:30080/TCP`. **The NodePort survives** — a LoadBalancer Service is a
  NodePort Service with an address in front. Point that out.
- `curl http://$IP` returns the voting page **from visora**.
- After scaling, the IP is unchanged.

### If it fails

- `EXTERNAL-IP` stuck `<pending>` → `kubectl -n metallb-system logs -l
  component=controller`. Usually the pool is outside the kind subnet.
- ⚠️ **The HPA fights you.** Lab 32 left an HPA with `min=2` on `vote`; the
  `scale --replicas=4` will be reverted within a minute. That is the HPA doing
  its job, not a failure. To make the scale stick:
  `kubectl delete hpa vote` first.
- `curl` from **your laptop** to `172.18.255.200` will never work. That address
  lives on visora's Docker bridge network — it is "external" to the *cluster*, not
  to the internet. Say this out loud in class; someone always tries it.

### Teaching note

This is what the cloud does for you. On EKS, `type: LoadBalancer` makes AWS
provision a real NLB with a real public IP and a real monthly bill. MetalLB does
the same job with ARP on a local L2 network. The Kubernetes object is
byte-identical — only the controller behind it differs. That is the portability
argument, demonstrated rather than asserted.

### Report back

`docker network inspect kind -f '{{ (index .IPAM.Config 0).Subnet }}'`,
`kubectl get svc vote`, and the `curl http://$IP` output.

---

## Lab 36 · ⚠️ Rebuild the cluster on Calico

**Slide** 182
**Goal** NetworkPolicy is only as real as the plugin enforcing it. kind's default
CNI (kindnet) enforces **nothing** — it accepts NetworkPolicy objects and silently
ignores them.

### ⚠️⚠️ Read this before you start

`kind delete cluster` destroys **everything from Labs 01–35**: the cluster,
every Deployment, Service, Secret, ConfigMap, PVC and all its data, the Ingress
controller, MetalLB and metrics-server. Budget **30–40 minutes** including the
restore.

Your **images are safe** — they live in visora's Docker daemon, not in the
cluster. You do not rebuild them; you only re-`kind load` them.

**Two ways to run this course. Decide before you teach it:**

| | Pros | Cons |
|---|---|---|
| **A · as written** — kindnet for Days 1–3, rebuild on Calico here | Students *see* the policy silently fail first, which is the real lesson | 30–40 min of Day 4 spent rebuilding, and one chance to get the restore wrong in front of the class |
| **B · Calico from Lab 01** — put `disableDefaultCNI` in Lab 01's kind.yaml | No teardown, no risk, no lost time | You have to *assert* that kindnet ignores policy instead of demonstrating it |

I lean **B for a live class, A for this dry run** — we should prove the restore
works at least once, on a day when only we are watching. **Tell me which you want
and I will fix the slides to match.**

### Steps

**1 · optional — prove kindnet ignores policy first (2 minutes, worth it)**

```bash
kubectl apply -f - <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: deny-all, namespace: vote}
spec:
  podSelector: {}
  policyTypes: [Ingress]
EOF

# a deny-all policy is now in force. It should block everything:
kubectl run probe --rm -it --restart=Never --image=busybox:1.36 \
  -- nc -zv -w2 redis 6379
# ... and it connects anyway. kindnet accepted the object and ignored it.

kubectl delete networkpolicy deny-all -n vote
```

**2 · rebuild**

```bash
kind delete cluster --name iti

cat > ~/kind-day4.yaml <<'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
  podSubnet: "192.168.0.0/16"
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs: {node-labels: "ingress-ready=true"}
  extraPortMappings:
  - {containerPort: 80,    hostPort: 80}
  - {containerPort: 443,   hostPort: 443}
  - {containerPort: 30080, hostPort: 30080}
- role: worker
- role: worker
EOF

kind create cluster --name iti --config ~/kind-day4.yaml

# EXPECTED: every node NotReady. There is no CNI yet.
kubectl get nodes
```

Note `disableDefaultCNI` is a **config-file field**, not a CLI flag. There is no
`--disable-default-cni`.

**3 · install Calico**

```bash
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/calico.yaml

kubectl wait --for=condition=ready pod -l k8s-app=calico-node \
  -n kube-system --timeout=600s

kubectl get nodes
kubectl get pod -A -o wide | head -20
```

**4 · restore the app** — reload images, then apply the answer key

```bash
kubectl config set-context --current --namespace=vote

for i in vote result worker; do
  kind load docker-image iti/$i:v1 --name iti
done

kubectl apply -f ~/ITI-k8s/k8s-manifests/00-namespace.yaml
kubectl apply -f ~/ITI-k8s/k8s-manifests/

kubectl -n vote rollout status deploy/vote  --timeout=300s
kubectl -n vote rollout status deploy/db    --timeout=300s
kubectl -n vote rollout status deploy/worker --timeout=300s
kubectl get all -n vote
```

⚠️ `k8s-manifests/80-networkpolicy.yaml` is the **answer key** for Lab 37. If you
want the class to write those policies themselves, apply everything except it:

```bash
for f in ~/ITI-k8s/k8s-manifests/[0-7]*.yaml; do kubectl apply -f "$f"; done
```

**5 · re-install the Day 4 add-ons you still need**

```bash
# Ingress (Lab 34)
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait -n ingress-nginx --for=condition=ready pod \
  -l app.kubernetes.io/component=controller --timeout=300s

# metrics-server (Lab 31) — only if you plan to redo the HPA
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch deploy metrics-server -n kube-system --type=json \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
kubectl rollout status deploy/metrics-server -n kube-system --timeout=180s
```

MetalLB (Lab 35) is **not** needed for Lab 37 or 38 — skip it unless you want it.

### Pass when

- Step 2: `kubectl get nodes` → all three **`NotReady`**. That is correct; a node
  with no CNI cannot admit Pods. CoreDNS will sit `Pending` too.
- Step 3: all three nodes **`Ready`** within 2–5 minutes, and
  `kubectl get pod -A -o wide` shows Pod IPs in `192.168.x.x` (Calico's range),
  not `10.244.x.x` (kindnet's).
- Step 4: `kubectl get all -n vote` shows five Deployments available and the
  Services with endpoints.
- The app works again: `curl -s http://localhost:30080 | head -n3`.

### If it fails

- Nodes stuck `NotReady` past 5 min → `kubectl -n kube-system get pods | grep
  calico` and `kubectl -n kube-system logs -l k8s-app=calico-node --tail=50`.
  On a small VPS the Calico node agent is the memory-hungriest thing in this
  course — check `free -h`.
- Pods `ErrImageNeverPull` → step 4's `kind load` loop. The new cluster's nodes
  have empty image stores.
- `db` starts empty → **expected.** The PVC and its data went with the old
  cluster. Cast new votes.

### Report back

`kubectl get nodes` **before and after** Calico (the NotReady → Ready flip),
`kubectl get pod -A -o wide | head` showing 192.168.x.x IPs, `kubectl get all -n
vote`, and the `curl localhost:30080` result. Also tell me **A or B** for the
live class.

---

## Lab 37 · NetworkPolicy — lock down the data tier

**Slide** 183
**Goal** Only `vote` and `worker` may reach `redis`; only `worker` and `result`
may reach `db`.
**Needs** Lab 36 (Calico), and the app restored and working.

### Steps

**1 · prove it is open**

```bash
kubectl run probe --rm -it --restart=Never --image=busybox:1.36 \
  -- sh -c 'nc -zv -w2 redis 6379; nc -zv -w2 db 5432'
```

Both open. That is Kubernetes' default: **every Pod can reach every Pod.**

**2 · close it**

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: redis-allow}
spec:
  podSelector:
    matchLabels: {app: redis}
  policyTypes: [Ingress]
  ingress:
  - from:
    - podSelector: {matchLabels: {app: vote}}
    - podSelector: {matchLabels: {app: worker}}
    ports:
    - {protocol: TCP, port: 6379}
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: db-allow}
spec:
  podSelector:
    matchLabels: {app: db}
  policyTypes: [Ingress]
  ingress:
  - from:
    - podSelector: {matchLabels: {app: worker}}
    - podSelector: {matchLabels: {app: result}}
    ports:
    - {protocol: TCP, port: 5432}
EOF

kubectl get networkpolicy
kubectl describe networkpolicy redis-allow
```

**3 · verify both directions**

```bash
# an unlabelled Pod is now cut off
kubectl run probe --rm -it --restart=Never --image=busybox:1.36 \
  -- sh -c 'nc -zv -w2 redis 6379 || echo BLOCKED-REDIS; nc -zv -w2 db 5432 || echo BLOCKED-DB'

# a Pod that IS allowed still gets through
kubectl run probe2 --rm -it --restart=Never --labels=app=worker \
  --image=busybox:1.36 -- nc -zv -w2 db 5432
```

**4 · and the app itself still works**

Vote through the tunnel and confirm the result page still counts.

### Pass when

- Step 1: both `nc` calls report `open`.
- Step 3, first probe: **both** report `BLOCKED-…` after the ~2 s timeout.
- Step 3, second probe: `db (…:5432) open` — same image, same command, **only the
  label differs.**
- Step 4: the app is unaffected. `vote`, `worker` and `result` all carry labels
  the policies allow.

### If it fails

- Everything still connects → you are not on Calico.
  `kubectl -n kube-system get pods | grep calico` and check the Pod IP range:
  `kubectl get pod -o wide`. `10.244.x.x` means kindnet; redo Lab 36.
- The **app** breaks → your app Pods' labels do not match what the policies allow.
  `kubectl get pods --show-labels`.

### Teaching note

Three rules that cover most NetworkPolicy confusion:

1. **Default is allow-all.** A namespace with no policy is wide open.
2. **A policy is additive whitelisting, and it only applies to Pods its
   `podSelector` selects.** The moment *one* policy selects a Pod, that Pod
   becomes default-deny for the listed `policyTypes` — everything not explicitly
   allowed is dropped.
3. **The YAML lies to you.** Two `- podSelector:` entries as separate list items
   mean **OR**. Put both selectors under one list item and it means **AND**. The
   difference is one dash and it is the most common NetworkPolicy bug in the
   world.

### Report back

The `nc` output from step 1, both probes from step 3, and confirmation the app
still works.

---

## Lab 38 · The troubleshooting gauntlet

**Slide** 198
**Goal** Five planted faults, thirty minutes, one working Voting App at the end.
**Needs** Lab 36 (a working restored app).

Run in pairs: one student runs `break.sh`, the other fixes it without being told
what was broken.

### Steps

**1 · save the script**

```bash
cat > ~/break.sh <<'EOF'
#!/bin/sh
# 1 image that does not exist
kubectl set image deploy/vote vote=vote:v9-typo

# 2 memory limit far too small
kubectl patch deploy worker -p '{"spec":{"template":{"spec":{"containers":[{"name":"worker","resources":{"limits":{"memory":"8Mi"}}}]}}}}'

# 3 service selector no longer matches
kubectl patch svc redis -p '{"spec":{"selector":{"app":"redis-cache"}}}'

# 4 readiness probe on a path that 404s
kubectl patch deploy result -p '{"spec":{"template":{"spec":{"containers":[{"name":"result","readinessProbe":{"httpGet":{"path":"/healthz","port":80}}}]}}}}'

# 5 requests no node can satisfy
kubectl set resources deploy/db --requests=cpu=32,memory=64Gi

echo "5 faults planted. good luck."
EOF
chmod +x ~/break.sh
```

**2 · take a snapshot first, so you can always get back**

```bash
kubectl get deploy,svc -n vote -o yaml > ~/before-gauntlet.yaml
```

**3 · plant and hunt**

```bash
~/break.sh
kubectl get pods -n vote
```

Work the toolkit in order. Do not guess:

```bash
kubectl get pods                    # what is not Running?
kubectl describe pod <name>         # read the EVENTS
kubectl logs <name>                 # only if it actually started
kubectl get endpoints               # any Service with <none>?
kubectl get events --sort-by=.lastTimestamp | tail -20
```

**4 · the answers** — for the instructor, not the student

<details>
<summary>Fault → symptom → fix</summary>

| # | Symptom | Where it shows | Fix |
|---|---|---|---|
| 1 | `vote` Pods `ErrImagePull` / `ImagePullBackOff` | `describe pod` Events | `kubectl set image deploy/vote vote=iti/vote:v1` |
| 2 | `worker` `CrashLoopBackOff`, exit 137 | `describe pod` → `Last State: OOMKilled` | `kubectl set resources deploy/worker --limits=memory=512Mi` |
| 3 | app half-works; votes are not saved | `kubectl get endpoints redis` → `<none>` | `kubectl patch svc redis -p '{"spec":{"selector":{"app":"redis"}}}'` |
| 4 | `result` `0/1 Running`, `RESTARTS 0`, no endpoints | `describe pod` → `Readiness probe failed: 404` | patch the probe path back to `/` |
| 5 | `db` Pod `Pending`, forever | `describe pod` → `0/3 nodes available: Insufficient cpu` | `kubectl set resources deploy/db --requests=cpu=250m,memory=512Mi` |

</details>

### Pass when

- All five are found **by reading output**, not by reading the answer table.
- End state: `kubectl get pods -n vote` all `Running` and `READY`, all four
  Services have endpoints, and a fresh vote reaches the result page.

### Teaching note

Each fault teaches a different first move, and together they are the whole
debugging syllabus:

| Symptom class | First command |
|---|---|
| Pod not `Running` | `kubectl describe pod` — read the Events |
| Pod `Running` but `0/1` | probes — `describe`, look for `Readiness probe failed` |
| Pod restarting | `kubectl logs --previous` and `describe` for `Last State` |
| Pod `Pending` | `describe` — the scheduler writes down exactly why |
| Everything green, nothing works | `kubectl get endpoints` |

### Report back

Which faults you found, in what order, from which command — and the final
`kubectl get pods,endpoints -n vote`.

---

## Lab 39 · Final challenge

**Slide** 203
**Goal** Rebuild the whole Voting App from scratch, in a clean namespace, from
memory. 90 minutes.
**Needs** everything.

### The brief

Namespace `vote-final`. Ten requirements:

1. All five components as **Deployments** — `vote` (2 replicas), `result`,
   `worker`, `redis`, `db`.
2. Services named exactly **`redis`** and **`db`** (the apps default to those
   hostnames), plus `vote` and `result`.
3. `vote` reachable from outside the cluster.
4. Vote options come from a **ConfigMap**.
5. The Postgres password comes from a **Secret**, consumed by all three of `db`,
   `worker` and `result`.
6. `db` has a **PVC** and survives a Pod delete with its data.
7. `worker` waits for `db` with an **init container**.
8. **Readiness probes** on `vote`, `result` and `db`.
9. **requests and limits** on every container; `db` must be QoS `Guaranteed`.
10. An **HPA** on `vote` — min 2, max 8, at 60% CPU.

### Steps

```bash
kubectl create namespace vote-final
kubectl config set-context --current --namespace=vote-final

mkdir -p ~/final && cd ~/final
# write your YAML here, one file per component
kubectl apply -f .

kubectl get all,cm,secret,pvc,ing,hpa,netpol
```

### Pass when

Self-check, in order:

```bash
kubectl get pods                       # all Running, all READY
kubectl get endpoints                  # every Service has IPs
kubectl get pod -o custom-columns=NAME:.metadata.name,QOS:.status.qosClass
                                       # db must be Guaranteed
kubectl get pvc                        # Bound
kubectl get hpa                        # TARGETS not <unknown>
kubectl delete pod -l app=db           # then re-check the tally survived
```

And the real test: **vote in a browser, see the count change on the result page.**

### Instructor notes

The answer key is `~/ITI-k8s/k8s-manifests/`. Do not hand it out until they have
tried. Predictable stumbles, roughly in order of frequency:

- Service named `postgres` instead of `db` → silently broken app, no error anywhere
- `imagePullPolicy` forgotten → `ErrImageNeverPull`
- Deployment `selector` not matching the Pod template `labels` → the API rejects it
- Secret keys renamed but the Deployment still references the old names
- HPA created before any CPU **request** exists → `TARGETS <unknown>`

### Report back

Whether the ten requirements are achievable as written, anything ambiguous in the
brief, and roughly how long it took you.

---

## Lab 40 · ⚠️ Tear it all down

**Slide** 205
**Goal** Leave visora as clean as you found it.

### Steps

```bash
# namespaces first, if you want to watch things go
kubectl delete namespace vote vote-final demo --ignore-not-found
kubectl delete namespace ingress-nginx metallb-system --ignore-not-found

# the fastest, most complete option
kind delete cluster --name iti
kind get clusters                     # "No kind clusters found."

# reclaim the disk — the images and build cache are GBs
docker images | grep iti/
docker system df
docker system prune -af --volumes     # ⚠️ removes ALL unused docker data on visora
```

⚠️ `docker system prune -af --volumes` removes every unused image, container and
volume on the machine — **not just this course's**. If visora runs anything else
in Docker, use the targeted version instead:

```bash
docker rmi iti/vote:v1 iti/vote:v2 iti/result:v1 iti/worker:v1
docker builder prune -f
```

Finally:

```bash
docker ps -a
free -h
df -h /
```

### Pass when

- `kind get clusters` → `No kind clusters found.`
- `docker ps -a` shows no `iti-*` containers.
- `df -h /` has recovered most of the space Lab 06 consumed.

### Report back

`kind get clusters`, `docker ps -a`, and `df -h /` before and after.
---

# The `result-lab-NN.md` template

Copy this, fill it in, share it. Paste **real output**, not a summary — the
difference between `ImagePullBackOff` and `ErrImageNeverPull` is the whole
finding, and "it worked" throws it away.

````markdown
# result-lab-07.md

**Lab** 07 — Run the app as bare Pods, then kill one
**Date** 2026-07-2X
**Host** visora
**Verdict** PASS / PASS-WITH-NOTES / FAIL

## What I ran

<paste the commands you actually ran, including any you had to change>

## Output

```
<paste raw terminal output — the whole thing, not the interesting bit>
```

## Pass-when checklist

- [x] both Pods 1/1 Running
- [x] redis-cli ping -> PONG
- [ ] the watch stayed empty   <- IT DID NOT, see below

## Deviations

<anything you typed differently from LABS.md, and why>

## Problems

<error text, verbatim>

## Answers to the ❓ Confirm questions

<the lab's ❓ blocks, answered>

## Timing

<how long the lab took, wall clock — I use this to plan the four days>
````

Rules that make the loop work:

- **One lab per file.** Do not batch.
- **Raw output.** Copy-paste beats retyping; retyping loses the exact wording.
- **Report partial passes as PASS-WITH-NOTES**, not PASS. A step you had to work
  around is a step that will break in front of 25 students.
- **Answer every ❓.** Those are the places I am guessing.
- **Include timings.** Lab 06 (the Maven build) and Lab 36 (the Calico rebuild)
  decide whether the four-day schedule holds.

---

# HANDOVER — read this first if you are a new Claude session

## What this project is

`/Users/ziyadtarek/Desktop/iti-k8s-2026` — a 4-day hands-on Kubernetes course for
ITI DevOps 2026 students who are complete beginners.

| File | What it is |
|---|---|
| `k8s-slides.html` | **The deliverable.** 209 slides, 60 lab slides, 4 days. Generated — never hand-edit |
| `LABS.md` | **This file.** The runnable version of every lab, for the dry run |
| `COURSE-REVIEW.md` | The curriculum review that drove the rebuild. §15 records what shipped |
| `tools/` | The generator. `content_day{1..4}.py` → `assemble.py` → `k8s-slides.html` |
| `voting-app/` | The app the whole course is built around (Flask + Node + Java + redis + postgres) |
| `k8s-manifests/` | Instructor answer key — the Day 4 end state, and the restore path for Lab 36 |

Live at **https://ziyad-tarek1.github.io/ITI-k8s/** (GitHub Pages, `master`).

## What we are doing right now

**Validating every lab on a real server before it is taught.** Nothing in the deck
has ever been run against a live cluster — Docker was unavailable on the authoring
machine, which is recorded in `COURSE-REVIEW.md` §15.

The loop, per lab:

1. Ziyad `ssh visora`, runs one lab from `LABS.md` top to bottom.
2. Ziyad writes `result-lab-<NN>.md` and shares it.
3. **You**: check it against that lab's **Pass when** block.
   - Pass → confirm, and say what to run next.
   - Fail → find the root cause, fix **`LABS.md` and the slides**, then have the
     lab re-run.

`visora` = `89.116.25.8`, user `ziyad`, key at
`~/Documents/visora-server/keys/ziyad`. **Ziyad runs the commands, not you.**
Do not SSH in and "just check" — the point is that the procedure works when a
human follows it.

## The rules that matter

**1 · Numbering.** `LABS.md`'s Lab Map table is authoritative. The slide eyebrows
("Lab 1", "Lab 9") repeat and are unreliable — several are leftovers from the
deck's original 8-lab version. `result-lab-NN.md` always uses the Lab Map's NN.

**2 · Fix both places.** A bug found in a lab exists in the slides too. Fixing
only `LABS.md` means the deck — the artifact students actually see — keeps
teaching the broken thing. Slide edits go through the generator:

```bash
# edit tools/content_day<N>.py, then:
python3 tools/assemble.py     # rebuilds k8s-slides.html from tools/deck-base.html
python3 tools/autofit.py      # re-fits any slide whose content grew
python3 tools/verify.py       # structure, balance, day markers, duplicate titles
python3 tools/checks.py       # kubectl --dry-run on every embedded manifest
```

Never hand-edit `k8s-slides.html`; the next `assemble.py` run overwrites it.
Assembly is idempotent — rebuilding without source changes is byte-identical.

**3 · Commit every step.** Ziyad's standing preference: one commit per meaningful
step, not one big commit at the end. Push to `origin/master`; Pages redeploys
automatically.

**4 · Do not invent labs.** This phase is *transcribe, adapt, verify* the labs
that exist in the deck. Adding content is a different task.

## Open questions Ziyad still has to decide

- **Lab 36 (Calico rebuild), option A or B.** As written, Day 4 deletes the
  cluster mid-session and rebuilds on Calico so students *see* kindnet ignore a
  NetworkPolicy. The alternative is Calico from Lab 01 — safer, less vivid. See
  Lab 36's table. Not yet answered.
- **Ports 80/443 on visora.** Lab 00 checks. If they are taken by an existing web
  server, the kind config shifts to 8080/8443 and Lab 34 changes with it.

## Bugs found so far

Found by reading the slide source against the app source, **before running
anything**. All five are fixed in both `LABS.md` and the slides.

| # | Where | Problem | Status |
|---|---|---|---|
| B1 | Slide 80 | `sed 's/Cats vs Dogs/…/'` matches nothing — the template holds `{{option_a}} vs {{option_b}}!`. The v2 image would be identical to v1 and the rollout lab shows no change | fixed |
| B2 | Slides 52, 80 | `cd voting-app` vs `cd ~/voting-app`; neither exists until the repo is cloned, and no slide says to clone it | fixed — clone step added to slide 52 |
| B3 | Slides 93 → 94 | Both claim `nodePort: 30080`. Slide 94 fails with `provided port is already allocated` and the app never comes up | fixed — slides 79 and 93 rewritten to run in `demo`, and 93 now deletes `web-np` |
| B4 | Slide 182 | The Calico rebuild destroys Labs 01–35 and no slide says to restore anything, but slide 183 immediately probes `redis` and `db`. The rebuild config also dropped the `ingress-ready` node label, silently breaking any later ingress-nginx reinstall | fixed — label restored, and the note now names the `kind load` + `k8s-manifests/` restore |
| B5 | Slide 40 | `kubectl label pod web-1 tier-` removes a label `web-1` never had → `label "tier" not found` | fixed — uses `env-` |

## Progress log

Update this table as results come in. **This is the state of the dry run** — a new
session should read it first.

| Lab | Status | Result file | Notes |
|---|---|---|---|
| 00 | not run | — | |
| 01 | not run | — | |
| 02 | not run | — | |
| 03 | not run | — | |
| 04 | not run | — | |
| 05 | not run | — | |
| 06 | not run | — | |
| 07 | not run | — | |
| 08 | not run | — | |
| 09 | not run | — | |
| 10 | not run | — | |
| 11 | not run | — | |
| 12 | not run | — | |
| 13 | not run | — | |
| 14 | not run | — | |
| 15 | not run | — | |
| 16 | not run | — | |
| 17 | not run | — | |
| 18 | not run | — | |
| 19 | not run | — | |
| 20 | not run | — | |
| 21 | not run | — | |
| 22 | not run | — | |
| 23 | not run | — | |
| 24 | not run | — | |
| 25 | not run | — | |
| 26 | not run | — | |
| 27 | not run | — | |
| 28 | not run | — | |
| 29 | not run | — | |
| 30 | not run | — | |
| 31 | not run | — | |
| 32 | not run | — | |
| 33 | not run | — | |
| 34 | not run | — | |
| 35 | not run | — | |
| 36 | not run | — | |
| 37 | not run | — | |
| 38 | not run | — | |
| 39 | not run | — | |
| 40 | not run | — | |

## Suggested order for the dry run

Not strictly 00 → 40 in one sitting. The dependency chain means you cannot skip,
but you can stop at these points and resume later:

| Session | Labs | Wall clock | Why it stops here |
|---|---|---|---|
| 1 | 00 – 06 | ~1 h (mostly the Maven build) | the cluster and the images exist |
| 2 | 07 – 09 | ~45 min | end of Day 1 content |
| 3 | 10 – 17 | ~1.5 h | the app works end to end — the biggest milestone |
| 4 | 18 – 27 | ~2 h | Lab 26 alone is 15 min and is the payoff lab |
| 5 | 28 – 35 | ~1.5 h | last point before the destructive lab |
| 6 | 36 – 40 | ~1.5 h | the rebuild, and teardown |

Total ≈ **8 hours** of machine time to validate a 4-day course. Labs 06, 26, 32
and 36 are the slow ones and none of them can be rushed.
