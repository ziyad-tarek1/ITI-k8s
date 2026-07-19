# Voting App — Kubernetes manifests (instructor answer key)

The end state the four days build toward. Students write these incrementally;
this directory is the reference, not a starting point.

## What gets added when

| Day | Added |
|---|---|
| 1 | Bare Pods only — nothing here. Students feel the pain of no controller. |
| 2 | `Deployment` + `Service` for all five components |
| 3 | `ConfigMap`, `Secret`, `PersistentVolumeClaim`, probes |
| 4 | `resources`, `HorizontalPodAutoscaler`, `Ingress`, `NetworkPolicy` |

## Hard constraints

1. **The Services must be named `redis` and `db`.** The apps default to those
   hostnames. A Service named `postgres` gives a silently broken app.
2. **`imagePullPolicy: IfNotPresent` everywhere.** Images are built locally and
   pushed into the cluster with `kind load docker-image`; without this, kind
   tries to pull the tag from Docker Hub and every Pod lands in `ErrImagePull`.
3. **NetworkPolicy needs Calico.** kind's default CNI (kindnet) ignores
   NetworkPolicy by design ([kind#3705](https://github.com/kubernetes-sigs/kind/issues/3705)).
   The Day 4 cluster sets `networking.disableDefaultCNI: true` in its config
   file — this is a config field, **not** a CLI flag — and installs Calico.
   Pods stay `Pending` until Calico is up; that is expected.

## Apply order

```bash
kubectl apply -f 00-namespace.yaml
kubectl apply -f .          # the rest is order-independent
kubectl -n vote rollout status deploy/vote
```

## Build and load the images first

```bash
cd voting-app
docker build -t voteapp/worker:1.0 ./worker &     # slowest — start it first
docker build -t voteapp/vote:1.0   ./vote
docker build -t voteapp/result:1.0 ./result       # plain build = prod stage
wait
for i in vote result worker; do
  kind load docker-image voteapp/$i:1.0 --name iti
done
```
