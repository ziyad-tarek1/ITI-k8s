#!/usr/bin/env python3
"""Day 2 content — Workloads & Networking.

Blocks are keyed by name so the assembler can splice them between the kept
slides from the original deck. Every slide carries day=2.

The Voting App is the spine: five components in namespace `vote`, images
built locally on Day 1 and pushed into kind with `kind load docker-image`,
which is why every manifest here sets `imagePullPolicy: IfNotPresent`.
"""
from deck import cards, col, divider, hl, lab, note, slide, steps, table, term, two

# ---------------------------------------------------------------- tone hexes
# The .t-* classes set --tone/--tone-l; inline diagram nodes need the raw value.
TEAL, BLUE, GREEN, AMBER, MAROON, SLATE, VIOLET, GOLD = (
    "#2fc8a8", "#2496ed", "#46c95c", "#d98b22",
    "#c2273a", "#7089ad", "#8a7bd8", "#e3b341",
)


def tl(rows, gap=11):
    """A labelled timeline: rows of (label, [(text, tone, flex)]).

    Used by the rolling-update timeline and the init-vs-sidecar timeline.
    """
    out = []
    for label, boxes in rows:
        bx = "".join(
            f'<div class="vc-box" style="--tone:{tone};flex:{flex}">{txt}</div>'
            for txt, tone, flex in boxes
        )
        out.append(
            f'<div class="vc-row">'
            f'<div class="vc-link" style="width:120px;flex:none;text-align:right">{label}</div>'
            f'<div class="flowd" style="flex:1;gap:10px">{bx}</div></div>'
        )
    return f'<div class="stackd" style="gap:{gap}px">' + "".join(out) + "</div>"


def pm(nodes, links):
    """portmap row: nodes[i] separated by links[i] (top-label, bottom-label)."""
    parts = []
    for i, (title, sub, tone) in enumerate(nodes):
        if i:
            top, bot = links[i - 1]
            parts.append(
                f'<div class="pm-link"><div class="lb">{top}</div>'
                f'<div class="ln"></div><div class="lb2">{bot}</div></div>'
            )
        parts.append(
            f'<div class="pm-node" style="--tone:{tone}">'
            f'<div class="t">{title}</div><div class="s">{sub}</div></div>'
        )
    return '<div class="portmap r">' + "".join(parts) + "</div>"


def leg(items):
    """pm-legend: (key, explanation) pairs, two columns."""
    inner = "".join(
        f'<div class="pm-leg" style="--tone:{tone}"><div class="k">{k}</div>'
        f'<div class="v">{v}</div></div>'
        for k, v, tone in items
    )
    return f'<div class="pm-legend">{inner}</div>'


def panel(title, body, tone="t-teal", style=""):
    st = f' style="{style}"' if style else ""
    return (
        f'<div class="panel tone {tone}"{st}><div class="panel-t">'
        f'<span class="dot"></span>{title}</div>{body}</div>'
    )


def bul(items, cls="bul"):
    li = "".join(f"<li>{i}</li>" for i in items)
    return f'<ul class="{cls} r">{li}</ul>'


# =============================================================== day2open (2)
day2open = [
    divider(
        "09",
        "Workloads & Networking",
        "Yesterday you created Pods by hand and they stayed dead. Today a controller "
        "keeps them alive and a Service gives them a name.",
        [
            "ReplicaSets & Deployments",
            "Rollouts, history, rollback & restart",
            "Services, Endpoints & the four ports",
            "Cluster DNS & CoreDNS",
            "Multi-container Pods & init containers",
        ],
        notes=(
            "Open Day 2 by pointing backwards, not forwards. Yesterday ended with five bare "
            "Pods that half-worked and did not come back when killed. Everything today is a "
            "fix for something they already felt. By the end of the day the Voting App runs "
            "end to end for the first time &mdash; say that out loud, it is the day's carrot."
        ),
        day=2,
    ),
    slide(
        "Why bare Pods failed you",
        two(
            col(
                term(
                    "yesterday, in namespace vote",
                    "kubectl -n vote get pods\n"
                    "# NAME     READY   STATUS    RESTARTS   AGE\n"
                    "# vote     1/1     Running   0          18m\n"
                    "# redis    1/1     Running   0          18m\n\n"
                    "# now kill one\n"
                    "kubectl -n vote delete pod vote\n\n"
                    "kubectl -n vote get pods\n"
                    "# redis    1/1     Running   0          19m\n"
                    "# ...and vote is simply gone. Forever.",
                ),
            ),
            col(
                bul(
                    [
                        "<b>Nothing owns a bare Pod.</b> Delete it, drain its node, or let it "
                        "OOM &mdash; no controller notices and nothing recreates it.",
                        "<b>No replicas.</b> One Pod is one point of failure. You cannot scale "
                        "a Pod; you can only write the manifest again with a different name.",
                        "<b>No versioning.</b> Changing the image means delete + recreate &mdash; "
                        "a hard cut with downtime and no way back.",
                        "<b>No stable address.</b> Each new Pod gets a new IP, so nothing can "
                        "reliably find <code>redis</code> or <code>db</code>.",
                    ]
                ),
                note(
                    "n-why",
                    "Two objects fix all four. A <b>Deployment</b> owns and heals the Pods; a "
                    "<b>Service</b> gives them one address that never moves. That is Day 2.",
                    title="So what fixes this?",
                    style="margin-top:22px",
                ),
            ),
            ratio="1.02fr 1fr",
            gap=40,
        ),
        eyebrow="Where we left off",
        kicker="Five components running in namespace <code>vote</code> &mdash; and one "
        "<code>kubectl delete</code> away from permanent loss.",
        notes=(
            "Re-run yesterday's delete live if you have the cluster up; it takes ten seconds "
            "and it lands harder than a bullet list. The point students must leave with is that "
            "a Pod is not a workload, it is the unit a workload is made of. Everything on Day 2 "
            "is a controller or an abstraction sitting on top of the Pod, not a replacement for it."
        ),
        day=2,
    ),
]

# ============================================================== replicaset (2)
replicaset = [
    slide(
        "The ReplicaSet &mdash; a controller that counts",
        tl(
            [
                (
                    "desired: 3",
                    [
                        ("Pod vote-a &middot; Running", GREEN, 1),
                        ("Pod vote-b &middot; Running", GREEN, 1),
                        ("Pod vote-c &middot; Running", GREEN, 1),
                    ],
                ),
                (
                    "node dies",
                    [
                        ("Pod vote-a &middot; Running", GREEN, 1),
                        ("Pod vote-b &middot; Running", GREEN, 1),
                        ("Pod vote-c &middot; Lost", MAROON, 1),
                    ],
                ),
                (
                    "observed: 2",
                    [
                        ("Pod vote-a &middot; Running", GREEN, 1),
                        ("Pod vote-b &middot; Running", GREEN, 1),
                        ("2 &lt; 3 &rarr; create one", AMBER, 1),
                    ],
                ),
                (
                    "reconciled",
                    [
                        ("Pod vote-a &middot; Running", GREEN, 1),
                        ("Pod vote-b &middot; Running", GREEN, 1),
                        ("Pod vote-d &middot; Running", GREEN, 1),
                    ],
                ),
            ]
        )
        + cards(
            [
                (
                    "&#128290;",
                    "It only counts",
                    "Its entire job: keep the number of Pods matching its selector equal to "
                    "<code>replicas</code>. Too few &rarr; create. Too many &rarr; delete.",
                    "t-teal",
                ),
                (
                    "&#127991;",
                    "It finds Pods by label",
                    "It does not track Pods by name. It runs a selector query &mdash; any Pod "
                    "wearing the right labels is <em>its</em> Pod, even one you made by hand.",
                    "t-blue",
                ),
                (
                    "&#128260;",
                    "It never updates a Pod",
                    "Changing the template does <b>not</b> touch running Pods. A ReplicaSet has "
                    "no notion of a rollout &mdash; that is exactly the gap a Deployment fills.",
                    "t-amber",
                ),
            ]
        ),
        eyebrow="The layer under Deployments",
        kicker="One job, done forever: make the number of matching Pods equal "
        "<code>spec.replicas</code>.",
        notes=(
            "Students meet the ReplicaSet as a box in a diagram and never think about it again, "
            "which is fine until something breaks. Teach it as the world's dumbest control loop: "
            "count Pods matching a selector, compare to a number, act. Hammer the third card &mdash; "
            "a ReplicaSet cannot roll anything out, which is the whole reason Deployments exist."
        ),
        day=2,
    ),
    slide(
        "A ReplicaSet in YAML &mdash; and why you will never write one",
        two(
            col(
                term(
                    "replicaset.yaml",
                    "apiVersion: apps/v1\n"
                    "kind: ReplicaSet\n"
                    "metadata:\n"
                    "  name: vote\n"
                    "  namespace: vote\n"
                    "spec:\n"
                    "  replicas: 3\n"
                    "  selector:\n"
                    "    matchLabels:\n"
                    "      app: vote       # which Pods are mine\n"
                    "  template:           # <- a Pod, verbatim\n"
                    "    metadata:\n"
                    "      labels:\n"
                    "        app: vote     # must match the selector\n"
                    "    spec:\n"
                    "      containers:\n"
                    "        - name: vote\n"
                    "          image: iti/vote:v1\n"
                    "          imagePullPolicy: IfNotPresent",
                    cls="xs",
                ),
            ),
            col(
                bul(
                    [
                        "Compare it to the Deployment manifest &mdash; it is the "
                        "<b>same three fields</b>: <code>replicas</code>, "
                        "<code>selector</code>, <code>template</code>. A Deployment is a "
                        "ReplicaSet plus rollout machinery.",
                        "<b>Deployments create ReplicaSets for you</b> &mdash; one per revision. "
                        "Roll out three times and you own three ReplicaSets, two of them scaled "
                        "to zero, kept so <code>rollout undo</code> is instant.",
                        "Write a ReplicaSet directly and you throw away rolling updates, "
                        "history, rollback and <code>rollout restart</code> &mdash; for "
                        "<b>zero</b> benefit.",
                    ]
                ),
                term(
                    "see the ones you already own",
                    "kubectl -n vote get rs\n"
                    "# NAME             DESIRED   CURRENT   READY\n"
                    "# vote-6d4f8b9c7   3         3         3\n\n"
                    "# who owns this ReplicaSet?\n"
                    "kubectl -n vote get rs vote-6d4f8b9c7 \\\n"
                    "  -o jsonpath='{.metadata.ownerReferences[0].kind}'\n"
                    "# Deployment",
                    cls="xs",
                ),
                note(
                    "n-warn",
                    "Never <code>kubectl delete rs</code> under a live Deployment &mdash; the "
                    "Deployment controller simply recreates it seconds later. Delete the "
                    "<b>Deployment</b> instead.",
                    title="Do not fight the owner",
                    style="margin-top:18px",
                ),
            ),
            ratio="1fr 1.08fr",
            gap=36,
        ),
        eyebrow="Anatomy of a manifest",
        kicker="Worth reading once so the hash-suffixed <code>vote-6d4f8b9c7</code> in "
        "<code>get all</code> stops being a mystery.",
        notes=(
            "Show them the YAML, then tell them plainly they will never type it. The reason to "
            "teach it is diagnostic: when they run <code>kubectl get all</code> and see a "
            "hash-suffixed ReplicaSet they should know exactly what it is and who made it. "
            "The ownerReferences trick is worth doing live &mdash; it makes the ownership chain "
            "Deployment &rarr; ReplicaSet &rarr; Pod concrete rather than diagrammatic."
        ),
        day=2,
    ),
]

# ============================================================= deploy_extra (1)
deploy_extra = [
    slide(
        "The Deployment selector is immutable",
        two(
            col(
                term(
                    "you edit the selector and re-apply",
                    "# vote/deployment.yaml, changing app: vote -> app: vote-web\n"
                    "kubectl -n vote apply -f vote/deployment.yaml\n\n"
                    "# The Deployment \"vote\" is invalid: spec.selector:\n"
                    "#   Invalid value: v1.LabelSelector{MatchLabels:\n"
                    "#   map[string]string{\"app\":\"vote-web\"}, ...}:\n"
                    "#   field is immutable",
                ),
                note(
                    "n-warn",
                    "This is not a bug and there is no <code>--force-selector</code>. "
                    "<code>spec.selector</code> is fixed for the life of the object &mdash; on "
                    "Deployments, ReplicaSets, DaemonSets and StatefulSets alike.",
                    title="No flag will save you",
                    style="margin-top:20px",
                ),
            ),
            col(
                term(
                    "the fix: replace the object, keep the Pods",
                    "# 1. delete the Deployment, orphan its Pods so traffic keeps flowing\n"
                    "kubectl -n vote delete deploy vote --cascade=orphan\n\n"
                    "# 2. apply the new manifest with the new selector\n"
                    "kubectl -n vote apply -f vote/deployment.yaml\n\n"
                    "# 3. the new Deployment makes its own Pods; sweep the orphans\n"
                    "kubectl -n vote delete pod -l app=vote\n\n"
                    "# no traffic to protect? just do the blunt version\n"
                    "kubectl -n vote replace --force -f vote/deployment.yaml",
                    cls="xs",
                ),
                note(
                    "n-why",
                    "The selector is the Deployment&rsquo;s <b>identity</b>. Change it and the "
                    "controller would instantly disown every running Pod &mdash; leaving them "
                    "alive, unmanaged and invisible. The API refuses rather than orphan your "
                    "workload behind your back.",
                    title="Why lock it?",
                    style="margin-top:18px",
                ),
            ),
            ratio="1fr 1fr",
            gap=34,
        ),
        eyebrow="The error you are going to hit",
        kicker="Change <code>spec.selector</code> on a live Deployment and the API server "
        "rejects it outright. Every student hits this once.",
        notes=(
            "Pre-empt this one &mdash; it is guaranteed to happen the first time somebody tidies "
            "their labels, and if they have not seen it they assume the cluster is broken. Say "
            "the rule as a sentence: labels on the template are editable, the selector is not. "
            "The <code>--cascade=orphan</code> version is the one to remember; it is how you do "
            "this without dropping traffic in production."
        ),
        day=2,
    ),
]

# ================================================================ vadeploy (2)
_VOTE_DEPLOY = (
    "cat <<'EOF' | kubectl apply -f -\n"
    "apiVersion: apps/v1\n"
    "kind: Deployment\n"
    "metadata:\n"
    "  name: vote\n"
    "  namespace: vote\n"
    "spec:\n"
    "  replicas: 2\n"
    "  selector:\n"
    "    matchLabels:\n"
    "      app: vote\n"
    "  template:\n"
    "    metadata:\n"
    "      labels:\n"
    "        app: vote\n"
    "    spec:\n"
    "      containers:\n"
    "        - name: vote\n"
    "          image: iti/vote:v1\n"
    "          imagePullPolicy: IfNotPresent   # built locally, kind-loaded\n"
    "          ports:\n"
    "            - containerPort: 80\n"
    "EOF"
)

# The two locally-built images. Folded into flow style so four manifests fit
# two side-by-side panels instead of scrolling off the slide.
_APP_DEPLOYS = (
    "cat <<'EOF' | kubectl apply -f -\n"
    "apiVersion: apps/v1\n"
    "kind: Deployment\n"
    "metadata: {name: result}\n"
    "spec:\n"
    "  selector: {matchLabels: {app: result}}\n"
    "  template:\n"
    "    metadata: {labels: {app: result}}\n"
    "    spec: {containers: [{name: result, image: \"iti/result:v1\",\n"
    "      imagePullPolicy: IfNotPresent, ports: [{containerPort: 80}]}]}\n"
    "---\n"
    "apiVersion: apps/v1\n"
    "kind: Deployment\n"
    "metadata: {name: worker}     # no ports - nothing ever calls worker\n"
    "spec:\n"
    "  selector: {matchLabels: {app: worker}}\n"
    "  template:\n"
    "    metadata: {labels: {app: worker}}\n"
    "    spec: {containers: [{name: worker, image: \"iti/worker:v1\",\n"
    "      imagePullPolicy: IfNotPresent}]}\n"
    "EOF"
)

_INFRA_DEPLOYS = (
    "cat <<'EOF' | kubectl apply -f -\n"
    "apiVersion: apps/v1\n"
    "kind: Deployment\n"
    "metadata: {name: redis}      # Docker Hub image - no pull policy\n"
    "spec:\n"
    "  selector: {matchLabels: {app: redis}}\n"
    "  template:\n"
    "    metadata: {labels: {app: redis}}\n"
    "    spec: {containers: [{name: redis, image: \"redis:alpine\",\n"
    "      ports: [{containerPort: 6379}]}]}\n"
    "---\n"
    "apiVersion: apps/v1\n"
    "kind: Deployment\n"
    "metadata: {name: db}         # POSTGRES_USER defaults to postgres\n"
    "spec:\n"
    "  selector: {matchLabels: {app: db}}\n"
    "  template:\n"
    "    metadata: {labels: {app: db}}\n"
    "    spec: {containers: [{name: db, image: \"postgres:14\",\n"
    "      env: [{name: POSTGRES_PASSWORD, value: postgres}]}]}\n"
    "EOF\n\n"
    "kubectl get deploy,rs,pods   # the whole ownership chain"
)

vadeploy = [
    lab(
        "Voting App: bare Pods &rarr; Deployments",
        two(
            col(
                term("clear yesterday's bare Pods", _VOTE_DEPLOY, cls="xs"),
            ),
            col(
                term(
                    "first, remove the unmanaged Pods",
                    "kubectl config set-context --current --namespace=vote\n"
                    "kubectl get pods\n\n"
                    "# bare Pods have no owner - delete them by hand\n"
                    "kubectl delete pod --all\n"
                    "kubectl get pods   # No resources found",
                    cls="xs",
                ),
                bul(
                    [
                        "<code>replicas: 2</code> on <code>vote</code> so the load balancing "
                        "is visible later &mdash; the page footer prints the Pod hostname.",
                        "<b><code>imagePullPolicy: IfNotPresent</code> is mandatory.</b> "
                        "<code>iti/vote:v1</code> only exists inside the kind nodes because you ran "
                        "<code>kind load docker-image</code>. Without it the kubelet tries "
                        "Docker Hub and you get <code>ErrImagePull</code>.",
                        "The template labels and the selector are the same string. That equality "
                        "is the only thing connecting this Deployment to its Pods.",
                    ],
                    cls="bul tight",
                ),
                note(
                    "n-tip",
                    "Setting the namespace on your context once beats typing <code>-n vote</code> "
                    "two hundred times today. Check it with "
                    "<code>kubectl config view --minify | grep namespace</code>.",
                    style="margin-top:16px",
                ),
            ),
            ratio="1fr 1.1fr",
            gap=32,
        ),
        eyebrow="Lab 9 &middot; Workloads (1 of 2)",
        kicker="Same containers, same namespace &mdash; now with an owner. Start with "
        "<code>vote</code>, the one you know best.",
        notes=(
            "Do the delete first and let them see the empty namespace &mdash; it makes the point "
            "that these Pods were never coming back on their own. Then apply the Deployment and "
            "immediately delete one of its Pods; a replacement appears in about a second. That "
            "contrast, five minutes apart, is the entire argument for controllers."
        ),
        day=2,
    ),
    lab(
        "&hellip;and the other four components",
        two(
            col(term("the two images you built", _APP_DEPLOYS, cls="xs")),
            col(term("the two off-the-shelf images", _INFRA_DEPLOYS, cls="xs")),
            ratio="1fr 1fr",
            gap=30,
        ),
        eyebrow="Lab 9 &middot; Workloads (2 of 2)",
        kicker="Same manifest, folded into flow style. Note <b>no <code>ports:</code> on "
        "<code>worker</code></b> &mdash; nothing calls it, so it will never get a Service "
        "either.",
        notes=(
            "Point out that <code>redis:alpine</code> and <code>postgres:14</code> come from "
            "Docker Hub, so they do not need IfNotPresent &mdash; only the images the class "
            "built do. Dwell on worker having no ports: not everything needs a Service, and "
            "that instinct costs people marks in interviews. Close by saying the app is still "
            "broken and naming the reason: there is no DNS name for redis yet. That sets up "
            "the Services block."
        ),
        day=2,
    ),
]

# ================================================================= rollouts (4)
rollouts = [
    slide(
        "How a rolling update actually moves",
        tl(
            [
                (
                    "start",
                    [
                        ("v1", GREEN, 1), ("v1", GREEN, 1), ("v1", GREEN, 1), ("v1", GREEN, 1),
                    ],
                ),
                (
                    "+ surge",
                    [
                        ("v1", GREEN, 1), ("v1", GREEN, 1), ("v1", GREEN, 1), ("v1", GREEN, 1),
                        ("v2 Pending", AMBER, 1),
                    ],
                ),
                (
                    "v2 Ready",
                    [
                        ("v1", GREEN, 1), ("v1", GREEN, 1), ("v1", GREEN, 1),
                        ("v1 Terminating", MAROON, 1), ("v2", BLUE, 1),
                    ],
                ),
                (
                    "repeat &times;3",
                    [
                        ("v1", GREEN, 1), ("v2", BLUE, 1), ("v2", BLUE, 1),
                        ("v2", BLUE, 1), ("v2 Pending", AMBER, 1),
                    ],
                ),
                (
                    "done",
                    [
                        ("v2", BLUE, 1), ("v2", BLUE, 1), ("v2", BLUE, 1), ("v2", BLUE, 1),
                    ],
                ),
            ]
        )
        + two(
            col(
                term(
                    "spec.strategy",
                    "spec:\n"
                    "  replicas: 4\n"
                    "  strategy:\n"
                    "    type: RollingUpdate\n"
                    "    rollingUpdate:\n"
                    "      maxSurge: 1          # extra Pods allowed above 4\n"
                    "      maxUnavailable: 0    # never dip below 4 ready\n",
                    cls="xs",
                ),
            ),
            col(
                bul(
                    [
                        "<code>maxSurge</code> &mdash; how far <b>above</b> "
                        "<code>replicas</code> you may go. Costs capacity, buys safety.",
                        "<code>maxUnavailable</code> &mdash; how far <b>below</b> ready you may "
                        "dip. <code>0</code> means capacity never drops.",
                        "Defaults are <b>25% each</b>, which on 4 replicas rounds to surge 1 / "
                        "unavailable 1. Both zero is illegal &mdash; nothing could ever move.",
                    ],
                    cls="bul tight",
                ),
                note(
                    "n-warn",
                    "&ldquo;Ready&rdquo; here means <b>the container started</b>, not "
                    "&ldquo;the app can serve&rdquo;. Until you add a readiness probe on Day 3 a "
                    "rolling update still drops requests &mdash; capacity holds, correctness does not.",
                    title="Ready &ne; able to serve",
                    style="margin-top:14px",
                ),
            ),
            ratio="1fr 1.15fr",
            gap=30,
        ),
        eyebrow="Rollout mechanics",
        kicker="A new ReplicaSet is scaled up while the old one is scaled down &mdash; two "
        "numbers control the whole dance.",
        notes=(
            "Walk the timeline row by row with a finger; it is the clearest way to show that "
            "both ReplicaSets exist at once. Emphasise that Kubernetes is scaling two "
            "ReplicaSets in opposite directions, not mutating Pods. The warning box matters: "
            "we promised zero downtime on Day 1 and we do not actually have it yet &mdash; "
            "tell them Day 3 pays that debt off with a lab."
        ),
        day=2,
    ),
    slide(
        "rollout status &mdash; watching it land",
        two(
            col(
                term(
                    "watch a rollout",
                    "kubectl set image deploy/vote vote=iti/vote:v2\n\n"
                    "kubectl rollout status deploy/vote\n"
                    "# Waiting for deployment \"vote\" rollout to finish:\n"
                    "#   1 out of 2 new replicas have been updated...\n"
                    "# Waiting for deployment \"vote\" rollout to finish:\n"
                    "#   1 old replicas are pending termination...\n"
                    "# deployment \"vote\" successfully rolled out\n\n"
                    "# useful in CI - exits non-zero if it stalls\n"
                    "kubectl rollout status deploy/vote --timeout=120s\n"
                    "echo $?",
                ),
            ),
            col(
                bul(
                    [
                        "It <b>blocks</b> until every replica is updated and available, then "
                        "exits <code>0</code>. That is why it belongs in every deploy pipeline "
                        "&mdash; without it your CI reports success before the app is up.",
                        "If the new Pods never become ready, the Deployment gives up after "
                        "<code>progressDeadlineSeconds</code> (default <b>600</b>) and the "
                        "command exits non-zero.",
                        "It does <b>not</b> roll back on failure. A stalled rollout just sits "
                        "there, half old and half new, until a human acts.",
                    ]
                ),
                term(
                    "when it stalls, ask why",
                    "kubectl rollout status deploy/vote\n"
                    "# error: deployment \"vote\" exceeded its progress deadline\n\n"
                    "kubectl describe deploy vote | tail -20\n"
                    "kubectl get pods -l app=vote\n"
                    "# vote-7f9c... 0/1  ImagePullBackOff",
                    cls="xs",
                ),
            ),
            ratio="1fr 1.05fr",
            gap=34,
        ),
        eyebrow="Verb 1 of 4",
        kicker="The command that turns &ldquo;I applied it&rdquo; into &ldquo;it is actually "
        "running&rdquo;.",
        notes=(
            "The exit code is the part people miss. In a pipeline <code>kubectl apply</code> "
            "succeeding only means the API server accepted the YAML &mdash; "
            "<code>rollout status</code> is what proves the Pods came up. Stress that a failed "
            "rollout does not auto-revert; Kubernetes stops, it does not undo. Someone always "
            "assumes it heals itself."
        ),
        day=2,
    ),
    slide(
        "rollout history &amp; the CHANGE-CAUSE",
        two(
            col(
                term(
                    "what changed, and when",
                    "kubectl rollout history deploy/vote\n"
                    "# REVISION  CHANGE-CAUSE\n"
                    "# 1         <none>\n"
                    "# 2         <none>\n"
                    "# 3         vote v2: new option labels\n\n"
                    "# the full Pod template of one revision\n"
                    "kubectl rollout history deploy/vote --revision=2\n"
                    "# Pod Template:\n"
                    "#   Containers:\n"
                    "#    vote:\n"
                    "#     Image:  iti/vote:v1\n"
                    "#     ...",
                    cls="xs",
                ),
            ),
            col(
                term(
                    "fill the column in: annotate the template",
                    "# best: put it in the manifest, one atomic apply\n"
                    "metadata:\n"
                    "  annotations:\n"
                    "    kubernetes.io/change-cause: \"vote v2: new option labels\"\n\n"
                    "# quick version, imperative\n"
                    "kubectl annotate deploy/vote --overwrite \\\n"
                    "  kubernetes.io/change-cause=\"vote v2: new option labels\"",
                    cls="xs",
                ),
                bul(
                    [
                        "One revision = one <b>ReplicaSet</b>. History is just the ReplicaSets "
                        "the Deployment still owns &mdash; keep more with "
                        "<code>revisionHistoryLimit</code> (default <b>10</b>).",
                        "A revision is only created when the <b>Pod template</b> changes. "
                        "Scaling to 10 replicas does not make a new revision.",
                        "<code>&lt;none&gt;</code> forever is the norm, and it makes a 3am "
                        "rollback a guessing game. <b>Set the change-cause.</b>",
                    ],
                    cls="bul tight",
                ),
                note(
                    "n-warn",
                    "The old <code>--record</code> flag is <b>deprecated</b> and gone from "
                    "recent kubectl. Annotate the object instead.",
                    style="margin-top:14px",
                ),
            ),
            ratio="1fr 1.12fr",
            gap=32,
        ),
        eyebrow="Verbs 2 &amp; 3 of 4",
        kicker="Every revision is a ReplicaSet parked at zero, waiting to be useful.",
        notes=(
            "Run <code>get rs</code> next to <code>rollout history</code> so they see the "
            "one-to-one mapping &mdash; revision numbers are not magic, they are ReplicaSets. "
            "The scaling point catches people out: they scale, expect revision 4, and get "
            "nothing. And insist on change-cause; the empty column is the single most common "
            "regret during a real incident."
        ),
        day=2,
    ),
    slide(
        "rollout restart &amp; rollout undo",
        two(
            col(
                panel(
                    "restart &mdash; replace every Pod, same spec",
                    term(
                        "graceful, rolling, no downtime dip",
                        "kubectl rollout restart deploy/vote\n"
                        "kubectl rollout status deploy/vote",
                        cls="xs",
                    )
                    + bul(
                        [
                            "It stamps <code>kubectl.kubernetes.io/restartedAt</code> onto the "
                            "Pod template. New template &rarr; new ReplicaSet &rarr; normal "
                            "rolling replacement.",
                            "Nothing about your app changes &mdash; same image, same config, "
                            "fresh processes.",
                        ],
                        cls="bul tight",
                    ),
                    tone="t-violet",
                ),
            ),
            col(
                panel(
                    "undo &mdash; go back a revision",
                    term(
                        "instant, because the old RS still exists",
                        "kubectl rollout undo deploy/vote\n\n"
                        "# or to a specific revision\n"
                        "kubectl rollout undo deploy/vote --to-revision=2",
                        cls="xs",
                    )
                    + bul(
                        [
                            "It scales the old ReplicaSet back up and the current one down &mdash; "
                            "no image pull, no rebuild, seconds.",
                            "The rollback becomes a <b>new</b> revision at the top of the "
                            "history. You never lose the trail.",
                        ],
                        cls="bul tight",
                    ),
                    tone="t-gold",
                ),
            ),
            ratio="1fr 1fr",
            gap=30,
        )
        + note(
            "n-warn",
            "A ConfigMap or Secret consumed as <b>environment variables</b> is read once, at "
            "container start. Change it and running Pods keep the old values forever &mdash; "
            "<code>rollout restart</code> is the fix. Mounted as files they do update in place, "
            "eventually. We will hit this on Day 3.",
            title="Why you will actually need restart",
            style="margin-top:20px",
        ),
        eyebrow="Verb 4 of 4",
        kicker="Two commands that both work by creating a new ReplicaSet &mdash; one forwards, "
        "one backwards.",
        notes=(
            "Restart is the verb nobody teaches and everybody needs. Give the three real reasons: "
            "picking up a changed ConfigMap or Secret, forcing a re-pull of a mutable tag, and "
            "clearing a wedged in-memory state. Then contrast with the wrong instinct &mdash; "
            "<code>delete pod</code> kills them all at once, restart rolls them. The Day 3 "
            "forward reference is deliberate; leave it hanging."
        ),
        day=2,
    ),
]

# ================================================================ varollout (2)
varollout = [
    lab(
        "Roll out a new vote image",
        two(
            col(
                term(
                    "build v2 and get it into kind",
                    "cd ~/voting-app\n\n"
                    "# make a visible change - edit the page heading\n"
                    "sed -i 's/Cats vs Dogs/Cats vs Dogs v2/' vote/templates/index.html\n\n"
                    "docker build -t iti/vote:v2 ./vote\n\n"
                    "# the cluster cannot see your local daemon - push it in\n"
                    "kind load docker-image iti/vote:v2 --name iti\n\n"
                    "# prove it landed on the nodes\n"
                    "docker exec iti-worker crictl images | grep vote",
                    cls="xs",
                ),
            ),
            col(
                term(
                    "ship it, with a reason attached",
                    "kubectl set image deploy/vote vote=iti/vote:v2\n\n"
                    "kubectl annotate deploy/vote --overwrite \\\n"
                    "  kubernetes.io/change-cause=\"vote v2: heading change\"\n\n"
                    "# in a second pane, watch the Pods turn over\n"
                    "kubectl get pods -l app=vote -w\n\n"
                    "# in the first, watch the rollout finish\n"
                    "kubectl rollout status deploy/vote\n\n"
                    "# two ReplicaSets now - old one parked at 0\n"
                    "kubectl get rs -l app=vote",
                    cls="xs",
                ),
                note(
                    "n-tip",
                    "Two panes or this lab is invisible. <code>get pods -w</code> on the left, "
                    "<code>rollout status</code> on the right &mdash; the surge Pod appearing "
                    "before the old one terminates is the whole lesson.",
                    style="margin-top:16px",
                ),
            ),
            ratio="1fr 1.05fr",
            gap=32,
        ),
        eyebrow="Lab 10 &middot; Rollouts (1 of 2)",
        kicker="Real image, real change, real rolling update &mdash; and one command back "
        "if you hate it.",
        notes=(
            "The <code>kind load</code> step is the one they will forget, and the symptom is "
            "<code>ErrImagePull</code> on a tag that exists perfectly well in "
            "<code>docker images</code>. Make them say out loud why: the kind nodes are "
            "separate container runtimes with their own image stores. The crictl check is worth "
            "running once so they can debug it themselves next time."
        ),
        day=2,
    ),
    lab(
        "Read the history, then undo it",
        two(
            col(
                term(
                    "inspect what you just did",
                    "kubectl rollout history deploy/vote\n"
                    "# REVISION  CHANGE-CAUSE\n"
                    "# 1         <none>\n"
                    "# 2         vote v2: heading change\n\n"
                    "# what image was revision 1 running?\n"
                    "kubectl rollout history deploy/vote --revision=1\n\n"
                    "# confirm the live Pods are on v2\n"
                    "kubectl get pods -l app=vote \\\n"
                    "  -o jsonpath='{.items[*].spec.containers[0].image}'\n"
                    "# iti/vote:v2 iti/vote:v2",
                    cls="xs",
                ),
            ),
            col(
                term(
                    "roll it back",
                    "kubectl rollout undo deploy/vote\n"
                    "kubectl rollout status deploy/vote\n\n"
                    "# back on v1 - and note the new revision 3\n"
                    "kubectl rollout history deploy/vote\n"
                    "# REVISION  CHANGE-CAUSE\n"
                    "# 2         vote v2: heading change\n"
                    "# 3         <none>\n\n"
                    "# the old ReplicaSet was scaled back up, not rebuilt\n"
                    "kubectl get rs -l app=vote\n\n"
                    "# and force a clean restart just to see it\n"
                    "kubectl rollout restart deploy/vote",
                    cls="xs",
                ),
                note(
                    "n-info",
                    "Revision <b>1 disappears</b> after the undo and reappears as revision 3. "
                    "Rolling back is itself a change, so it gets its own number &mdash; the "
                    "history is a log, not a stack.",
                    style="margin-top:16px",
                ),
            ),
            ratio="1fr 1.05fr",
            gap=32,
        ),
        eyebrow="Lab 10 &middot; Rollouts (2 of 2)",
        kicker="Undo is fast because nothing is rebuilt &mdash; the old ReplicaSet never left.",
        notes=(
            "Time the undo out loud; it is usually under five seconds and that surprises people. "
            "Explain it costs nothing because the v1 ReplicaSet was sitting at zero the whole "
            "time. The renumbering after undo confuses everyone once &mdash; walk through it "
            "slowly. Finish with <code>rollout restart</code> so they have run all four verbs."
        ),
        day=2,
    ),
]

# ================================================================ svc_extra (3)
svc_extra = [
    slide(
        "Headless Services &mdash; clusterIP: None",
        two(
            col(
                term(
                    "headless.yaml",
                    "apiVersion: v1\n"
                    "kind: Service\n"
                    "metadata:\n"
                    "  name: db\n"
                    "  namespace: vote\n"
                    "spec:\n"
                    "  clusterIP: None      # <- headless\n"
                    "  selector:\n"
                    "    app: db\n"
                    "  ports:\n"
                    "    - port: 5432\n"
                    "      targetPort: 5432",
                    cls="xs",
                ),
                note(
                    "n-info",
                    "No virtual IP, no kube-proxy rules, no load balancing. DNS does all the "
                    "work &mdash; the Service becomes a name that returns a <b>list</b>.",
                    style="margin-top:16px",
                ),
            ),
            col(
                term(
                    "what DNS returns",
                    "# normal ClusterIP Service\n"
                    "nslookup db\n"
                    "# Address: 10.96.148.22        <- one stable virtual IP\n\n"
                    "# headless Service, 3 backing Pods\n"
                    "nslookup db\n"
                    "# Address: 10.244.1.9          <- the Pod IPs\n"
                    "# Address: 10.244.2.4          <- themselves\n"
                    "# Address: 10.244.3.7",
                    cls="xs",
                ),
                bul(
                    [
                        "<b>Use it when the client must pick.</b> Database replicas where one "
                        "is the primary; Kafka brokers; anything doing its own sharding or "
                        "leader election.",
                        "<b>StatefulSets need it</b> &mdash; it is what gives each Pod a stable "
                        "per-Pod DNS name like <code>db-0.db.vote.svc.cluster.local</code>. "
                        "We meet those on Day 3.",
                        "<b>Do not reach for it by default.</b> A plain ClusterIP is right for "
                        "the other 95% &mdash; stateless things you want load-balanced.",
                    ],
                    cls="bul tight",
                ),
            ),
            ratio="1fr 1.15fr",
            gap=32,
        ),
        eyebrow="The fourth kind of Service",
        kicker="Sometimes you do <em>not</em> want load balancing &mdash; you want the actual "
        "list of Pods.",
        notes=(
            "Frame this as the opposite of everything they just learned: a Service that "
            "deliberately refuses to hide the Pods. The one-line rule is &lsquo;headless when "
            "the client needs to choose a specific backend&rsquo;. Do not go deep on "
            "StatefulSets here &mdash; just plant that headless is a prerequisite for them so "
            "Day 3 has somewhere to land."
        ),
        day=2,
    ),
    slide(
        "Endpoints &mdash; the missing link",
        pm(
            [
                ("Service", "vote &middot; 10.96.4.11:80", TEAL),
                ("EndpointSlice", "the live Pod list", VIOLET),
                ("Pods", "10.244.1.9:80 &middot; 10.244.2.4:80", GREEN),
            ],
            [
                ("selector: app=vote", "endpoints controller watches"),
                ("kube-proxy programmes these", "actual traffic destination"),
            ],
        )
        + two(
            col(
                term(
                    "look at the link",
                    "kubectl get endpoints vote\n"
                    "# NAME   ENDPOINTS                       AGE\n"
                    "# vote   10.244.1.9:80,10.244.2.4:80     4m\n\n"
                    "# the modern object kube-proxy actually reads\n"
                    "kubectl get endpointslices -l "
                    "kubernetes.io/service-name=vote\n\n"
                    "kubectl describe endpoints vote",
                    cls="xs",
                ),
            ),
            col(
                bul(
                    [
                        "A Service does <b>not</b> point at Pods. A controller watches the "
                        "selector and writes the matching Pod IPs into an "
                        "<b>EndpointSlice</b>; kube-proxy programmes the node from that.",
                        "<b>Only ready Pods are listed.</b> This is precisely how a readiness "
                        "probe removes a Pod from traffic without killing it &mdash; Day 3.",
                        "<code>ENDPOINTS</code> empty on a Service you believe is fine means "
                        "<b>the selector matches nothing</b>. It is the fastest diagnosis in "
                        "Kubernetes and almost nobody knows to look.",
                    ],
                    cls="bul tight",
                ),
                note(
                    "n-tip",
                    "&ldquo;Service returns connection refused&rdquo; &rarr; "
                    "<code>kubectl get endpoints &lt;svc&gt;</code> <b>first</b>. Empty means a "
                    "label problem; populated means an app problem. Two seconds, half the "
                    "search space gone.",
                    style="margin-top:14px",
                ),
            ),
            ratio="1fr 1.15fr",
            gap=32,
        ),
        eyebrow="Service &rarr; Endpoints &rarr; Pod",
        kicker="The object in the middle that students never see &mdash; and the first thing "
        "to check when a Service &ldquo;does not work&rdquo;.",
        notes=(
            "This slide converts hours of future frustration into one command. Make them repeat "
            "the diagnostic rule back to you: empty endpoints means labels, populated endpoints "
            "means the app. Mention that Endpoints is the legacy object and EndpointSlice is "
            "what actually scales, but <code>get endpoints</code> is still the friendlier read "
            "and is not going anywhere."
        ),
        day=2,
    ),
    slide(
        "The four ports, on one traffic path",
        pm(
            [
                ("Node", "any node, :30080", SLATE),
                ("Service", "vote, ClusterIP :80", TEAL),
                ("Pod", "10.244.1.9, app on :80", GREEN),
            ],
            [
                ("nodePort: 30080", "external clients land here"),
                ("port: 80 &rarr; targetPort: 80", "in-cluster clients dial port"),
            ],
        )
        + leg(
            [
                (
                    "containerPort",
                    "In the <b>Pod</b> spec. Pure documentation &mdash; it opens nothing. The app "
                    "listening is what matters. Get it wrong and everything still works.",
                    GREEN,
                ),
                (
                    "targetPort",
                    "In the <b>Service</b>. The port on the Pod traffic is forwarded to. This one "
                    "<b>must</b> match what the app actually listens on, or you get connection refused.",
                    AMBER,
                ),
                (
                    "port",
                    "In the <b>Service</b>. The Service&rsquo;s own port &mdash; what other Pods "
                    "dial: <code>http://vote:80</code>. Free choice; it need not equal targetPort.",
                    TEAL,
                ),
                (
                    "nodePort",
                    "In the <b>Service</b>, <code>type: NodePort</code> only. A port opened on "
                    "<b>every</b> node, range <code>30000&ndash;32767</code>. Omit it and one is "
                    "assigned.",
                    SLATE,
                ),
            ]
        ),
        eyebrow="The #1 confusion in Kubernetes",
        kicker="Read them outside-in: <code>nodePort</code> &rarr; <code>port</code> &rarr; "
        "<code>targetPort</code> &rarr; the app.",
        notes=(
            "Slow down here &mdash; this is the single most confused topic in the whole course. "
            "Walk the arrow left to right and name each port as you cross it. The two facts that "
            "unstick people: containerPort is informational and changing it fixes nothing, and "
            "targetPort is the only one that must match reality. Ask three students to name the "
            "port a Pod dials to reach the Service &mdash; the answer is <code>port</code>."
        ),
        day=2,
    ),
]

# ===================================================================== dns (3)
dns = [
    slide(
        "CoreDNS and the FQDN pattern",
        two(
            col(
                panel(
                    "Every Service gets a name",
                    '<div class="stackd tight" style="margin-top:6px">'
                    '<div class="bx t-teal sm"><span class="bx-l">'
                    "redis.vote.svc.cluster.local</span>"
                    '<span class="bx-s">service . namespace . svc . cluster domain</span></div>'
                    '<div class="arrow-d">&darr; CoreDNS answers with</div>'
                    '<div class="bx t-green sm"><span class="bx-l">10.96.18.44</span>'
                    '<span class="bx-s">the Service ClusterIP</span></div></div>'
                    + '<p style="font-size:20px;color:var(--dim);margin-top:16px;line-height:1.45">'
                    "CoreDNS runs as a Deployment in <code>kube-system</code>, fronted by a "
                    "Service called <code>kube-dns</code>. Every Pod&rsquo;s "
                    "<code>/etc/resolv.conf</code> points at it &mdash; the kubelet writes that "
                    "file at Pod creation.</p>",
                    tone="t-teal",
                ),
            ),
            col(
                term(
                    "four names, one Service",
                    "# from a Pod in namespace vote\n"
                    "curl http://redis:6379                       # same namespace\n"
                    "curl http://redis.vote:6379                  # + namespace\n"
                    "curl http://redis.vote.svc:6379              # + type\n"
                    "curl http://redis.vote.svc.cluster.local     # fully qualified\n\n"
                    "# from a Pod in a DIFFERENT namespace, the short\n"
                    "# name fails - you must qualify it\n"
                    "curl http://redis.vote:6379",
                    cls="xs",
                ),
                note(
                    "n-warn",
                    "The short name only works <b>inside the same namespace</b>. Cross-namespace "
                    "calls need at least <code>&lt;service&gt;.&lt;namespace&gt;</code> &mdash; "
                    "this is the number one &ldquo;but it worked in dev&rdquo; bug.",
                    style="margin-top:16px",
                ),
            ),
            ratio="1fr 1.12fr",
            gap=34,
        ),
        eyebrow="Service discovery",
        kicker="<code>&lt;service&gt;.&lt;namespace&gt;.svc.cluster.local</code> &mdash; learn "
        "this shape and you never hard-code an IP again.",
        notes=(
            "Write the FQDN on the board and dissect it left to right. The critical takeaway is "
            "that the short name is a convenience that only holds within one namespace &mdash; "
            "students move a Deployment to a new namespace, the short name stops resolving, and "
            "they blame the network. Also worth saying: DNS resolves to the Service IP, never to "
            "a Pod IP, unless the Service is headless."
        ),
        day=2,
    ),
    slide(
        "Search domains and ndots",
        two(
            col(
                term(
                    "/etc/resolv.conf inside a Pod in namespace vote",
                    "nameserver 10.96.0.10\n"
                    "search vote.svc.cluster.local svc.cluster.local cluster.local\n"
                    "options ndots:5",
                    cls="xs",
                ),
                bul(
                    [
                        "<b><code>search</code></b> is why <code>redis</code> alone resolves: "
                        "the resolver appends each suffix in turn until one answers. "
                        "<code>redis</code> &rarr; <code>redis.vote.svc.cluster.local</code>.",
                        "<b><code>ndots:5</code></b> means &ldquo;a name with fewer than 5 dots "
                        "is tried against the search list <em>first</em>&rdquo;. "
                        "<code>redis.vote</code> has one dot, so the suffixes are tried before "
                        "the name is treated as absolute.",
                    ],
                    cls="bul tight",
                ),
            ),
            col(
                term(
                    "the cost of ndots:5",
                    "# api.github.com has 2 dots -> tried as:\n"
                    "#   api.github.com.vote.svc.cluster.local   NXDOMAIN\n"
                    "#   api.github.com.svc.cluster.local        NXDOMAIN\n"
                    "#   api.github.com.cluster.local            NXDOMAIN\n"
                    "#   api.github.com                          OK\n"
                    "# four lookups for one external call\n\n"
                    "# the fix: a trailing dot makes it absolute\n"
                    "curl https://api.github.com./",
                    cls="xs",
                ),
                note(
                    "n-info",
                    "You can also override it per Pod with "
                    "<code>spec.dnsConfig.options</code>. Real clusters with chatty external "
                    "calls tune this &mdash; four NXDOMAINs per request adds up fast.",
                    style="margin-top:16px",
                ),
                note(
                    "n-tip",
                    "In-cluster names are cheap because they hit on the <b>first</b> suffix. "
                    "It is external hostnames that pay the tax.",
                    style="margin-top:14px",
                ),
            ),
            ratio="1fr 1.08fr",
            gap=32,
        ),
        eyebrow="Why the short name works at all",
        kicker="The magic is ordinary resolver config &mdash; the kubelet writes it into every "
        "Pod.",
        notes=(
            "This slide de-mystifies DNS: there is no Kubernetes magic, just a search list and "
            "an ndots setting your OS has always had. The ndots:5 penalty is a genuine "
            "production issue and a great interview answer, so give it thirty seconds. Do not "
            "let this run long &mdash; the lab that follows makes it concrete anyway."
        ),
        day=2,
    ),
    lab(
        "Resolve names from inside the cluster",
        two(
            col(
                term(
                    "get a shell with DNS tools in it",
                    "kubectl run dnsutils -n vote --rm -it --restart=Never \\\n"
                    "  --image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.3 \\\n"
                    "  -- /bin/sh\n\n"
                    "# inside the Pod:\n"
                    "cat /etc/resolv.conf\n\n"
                    "nslookup redis\n"
                    "nslookup redis.vote.svc.cluster.local\n\n"
                    "# a Service in another namespace - short name fails\n"
                    "nslookup kubernetes.default\n"
                    "nslookup kube-dns.kube-system.svc.cluster.local\n\n"
                    "# see the answer as a resolver sees it\n"
                    "dig +search +short redis\n"
                    "exit",
                    cls="xs",
                ),
            ),
            col(
                term(
                    "then, from your terminal",
                    "# CoreDNS itself\n"
                    "kubectl -n kube-system get pods -l k8s-app=kube-dns\n"
                    "kubectl -n kube-system get svc kube-dns\n\n"
                    "# the Corefile CoreDNS is configured with\n"
                    "kubectl -n kube-system get cm coredns \\\n"
                    "  -o jsonpath='{.data.Corefile}'\n\n"
                    "# and the link the name resolves to\n"
                    "kubectl -n vote get endpoints redis\n"
                    "kubectl -n vote get svc redis -o wide",
                    cls="xs",
                ),
                bul(
                    [
                        "Confirm the ClusterIP from <code>get svc</code> is exactly the address "
                        "<code>nslookup</code> returned. Name &rarr; Service IP &rarr; Endpoints "
                        "&rarr; Pod IPs: walk the whole chain once.",
                        "<code>kubernetes.default</code> is the API server&rsquo;s own Service "
                        "&mdash; it resolves from every namespace, which makes it the ideal "
                        "&ldquo;is DNS alive?&rdquo; probe.",
                    ],
                    cls="bul tight",
                ),
            ),
            ratio="1.05fr 1fr",
            gap=32,
        ),
        eyebrow="Lab 13 &middot; DNS",
        kicker="Names in, IPs out &mdash; then match those IPs against the Endpoints object "
        "by hand.",
        notes=(
            "The dnsutils image is worth naming explicitly because busybox&rsquo;s nslookup is "
            "notoriously broken against cluster DNS and will hand you confusing NXDOMAINs. Have "
            "them read <code>/etc/resolv.conf</code> before any lookup so the search list is on "
            "screen when they see the short name resolve. Finish by matching nslookup output to "
            "<code>get endpoints</code> &mdash; that connection is the point of the lab."
        ),
        day=2,
    ),
]

# =================================================================== vasvc (2)
_SVCS = (
    "cat <<'EOF' | kubectl apply -f -\n"
    "apiVersion: v1\n"
    "kind: Service\n"
    "metadata: {name: redis}      # NAME IS LOAD-BEARING\n"
    "spec: {selector: {app: redis},\n"
    "  ports: [{port: 6379, targetPort: 6379}]}\n"
    "---\n"
    "apiVersion: v1\n"
    "kind: Service\n"
    "metadata: {name: db}         # NAME IS LOAD-BEARING\n"
    "spec: {selector: {app: db}, ports: [{port: 5432, targetPort: 5432}]}\n"
    "---\n"
    "apiVersion: v1\n"
    "kind: Service\n"
    "metadata: {name: vote}\n"
    "spec: {type: NodePort, selector: {app: vote},\n"
    "  ports: [{port: 80, targetPort: 80, nodePort: 30080}]}\n"
    "---\n"
    "apiVersion: v1\n"
    "kind: Service\n"
    "metadata: {name: result}\n"
    "spec: {selector: {app: result}, ports: [{port: 80, targetPort: 80}]}\n"
    "EOF"
)

vasvc = [
    lab(
        "Services for all five components",
        two(
            col(term("four Services &mdash; worker gets none", _SVCS, cls="xs")),
            col(
                note(
                    "n-warn",
                    "The apps <b>hard-code their hostnames</b>. "
                    "<code>vote/app.py</code> does <code>Redis(host=\"redis\")</code>; "
                    "<code>result/server.js</code> and <code>Worker.java</code> both connect to "
                    "<code>db</code>. Name the Service <code>postgres</code> or "
                    "<code>redis-svc</code> and the Pods stay <b>Running and Ready</b> while the "
                    "app is silently, completely broken. The Service name <em>is</em> the DNS "
                    "name &mdash; it must be exactly <code>redis</code> and exactly "
                    "<code>db</code>.",
                    title="Get these two names wrong and nothing works",
                ),
                bul(
                    [
                        "<code>vote</code> is a <b>NodePort on 30080</b> &mdash; the port our "
                        "kind config mapped to the host on Day 1, so a browser can reach it.",
                        "<code>result</code> stays <b>ClusterIP</b>; only 30080 is mapped, so we "
                        "reach it with <code>port-forward</code>.",
                        "<code>worker</code> gets <b>no Service</b>. It accepts no inbound "
                        "connections &mdash; it dials out to redis and db and that is all.",
                    ],
                    cls="bul tight",
                )
                + note(
                    "n-tip",
                    "A Service in namespace <code>vote</code> named <code>vote</code> is "
                    "perfectly legal &mdash; namespaces, Deployments and Services live in "
                    "different name scopes.",
                    style="margin-top:14px",
                ),
            ),
            ratio="1.02fr 1fr",
            gap=32,
        ),
        eyebrow="Lab 12 &middot; The app comes alive (1 of 2)",
        kicker="Four ClusterIP-and-friends objects and the Voting App finally has a nervous "
        "system.",
        notes=(
            "Say the naming warning twice and write <code>redis</code> and <code>db</code> on "
            "the board. Someone will name it <code>postgres</code> because it feels tidier, and "
            "they will lose twenty minutes to an app that looks perfectly healthy in "
            "<code>get pods</code>. Turn it into the lesson: the Service name is the DNS name, "
            "so it is part of your application contract, not a label you pick for aesthetics."
        ),
        day=2,
    ),
    lab(
        "End to end &mdash; cast a vote, watch it count",
        two(
            col(
                term(
                    "verify the wiring, then use it",
                    "kubectl get svc,endpoints\n"
                    "# every Service must show real IPs under ENDPOINTS\n\n"
                    "# vote in a browser (kind mapped 30080 to the host)\n"
                    "curl -s http://localhost:30080 | head -n 20\n\n"
                    "# result has no NodePort - forward it\n"
                    "kubectl port-forward svc/result 5001:80\n"
                    "# then open http://localhost:5001\n\n"
                    "# the worker should now be doing its job\n"
                    "kubectl logs -l app=worker --tail=20\n"
                    "# Processing vote for 'a' by '3f8c...'",
                    cls="xs",
                ),
            ),
            col(
                steps(
                    [
                        "Open <b>http://localhost:30080</b> and vote. The page footer prints the "
                        "Pod hostname &mdash; reload a few times and watch it alternate between "
                        "your two <code>vote</code> replicas. That is the Service load-balancing.",
                        "The vote is pushed to <b>redis</b> by name. "
                        "<code>kubectl logs -l app=worker</code> shows it being pulled off the "
                        "queue and written to <b>db</b>.",
                        "Open the forwarded <b>result</b> page and watch the tally update live "
                        "over the WebSocket.",
                        "Now the proof: <code>kubectl delete pod -l app=vote</code>. New Pods, "
                        "new IPs, new Endpoints &mdash; and the page still works, because "
                        "nothing ever knew the IPs.",
                    ]
                ),
            ),
            ratio="1fr 1.05fr",
            gap=32,
        ),
        eyebrow="Lab 12 &middot; The app comes alive (2 of 2)",
        kicker="First time the whole thing works. Deployments keep it alive, Services let the "
        "parts find each other.",
        notes=(
            "This is the emotional high point of Day 2 &mdash; do not rush past it. Get everyone "
            "voting at once so the result page moves visibly. Then run the delete and let them "
            "see the app survive its frontend being destroyed; that is the payoff for two "
            "abstractions they only half-believed an hour ago. If someone is broken, the first "
            "command is <code>kubectl get endpoints</code>, not <code>logs</code>."
        ),
        day=2,
    ),
]

# =========================================================== multicontainer (4)
multicontainer = [
    slide(
        "Multi-container Pods &mdash; what is actually shared",
        two(
            col(
                panel(
                    "One Pod, two containers",
                    '<div class="stackd" style="gap:10px;margin-top:6px">'
                    '<div class="flowd">'
                    '<div class="fl-box" style="--tone:#2fc8a8">app</div>'
                    '<div class="fl-box" style="--tone:#2496ed">helper</div></div>'
                    '<div class="lay" style="height:54px;--tone:#2fc8a8">'
                    '<span class="lay-l">shared network namespace</span>'
                    '<span class="lay-s">one Pod IP &middot; one port space</span></div>'
                    '<div class="lay" style="height:54px;--tone:#e3b341">'
                    '<span class="lay-l">shared volumes</span>'
                    '<span class="lay-s">whatever you mount into both</span></div>'
                    '<div class="lay hw" style="height:48px">'
                    '<span class="lay-l">NOT shared: filesystems, processes</span></div></div>',
                    tone="t-teal",
                ),
            ),
            col(
                bul(
                    [
                        "<b>They reach each other on <code>localhost</code>.</b> Same network "
                        "namespace, so the helper curls <code>http://localhost:80</code> &mdash; "
                        "no Service, no DNS, no IP.",
                        "<b>One port space.</b> Two containers cannot both bind <code>:80</code> "
                        "in one Pod &mdash; the second crashes with <em>address already in use</em>.",
                        "<b>Root filesystems stay separate.</b> To share files you must mount the "
                        "<em>same</em> volume (usually an <code>emptyDir</code>) into both.",
                        "<b>Scheduled and killed together</b>, always on one node. If you would "
                        "ever want to scale them independently, they are two Pods.",
                    ]
                ),
                note(
                    "n-warn",
                    "Do not put your app and its database in one Pod. The test is simple: would "
                    "you ever scale, upgrade or restart them separately? If yes &mdash; and for "
                    "a database it is always yes &mdash; they are separate Pods.",
                    title="The most common misuse",
                    style="margin-top:16px",
                ),
            ),
            ratio="1fr 1.12fr",
            gap=34,
        ),
        eyebrow="Beyond one container",
        kicker="Containers in a Pod share an IP and can share volumes &mdash; they do not share "
        "a filesystem.",
        notes=(
            "About 95% of Pods hold exactly one container, so lead with when <em>not</em> to do "
            "this. The localhost property is the one worth demonstrating &mdash; it surprises "
            "people that no Service is involved. The port-collision point saves a debugging "
            "session later; say it explicitly rather than leaving it as an exercise."
        ),
        day=2,
    ),
    slide(
        "Init containers &mdash; run first, run to completion",
        two(
            col(
                term(
                    "worker waits for db",
                    "spec:\n"
                    "  initContainers:\n"
                    "    - name: wait-for-db\n"
                    "      image: postgres:14\n"
                    "      command:\n"
                    "        - sh\n"
                    "        - -c\n"
                    "        - until pg_isready -h db -p 5432; do\n"
                    "            echo waiting for db; sleep 2; done\n"
                    "  containers:\n"
                    "    - name: worker\n"
                    "      image: iti/worker:v1\n"
                    "      imagePullPolicy: IfNotPresent",
                    cls="xs",
                ),
            ),
            col(
                bul(
                    [
                        "They run <b>in order, one at a time</b>, and each must exit <b>0</b> "
                        "before the next starts. Only when all of them succeed do the app "
                        "containers start.",
                        "A failing init container is retried per the Pod&rsquo;s "
                        "<code>restartPolicy</code> &mdash; the Pod sits in "
                        "<code>Init:0/1</code> or <code>Init:CrashLoopBackOff</code>, and the "
                        "app never starts. That is the desired behaviour.",
                        "They can use a <b>different image</b> from the app &mdash; put "
                        "<code>psql</code>, <code>git</code> or <code>curl</code> in the init "
                        "container and keep the app image clean.",
                        "Classic uses: wait for a dependency, run a schema migration, fetch "
                        "config or a secret into a shared <code>emptyDir</code>, fix volume "
                        "permissions.",
                    ],
                    cls="bul tight",
                ),
                note(
                    "n-tip",
                    "<code>kubectl logs &lt;pod&gt; -c wait-for-db</code> &mdash; init "
                    "container logs need the <code>-c</code> flag, and a Pod stuck at "
                    "<code>Init:0/1</code> is telling you its dependency is not there.",
                    style="margin-top:14px",
                ),
            ),
            ratio="1fr 1.14fr",
            gap=32,
        ),
        eyebrow="Ordering, at the platform level",
        kicker="A container that must finish successfully <em>before</em> your app is allowed "
        "to start.",
        notes=(
            "The mental model is a gate, not a helper. Emphasise exit code zero &mdash; the "
            "init container must terminate successfully, so a long-running process there hangs "
            "the Pod forever. Note that <code>get pods</code> reports a distinct "
            "<code>Init:0/1</code> status; recognising it is worth more to a beginner than the "
            "YAML is. The <code>-c</code> flag for logs catches everyone out once."
        ),
        day=2,
    ),
    slide(
        "The sidecar pattern",
        cards(
            [
                (
                    "&#128221;",
                    "Log shipper",
                    "App writes to a file in a shared <code>emptyDir</code>; the sidecar tails "
                    "it and ships it out. The app never learns your logging stack exists.",
                    "t-teal",
                ),
                (
                    "&#128737;",
                    "Service mesh proxy",
                    "Envoy in every Pod, intercepting all traffic for mTLS, retries and "
                    "tracing. This is what Istio and Linkerd actually are.",
                    "t-blue",
                ),
                (
                    "&#128260;",
                    "Config reloader",
                    "Watches a mounted ConfigMap for changes and signals the app to reload &mdash; "
                    "no restart, no coupling.",
                    "t-violet",
                ),
            ],
        )
        + two(
            col(
                bul(
                    [
                        "A sidecar runs <b>alongside</b> the app for the whole life of the Pod "
                        "&mdash; long-running, not run-to-completion.",
                        "The value is <b>separation of concerns</b>: your app keeps doing one "
                        "thing, the platform concern lives in its own container with its own "
                        "image and release cycle.",
                        "It is the second-most-used Pod pattern after &ldquo;just one "
                        "container&rdquo;, and the reason multi-container Pods exist at all.",
                    ],
                    cls="bul tight",
                ),
            ),
            col(
                note(
                    "n-info",
                    "Since <b>Kubernetes 1.29</b> there is a proper sidecar: an init container "
                    "with <code>restartPolicy: Always</code>. It starts before the app "
                    "containers, keeps running alongside them, and shuts down after them &mdash; "
                    "which finally fixes log shippers dying before the app finishes writing.",
                    title="The modern spelling",
                ),
                note(
                    "n-warn",
                    "A sidecar shares the Pod&rsquo;s CPU and memory budget and its lifecycle. "
                    "Three sidecars around a small app is three times the resource footprint "
                    "and three more things that can crash the Pod.",
                    style="margin-top:14px",
                ),
            ),
            ratio="1fr 1.08fr",
            gap=32,
        ),
        eyebrow="The pattern you will meet in production",
        kicker="A long-running helper container that adds a capability the app does not have "
        "to know about.",
        notes=(
            "Anchor this with Istio &mdash; most students have heard of service meshes without "
            "knowing they are literally a container injected into every Pod. That single "
            "connection makes the pattern click. Mention the 1.29 native sidecar so they are not "
            "confused when they see <code>restartPolicy: Always</code> under "
            "<code>initContainers</code> in real manifests."
        ),
        day=2,
    ),
    slide(
        "Init container vs sidecar &mdash; the timeline",
        tl(
            [
                (
                    "Pod created",
                    [("scheduled, image pulls start", SLATE, 1)],
                ),
                (
                    "init phase",
                    [
                        ("init-1: wait-for-db &nbsp;runs &rarr; exits 0", AMBER, 2),
                        ("app: not started", SLATE, 1),
                        ("sidecar: not started", SLATE, 1),
                    ],
                ),
                (
                    "init phase",
                    [
                        ("init-2: migrate-schema &nbsp;runs &rarr; exits 0", AMBER, 2),
                        ("app: not started", SLATE, 1),
                        ("sidecar: not started", SLATE, 1),
                    ],
                ),
                (
                    "running",
                    [
                        ("init containers: gone", SLATE, 2),
                        ("app: running", GREEN, 1),
                        ("sidecar: running", BLUE, 1),
                    ],
                ),
                (
                    "Pod deleted",
                    [("app and sidecar terminate together", MAROON, 1)],
                ),
            ],
            gap=12,
        )
        + table(
            ["", "Init container", "Sidecar"],
            [
                ["<b>When</b>", "Before app containers", "Alongside app containers"],
                ["<b>Lifetime</b>", "Runs to completion, then gone", "Whole life of the Pod"],
                [
                    "<b>Order</b>",
                    "Sequential and guaranteed",
                    "Parallel &mdash; no ordering guarantee (pre-1.29)",
                ],
                [
                    "<b>Failure means</b>",
                    "App never starts &mdash; <code>Init:0/1</code>",
                    "App keeps running; Pod may go NotReady",
                ],
                [
                    "<b>Typical job</b>",
                    "Wait, migrate, fetch, chown",
                    "Ship logs, proxy traffic, reload config",
                ],
            ],
        ),
        eyebrow="Sequential vs parallel",
        kicker="Same <code>spec</code>, opposite lifecycles &mdash; one is a gate, the other "
        "is a companion.",
        notes=(
            "The table is the takeaway; the timeline is how you explain it. Trace one Pod down "
            "the rows with a finger and name what is alive at each tick. The row students should "
            "memorise is the failure row &mdash; an init container failure blocks the app "
            "entirely, a sidecar failure does not. That is the difference between a gate and a "
            "companion, and it is a common interview question."
        ),
        day=2,
    ),
]

# ================================================================== vainit (2)
vainit = [
    lab(
        "Make worker wait for db",
        two(
            col(
                term(
                    "patch the worker Deployment",
                    "cat <<'EOF' | kubectl apply -f -\n"
                    "apiVersion: apps/v1\n"
                    "kind: Deployment\n"
                    "metadata: {name: worker, namespace: vote}\n"
                    "spec:\n"
                    "  replicas: 1\n"
                    "  selector: {matchLabels: {app: worker}}\n"
                    "  template:\n"
                    "    metadata: {labels: {app: worker}}\n"
                    "    spec:\n"
                    "      initContainers:\n"
                    "        - name: wait-for-db\n"
                    "          image: postgres:14\n"
                    "          command:\n"
                    "            - sh\n"
                    "            - -c\n"
                    "            - until pg_isready -h db -p 5432; do\n"
                    "                echo waiting for db; sleep 2; done\n"
                    "      containers:\n"
                    "        - name: worker\n"
                    "          image: iti/worker:v1\n"
                    "          imagePullPolicy: IfNotPresent\n"
                    "EOF",
                    cls="xs",
                ),
            ),
            col(
                bul(
                    [
                        "<code>postgres:14</code> is reused as the init image purely because it "
                        "already ships <code>pg_isready</code> &mdash; and the node already has "
                        "the image, so there is nothing to pull.",
                        "<code>pg_isready</code> exits <b>0</b> only when Postgres is accepting "
                        "connections. Not &ldquo;the Pod is Running&rdquo;, not &ldquo;the port "
                        "is open&rdquo; &mdash; actually ready.",
                        "The app container keeps its own "
                        "<code>imagePullPolicy: IfNotPresent</code>. Easy to drop that line "
                        "while you are concentrating on the init container.",
                    ],
                    cls="bul tight",
                ),
                note(
                    "n-why",
                    "The Java worker already retries in a loop, so it does not crash &mdash; it "
                    "just sits there logging <code>Waiting for db</code> while "
                    "<code>kubectl get pods</code> cheerfully reports <b>1/1 Running</b>. "
                    "The init container turns that lie into an honest "
                    "<code>Init:0/1</code>, and it is the pattern you <em>must</em> use for the "
                    "many apps that do not retry at all.",
                    title="Why bother if the app retries?",
                    style="margin-top:16px",
                ),
            ),
            ratio="1.05fr 1fr",
            gap=32,
        ),
        eyebrow="Lab 14 &middot; Init containers (1 of 2)",
        kicker="Move the dependency wait out of the application and into the platform, where "
        "it is visible.",
        notes=(
            "Be precise about the motivation or a sharp student will call you out: this worker "
            "does retry, it does not crash. The real argument is honesty of status &mdash; a "
            "Pod reporting Ready while it cannot reach its database is worse than a Pod that "
            "says it is waiting. Ask them how many apps they have written that retry their "
            "database connection forever. The answer is usually none."
        ),
        day=2,
    ),
    lab(
        "Prove the gate works",
        two(
            col(
                term(
                    "take the database away",
                    "# scale db to zero - the dependency vanishes\n"
                    "kubectl scale deploy/db --replicas=0\n\n"
                    "# force worker to start from scratch\n"
                    "kubectl rollout restart deploy/worker\n\n"
                    "kubectl get pods -l app=worker -w\n"
                    "# NAME            READY   STATUS     RESTARTS\n"
                    "# worker-8c4...   0/1     Init:0/1   0\n"
                    "# ...and it stays there\n\n"
                    "# the init container is telling you why\n"
                    "kubectl logs -l app=worker -c wait-for-db --tail=5\n"
                    "# db:5432 - no response",
                    cls="xs",
                ),
            ),
            col(
                term(
                    "give it back",
                    "kubectl scale deploy/db --replicas=1\n\n"
                    "# within seconds the gate opens\n"
                    "kubectl get pods -l app=worker -w\n"
                    "# worker-8c4...   0/1     Init:0/1    0\n"
                    "# worker-8c4...   0/1     PodInitializing\n"
                    "# worker-8c4...   1/1     Running     0\n\n"
                    "kubectl describe pod -l app=worker | grep -A4 'Init Containers'\n\n"
                    "# and the app resumes\n"
                    "kubectl logs -l app=worker --tail=10\n"
                    "# Watching vote queue",
                    cls="xs",
                ),
                note(
                    "n-tip",
                    "<code>kubectl describe pod</code> lists init containers in their own "
                    "section with their own <code>State</code> and exit codes. It is the first "
                    "place to look when a Pod is wedged in <code>Init:</code> anything.",
                    style="margin-top:16px",
                ),
            ),
            ratio="1fr 1.05fr",
            gap=32,
        ),
        eyebrow="Lab 14 &middot; Init containers (2 of 2)",
        kicker="Break the dependency on purpose, watch the Pod refuse to start, then fix it "
        "and watch the gate open.",
        notes=(
            "Scaling <code>db</code> to zero is the cleanest way to simulate a missing "
            "dependency and it is instantly reversible, so nobody wrecks their cluster. Leave "
            "the Pod sitting in <code>Init:0/1</code> for a minute so the status burns in &mdash; "
            "they will meet it again in the wild. Make sure they run "
            "<code>logs -c wait-for-db</code>; without <code>-c</code> kubectl errors out and "
            "that error is itself a teaching moment."
        ),
        day=2,
    ),
]

# ================================================================= day2end (3)
day2end = [
    lab(
        "Planted failure: a Service with no Endpoints",
        two(
            col(
                term(
                    "apply the break, then diagnose it",
                    "# a Service for result, with one character wrong\n"
                    "cat <<'EOF' | kubectl apply -f -\n"
                    "apiVersion: v1\n"
                    "kind: Service\n"
                    "metadata: {name: result-broken, namespace: vote}\n"
                    "spec:\n"
                    "  selector: {app: results}      # the Pods are app=result\n"
                    "  ports: [{port: 80, targetPort: 80}]\n"
                    "EOF\n\n"
                    "kubectl run probe --rm -it --restart=Never \\\n"
                    "  --image=curlimages/curl -- curl -sS --max-time 5 \\\n"
                    "  http://result-broken\n"
                    "# curl: (28) Connection timed out",
                    cls="xs",
                ),
            ),
            col(
                steps(
                    [
                        "The Service exists and has a ClusterIP &mdash; "
                        "<code>kubectl get svc result-broken</code> looks perfectly healthy. "
                        "Nothing here tells you anything.",
                        "<b>Check the link:</b> "
                        "<code>kubectl get endpoints result-broken</code> &rarr; "
                        "<code>ENDPOINTS: &lt;none&gt;</code>. The Service is pointing at "
                        "nothing at all.",
                        "<b>Ask what the selector matches:</b> "
                        "<code>kubectl get pods -l app=results</code> &rarr; "
                        "<em>No resources found</em>. Now compare with "
                        "<code>kubectl get pods --show-labels</code>.",
                        "<b>Fix it:</b> <code>kubectl patch svc result-broken -p "
                        "'{\"spec\":{\"selector\":{\"app\":\"result\"}}}'</code>, then re-check "
                        "endpoints &mdash; a Pod IP appears within a second and curl succeeds.",
                    ]
                ),
                note(
                    "n-warn",
                    "Nothing warns you. A selector that matches zero Pods is <b>valid</b> &mdash; "
                    "the API server accepts it, the Service gets an IP, and every request just "
                    "hangs. This is the most common self-inflicted networking bug in Kubernetes.",
                    style="margin-top:14px",
                ),
            ),
            ratio="1fr 1.1fr",
            gap=32,
        ),
        eyebrow="Lab 15 &middot; Troubleshooting",
        kicker="Everything is green, nothing works. Find it in under two minutes.",
        notes=(
            "Do not give them the answer &mdash; let them flounder for a couple of minutes, "
            "because the frustration is what makes the endpoints check stick. Then walk the "
            "four steps as a repeatable playbook: Service exists? Endpoints populated? Selector "
            "matches Pods? Labels correct? Point out that they diagnosed it entirely with "
            "<code>get</code>, never once reading an application log."
        ),
        day=2,
    ),
    slide(
        "You are here &mdash; end of Day 2",
        '<div class="stackd" style="gap:14px">'
        + '<div class="flowd">'
        '<div class="fl-box" style="--tone:#2496ed;font-size:19px">'
        "browser &rarr; :30080</div>"
        '<div class="fl-arrow">&rarr;</div>'
        '<div class="fl-box" style="--tone:#2fc8a8;font-size:19px">'
        "svc/vote<br>NodePort</div>"
        '<div class="fl-arrow">&rarr;</div>'
        '<div class="fl-box" style="--tone:#46c95c;font-size:19px">'
        "deploy/vote<br>2 replicas</div>"
        '<div class="fl-arrow">&rarr;</div>'
        '<div class="fl-box" style="--tone:#2fc8a8;font-size:19px">'
        "svc/redis<br>ClusterIP</div>"
        '<div class="fl-arrow">&rarr;</div>'
        '<div class="fl-box" style="--tone:#46c95c;font-size:19px">'
        "deploy/redis</div></div>"
        + '<div class="flowd">'
        '<div class="fl-box" style="--tone:#8a7bd8;font-size:19px">'
        "deploy/worker<br>init: wait-for-db &middot; no Service</div>"
        '<div class="fl-arrow">&rarr;</div>'
        '<div class="fl-box" style="--tone:#2fc8a8;font-size:19px">'
        "svc/db<br>ClusterIP</div>"
        '<div class="fl-arrow">&rarr;</div>'
        '<div class="fl-box" style="--tone:#46c95c;font-size:19px">'
        "deploy/db<br>postgres:14</div>"
        '<div class="fl-arrow">&rarr;</div>'
        '<div class="fl-box" style="--tone:#2fc8a8;font-size:19px">'
        "svc/result<br>ClusterIP</div>"
        '<div class="fl-arrow">&rarr;</div>'
        '<div class="fl-box" style="--tone:#46c95c;font-size:19px">'
        "deploy/result</div></div></div>"
        + cards(
            [
                (
                    "&#9989;",
                    "New today",
                    "5 Deployments &middot; 4 Services &middot; EndpointSlices &middot; "
                    "cluster DNS &middot; one init container. The app works end to end.",
                    "t-green",
                ),
                (
                    "&#9888;",
                    "Still wrong",
                    "The Postgres password is in plain YAML. All state is in the Pod &mdash; "
                    "kill <code>db</code> and every vote is gone. No probe, so "
                    "&ldquo;zero downtime&rdquo; is still a promise, not a fact.",
                    "t-amber",
                ),
                (
                    "&#128197;",
                    "Tomorrow",
                    "Secrets and ConfigMaps, PersistentVolumes so votes survive, and the three "
                    "probes &mdash; including the lab that finally makes the rollout truly "
                    "zero-downtime.",
                    "t-blue",
                ),
            ]
        ),
        eyebrow="Day 2 recap",
        kicker="Five Deployments, four Services, one init container &mdash; and the Voting App "
        "running for the first time.",
        notes=(
            "Put the diagram up and have the room narrate it: a vote enters at 30080, hits the "
            "vote Service, lands on a replica, goes to redis by name, gets pulled by the worker, "
            "is written to db, and shows up on result. If they can tell that story unprompted, "
            "Day 2 landed. Then dwell on the amber card &mdash; naming tomorrow&rsquo;s problems "
            "today is what makes Day 3 feel necessary rather than arbitrary."
        ),
        day=2,
    ),
    slide(
        "Interview questions &mdash; Day 2",
        two(
            col(
                bul(
                    [
                        "<b>1. What does a Deployment give you that a ReplicaSet does not?</b>"
                        '<span style="display:block;font-size:19px;color:var(--faint);'
                        'margin-top:5px">Rolling updates, revision history and rollback. A '
                        "ReplicaSet only maintains a count.</span>",
                        "<b>2. Why is <code>spec.selector</code> immutable?</b>"
                        '<span style="display:block;font-size:19px;color:var(--faint);'
                        'margin-top:5px">Changing it would silently orphan every running Pod. '
                        "Delete with <code>--cascade=orphan</code> and re-apply.</span>",
                        "<b>3. Explain <code>maxSurge</code> and <code>maxUnavailable</code>.</b>"
                        '<span style="display:block;font-size:19px;color:var(--faint);'
                        'margin-top:5px">Pods allowed above desired, and allowed below ready. '
                        "Both default to 25%; both zero is rejected.</span>",
                        "<b>4. A rollout is stuck. What do you run?</b>"
                        '<span style="display:block;font-size:19px;color:var(--faint);'
                        'margin-top:5px"><code>rollout status</code>, then <code>get pods</code> '
                        "and <code>describe</code> for the Events. It never rolls back by "
                        "itself.</span>",
                    ],
                    cls="bul tight",
                ),
            ),
            col(
                bul(
                    [
                        "<b>5. Difference between <code>port</code>, <code>targetPort</code>, "
                        "<code>nodePort</code> and <code>containerPort</code>?</b>"
                        '<span style="display:block;font-size:19px;color:var(--faint);'
                        'margin-top:5px">Service port, Pod port it forwards to, port on every '
                        "node, and a purely informational field in the Pod spec.</span>",
                        "<b>6. A Service returns nothing. First command?</b>"
                        '<span style="display:block;font-size:19px;color:var(--faint);'
                        'margin-top:5px"><code>kubectl get endpoints &lt;svc&gt;</code>. Empty '
                        "means the selector matches no ready Pods.</span>",
                        "<b>7. When would you use a headless Service?</b>"
                        '<span style="display:block;font-size:19px;color:var(--faint);'
                        'margin-top:5px">When the client must address individual Pods &mdash; '
                        "DNS returns Pod IPs. Required by StatefulSets.</span>",
                        "<b>8. Init container versus sidecar?</b>"
                        '<span style="display:block;font-size:19px;color:var(--faint);'
                        'margin-top:5px">Init runs to completion, in order, before the app; a '
                        "sidecar runs alongside it for the Pod&rsquo;s whole life.</span>",
                    ],
                    cls="bul tight",
                ),
            ),
            ratio="1fr 1fr",
            gap=40,
        ),
        eyebrow="Check yourself",
        kicker="Eight questions from today&rsquo;s material. Answer out loud before you read "
        "the grey line.",
        notes=(
            "Run this as cold-call, not as a slide you read. Give one question per student and "
            "let the room correct them. Questions 5 and 6 are the two that come up most often in "
            "real interviews, so spend the time there. If the room stumbles on the four ports, "
            "go back to that slide &mdash; it is worth the five minutes."
        ),
        day=2,
    ),
]

# ------------------------------------------------------------------- export
BLOCKS = {
    "day2open": day2open,
    "replicaset": replicaset,
    "deploy_extra": deploy_extra,
    "vadeploy": vadeploy,
    "rollouts": rollouts,
    "varollout": varollout,
    "svc_extra": svc_extra,
    "dns": dns,
    "vasvc": vasvc,
    "multicontainer": multicontainer,
    "vainit": vainit,
    "day2end": day2end,
}


if __name__ == "__main__":
    for name, secs in BLOCKS.items():
        for s in secs:
            assert s.startswith("<section"), name
            assert s.endswith("</section>"), name
            assert 'data-day="2"' in s, name
    print({k: len(v) for k, v in BLOCKS.items()})
    print("total", sum(len(v) for v in BLOCKS.values()))
