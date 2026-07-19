#!/usr/bin/env python3
"""Day 1 content blocks for the ITI Kubernetes deck.

BLOCKS maps a block name -> list of finished <section> strings. The assembler
splices each block into k8s-slides.html at the position the curriculum plan
(COURSE-REVIEW.md §7) gives it. Every slide here is stamped day=1.

Image/namespace conventions used across the Voting App labs and reused by the
Day 2+ blocks:
    images     iti/vote:v1  iti/result:v1  iti/worker:v1
    cluster    iti          (so kind node container = iti-control-plane)
    namespace  vote
    services   redis, db    -- names are load-bearing, the app hardcodes them
"""
from deck import cards, col, hl, lab, note, slide, steps, table, term, two

# ------------------------------------------------------------------ helpers
# ponytail: three one-line wrappers over the deck's diagram primitives; the
# alternative is the same markup pasted forty times.
TONE = {
    "blue": "#2496ed", "maroon": "#c2273a", "gold": "#e3b341", "teal": "#2fc8a8",
    "green": "#46c95c", "amber": "#d98b22", "slate": "#7089ad", "violet": "#8a7bd8",
}


def bx(label, sub, tone, grow=True):
    f = "flex:1;" if grow else ""
    return (
        f'<div class="bx" style="{f}--tone:{TONE[tone]}">'
        f'<div class="bx-l">{label}</div><div class="bx-s">{sub}</div></div>'
    )


def flow(*parts, gap=14):
    return f'<div class="flowd" style="gap:{gap}px">' + "".join(parts) + "</div>"


def arrow(ch="&rarr;"):
    return f'<div class="fl-arrow">{ch}</div>'


def panel(title, body, tone):
    return (
        f'<div class="panel tone t-{tone} r"><div class="panel-t">'
        f'<span class="dot"></span>{title}</div>{body}</div>'
    )


def bul(items, cls="bul r"):
    return f'<ul class="{cls}">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


# =========================================================== 00 roadmap (×1)
ROADMAP4 = [
    slide(
        "Four days, one application",
        table(
            ["Day", "Theme", "What you learn", "The Voting App becomes&hellip;"],
            [
                ["<b>1</b>", "<b>Foundations</b><br>&amp; first contact",
                 "Containers &rarr; orchestration &middot; architecture &middot; kind &middot; "
                 "<code>kubectl</code> &middot; namespaces &middot; labels &amp; selectors &middot; "
                 "Pods, lifecycle &amp; failure states &middot; env/command/args &middot; debugging",
                 "&hellip;a pair of <b>bare Pods</b>. It half-works. Kill one and nothing "
                 "comes back."],
                ["<b>2</b>", "<b>Workloads</b><br>&amp; networking",
                 "ReplicaSets &middot; Deployments &middot; rolling updates &amp; rollback &middot; "
                 "Services (ClusterIP/NodePort/LoadBalancer) &middot; Endpoints &middot; CoreDNS "
                 "&middot; multi-container Pods, init &amp; sidecar",
                 "&hellip;<b>Deployments + Services</b>. The app works end-to-end for the "
                 "first time."],
                ["<b>3</b>", "<b>Configuration,</b><br>storage &amp; health",
                 "ConfigMaps &middot; Secrets &middot; emptyDir &amp; hostPath &middot; PV / PVC / "
                 "StorageClass &middot; StatefulSet intro &middot; liveness, readiness &amp; "
                 "startup probes",
                 "&hellip;<b>configured and durable</b>. Votes survive a Pod kill; the "
                 "password leaves the YAML."],
                ["<b>4</b>", "<b>Scheduling, scale</b><br>&amp; production",
                 "requests/limits &amp; QoS &middot; affinity, taints &amp; tolerations &middot; "
                 "metrics-server &amp; HPA &middot; Jobs &amp; CronJobs &middot; Ingress &middot; "
                 "CNI &amp; NetworkPolicy &middot; Helm &middot; troubleshooting",
                 "&hellip;<b>production-shaped</b>: autoscaled, routed by Ingress, locked "
                 "down by policy."],
            ],
            note(
                "n-tip",
                "The footer on every slide carries its day &mdash; screenshot anything and "
                "you will still know where it came from.",
            ),
        ),
        eyebrow="Roadmap",
        kicker="Every concept is taught on the <b>same application</b>. It gets deeper each "
               "day, never replaced &mdash; so nothing you learn is thrown away.",
        notes="Set the arc up front: they are not doing four disconnected days of nginx "
              "examples, they are building one real app four times over. Point at the last "
              "column &mdash; that is the payoff column, and Day 1 deliberately ends with "
              "something broken. Tell them the frustration on Day 1 is the lesson.",
        day=1,
    ),
]

# ==================================================== 03b object model (×2)
ARCH_EXTRA = [
    slide(
        "Everything is an object",
        two(
            col(
                term(
                    "any-object.yaml",
                    """apiVersion: apps/v1        # which API group + version
kind: Deployment          # what type of object
metadata:                 # who am I
  name: vote
  namespace: vote
  labels:
    app: vote
spec:                     # what I WANT (you write this)
  replicas: 3
status:                   # what IS (the cluster writes this)
  readyReplicas: 3""",
                )
            ),
            col(
                steps([
                    "<b>apiVersion</b> &mdash; which API group and version. <code>v1</code> "
                    "for core objects (Pod, Service), <code>apps/v1</code> for workloads.",
                    "<b>kind</b> &mdash; the object type. Together with apiVersion it tells "
                    "the api-server which schema to validate against.",
                    "<b>metadata</b> &mdash; name, namespace, labels, annotations. Identity.",
                    "<b>spec</b> &mdash; <b>desired state</b>. This is the only part you write.",
                    "<b>status</b> &mdash; <b>observed state</b>. A controller writes it; you "
                    "only ever read it.",
                ]),
                note(
                    "n-why",
                    "Because this shape never changes. Learn five fields once and every "
                    "object you meet for the rest of the course &mdash; ConfigMap, PVC, "
                    "HPA, NetworkPolicy &mdash; is already familiar.",
                    title="Why it matters",
                ),
            ),
            ratio="1.05fr 1fr",
        ),
        eyebrow="The object model",
        kicker="Pods, Services, Secrets, nodes &mdash; every single one is the same "
               "five-field envelope. <b>spec is your wish; status is the cluster&rsquo;s report.</b>",
        notes="This is the single highest-leverage slide of the morning. Drill spec versus "
              "status until it is automatic &mdash; the whole control loop is just "
              "controllers grinding status towards spec. Students who miss this spend the "
              "week thinking kubectl apply is an imperative command. Mention "
              "kubectl explain as the offline manual for every field.",
        day=1,
    ),
    slide(
        "How objects relate &mdash; the hierarchy",
        col(
            flow(
                bx("Deployment", "you create this", "violet"),
                arrow(),
                bx("ReplicaSet", "keeps the count", "blue"),
                arrow(),
                bx("Pod", "runs containers", "teal"),
                arrow(),
                bx("Container", "your image", "green"),
            ),
            two(
                panel(
                    "Ownership &mdash; who makes whom",
                    bul([
                        "Each object records its parent in <code>metadata.ownerReferences</code>.",
                        "Delete the parent and <b>garbage collection</b> takes the children "
                        "with it &mdash; that is why deleting a Deployment removes its Pods.",
                        "Other chains: <code>Service &rarr; Endpoints</code>, "
                        "<code>PVC &rarr; PV</code>, <code>CronJob &rarr; Job &rarr; Pod</code>, "
                        "<code>HPA &rarr; Deployment</code>.",
                        "You almost never create the middle of a chain by hand.",
                    ], "bul tight r"),
                    "violet",
                ),
                panel(
                    "Two scopes &mdash; where an object lives",
                    bul([
                        "<b>Namespaced</b> &mdash; lives inside one namespace. Pod, Service, "
                        "Deployment, ConfigMap, Secret, PVC. Needs <code>-n</code>.",
                        "<b>Cluster-scoped</b> &mdash; belongs to the whole cluster. Node, "
                        "Namespace, PersistentVolume, StorageClass, ClusterRole. "
                        "<code>-n</code> is ignored.",
                        "<code>kubectl api-resources</code> lists every type and its scope.",
                    ], "bul tight r"),
                    "amber",
                ),
                ratio="1fr 1fr",
                gap=28,
            ),
        ),
        eyebrow="Resource hierarchy",
        kicker="Objects are not a flat pile. Most are <b>owned</b> by another object, and "
               "each one is either cluster-wide or scoped to a namespace.",
        notes="Draw the chain left to right and say out loud that they will only ever "
              "author the leftmost box. The ownerReferences point explains a question you "
              "will get all week: why deleting one thing deletes five. Park the scope "
              "column &mdash; the namespace section next expands it properly.",
        day=1,
    ),
]

# ======================================================== 06 namespaces (×4)
NAMESPACES = [
    slide(
        "Namespaces &mdash; virtual sub-clusters",
        two(
            panel(
                "One cluster, partitioned",
                '<div class="stackd" style="gap:12px">'
                + flow(
                    bx("ns: dev", "vote &middot; redis &middot; db", "teal"),
                    bx("ns: prod", "vote &middot; redis &middot; db", "blue"),
                    bx("ns: kube-system", "coredns &middot; kube-proxy", "slate"),
                    gap=12,
                )
                + '<div class="lay" style="height:58px;--tone:#7089ad">'
                '<span class="lay-l">one cluster &middot; the same nodes underneath</span>'
                "</div></div>"
                + '<p style="margin-top:16px;font-size:20px;color:var(--dim)">'
                "Three Services can all be called <code>redis</code>. Names must be unique "
                "<b>within</b> a namespace, not across the cluster.</p>",
                "teal",
            ),
            col(
                bul([
                    "A namespace is a <b>name scope</b> &mdash; a folder for object names.",
                    "It is the unit for <b>RBAC</b> (who can do what) and "
                    "<b>ResourceQuota</b> (how much a team may consume).",
                    "Everything you have created so far landed in <code>default</code>. "
                    "In production, <code>default</code> should be empty.",
                    "<code>kube-system</code> holds the cluster&rsquo;s own components "
                    "&mdash; look, never touch.",
                ]),
                note(
                    "n-warn",
                    "A Pod in <code>dev</code> can reach a Service in <code>prod</code> by "
                    "its FQDN, and nothing stops it. Namespaces scope <b>names, RBAC and "
                    "quota &mdash; not packets</b>. <b>NetworkPolicy</b> is what blocks "
                    "traffic; we build one on Day 4.",
                    title="Namespaces are NOT network isolation",
                ),
            ),
            ratio="1.1fr 1fr",
        ),
        eyebrow="06 Namespaces",
        kicker="One physical cluster, carved into <b>virtual sub-clusters</b> so teams and "
               "environments stop colliding.",
        notes="Students meet namespaces as a flag they had to type in Lab 3 &mdash; now give "
              "them the concept. The warning box is a top-three misconception: say it out "
              "loud, twice. Ask the room &lsquo;does putting prod in its own namespace stop "
              "dev from talking to it?&rsquo; and let someone answer yes before you correct "
              "it. That moment is what makes NetworkPolicy land on Day 4.",
        day=1,
    ),
    slide(
        "Namespaced vs cluster-scoped",
        two(
            col(
                term(
                    "which is which",
                    """# every resource type, with its scope
kubectl api-resources --namespaced=true  | head
kubectl api-resources --namespaced=false

# the flag is silently ignored on cluster-scoped types
kubectl get nodes -n vote        # same nodes as always

# what actually lives in a namespace
kubectl get all -n kube-system""",
                ),
                note(
                    "n-tip",
                    "<code>kubectl get all</code> is a lie &mdash; it shows a handful of "
                    "common types, not everything. It will not show Secrets, ConfigMaps or "
                    "PVCs. Ask for those by name.",
                ),
            ),
            table(
                ["", "Namespaced", "Cluster-scoped"],
                [
                    ["Examples",
                     "Pod, Service, Deployment,<br>ConfigMap, Secret, PVC, Job",
                     "Node, Namespace, PersistentVolume,<br>StorageClass, ClusterRole"],
                    ["Name must be unique&hellip;", "within its namespace", "across the whole cluster"],
                    ["<code>-n</code> flag", "required (defaults to your context)", "ignored"],
                    ["Deleted with the namespace?", "<b>Yes</b> &mdash; all of them", "No"],
                ],
            ),
            ratio="1fr 1.15fr",
        ),
        eyebrow="Scope",
        kicker="Every resource <b>type</b> is one or the other, permanently. "
               "<code>kubectl api-resources</code> is the authoritative list.",
        notes="The last row is the one that bites: deleting a namespace deletes everything "
              "inside it, silently and irreversibly, and the delete can hang for minutes "
              "while finalizers run. Show api-resources live rather than reading the table "
              "&mdash; it teaches them to answer this question themselves.",
        day=1,
    ),
    slide(
        "Namespaces change your DNS names",
        col(
            '<div class="cli-gram r"><div class="line">'
            '<span class="g1">redis</span><span class="g0">.</span>'
            '<span class="g2">vote</span><span class="g0">.</span>'
            '<span class="g3">svc</span><span class="g0">.</span>'
            '<span class="g4">cluster.local</span></div></div>',
            two(
                col(
                    table(
                        ["Part", "Means"],
                        [
                            ["<code>redis</code>", "the <b>Service</b> name"],
                            ["<code>vote</code>", "its <b>namespace</b>"],
                            ["<code>svc</code>", "it is a Service (not a Pod record)"],
                            ["<code>cluster.local</code>", "the cluster DNS domain"],
                        ],
                    ),
                ),
                col(
                    bul([
                        "<b>Same namespace?</b> Short name is enough: <code>redis</code>.",
                        "<b>Different namespace?</b> You need at least "
                        "<code>redis.vote</code>. The short name will not resolve.",
                        "Pods get a <code>search</code> list in "
                        "<code>/etc/resolv.conf</code> &mdash; that is what makes the short "
                        "form work at all.",
                        "<b>CoreDNS</b> in <code>kube-system</code> serves all of it.",
                    ], "bul tight r"),
                    note(
                        "n-warn",
                        "The Voting App hardcodes <code>Redis(host=&quot;redis&quot;)</code>. "
                        "So our Service <b>must</b> be named exactly <code>redis</code> and "
                        "live in the same namespace as <code>vote</code>. Name it "
                        "<code>redis-svc</code> and the app breaks with no error you would "
                        "recognise.",
                        title="DNS name == Service name",
                    ),
                ),
                ratio="1fr 1.15fr",
                gap=30,
            ),
        ),
        eyebrow="DNS impact",
        kicker="A namespace is baked into every Service&rsquo;s DNS name. Cross a namespace "
               "boundary and the short name stops working.",
        notes="Read the FQDN aloud right to left &mdash; domain, kind, namespace, name &mdash; "
              "it sticks better that way. The warning is the single most likely cause of a "
              "silently broken lab this afternoon, so flag it before they write any YAML. "
              "Promise them the nslookup lab on Day 2 where they prove all of this from "
              "inside a Pod.",
        day=1,
    ),
    lab(
        "Create, switch, live in a namespace",
        two(
            col(
                term(
                    "namespaces",
                    """# create one (imperative, then see the object)
kubectl create namespace vote
kubectl get namespace
kubectl describe namespace vote

# run something in it explicitly
kubectl run tmp --image=nginx:1.27 -n vote
kubectl get pods                 # not there - wrong namespace!
kubectl get pods -n vote         # there it is
kubectl get pods -A              # every namespace at once""",
                ),
                term(
                    "stop typing -n",
                    """# make vote the default for THIS context
kubectl config set-context --current --namespace=vote
kubectl config view --minify | grep namespace

kubectl get pods                 # now it just works
kubectl delete pod tmp""",
                ),
            ),
            col(
                steps([
                    "Create it, then <code>describe</code> it &mdash; a namespace is a real "
                    "object with a status, not just a label.",
                    "Run a Pod with <code>-n vote</code>, then <code>get pods</code> without "
                    "the flag. <b>Empty.</b> That confusion is worth feeling once now.",
                    "<code>-A</code> (or <code>--all-namespaces</code>) is your "
                    "&ldquo;where on earth did it go&rdquo; command.",
                    "Set the default namespace on your context so the rest of today is "
                    "flag-free.",
                ]),
                note(
                    "n-warn",
                    "<code>kubectl delete namespace vote</code> deletes <b>everything</b> "
                    "inside it. There is no undo and no confirmation prompt. Read the "
                    "namespace in your prompt before every destructive command.",
                ),
                note(
                    "n-tip",
                    "<code>kubens</code> switches namespaces in one word. Install it later "
                    "&mdash; today, type the long form until it is muscle memory.",
                ),
            ),
            ratio="1.15fr 1fr",
        ),
        eyebrow="Lab 4 &middot; Namespaces",
        kicker="Build the namespace the Voting App will live in for the next four days, and "
               "make it your default.",
        notes="Everyone must finish this lab &mdash; every remaining Day 1 lab assumes the "
              "vote namespace exists and is their default context. Walk the room and check "
              "config view --minify output. The deliberate empty get pods in step 2 is the "
              "point of the lab, not a mistake; let them hit it.",
        day=1,
    ),
]

# ================================================= 07 labels & selectors (×5)
LABELS = [
    slide(
        "Labels &mdash; the glue of Kubernetes",
        two(
            col(
                term(
                    "pod.yaml",
                    """apiVersion: v1
kind: Pod
metadata:
  name: vote-abc123
  labels:
    app: vote            # what it is
    tier: frontend       # where it sits
    env: dev             # which environment
    version: v1          # which release""",
                ),
                note(
                    "n-info",
                    "Keys may carry an optional prefix: "
                    "<code>app.kubernetes.io/name</code>. Values: max 63 characters, "
                    "alphanumeric plus <code>-</code> <code>_</code> <code>.</code>, and "
                    "they must start and end alphanumeric.",
                ),
            ),
            col(
                bul([
                    "Labels are <b>key/value tags</b> in <code>metadata.labels</code>.",
                    "They are <b>identifying</b> information &mdash; meant to be queried.",
                    "Kubernetes never interprets them. <b>You</b> define the meaning; "
                    "controllers only match on them.",
                    "Nothing in Kubernetes finds a Pod by its name. Deployments, Services, "
                    "ReplicaSets and NetworkPolicies all find Pods <b>by label</b>.",
                ]),
                note(
                    "n-why",
                    "Loose coupling. A Service does not know or care which Pods exist &mdash; "
                    "it asks &ldquo;everything with <code>app=vote</code>&rdquo; and gets "
                    "today&rsquo;s answer. Pods can be replaced a hundred times and the "
                    "wiring never changes.",
                    title="Why labels instead of names",
                ),
            ),
            ratio="1fr 1.05fr",
        ),
        eyebrow="07 Labels &amp; Selectors",
        kicker="They look decorative in a manifest. They are actually <b>the wiring</b> "
               "&mdash; every controller in the cluster finds its Pods this way.",
        notes="They have already seen labels five times in passing; this is where they "
              "finally get named. Hammer the last bullet &mdash; nothing in Kubernetes "
              "addresses a Pod by name, ever. The conventional starter set is app, tier, "
              "env and version; tell them to agree on a scheme early because renaming "
              "labels later is genuinely painful.",
        day=1,
    ),
    slide(
        "Selectors &mdash; asking for a set of Pods",
        two(
            col(
                term(
                    "equality-based",
                    """# on the command line
kubectl get pods -l app=vote
kubectl get pods -l app=vote,tier=frontend   # AND
kubectl get pods -l env!=prod

# in a manifest (Service, older objects)
selector:
  app: vote
  tier: frontend""",
                ),
                note(
                    "n-info",
                    "Multiple terms are always <b>AND</b>. There is no OR in a label "
                    "selector &mdash; use <code>in (a, b)</code> instead.",
                ),
            ),
            col(
                term(
                    "set-based",
                    """kubectl get pods -l 'env in (dev, staging)'
kubectl get pods -l 'app notin (vote)'
kubectl get pods -l app            # key exists
kubectl get pods -l '!app'         # key absent""",
                ),
                term(
                    "matchLabels / matchExpressions",
                    """selector:
  matchLabels:
    app: vote
  matchExpressions:
    - key: tier
      operator: In
      values: [frontend, web]""",
                ),
            ),
            ratio="1fr 1fr",
        ),
        eyebrow="Selectors",
        kicker="A selector is a <b>query over labels</b>. Two dialects: equality-based and "
               "set-based &mdash; and modern objects use <code>matchLabels</code>.",
        notes="Frame a selector as a SELECT WHERE over labels; that clicks instantly for "
              "anyone who has written SQL. Services take the old flat selector; Deployments, "
              "ReplicaSets and Jobs take matchLabels or matchExpressions. Note that "
              "everything ANDs &mdash; the absence of OR surprises people. Quote the "
              "set-based ones in bash or the shell eats the parentheses.",
        day=1,
    ),
    slide(
        "How a selector finds its Pods",
        col(
            two(
                panel(
                    "The selector &mdash; a standing question",
                    '<div class="term xs r"><div class="term-bar"><div class="dots">'
                    "<i></i><i></i><i></i></div><span class=\"term-label\">service.yaml</span>"
                    '<button class="copy">Copy</button></div><pre><code>'
                    + hl("kind: Service\nspec:\n  selector:\n    app: vote")
                    + "</code></pre></div>"
                    + '<p style="margin-top:16px;font-size:21px;color:var(--dim)">'
                    "Evaluated <b>continuously</b>, never once. Add a matching Pod at 3am "
                    "and it joins the Service at 3am.</p>",
                    "blue",
                ),
                panel(
                    "The Pods &mdash; answering it or not",
                    '<div class="stackd" style="gap:12px">'
                    + flow(bx("vote-abc", "app=vote &nbsp;&#10003; matches", "green"), gap=10)
                    + flow(bx("vote-def", "app=vote &nbsp;&#10003; matches", "green"), gap=10)
                    + flow(bx("redis-xyz", "app=redis &nbsp;&#10007; ignored", "slate"), gap=10)
                    + "</div>",
                    "teal",
                ),
                ratio="1fr 1fr",
                gap=30,
            ),
            note(
                "n-warn",
                "Typo a label and nothing errors. The Service is created, "
                "<code>kubectl get svc</code> looks perfectly healthy &mdash; it just "
                "selects <b>zero</b> Pods and every request times out. "
                "<code>kubectl get endpoints &lt;svc&gt;</code> showing "
                "<code>&lt;none&gt;</code> is the tell. We plant this failure on purpose on "
                "Day 2.",
                title="The silent failure",
            ),
        ),
        eyebrow="The core coupling",
        kicker="A selector does not point at Pods. It <b>describes</b> them &mdash; and the "
               "answer is recomputed every time anything changes.",
        notes="This is the mechanism the entire course rests on, so slow down here. Stress "
              "that the match is continuous, not a one-time binding &mdash; that is what "
              "makes self-healing and rolling updates possible at all. The warning is the "
              "number one reason a beginner's Service returns nothing; teach get endpoints "
              "as the reflex now so Day 2's planted failure is diagnosable.",
        day=1,
    ),
    slide(
        "Labels vs annotations",
        two(
            table(
                ["", "Labels", "Annotations"],
                [
                    ["Purpose", "<b>Identify</b> and group", "<b>Attach</b> arbitrary metadata"],
                    ["Queryable?", "<b>Yes</b> &mdash; indexed, selectable", "<b>No</b> &mdash; never selectable"],
                    ["Size", "&le; 63 chars, restricted charset", "Large &mdash; JSON, certs, whole configs"],
                    ["Used by", "Services, Deployments, NetworkPolicy&hellip;", "Tools: ingress-nginx, cert-manager, Helm"],
                    ["Example", "<code>app: vote</code>", "<code>kubernetes.io/change-cause: &quot;bump to v2&quot;</code>"],
                ],
            ),
            col(
                term(
                    "both in one manifest",
                    """metadata:
  name: vote
  labels:                     # for selecting
    app: vote
  annotations:                # for tools and humans
    owner: "platform-team@iti"
    kubernetes.io/change-cause: "bump vote to v2\"""",
                ),
                note(
                    "n-warn",
                    "If you will ever select on it, it is a <b>label</b>. If it is a note, a "
                    "URL, a checksum or a tool&rsquo;s configuration, it is an "
                    "<b>annotation</b>. Stuffing a paragraph into a label fails validation; "
                    "expecting <code>-l</code> to find an annotation silently returns nothing.",
                    title="Choosing between them",
                ),
            ),
            ratio="1.15fr 1fr",
        ),
        eyebrow="Contrast",
        kicker="Both are key/value maps in <code>metadata</code>. Only one of them can be "
               "<b>selected on</b> &mdash; and that is the whole difference.",
        notes="Give them the one-line test: can you imagine typing -l on it? Then it is a "
              "label. Annotations feel useless today and become essential on Day 2 &mdash; "
              "change-cause is what puts a readable reason in rollout history, and every "
              "Ingress annotation on Day 4 lands here.",
        day=1,
    ),
    lab(
        "Label, filter, relabel &mdash; watch a selector follow",
        two(
            col(
                term(
                    "label and filter",
                    """kubectl run web-1 --image=nginx:1.27 -l app=web,env=dev
kubectl run web-2 --image=nginx:1.27 -l app=web,env=prod
kubectl run cache --image=redis:alpine -l app=cache

kubectl get pods --show-labels
kubectl get pods -l app=web
kubectl get pods -l app=web,env=prod
kubectl get pods -l 'env in (dev, prod)'
kubectl get pods -L app,env        # labels as COLUMNS""",
                ),
                term(
                    "relabel a live Pod",
                    """# watch the selector in one terminal
kubectl get pods -l app=web -w

# in a second terminal - move cache into the set
kubectl label pod cache app=web --overwrite
# ...and back out again
kubectl label pod cache app=cache --overwrite

kubectl label pod web-1 tier-        # remove a label""",
                ),
            ),
            col(
                steps([
                    "Create three Pods with different labels &mdash; <code>-l</code> on "
                    "<code>kubectl run</code> sets them at birth.",
                    "<code>--show-labels</code> appends them all; <code>-L app,env</code> "
                    "promotes chosen keys to real columns. Learn both.",
                    "Filter with <code>-l</code>. Notice each query returns a "
                    "<b>set</b>, and the set changes as the world changes.",
                    "In the watch terminal, relabel <code>cache</code>. It <b>appears</b> in "
                    "the <code>app=web</code> stream without touching the query.",
                    "<code>tier-</code> (trailing dash) removes a label. Clean up: "
                    "<code>kubectl delete pod web-1 web-2 cache</code>.",
                ]),
                note(
                    "n-tip",
                    "<code>--overwrite</code> is required to change an existing label. "
                    "Without it, <code>kubectl label</code> refuses rather than silently "
                    "clobbering &mdash; a deliberate guardrail.",
                ),
            ),
            ratio="1.15fr 1fr",
        ),
        eyebrow="Lab 5 &middot; Labels",
        kicker="Two terminals. Run a watch on a selector, then relabel a Pod into it and "
               "out of it, live.",
        notes="Make them use two terminals &mdash; seeing the Pod pop into the watch stream "
              "the instant it is relabelled is the entire point, and it is invisible if "
              "they run the commands one after another. This is exactly how a Deployment "
              "adopts an orphan Pod and how a rolling update swaps traffic. Ask what would "
              "happen if a Service were selecting app=web right now.",
        day=1,
    ),
]

# ==================================================== 08b pod lifecycle (×5)
PODLIFE = [
    slide(
        "Pod phases &mdash; the five words in STATUS",
        two(
            table(
                ["Phase", "Meaning", "What to do"],
                [
                    ["<b>Pending</b>",
                     "Accepted, but not running yet &mdash; being scheduled, or images "
                     "still pulling.",
                     "<code>describe</code> it. Events say whether it is unschedulable or "
                     "just downloading."],
                    ["<b>Running</b>",
                     "Bound to a node; <b>at least one</b> container is running or starting.",
                     "Check <code>READY</code>, not the phase."],
                    ["<b>Succeeded</b>",
                     "All containers exited <code>0</code> and will not restart.",
                     "Normal for Jobs. Suspicious for a web server."],
                    ["<b>Failed</b>",
                     "All containers terminated and at least one exited non-zero.",
                     "<code>logs --previous</code> for the death note."],
                    ["<b>Unknown</b>",
                     "The api-server lost contact with the node.",
                     "Node problem, not a Pod problem. <code>get nodes</code>."],
                ],
            ),
            col(
                note(
                    "n-warn",
                    "<b>Running does not mean working.</b> The phase only says containers "
                    "were started. Read the <code>READY</code> column: <code>1/1</code> is "
                    "&ldquo;1 of 1 containers passing readiness&rdquo;. A Pod sitting at "
                    "<code>0/1 Running</code> is up and serving nobody.",
                    title="READY, not STATUS",
                ),
                note(
                    "n-info",
                    "The <code>STATUS</code> column is not always the phase. kubectl helpfully "
                    "substitutes the more useful reason &mdash; <code>CrashLoopBackOff</code>, "
                    "<code>ImagePullBackOff</code>, <code>Terminating</code>, "
                    "<code>Completed</code>. Those are the ones you will actually see.",
                ),
                term(
                    "read the phase",
                    """kubectl get pods
kubectl get pod vote -o jsonpath='{.status.phase}'
kubectl get pod vote -o yaml | head -40""",
                ),
            ),
            ratio="1.35fr 1fr",
        ),
        eyebrow="08 Pod lifecycle",
        kicker="A Pod is always in exactly one <b>phase</b>. Five values, and only two of "
               "them are good news.",
        notes="The READY warning is confusion point 14 and it costs students real hours "
              "&mdash; they see Running, declare victory, and cannot work out why nothing "
              "responds. Show a live get pods and point at both columns explicitly. Mention "
              "that STATUS is a friendly summary, not the raw phase, so they are not "
              "confused when CrashLoopBackOff appears there.",
        day=1,
    ),
    slide(
        "The lifecycle, as a state machine",
        col(
            flow(
                bx("Pending", "scheduling &middot; pulling", "gold"),
                arrow(),
                bx("Running", "containers started", "blue"),
                arrow(),
                bx("Succeeded", "all exited 0", "green"),
                gap=16,
            ),
            flow(
                '<div style="flex:1"></div>',
                bx("Failed", "exited non-zero", "maroon", grow=False),
                '<div style="flex:1"></div>',
                gap=16,
            ),
            panel(
                "The restart cycle &mdash; where CrashLoopBackOff comes from",
                flow(
                    bx("container starts", "", "teal"),
                    arrow(),
                    bx("crashes", "exit != 0", "maroon"),
                    arrow(),
                    bx("kubelet waits", "10s &rarr; 20s &rarr; 40s&hellip; 5m", "amber"),
                    arrow("&#8630;"),
                    bx("restarts it", "back to the top", "teal"),
                    gap=12,
                )
                + '<p style="margin-top:16px;font-size:21px;color:var(--dim)">The Pod stays '
                "in phase <b>Running</b> the whole time. Only <code>RESTARTS</code> and the "
                "<code>STATUS</code> text give it away.</p>",
                "maroon",
            ),
            note(
                "n-info",
                "Phases only move <b>forwards</b>. A Pod never goes back from Succeeded to "
                "Pending &mdash; when you see a &ldquo;restarted&rdquo; Pod, a "
                "<b>container</b> restarted inside the same Pod, or a controller made an "
                "entirely new Pod.",
            ),
        ),
        eyebrow="Diagram",
        kicker="Forward only &mdash; except for the container restart loop, which spins "
               "inside <code>Running</code> and is where most of your debugging happens.",
        notes="Walk the top row left to right, then drop to the crash cycle and emphasise "
              "the back-off doubling &mdash; that delay is why a broken Pod seems to hang "
              "instead of spamming. The key insight is the last note: the crash loop lives "
              "inside Running, so students who filter on phase will miss it entirely.",
        day=1,
    ),
    slide(
        "Container states &amp; restartPolicy",
        two(
            col(
                panel(
                    "Three container states",
                    bul([
                        "<b>Waiting</b> &mdash; not running yet. Carries a <code>reason</code>: "
                        "<code>ContainerCreating</code>, <code>ImagePullBackOff</code>, "
                        "<code>CrashLoopBackOff</code>.",
                        "<b>Running</b> &mdash; executing, with a <code>startedAt</code>.",
                        "<b>Terminated</b> &mdash; finished, with an <code>exitCode</code>, "
                        "<code>reason</code> and <code>finishedAt</code>.",
                    ], "bul tight r"),
                    "violet",
                ),
                term(
                    "where the truth lives",
                    """kubectl describe pod vote | sed -n '/Containers:/,/Events/p'

# exit code of the last crash
kubectl get pod vote \\
  -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}'""",
                ),
            ),
            col(
                table(
                    ["<code>restartPolicy</code>", "Restarts when&hellip;", "Use for"],
                    [
                        ["<b>Always</b> <i>(default)</i>", "container exits &mdash; whatever "
                         "the code", "long-running servers: vote, result, redis"],
                        ["<b>OnFailure</b>", "exit code is non-zero only", "Jobs and batch work"],
                        ["<b>Never</b>", "never &mdash; the Pod goes to Failed/Succeeded",
                         "one-shot debugging Pods"],
                    ],
                ),
                note(
                    "n-warn",
                    "<code>restartPolicy</code> applies to <b>containers inside</b> the Pod, "
                    "not to the Pod itself. A dead Pod is never resurrected by this setting "
                    "&mdash; a bare Pod that gets deleted is gone forever. That is what "
                    "Deployments are for, and you will feel it in Lab 6.",
                    title="It restarts containers, not Pods",
                ),
            ),
            ratio="1fr 1.1fr",
        ),
        eyebrow="Inside the Pod",
        kicker="The phase is the summary. The <b>container state</b> is where the reason "
               "and the exit code actually live.",
        notes="Teach the exit-code habit now: 0 is clean, 1 is the app throwing, 137 is "
              "SIGKILL which usually means OOMKilled, 143 is SIGTERM. The warning sets up "
              "this afternoon's bare-Pod lab &mdash; students routinely assume "
              "restartPolicy: Always means the Pod is immortal, then delete one and are "
              "shocked when nothing returns.",
        day=1,
    ),
    slide(
        "CrashLoopBackOff",
        two(
            col(
                '<div class="failbox r"><div class="fb-h">'
                '<span class="fb-badge">STATUS</span>'
                '<span class="fb-t">CrashLoopBackOff</span></div>'
                '<div class="term xs"><div class="term-bar"><div class="dots">'
                "<i></i><i></i><i></i></div><span class=\"term-label\">kubectl get pods</span>"
                '<button class="copy">Copy</button></div><pre><code>'
                + hl(
                    "NAME     READY   STATUS             RESTARTS      AGE\n"
                    "worker   0/1     CrashLoopBackOff   5 (46s ago)   4m12s"
                )
                + "</code></pre></div>"
                '<div class="fb-note">Your container <b>starts fine and then dies</b>. '
                "Kubernetes restarts it, it dies again, and the wait between attempts "
                "doubles: 10s, 20s, 40s&hellip; capped at 5 minutes. <b>The image is fine "
                "&mdash; the process is not.</b></div></div>",
                note(
                    "n-warn",
                    "It is <b>not</b> an error in itself &mdash; it is Kubernetes telling you "
                    "it has given up restarting quickly. The real error is in the logs of "
                    "the run that already ended, which is why "
                    "<code>--previous</code> matters.",
                ),
            ),
            col(
                panel(
                    "Why it happens",
                    bul([
                        "The app throws on startup &mdash; missing env var, bad config, "
                        "unreachable dependency. <b>Most common.</b>",
                        "A dependency is not up yet: <code>worker</code> starting before "
                        "<code>db</code> exists.",
                        "The command exits immediately &mdash; a container with nothing to "
                        "do in the foreground.",
                        "Wrong <code>command</code>/<code>args</code>, or the binary is not "
                        "at that path.",
                        "OOMKilled &mdash; exit <code>137</code>, memory limit too low (Day 4).",
                    ], "bul tight r"),
                    "maroon",
                ),
                term(
                    "how to read it",
                    """kubectl describe pod worker      # Last State + Exit Code
kubectl logs worker --previous   # logs of the run that DIED
kubectl get events --sort-by=.lastTimestamp | tail""",
                ),
            ),
            ratio="1fr 1.05fr",
        ),
        eyebrow="Failure state 1",
        kicker="The most common failure in Kubernetes, and the one students misread most: "
               "<b>the container is starting successfully &mdash; and then exiting.</b>",
        notes="Drill --previous until it is automatic. Plain kubectl logs on a "
              "crash-looping Pod usually returns nothing or a truncated line, because the "
              "current container has not started yet; the evidence is in the corpse of the "
              "previous one. Tell them the back-off delay is why the cluster looks frozen "
              "&mdash; it is waiting, not stuck.",
        day=1,
    ),
    slide(
        "ImagePullBackOff &amp; ErrImagePull",
        two(
            col(
                '<div class="failbox r"><div class="fb-h">'
                '<span class="fb-badge">STATUS</span>'
                '<span class="fb-t">ImagePullBackOff</span></div>'
                '<div class="term xs"><div class="term-bar"><div class="dots">'
                "<i></i><i></i><i></i></div><span class=\"term-label\">kubectl describe pod</span>"
                '<button class="copy">Copy</button></div><pre><code>'
                + hl(
                    "Events:\n"
                    "  Warning  Failed   Failed to pull image \"iti/vote:v99\"\n"
                    "  Warning  Failed   Error: ErrImagePull\n"
                    "  Normal   BackOff  Back-off pulling image \"iti/vote:v99\""
                )
                + "</code></pre></div>"
                '<div class="fb-note"><b>ErrImagePull</b> is the first failed attempt. '
                "<b>ImagePullBackOff</b> is what it becomes once the kubelet starts waiting "
                "between retries. Same problem &mdash; the node <b>cannot get the image</b>, "
                "so no container ever starts.</div></div>",
                note(
                    "n-warn",
                    "The Pod never reaches Running and there are <b>no logs to read</b> "
                    "&mdash; there is no container yet. <code>kubectl logs</code> will tell "
                    "you so. <b><code>describe</code> is the only tool that works here.</b>",
                ),
            ),
            col(
                panel(
                    "Why it happens",
                    bul([
                        "Typo in the image name or tag. <b>Check this first, always.</b>",
                        "The tag does not exist in the registry &mdash; "
                        "<code>:v99</code> when only <code>:v1</code> was pushed.",
                        "Private registry with no <code>imagePullSecret</code> "
                        "&rarr; <code>unauthorized</code>.",
                        "<b>Our number-one cause today:</b> a locally built image never "
                        "loaded into kind, so the node tries Docker Hub and finds nothing.",
                        "Rate limits or no outbound network from the node.",
                    ], "bul tight r"),
                    "amber",
                ),
                term(
                    "how to read it",
                    """kubectl describe pod vote | sed -n '/Events/,$p'

# is the image actually on the node?
docker exec iti-control-plane crictl images | grep iti/

# fix: load it, and never let it try to pull
kind load docker-image iti/vote:v1 --name iti""",
                ),
            ),
            ratio="1fr 1.05fr",
        ),
        eyebrow="Failure state 2",
        kicker="The node could not fetch the image. Nothing ran, nothing logged &mdash; "
               "<code>describe</code> is your only witness.",
        notes="This is the failure that will derail this afternoon if you do not pre-empt "
              "it, because every locally built image hits it without kind load plus "
              "imagePullPolicy: IfNotPresent. Make the no-logs point explicitly &mdash; "
              "students burn ten minutes running kubectl logs against a Pod that has no "
              "container. Distinguish ErrImagePull from ImagePullBackOff once, then move on.",
        day=1,
    ),
]

# =============================================== 09 container config (×3)
ENVARGS = [
    slide(
        "Environment variables in a Pod",
        two(
            col(
                term(
                    "vote-pod.yaml",
                    """spec:
  containers:
    - name: vote
      image: iti/vote:v1
      env:
        - name: OPTION_A          # literal value
          value: "Tabs"
        - name: OPTION_B
          value: "Spaces"
        - name: MY_POD_IP         # from the Pod itself
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
        - name: MY_NODE
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName""",
                ),
            ),
            col(
                bul([
                    "<code>env</code> is a <b>list</b>, not a map &mdash; every entry needs "
                    "<code>name</code> plus one of <code>value</code> / "
                    "<code>valueFrom</code>.",
                    "<code>value</code> must be a <b>string</b>. Quote your numbers or the "
                    "api-server rejects the manifest.",
                    "<code>valueFrom.fieldRef</code> is the <b>Downward API</b> &mdash; the "
                    "Pod reading its own metadata: <code>metadata.name</code>, "
                    "<code>metadata.namespace</code>, <code>status.podIP</code>, "
                    "<code>spec.nodeName</code>.",
                    "Later this week: <code>configMapKeyRef</code> and "
                    "<code>secretKeyRef</code> pull values from real config objects (Day 3).",
                ]),
                note(
                    "n-warn",
                    "Environment variables are set <b>once, at container start</b>. Change "
                    "them and nothing happens to the running Pod &mdash; you must recreate "
                    "it. There is no live reload; that surprises everyone on Day 3.",
                ),
                term(
                    "verify",
                    """kubectl exec vote -- env | sort
kubectl exec vote -- printenv OPTION_A""",
                ),
            ),
            ratio="1fr 1.05fr",
        ),
        eyebrow="09 Container config",
        kicker="The same idea as Compose&rsquo;s <code>environment:</code> &mdash; just a "
               "list instead of a map. This is how <code>vote</code> learns what to put on "
               "the ballot.",
        notes="Connect it straight back to Compose so it feels like a rename, not a new "
              "concept. The two things they get wrong: forgetting env is a list of "
              "name/value objects, and passing an unquoted number. Flag the "
              "set-once warning now &mdash; it is the reason rollout restart exists and it "
              "saves a long argument on Day 3.",
        day=1,
    ),
    slide(
        "command vs args",
        two(
            col(
                term(
                    "override both",
                    """spec:
  containers:
    - name: demo
      image: busybox:1.36
      command: ["sh", "-c"]              # replaces ENTRYPOINT
      args: ["echo hi; sleep 3600"]      # replaces CMD""",
                ),
                term(
                    "override only the arguments",
                    """spec:
  containers:
    - name: redis
      image: redis:alpine
      args: ["--maxmemory", "100mb"]     # image ENTRYPOINT kept""",
                ),
            ),
            col(
                steps([
                    "<b>Neither set</b> &mdash; the image&rsquo;s ENTRYPOINT and CMD run. "
                    "This is what you want almost every time.",
                    "<b><code>args</code> only</b> &mdash; ENTRYPOINT kept, CMD replaced. The "
                    "usual way to pass flags to an image.",
                    "<b><code>command</code> only</b> &mdash; ENTRYPOINT replaced and "
                    "<b>CMD is dropped entirely</b>. This one catches people out.",
                    "<b>Both set</b> &mdash; the image&rsquo;s own settings are ignored "
                    "completely. Total control.",
                ]),
                note(
                    "n-warn",
                    "Both are <b>YAML lists</b>, not shell strings. "
                    "<code>command: [&quot;echo hi &amp;&amp; sleep 60&quot;]</code> does not "
                    "work &mdash; there is no shell to interpret <code>&amp;&amp;</code>. "
                    "If you need shell syntax, ask for one: "
                    "<code>[&quot;sh&quot;, &quot;-c&quot;, &quot;&hellip;&quot;]</code>.",
                    title="No shell unless you ask",
                ),
            ),
            ratio="1.05fr 1fr",
        ),
        eyebrow="Overriding the image",
        kicker="Two optional fields that replace what the image was built to run. Set them "
               "rarely &mdash; but know exactly what they do.",
        notes="The no-shell warning is worth a live demo: run a Pod with a pipe or "
              "ampersand in command and watch it fail, then fix it with sh -c. Emphasise "
              "case 3 &mdash; setting command alone silently discards the image's CMD, and "
              "that is the source of many mysterious instant exits.",
        day=1,
    ),
    slide(
        "How it maps to Docker",
        two(
            table(
                ["Docker / Dockerfile", "Kubernetes", "Effect"],
                [
                    ["<code>ENTRYPOINT</code>", "<code>command</code>", "the executable"],
                    ["<code>CMD</code>", "<code>args</code>", "the arguments to it"],
                    ["<code>docker run img</code>", "neither field set", "ENTRYPOINT + CMD, as built"],
                    ["<code>docker run img foo</code>", "<code>args: [&quot;foo&quot;]</code>",
                     "ENTRYPOINT + <code>foo</code>"],
                    ["<code>--entrypoint sh img</code>", "<code>command: [&quot;sh&quot;]</code>",
                     "<code>sh</code> only &mdash; CMD discarded"],
                    ["<code>ENV FOO=bar</code>", "<code>env: [{name: FOO, value: &quot;bar&quot;}]</code>",
                     "same variable, different syntax"],
                ],
            ),
            col(
                note(
                    "n-tip",
                    "The naming is genuinely unhelpful. Memorise the pair: "
                    "<b><code>command</code> = ENTRYPOINT</b>, "
                    "<b><code>args</code> = CMD</b>. Everything else follows.",
                ),
                term(
                    "check what an image ships with",
                    """docker inspect iti/vote:v1 \\
  --format '{{.Config.Entrypoint}} {{.Config.Cmd}}'

# and what the Pod actually ran
kubectl get pod vote -o jsonpath='{.spec.containers[0].command}'""",
                ),
                note(
                    "n-info",
                    "Our <code>vote</code> image ships "
                    "<code>CMD [&quot;gunicorn&quot;, &quot;app:app&quot;, &quot;-b&quot;, "
                    "&quot;0.0.0.0:80&quot;]</code> and no ENTRYPOINT &mdash; so in "
                    "Kubernetes we set <b>neither</b> field and it just runs.",
                ),
            ),
            ratio="1.3fr 1fr",
        ),
        eyebrow="Docker &rarr; Kubernetes",
        kicker="Same two concepts, different names. This table is the whole translation.",
        notes="Everyone in the room already knows Docker, so sell this as vocabulary, not "
              "new behaviour. The last note ties it to the image they are about to build "
              "&mdash; point out that the right answer for the Voting App is to override "
              "nothing at all, and that Compose overriding the command is a "
              "development-only habit they should leave behind.",
        day=1,
    ),
]

# ============================================ Lab: build the images (×3)
VAIMAGES = [
    lab(
        "Meet the Voting App &mdash; and start the slow build",
        two(
            col(
                term(
                    "start the worker FIRST",
                    """cd voting-app
ls                     # vote/ result/ worker/ docker-compose.yml

# The Java worker is Maven-based: it resolves, verifies and packages.
# On a cold cache that is 5-15 MINUTES. Start it NOW, in the
# background, and we will teach the other two while it runs.
docker build -t iti/worker:v1 ./worker > /tmp/worker.log 2>&1 &

jobs                   # confirm it is running
tail -f /tmp/worker.log      # peek any time, Ctrl-C to stop watching""",
                ),
                note(
                    "n-warn",
                    "Do not wait for this build with 25 people on one wifi. Kick it off, "
                    "background it, and move on. If you sit and watch it, you lose fifteen "
                    "minutes of the day.",
                ),
            ),
            col(
                panel(
                    "Five components, five lessons",
                    '<div class="stackd" style="gap:12px">'
                    + flow(
                        bx("vote", "Python/Flask :80", "blue"),
                        arrow(),
                        bx("redis", "queue", "maroon"),
                        gap=12,
                    )
                    + flow(
                        bx("worker", "Java &middot; no Service", "amber"),
                        arrow(),
                        bx("db", "Postgres", "violet"),
                        arrow(),
                        bx("result", "Node :80", "green"),
                        gap=12,
                    )
                    + "</div>"
                    + '<p style="margin-top:16px;font-size:20px;color:var(--dim)">'
                    "<code>vote</code> pushes to <code>redis</code>. <code>worker</code> "
                    "drains <code>redis</code> into <code>db</code>. <code>result</code> "
                    "reads <code>db</code>. We build the three we own; "
                    "<code>redis</code> and <code>db</code> come from Docker Hub.</p>",
                    "teal",
                ),
                bul([
                    "This app is the spine of all four days. Every concept lands on it.",
                    "You <b>build from source</b> &mdash; no prebuilt shortcut. That is what "
                    "makes the <code>kind load</code> lesson real.",
                    "Tag everything <code>iti/&lt;name&gt;:v1</code>. Day 2 builds "
                    "<code>:v2</code> and rolls between them.",
                ], "bul tight r"),
            ),
            ratio="1.1fr 1fr",
        ),
        eyebrow="Lab 6a &middot; Images",
        kicker="Three images to build. One of them is slow &mdash; so it goes first, in the "
               "background, before anything else.",
        notes="Get the worker build started in the first sixty seconds of this lab, before "
              "you explain anything &mdash; talk over it while it runs. Walk the room and "
              "check the ampersand is actually there; a foreground build is how one student "
              "ends up fifteen minutes behind everyone else. Sketch the five-box diagram on "
              "the whiteboard too; you will point at it all week.",
        day=1,
    ),
    lab(
        "Build vote and result while worker runs",
        two(
            col(
                term(
                    "vote &mdash; Python/Flask",
                    """docker build -t iti/vote:v1 ./vote
# python:3.11-slim + pip install. Fast.
# CMD is gunicorn on :80 - the container listens on 80, not 5000.""",
                ),
                term(
                    "result &mdash; Node, multi-stage",
                    """docker build -t iti/result:v1 ./result

# The Dockerfile is:  base -> dev -> prod
# A plain build stops at the LAST stage = prod. That is what we want.

# Do NOT do this - it is the Compose stage (nodemon, dev deps):
#   docker build --target dev -t iti/result:v1 ./result""",
                ),
                term(
                    "confirm all three",
                    """wait                       # block until the worker build finishes
tail -20 /tmp/worker.log
docker images | grep iti/""",
                ),
            ),
            col(
                steps([
                    "Build <code>vote</code>. Note the image serves on <b>:80</b> &mdash; "
                    "Compose mapped it to 5000 on your laptop, but inside the container it "
                    "has always been 80.",
                    "Build <code>result</code>. <b>No <code>--target</code>.</b> The final "
                    "stage in the Dockerfile is <code>prod</code>, so a plain build gives "
                    "you the production image.",
                    "<code>wait</code> blocks until the backgrounded worker build finishes. "
                    "Check the tail of the log for <code>BUILD SUCCESS</code>.",
                    "You should now see exactly three <code>iti/</code> images.",
                ]),
                note(
                    "n-warn",
                    "<code>docker-compose.yml</code> builds <code>result</code> with "
                    "<code>target: dev</code> and overrides the command with "
                    "<code>nodemon</code>. That is a <b>development</b> convenience. Carry "
                    "that habit into Kubernetes and you ship a file-watcher into your "
                    "cluster.",
                    title="Compose habits do not transfer",
                ),
            ),
            ratio="1.1fr 1fr",
        ),
        eyebrow="Lab 6b &middot; Images",
        kicker="Two fast builds while the slow one runs behind you. Then collect all three.",
        notes="The container-port point pays off tomorrow when they meet targetPort &mdash; "
              "say clearly that 5000 was a Compose port mapping and has no meaning here. "
              "Expect at least one student to reach for --target dev out of Compose muscle "
              "memory; the warning box exists specifically for them.",
        day=1,
    ),
    lab(
        "Load the images into kind &mdash; or nothing runs",
        two(
            col(
                term(
                    "kind load",
                    """kind load docker-image iti/vote:v1   --name iti
kind load docker-image iti/result:v1 --name iti
kind load docker-image iti/worker:v1 --name iti

# prove they landed on the node itself
docker exec iti-control-plane crictl images | grep iti/""",
                ),
                term(
                    "and pin the pull policy",
                    """spec:
  containers:
    - name: vote
      image: iti/vote:v1
      imagePullPolicy: IfNotPresent   # MANDATORY for local images""",
                ),
            ),
            col(
                note(
                    "n-why",
                    "kind nodes are <b>Docker containers with their own image store</b>. "
                    "Your laptop&rsquo;s Docker daemon and the cluster&rsquo;s container "
                    "runtime are two different worlds. <code>docker images</code> showing "
                    "the image means nothing to the kubelet.",
                    title="Why this step exists",
                ),
                note(
                    "n-warn",
                    "Skip <code>kind load</code>, or leave <code>imagePullPolicy</code> "
                    "unset, and every Pod lands in <b>ImagePullBackOff</b> &mdash; the node "
                    "asks Docker Hub for <code>iti/vote:v1</code>, which does not exist "
                    "there. This is the <b>single most likely way today derails</b>.",
                    title="Both steps, or nothing runs",
                ),
                table(
                    ["<code>imagePullPolicy</code>", "Behaviour", "Default when&hellip;"],
                    [
                        ["<code>IfNotPresent</code>", "use the local copy if present",
                         "tag is <b>not</b> <code>:latest</code>"],
                        ["<code>Always</code>", "pull every time a container starts",
                         "tag <b>is</b> <code>:latest</code>, or omitted"],
                        ["<code>Never</code>", "local only, fail if missing", "&mdash;"],
                    ],
                ),
            ),
            ratio="1fr 1.1fr",
        ),
        eyebrow="Lab 6c &middot; Images",
        kicker="Your images exist on your laptop. The cluster cannot see them. <b>Two steps "
               "fix that &mdash; and both are mandatory.</b>",
        notes="Do not let anyone move past this slide until crictl images shows all three. "
               "The table explains the trap: :latest silently defaults to Always, which is "
               "why students who tag :latest fail even after loading. Tell them this is also "
               "why pinned tags are a production rule, not just a lab convention &mdash; it "
               "comes back on Day 4.",
        day=1,
    ),
]

# ======================================== Lab: the app as bare Pods (×2)
VAPODS = [
    lab(
        "Run the Voting App as bare Pods",
        two(
            col(
                term(
                    "day1-pods.yaml",
                    """apiVersion: v1
kind: Pod
metadata:
  name: redis
  labels:
    app: redis
spec:
  containers:
    - name: redis
      image: redis:alpine
      ports:
        - containerPort: 6379
---
apiVersion: v1
kind: Service          # so DNS name "redis" exists
metadata:
  name: redis
spec:
  selector:
    app: redis
  ports:
    - port: 6379
      targetPort: 6379
---
apiVersion: v1
kind: Pod
metadata:
  name: vote
  labels:
    app: vote
spec:
  containers:
    - name: vote
      image: iti/vote:v1
      imagePullPolicy: IfNotPresent
      ports:
        - containerPort: 80""",
                ),
            ),
            col(
                term(
                    "apply and check",
                    """kubectl apply -f day1-pods.yaml -n vote
kubectl get pods -n vote -o wide
kubectl get svc,endpoints -n vote

kubectl logs vote -n vote            # gunicorn booting on :80
kubectl exec redis -n vote -- redis-cli ping    # PONG""",
                ),
                note(
                    "n-warn",
                    "The Service <b>must</b> be named <code>redis</code>. "
                    "<code>vote/app.py</code> hardcodes "
                    "<code>Redis(host=&quot;redis&quot;)</code> &mdash; call it "
                    "<code>redis-svc</code> and the page loads fine but every vote silently "
                    "fails.",
                    title="The name is load-bearing",
                ),
                note(
                    "n-info",
                    "Yes, we are creating a Service before we have taught Services. Today it "
                    "exists only to give <code>redis</code> a DNS name. Tomorrow it gets a "
                    "whole section.",
                ),
            ),
            ratio="1.05fr 1fr",
        ),
        eyebrow="Lab 7a &middot; Voting App",
        kicker="Two Pods and one Service, in the <code>vote</code> namespace. This is the "
               "worst way to run an application &mdash; and that is exactly the point.",
        notes="Everything here is deliberately primitive: bare Pods, a hand-written "
              "Service, no controllers. Let them enjoy it working for about three minutes. "
              "Watch for the namespace &mdash; if they set the default context in Lab 4 the "
              "-n flags are redundant, but leave them in the slides so nobody is lost. "
              "PONG from redis-cli is the checkpoint before moving on.",
        day=1,
    ),
    lab(
        "Now kill a Pod &mdash; nothing comes back",
        two(
            col(
                term(
                    "break it",
                    """kubectl get pods -n vote
kubectl delete pod redis -n vote

kubectl get pods -n vote          # only "vote" is left
kubectl get endpoints redis -n vote   # ENDPOINTS: <none>

# wait as long as you like. Nothing is coming.
kubectl get pods -n vote -w""",
                ),
                term(
                    "and the app half-dies",
                    """# the page still loads - it is a stateless Flask app...
kubectl port-forward pod/vote 8080:80 -n vote
# ...but casting a vote now errors: redis is gone

# the only fix available to you today
kubectl apply -f day1-pods.yaml -n vote""",
                ),
            ),
            col(
                '<div class="failbox r"><div class="fb-h">'
                '<span class="fb-badge">EXPECTED</span>'
                '<span class="fb-t">This is supposed to hurt</span></div>'
                '<div class="fb-note">A bare Pod has <b>no guardian</b>. Nothing in the '
                "cluster believes there should be a <code>redis</code> Pod &mdash; you "
                "created one, and now there is not one. There is no desired state to "
                "reconcile against.</div></div>",
                bul([
                    "<code>restartPolicy: Always</code> did <b>not</b> save you &mdash; it "
                    "restarts <b>containers</b> inside a live Pod, never a deleted Pod.",
                    "Same story if the <b>node</b> dies, or the Pod is evicted for memory.",
                    "The Service survived, because a Service is not a Pod &mdash; it just "
                    "has nothing to point at. <code>ENDPOINTS: &lt;none&gt;</code>.",
                    "<b>Tomorrow:</b> a Deployment holds the desired state, and this same "
                    "delete gets replaced in about two seconds.",
                ]),
                note(
                    "n-tip",
                    "Leave the app broken and go to break. Day 2 opens by fixing exactly "
                    "this, and the contrast is the lesson.",
                ),
            ),
            ratio="1.05fr 1fr",
        ),
        eyebrow="Lab 7b &middot; Feel the problem",
        kicker="Delete the <code>redis</code> Pod and watch <b>nothing at all</b> happen. "
               "No self-healing, no replacement, no alarm.",
        notes="Resist the urge to explain Deployments here &mdash; the frustration is the "
              "teaching device and it only works if you let it sit. Ask the room what they "
              "expected to happen, and why. Point at the ENDPOINTS: <none> output because "
              "they will meet that exact symptom again on Day 2 as a planted failure.",
        day=1,
    ),
]

# ================================================ 10 debugging toolkit (×6)
DEBUG1 = [
    slide(
        "The debugging toolkit",
        col(
            cards(
                [
                    ("&#128269;", "describe",
                     "Object state <b>plus the Events tail</b>. Your first move, every time. "
                     "Works even when no container exists.", "t-blue"),
                    ("&#128220;", "logs",
                     "What the app said. <code>-f</code> to follow, <code>--previous</code> "
                     "for the run that crashed, <code>-c</code> to pick a container.", "t-teal"),
                    ("&#128421;", "exec",
                     "A shell <b>inside</b> the running container. Check files, env, DNS, "
                     "reachability &mdash; from where the app actually lives.", "t-violet"),
                    ("&#128276;", "get events",
                     "The cluster&rsquo;s activity feed. <code>--sort-by</code> is not "
                     "optional &mdash; unsorted output is unreadable.", "t-amber"),
                    ("&#128225;", "port-forward",
                     "A private tunnel from your laptop to one Pod or Service. Test a UI "
                     "with no Ingress and no NodePort.", "t-green"),
                    ("&#128190;", "cp",
                     "Copy files in or out of a container. Pull a log file, push a fixed "
                     "config to test a theory.", "t-gold"),
                ],
                cols=3,
            ),
            note(
                "n-tip",
                "Work in this order: <b>describe &rarr; logs &rarr; events &rarr; exec</b>. "
                "Three of the four are read-only and cost you nothing. Reaching for "
                "<code>exec</code> first is a habit that wastes time on a Pod that never "
                "started.",
            ),
        ),
        eyebrow="10 Debugging I",
        kicker="Six commands solve nearly every problem you will meet this week. Learn the "
               "<b>order</b> you reach for them, not just the flags.",
        notes="Tell them plainly: nobody debugs Kubernetes by reading YAML harder. These six "
              "are the whole toolkit for the first year. The ordering tip matters &mdash; "
              "beginners exec into everything, which is useless when the container never "
              "started, and describe would have told them in two seconds.",
        day=1,
    ),
    slide(
        "describe &mdash; and the Events tail",
        two(
            col(
                term(
                    "kubectl describe",
                    """kubectl describe pod vote -n vote

# jump straight to the part that matters
kubectl describe pod vote -n vote | sed -n '/Events/,$p'

# works on anything
kubectl describe node iti-worker
kubectl describe svc redis -n vote""",
                ),
                note(
                    "n-info",
                    "Events are <b>garbage-collected after about an hour</b>. An empty "
                    "Events section on an old Pod means &ldquo;nothing recently&rdquo;, not "
                    "&ldquo;nothing ever went wrong&rdquo;.",
                ),
            ),
            col(
                panel(
                    "What describe gives you that get -o yaml does not",
                    bul([
                        "<b>Events</b> &mdash; scheduling decisions, image pulls, probe "
                        "failures, OOM kills, in time order.",
                        "<b>Last State</b> with the <code>Exit Code</code> and reason of the "
                        "previous container.",
                        "<b>Conditions</b> &mdash; PodScheduled, Initialized, "
                        "ContainersReady, Ready.",
                        "Resolved values: which node, which IP, which image ID actually ran.",
                    ], "bul tight r"),
                    "blue",
                ),
                note(
                    "n-tip",
                    "The Events section is at the <b>bottom</b>. Scroll down &mdash; 90% of "
                    "&ldquo;why won&rsquo;t my Pod start&rdquo; answers itself in those four "
                    "lines, and students consistently read the top and give up.",
                ),
            ),
            ratio="1fr 1.05fr",
        ),
        eyebrow="First move",
        kicker="<code>describe</code> is the only one of the six that works when there is no "
               "container yet &mdash; which is precisely when you need it most.",
        notes="Run this live against a broken Pod rather than reading the slide. Make them "
              "physically scroll to the bottom; the habit of reading Events first is the "
              "single most valuable thing they take from today. Mention the one-hour GC so "
              "they do not misread an empty section as an all-clear.",
        day=1,
    ),
    slide(
        "logs and exec",
        two(
            col(
                term(
                    "kubectl logs",
                    """kubectl logs vote -n vote
kubectl logs vote -n vote -f            # follow, like tail -f
kubectl logs vote -n vote --tail=50
kubectl logs vote -n vote --since=10m

# THE crash-loop command: the run that already died
kubectl logs worker -n vote --previous

# multi-container Pod: pick one
kubectl logs mypod -c sidecar

# every Pod behind a label
kubectl logs -l app=vote -n vote --tail=20""",
                ),
            ),
            col(
                term(
                    "kubectl exec",
                    """kubectl exec vote -n vote -- env | sort
kubectl exec vote -n vote -- ls /app

# interactive shell
kubectl exec -it vote -n vote -- sh

# from inside: is redis actually reachable?
#   nslookup redis
#   nc -zv redis 6379""",
                ),
                note(
                    "n-warn",
                    "<code>--previous</code> is the flag people forget. On a crash-looping "
                    "Pod, plain <code>logs</code> shows the container that has not started "
                    "yet &mdash; usually nothing at all. <b>The evidence is always in the "
                    "previous run.</b>",
                ),
                note(
                    "n-info",
                    "Slim images have no shell, no <code>curl</code>, no "
                    "<code>nslookup</code>. When <code>exec</code> fails with "
                    "<code>executable file not found</code>, run a throwaway toolbox Pod "
                    "instead &mdash; <code>kubectl run tmp --rm -it "
                    "--image=nicolaka/netshoot -- bash</code>.",
                ),
            ),
            ratio="1.05fr 1fr",
        ),
        eyebrow="Looking inside",
        kicker="<code>logs</code> tells you what the app said. <code>exec</code> lets you "
               "stand where the app stands.",
        notes="Drill --previous once more; it is the difference between diagnosing a "
              "CrashLoopBackOff in thirty seconds and staring at an empty terminal for ten "
              "minutes. The netshoot tip saves the afternoon &mdash; our vote image is "
              "python:slim with no curl, and someone will try. Note logs -l works across a "
              "whole label set, which is how you tail a Deployment tomorrow.",
        day=1,
    ),
    slide(
        "events, port-forward and cp",
        two(
            col(
                term(
                    "the cluster activity feed",
                    """# unsorted output is useless - always sort
kubectl get events -n vote --sort-by=.lastTimestamp
kubectl get events -A --sort-by=.lastTimestamp | tail -20

# only the bad news
kubectl get events -n vote --field-selector type=Warning

# live feed
kubectl get events -n vote -w""",
                ),
                term(
                    "copy files in and out",
                    """kubectl cp vote:/app/app.py ./app.py -n vote     # out
kubectl cp ./fix.conf vote:/tmp/fix.conf -n vote  # in""",
                ),
            ),
            col(
                term(
                    "port-forward &mdash; a tunnel to one Pod",
                    """# localhost:8080 -> the Pod's :80
kubectl port-forward pod/vote 8080:80 -n vote

# works on a Service too
kubectl port-forward svc/redis 6379:6379 -n vote

# then, in another terminal / your browser
curl localhost:8080""",
                ),
                note(
                    "n-info",
                    "<code>port-forward</code> runs in the <b>foreground</b> and dies with "
                    "your terminal or the Pod. It is a debugging tool, not a way to expose "
                    "an app &mdash; that is what Services and Ingress are for.",
                ),
                note(
                    "n-tip",
                    "<code>get events</code> is namespaced. When a Pod will not schedule, "
                    "the useful event is often on the <b>node</b> or in "
                    "<code>kube-system</code> &mdash; reach for <code>-A</code>.",
                ),
            ),
            ratio="1fr 1.05fr",
        ),
        eyebrow="Reach and visibility",
        kicker="Events give you the cluster&rsquo;s side of the story. "
               "<code>port-forward</code> gets you to an app with no Ingress, no NodePort "
               "and no ceremony.",
        notes="port-forward is the fastest way to prove an app works before Services exist "
              "&mdash; they use it in the next lab. Stress that it is not a deployment "
              "strategy; someone always tries to demo an app to their manager over a "
              "port-forward. The --sort-by flag is not optional: show unsorted events once "
              "so they see how unreadable it is.",
        day=1,
    ),
    lab(
        "See the Voting App with port-forward",
        two(
            col(
                term(
                    "tunnel in",
                    """# make sure both Pods are back
kubectl apply -f day1-pods.yaml -n vote
kubectl get pods -n vote

# terminal 1 - keep this running
kubectl port-forward pod/vote 8080:80 -n vote""",
                ),
                term(
                    "terminal 2 &mdash; prove the vote landed",
                    """curl -s localhost:8080 | grep -i -E 'cats|dogs'

# vote from the browser: http://localhost:8080
# then count what redis received
kubectl exec redis -n vote -- redis-cli llen votes
kubectl exec redis -n vote -- redis-cli lrange votes 0 -1

kubectl logs vote -n vote -f      # watch requests arrive""",
                ),
            ),
            col(
                steps([
                    "Start the forward and leave it running. Closing that terminal closes "
                    "the tunnel.",
                    "Open <code>http://localhost:8080</code>. You should see the ballot "
                    "&mdash; <b>Cats vs Dogs</b>, the defaults from <code>app.py</code>.",
                    "Cast a vote, then ask redis directly: <code>llen votes</code> should go "
                    "up by one. That is the queue <code>worker</code> will drain tomorrow.",
                    "Tail the <code>vote</code> logs while you click. Gunicorn logs every "
                    "request &mdash; watch your own traffic arrive.",
                ]),
                note(
                    "n-why",
                    "There is no Service in front of <code>vote</code> and no Ingress. "
                    "<code>port-forward</code> is the <b>only</b> way to reach it today "
                    "&mdash; which is a good demonstration of why Services exist at all.",
                    title="Why we need the tunnel",
                ),
                note(
                    "n-tip",
                    "Cats and Dogs come from <code>OPTION_A</code> / <code>OPTION_B</code>, "
                    "which default in the code. Add them as <code>env</code> on the Pod and "
                    "the ballot changes &mdash; try <b>Tabs vs Spaces</b>.",
                ),
            ),
            ratio="1.05fr 1fr",
        ),
        eyebrow="Lab 8 &middot; Debugging",
        kicker="The first time you see the app you built, running in Kubernetes, in a "
               "browser. Then prove the vote really reached redis.",
        notes="This is the moment of the day &mdash; let them enjoy it, and make sure "
              "everybody gets the UI up before you move on. The redis-cli llen check is what "
              "turns 'the page loaded' into 'the system worked'. The env tip is a free "
              "preview of Day 3's ConfigMap lab; if you have time, have them do it now.",
        day=1,
    ),
    lab(
        "Planted failure #1 &mdash; diagnose it yourself",
        two(
            col(
                term(
                    "break it on purpose",
                    """kubectl run broken -n vote \\
  --image=iti/vote:v99 \\
  --image-pull-policy=IfNotPresent

kubectl get pod broken -n vote
# NAME     READY   STATUS             RESTARTS   AGE
# broken   0/1     ImagePullBackOff   0          45s""",
                ),
                term(
                    "your turn &mdash; diagnose before you read on",
                    """kubectl logs broken -n vote
kubectl describe pod broken -n vote | sed -n '/Events/,$p'
kubectl get events -n vote --sort-by=.lastTimestamp | tail -5

docker images | grep iti/vote
docker exec iti-control-plane crictl images | grep iti/vote""",
                ),
            ),
            col(
                steps([
                    "Run <code>logs</code> first. It returns <b>nothing useful</b> &mdash; "
                    "there is no container. Feel that dead end once.",
                    "Run <code>describe</code>. The Events tail names the image and the "
                    "exact failure: <code>Failed to pull image "
                    "&quot;iti/vote:v99&quot;</code>.",
                    "Confirm the diagnosis: <code>:v99</code> was never built and never "
                    "loaded. The tag does not exist anywhere.",
                    "Fix it: <code>kubectl delete pod broken -n vote</code> and re-run with "
                    "<code>:v1</code>. It starts immediately.",
                ]),
                note(
                    "n-warn",
                    "In the real world this is almost always a <b>typo in the tag</b> or an "
                    "image that was never pushed. Check the tag before you suspect anything "
                    "clever &mdash; registries, networks, secrets. It is the tag.",
                ),
                note(
                    "n-tip",
                    "Make this a habit: <b>symptom &rarr; describe &rarr; Events &rarr; "
                    "hypothesis &rarr; verify.</b> Day 4 is a whole gauntlet of these, timed.",
                ),
            ),
            ratio="1.05fr 1fr",
        ),
        eyebrow="Lab 9 &middot; Planted failure",
        kicker="A deliberately broken Pod. Do not read the answer &mdash; run the toolkit in "
               "order and let the cluster tell you.",
        notes="Give them five minutes with no help at all; the value is in the struggle, not "
              "the fix. Insist they run logs first and hit the dead end, because that is the "
              "lesson &mdash; no container means no logs, and describe is the only witness. "
              "Then have someone read their Events line aloud to the room.",
        day=1,
    ),
]

# ============================================================ wrap-up (×2)
DAY1END = [
    slide(
        "Day 1 &mdash; you are here",
        two(
            panel(
                "The Voting App today",
                '<div class="stackd" style="gap:14px">'
                + flow(
                    bx("Pod: vote", "iti/vote:v1 &middot; :80", "blue"),
                    arrow(),
                    bx("Service: redis", "ClusterIP", "slate"),
                    arrow(),
                    bx("Pod: redis", "redis:alpine", "maroon"),
                    gap=12,
                )
                + '<div class="lay" style="height:56px;--tone:#7089ad">'
                '<span class="lay-l">namespace: vote</span></div>'
                + flow(
                    bx("worker", "built, not deployed", "amber"),
                    bx("db", "not yet", "slate"),
                    bx("result", "built, not deployed", "slate"),
                    gap=12,
                )
                + "</div>"
                + '<p style="margin-top:16px;font-size:20px;color:var(--dim)">Three images '
                "built and loaded. Two Pods running. <b>Nothing is self-healing.</b></p>",
                "teal",
            ),
            col(
                bul([
                    "A cluster is a <b>control loop</b>: you declare <code>spec</code>, "
                    "controllers grind <code>status</code> towards it.",
                    "Every object is <b>apiVersion / kind / metadata / spec / status</b>.",
                    "<b>Namespaces</b> scope names, RBAC and quota &mdash; "
                    "<b>not network traffic</b>.",
                    "<b>Labels</b> are the wiring. Selectors are standing queries over them.",
                    "<b>Running &ne; working.</b> Read <code>READY</code>, then "
                    "<code>describe</code>, then the Events tail.",
                    "<b>CrashLoopBackOff</b> = the app dies on start. "
                    "<b>ImagePullBackOff</b> = the node never got the image.",
                    "A <b>bare Pod has no guardian</b>. Delete it and it is gone.",
                ], "bul tight r"),
                note(
                    "n-tip",
                    "<b>Tomorrow:</b> a Deployment restores that <code>redis</code> Pod in "
                    "two seconds, Services wire all five components together, and the "
                    "Voting App works end-to-end for the first time.",
                ),
            ),
            ratio="1.05fr 1fr",
        ),
        eyebrow="Recap",
        kicker="You built the images, you ran the app, and you broke it. <b>Everything "
               "missing from that diagram is Day 2, 3 and 4.</b>",
        notes="Point at the greyed-out boxes and name what each one is waiting for &mdash; "
              "worker and result need Deployments, db needs storage and a Secret. Close on "
              "the bare-Pod problem so the room leaves with an unresolved itch; tomorrow "
              "opens by scratching it. Remind them the footer says which day each slide came "
              "from when they review tonight.",
        day=1,
    ),
    slide(
        "Interview questions &mdash; Day 1",
        two(
            col(
                steps([
                    "<b>What is a Pod, and why is it the unit rather than the container?</b>"
                    "<br><span style=\"color:var(--faint)\">Shared network namespace and "
                    "volumes; smallest thing the scheduler places and the kubelet kills.</span>",
                    "<b>What are the five fields every Kubernetes object has?</b><br>"
                    '<span style="color:var(--faint)">apiVersion, kind, metadata, spec, '
                    "status &mdash; you write spec, controllers write status.</span>",
                    "<b>Are namespaces a security or network boundary?</b><br>"
                    '<span style="color:var(--faint)">No. They scope names, RBAC and quota. '
                    "Traffic crosses them freely until a NetworkPolicy says otherwise.</span>",
                    "<b>Difference between a label and an annotation?</b><br>"
                    '<span style="color:var(--faint)">Labels are indexed and selectable; '
                    "annotations are arbitrary metadata for tools and humans, never "
                    "selectable.</span>",
                ]),
            ),
            col(
                steps([
                    "<b>A Pod shows <code>Running</code> but the app is unreachable. Where "
                    "do you look?</b><br><span style=\"color:var(--faint)\">READY column "
                    "first, then describe &rarr; Events, then logs. Running only means "
                    "containers were started.</span>",
                    "<b>What does <code>CrashLoopBackOff</code> actually mean?</b><br>"
                    '<span style="color:var(--faint)">The container starts and exits '
                    "repeatedly; kubelet is backing off between restarts. Read "
                    "<code>logs --previous</code>.</span>",
                    "<b>How do <code>command</code> and <code>args</code> map to a "
                    "Dockerfile?</b><br><span style=\"color:var(--faint)\">command = "
                    "ENTRYPOINT, args = CMD. Setting command alone discards the image&rsquo;s "
                    "CMD.</span>",
                    "<b>Why does a locally built image fail to run on a kind cluster?</b><br>"
                    '<span style="color:var(--faint)">The node has its own image store: '
                    "<code>kind load docker-image</code>, plus "
                    "<code>imagePullPolicy: IfNotPresent</code>.</span>",
                ]),
            ),
            ratio="1fr 1fr",
            gap=30,
        ),
        eyebrow="Check yourself",
        kicker="Eight questions from today&rsquo;s material. If you can answer all eight out "
               "loud, Day 1 landed.",
        notes="Do not read the answers out &mdash; ask the questions cold and let the room "
              "work. Questions 3, 5 and 6 are the ones that separate people who understood "
              "from people who copied commands. Tell them these are real interview "
              "questions, not revision exercises, because that changes how hard they think.",
        day=1,
    ),
]

# ------------------------------------------------------------------ export
BLOCKS = {
    "roadmap4": ROADMAP4,
    "arch_extra": ARCH_EXTRA,
    "namespaces": NAMESPACES,
    "labels": LABELS,
    "podlife": PODLIFE,
    "envargs": ENVARGS,
    "vaimages": VAIMAGES,
    "vapods": VAPODS,
    "debug1": DEBUG1,
    "day1end": DAY1END,
}


def _check():
    """Guardrails the count-only smoke test cannot catch."""
    lab_blocks = {
        "namespaces": [3], "labels": [4], "vaimages": [0, 1, 2],
        "vapods": [0, 1], "debug1": [4, 5],
    }
    for name, secs in BLOCKS.items():
        for i, s in enumerate(secs):
            where = f"{name}[{i}]"
            assert s.startswith("<section") and s.endswith("</section>"), where
            assert 'data-day="1"' in s, f"{where}: missing day=1"
            assert 'data-notes="' in s and len(s.split('data-notes="')[1]) > 80, \
                f"{where}: empty instructor notes"
        for i in lab_blocks.get(name, []):
            assert 'class="slide labslide"' in secs[i], f"{name}[{i}] is not a lab"
            assert 'class="term' in secs[i], f"{name}[{i}]: lab with no commands"
    # the confusion points COURSE-REVIEW.md §9 requires stating out loud
    assert "n-warn" in NAMESPACES[0] and "NOT network isolation" in NAMESPACES[0]
    assert "n-warn" in LABELS[3]
    assert "n-warn" in PODLIFE[0] and "n-warn" in VAIMAGES[2]
    return {k: len(v) for k, v in BLOCKS.items()}


if __name__ == "__main__":
    counts = _check()
    print(counts, "total:", sum(counts.values()))
