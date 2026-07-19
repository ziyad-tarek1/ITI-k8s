#!/usr/bin/env python3
"""Day 4 content — scheduling, scaling, production & troubleshooting.

Every block is a list of finished <section> strings built with deck.py helpers.
Assembled by the deck builder; nothing here touches k8s-slides.html directly.
"""
from deck import cards, col, divider, lab, note, slide, steps, table, term, two

# --------------------------------------------------------- local composition
# Thin wrappers over CSS classes the existing deck already ships. No new CSS.


def bul(items, cls="bul tight"):
    return f'<ul class="{cls}">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def netcol(head, sub, boxes, para, tone):
    viz = '<div class="nl">&darr;</div>'.join(f'<div class="nb">{b}</div>' for b in boxes)
    return (
        f'<div class="net-col {tone} r"><div class="net-h">{head}</div>'
        f'<div class="net-s">{sub}</div><div class="net-viz">{viz}</div>'
        f"<p>{para}</p></div>"
    )


def nets(*cols_, n=3):
    style = f' style="grid-template-columns:repeat({n},1fr)"' if n != 3 else ""
    return f'<div class="nets"{style}>' + "".join(cols_) + "</div>"


def panel(title, body, tone="t-slate"):
    return (
        f'<div class="panel tone {tone} r"><div class="panel-t">'
        f'<span class="dot"></span>{title}</div>{body}</div>'
    )


def flow(items):
    """items: (label, sub, tone) rendered left-to-right with arrows."""
    parts = []
    for i, (lbl, sub, tone) in enumerate(items):
        if i:
            parts.append('<div class="fl-arrow">&rarr;</div>')
        parts.append(
            f'<div class="bx sm {tone} r" style="flex:1"><div class="bx-l">{lbl}</div>'
            f'<div class="bx-s">{sub}</div></div>'
        )
    return f'<div class="flowd">' + "".join(parts) + "</div>"


BLOCKS = {}

# ============================================================== 1. day4open
BLOCKS["day4open"] = [
    divider(
        "04",
        "Scheduling, Scaling &amp; Production",
        "Day 4. You can deploy an app. Today you make it survive a real cluster "
        "&mdash; and fix it when it does not.",
        [
            "Requests, limits &amp; QoS",
            "Scheduling: affinity, taints &amp; tolerations",
            "metrics-server, kubectl top &amp; the HPA",
            "Jobs &amp; CronJobs",
            "Ingress, CNI &amp; NetworkPolicy",
            "Helm, RBAC, DaemonSets &amp; quotas",
            "Troubleshooting &mdash; and the final challenge",
        ],
        notes=(
            "Set the frame for the day: everything so far made the app run, today makes it "
            "run in production. Two themes repeat &mdash; telling Kubernetes what your app "
            "needs (resources, scheduling) and telling it who may talk to whom (NetworkPolicy). "
            "The day ends with a timed troubleshooting gauntlet and a from-scratch rebuild, so "
            "warn them now that they will be graded on the last two hours."
        ),
        day=4,
    )
]

# ============================================================== 2. resources
BLOCKS["resources"] = [
    slide(
        "Requests schedule. Limits constrain.",
        two(
            term(
                "deployment.yaml &middot; every container",
                """resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 256Mi""",
                cls="sm",
            ),
            col(
                bul(
                    [
                        "<b>requests</b> &mdash; what the <b>scheduler</b> reserves. It is a "
                        "promise the node makes, subtracted from allocatable capacity whether "
                        "you use it or not.",
                        "<b>limits</b> &mdash; what the <b>kernel</b> enforces at runtime. "
                        "Nothing to do with placement; purely a ceiling.",
                        "No requests? The scheduler assumes zero and will happily cram your Pod "
                        "onto a node that has nothing left to give.",
                        "No limits? One runaway container can starve every neighbour on the node.",
                    ]
                ),
                note(
                    "n-warn",
                    "&ldquo;Requests schedule, limits constrain.&rdquo; If a Pod is "
                    "<code>Pending</code>, look at <b>requests</b>. If a Pod is being killed or "
                    "is slow, look at <b>limits</b>. They are never the same conversation.",
                    title="Say it out loud",
                ),
            ),
            ratio="1fr 1.15fr",
        ),
        eyebrow="Two numbers, two different jobs",
        kicker="The single most common cause of a broken production cluster is a container "
        "that declared neither.",
        notes=(
            "Hammer the one-liner &mdash; requests schedule, limits constrain &mdash; and make "
            "them repeat it. The mental model that fails is thinking requests is a minimum and "
            "limits is a maximum of the same thing; they are read by two different components at "
            "two different times. Point out that a node can be 100% requested and 5% actually "
            "busy, and that is working as designed."
        ),
        day=4,
    ),
    slide(
        "CPU is millicores. Memory is bytes.",
        table(
            ["Unit", "Means", "Example", "Watch out"],
            [
                [
                    "<code>1</code> / <code>1000m</code>",
                    "One full CPU core (one hyperthread)",
                    "<code>cpu: 1</code>",
                    "<code>1</code> and <code>1000m</code> are identical",
                ],
                [
                    "<code>500m</code>",
                    "Half a core &mdash; <b>m</b> is milli, a thousandth",
                    "<code>cpu: 500m</code>",
                    "<code>500m</code> is <b>not</b> 500 cores",
                ],
                [
                    "<code>100m</code>",
                    "A tenth of a core &mdash; a sane default for a small web app",
                    "<code>cpu: 100m</code>",
                    "Below <code>50m</code> and startup gets painful",
                ],
                [
                    "<code>Mi</code> / <code>Gi</code>",
                    "Power of two &mdash; 1 Mi = 1,048,576 bytes",
                    "<code>memory: 128Mi</code>",
                    "What you almost always want",
                ],
                [
                    "<code>M</code> / <code>G</code>",
                    "Power of ten &mdash; 1 M = 1,000,000 bytes",
                    "<code>memory: 128M</code>",
                    "<b>~5% smaller</b> than <code>128Mi</code>",
                ],
                [
                    "<i>(no suffix)</i>",
                    "Plain bytes",
                    "<code>memory: 134217728</code>",
                    "Legal, unreadable, never do this",
                ],
            ],
            note_after=note(
                "n-tip",
                "CPU is <b>compressible</b> &mdash; you can always give a container less of it "
                "and it just runs slower. Memory is <b>incompressible</b> &mdash; there is no "
                "&ldquo;a bit less RAM&rdquo;. That one property explains everything on the next "
                "slide.",
                style="margin-top:18px",
            ),
        ),
        eyebrow="Reading the numbers",
        kicker="Two units, two number systems, and one suffix that silently costs you 5%.",
        notes=(
            "The <code>m</code> suffix trips everyone once &mdash; someone will write "
            "<code>cpu: 500</code> meaning half a core and request 500 cores, and their Pod will "
            "sit Pending forever. Show them the Mi versus M distinction and tell them to just "
            "always use Mi and Gi. End on compressible versus incompressible, because that is the "
            "hinge for the next slide."
        ),
        day=4,
    ),
    slide(
        "At the limit: throttled or killed",
        nets(
            netcol(
                "CPU over limit",
                "compressible &middot; survivable",
                ["container wants 800m", "limit is 500m", "kernel THROTTLES it"],
                "The container keeps running, just slower. The CFS scheduler simply hands it "
                "fewer time slices. Symptom: <b>latency</b>, not a crash. Nothing in "
                "<code>kubectl get pods</code> changes &mdash; you have to look at metrics to "
                "even notice.",
                "t-blue",
            ),
            netcol(
                "Memory over limit",
                "incompressible &middot; fatal",
                ["container wants 300Mi", "limit is 256Mi", "kernel OOM-KILLS it"],
                "There is no such thing as running with less RAM. The kernel OOM killer "
                "terminates the process with <b>SIGKILL</b>. The container exits <b>137</b>, "
                "the Pod reports <b>OOMKilled</b>, and the kubelet restarts it &mdash; straight "
                "into <code>CrashLoopBackOff</code> if it happens again.",
                "t-maroon",
            ),
            netcol(
                "Node runs out",
                "pressure &middot; eviction",
                ["node memory low", "kubelet raises pressure", "Pods EVICTED by QoS"],
                "Different mechanism entirely. Nobody exceeded a limit &mdash; the <b>node</b> "
                "is short. The kubelet evicts whole Pods to reclaim, choosing victims by QoS "
                "class. Status shows <b>Evicted</b>, not OOMKilled.",
                "t-amber",
            ),
        ),
        eyebrow="What actually happens when you cross the line",
        kicker="Same idea, two completely different outcomes &mdash; and this is the exam "
        "question.",
        notes=(
            "This is the critical distinction of the whole block: CPU throttles, memory kills. "
            "Students consistently expect a CPU limit to kill the Pod and a memory limit to slow "
            "it down &mdash; it is exactly backwards. Make them say &ldquo;exit 137 means "
            "OOMKilled&rdquo; before you move on, because they will see it in the gauntlet lab "
            "this afternoon."
        ),
        day=4,
    ),
    slide(
        "QoS classes",
        two(
            steps(
                [
                    "Does <b>every</b> container set <b>both</b> requests and limits, with "
                    "<b>requests == limits</b> for CPU <i>and</i> memory? "
                    "&rarr; <b>Guaranteed</b>",
                    "Otherwise, does <b>at least one</b> container set a request or a limit for "
                    "anything? &rarr; <b>Burstable</b>",
                    "Nothing set anywhere in the Pod? &rarr; <b>BestEffort</b>",
                ]
            ),
            col(
                bul(
                    [
                        "You never <i>choose</i> a QoS class. Kubernetes derives it from what you "
                        "wrote, and stamps it on the Pod at admission time.",
                        "Read it back with "
                        "<code>kubectl get pod X -o jsonpath='{.status.qosClass}'</code>.",
                        "<b>Guaranteed</b> is the only class that gets exclusive CPU pinning on a "
                        "node with the static CPU manager &mdash; and the last to be evicted.",
                        "<b>BestEffort</b> is free real estate for the scheduler and the first "
                        "thing thrown overboard.",
                    ]
                ),
                note(
                    "n-warn",
                    "A Pod is only <b>Guaranteed</b> if <i>every</i> container qualifies. One "
                    "forgotten sidecar with no limits drops the entire Pod to "
                    "<b>Burstable</b> &mdash; and people spend hours wondering why.",
                ),
            ),
            ratio="1.05fr 1fr",
        ),
        eyebrow="A class you are assigned, not one you pick",
        kicker="Three classes, decided entirely by which of the four numbers you filled in.",
        notes=(
            "Walk the decision tree top to bottom with a real manifest on screen. The thing to "
            "stress is that QoS is derived, not declared &mdash; there is no <code>qos:</code> "
            "field, and students go looking for one. The all-containers rule is the gotcha; call "
            "it out and move on."
        ),
        day=4,
    ),
    slide(
        "Who gets thrown overboard first",
        two(
            table(
                ["Order", "Class", "Why it goes"],
                [
                    [
                        "<b>1st</b>",
                        "<b>BestEffort</b>",
                        "Asked for nothing, promised nothing. Zero cost to reclaim.",
                    ],
                    [
                        "<b>2nd</b>",
                        "<b>Burstable</b> <i>over</i> its request",
                        "Using more than it reserved. Ranked worst-offender first.",
                    ],
                    [
                        "<b>3rd</b>",
                        "<b>Burstable</b> <i>under</i> its request",
                        "Still inside its promise &mdash; only touched under real pressure.",
                    ],
                    [
                        "<b>last</b>",
                        "<b>Guaranteed</b>",
                        "Node made a hard promise. Evicted only to save the kubelet itself.",
                    ],
                ],
            ),
            col(
                bul(
                    [
                        "Eviction is a <b>node-level</b> decision under memory or disk pressure "
                        "&mdash; not a reaction to any one Pod misbehaving.",
                        "An evicted Pod is <b>deleted from that node</b>, then rescheduled by its "
                        "Deployment &mdash; a bare Pod is simply gone.",
                        "<code>kubectl get pod</code> shows <b>Evicted</b>; "
                        "<code>describe node</code> shows the pressure condition that caused it.",
                    ]
                ),
                note(
                    "n-tip",
                    "Practical rule for this course: give <b>everything</b> a request, give "
                    "<b>memory</b> a limit, and be careful with CPU limits &mdash; an aggressive "
                    "CPU limit throttles you into slowness that looks exactly like a bug.",
                ),
            ),
            ratio="1.1fr 1fr",
        ),
        eyebrow="Eviction order",
        kicker="When a node runs short, QoS class decides the casualty list.",
        notes=(
            "Frame this as the payoff for setting requests: the class you earn is the protection "
            "you get. The subtlety worth naming is that a Burstable Pod over its request is "
            "ranked before one under it &mdash; the node punishes the greedy, not the honest. "
            "Mention that Evicted Pod objects pile up and need cleaning; students will see dozens "
            "in a stressed cluster."
        ),
        day=4,
    ),
    lab(
        "Size the whole Voting App",
        two(
            term(
                "requests + limits",
                """# frontends: small, burstable
kubectl set resources deploy/vote deploy/result \\
  --requests=cpu=100m,memory=128Mi \\
  --limits=cpu=500m,memory=256Mi

# worker: no inbound traffic, steady burn
kubectl set resources deploy/worker \\
  --requests=cpu=100m,memory=256Mi \\
  --limits=cpu=500m,memory=512Mi

# redis: tiny
kubectl set resources deploy/redis \\
  --requests=cpu=50m,memory=64Mi \\
  --limits=cpu=200m,memory=256Mi

# db: the one that must never be evicted
kubectl set resources deploy/db \\
  --requests=cpu=250m,memory=512Mi \\
  --limits=cpu=250m,memory=512Mi""",
                cls="xs",
            ),
            term(
                "read it back",
                """# what class did each Pod earn?
kubectl get pod -o custom-columns=\\
NAME:.metadata.name,\\
QOS:.status.qosClass

# what has the node promised away?
kubectl describe node iti-worker \\
  | grep -A8 'Allocated resources'

# and the raw numbers on one Pod
kubectl get pod -l app=db \\
  -o jsonpath='{.items[0].spec.containers[0]\\
.resources}{"\\n"}'""",
                cls="xs",
            ),
            ratio="1.25fr 1fr",
            gap=28,
        )
        + note(
            "n-tip",
            "<b>db</b> deliberately has <code>requests == limits</code> &mdash; that makes it "
            "<b>Guaranteed</b> and the very last thing evicted. Everything else is "
            "<b>Burstable</b> on purpose. Check the <code>QOS</code> column and confirm you got "
            "what you expected.",
            style="margin-top:16px",
        ),
        eyebrow="Lab 24 &middot; Resources",
        kicker="<code>kubectl set resources</code> patches a live Deployment &mdash; no YAML "
        "editing, and every Pod rolls.",
        notes=(
            "Let them run it and then read the QoS column together; the db row saying Guaranteed "
            "is the moment the previous slide lands. The Allocated resources block on the node is "
            "worth a pause &mdash; show that percentages are of requests, not of actual usage, "
            "and that the node looks busy while doing almost nothing. Anyone whose Pods go "
            "Pending here has requested more than a kind node has; halve the numbers."
        ),
        day=4,
    ),
    lab(
        "Break it on purpose: OOMKilled",
        two(
            term(
                "1 &middot; a container that cannot fit",
                """cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: oomer
spec:
  restartPolicy: Never
  containers:
  - name: stress
    image: polinux/stress
    args: ["stress","--vm","1",
           "--vm-bytes","250M","--vm-hang","1"]
    resources:
      requests:
        memory: 32Mi
      limits:
        memory: 64Mi
EOF

kubectl get pod oomer -w""",
                cls="xs",
            ),
            col(
                term(
                    "2 &middot; read the verdict",
                    """kubectl get pod oomer \\
  -o jsonpath='{.status.containerStatuses[0]\\
.state.terminated.reason}{" exit "}\\
{.status.containerStatuses[0]\\
.state.terminated.exitCode}{"\\n"}'
# OOMKilled exit 137

kubectl describe pod oomer | grep -A5 'State'

kubectl delete pod oomer""",
                    cls="xs",
                ),
                note(
                    "n-warn",
                    "<b>137 = 128 + 9</b> &mdash; the process was <b>SIGKILL</b>ed. It got no "
                    "chance to flush, log, or shut down cleanly. If your app dies at 137 with no "
                    "error in its own logs, that is not a bug in your code &mdash; it is a memory "
                    "limit.",
                ),
            ),
            ratio="1fr 1.1fr",
            gap=28,
        ),
        eyebrow="Lab 25 &middot; Resources",
        kicker="A 64Mi limit and a container that wants 250Mi. Watch the kernel win.",
        notes=(
            "This is a deliberate failure &mdash; say so before they run it or half the room will "
            "think they broke the cluster. The key observation is that the app logs say nothing: "
            "SIGKILL leaves no trace inside the container, so the evidence lives only in the Pod "
            "status. Ask them what would happen with <code>restartPolicy: Always</code> and "
            "steer them to CrashLoopBackOff."
        ),
        day=4,
    ),
]

# ============================================================== 3. scheduling
BLOCKS["scheduling"] = [
    slide(
        "How a Pod finds a node",
        flow(
            [
                ("Pod created", "nodeName is empty", "t-slate"),
                ("FILTER", "which nodes <i>can</i> run it?", "t-blue"),
                ("SCORE", "which node is <i>best</i>?", "t-green"),
                ("BIND", "nodeName is written", "t-violet"),
            ]
        )
        + two(
            panel(
                "Filter &mdash; a hard yes or no",
                bul(
                    [
                        "Enough <b>allocatable</b> CPU and memory left for this Pod&rsquo;s "
                        "<b>requests</b>?",
                        "Does the node match the Pod&rsquo;s <code>nodeSelector</code> and "
                        "<b>required</b> node affinity?",
                        "Does the Pod <b>tolerate</b> every taint on the node?",
                        "Are the requested ports free? Can the node attach the PVC?",
                    ]
                ),
                "t-blue",
            ),
            panel(
                "Score &mdash; a ranking",
                bul(
                    [
                        "Spread Pods of the same Deployment across nodes.",
                        "Prefer nodes that already have the <b>image cached</b>.",
                        "Balance CPU and memory utilisation across the fleet.",
                        "Honour <b>preferred</b> affinity rules as soft points, not vetoes.",
                    ]
                ),
                "t-green",
            ),
            ratio="1fr 1fr",
            gap=28,
        ),
        eyebrow="The scheduler in two phases",
        kicker="Filter throws nodes out. Score ranks what is left. Highest score wins the bind.",
        notes=(
            "The mental model to install: filter is a veto, score is a preference. Zero nodes "
            "survive the filter and the Pod sits <code>Pending</code> forever with an Event "
            "explaining exactly which predicate failed &mdash; that Event is the answer to 90% of "
            "Pending questions. Point out the scheduler only ever writes one field, "
            "<code>nodeName</code>; the kubelet does everything after that."
        ),
        day=4,
    ),
    slide(
        "nodeSelector &mdash; the blunt instrument",
        two(
            term(
                "label the node, then demand it",
                """kubectl label node iti-worker disktype=ssd
kubectl get nodes -L disktype""",
                cls="sm",
            )
            + term(
                "pod spec",
                """spec:
  nodeSelector:
    disktype: ssd""",
                cls="sm",
            ),
            col(
                bul(
                    [
                        "Exact key/value match against <b>node labels</b>. Every label must "
                        "match &mdash; it is an AND, never an OR.",
                        "No match anywhere in the cluster &rarr; the Pod stays "
                        "<code>Pending</code> indefinitely. It does not fall back.",
                        "Nodes ship with useful labels already: "
                        "<code>kubernetes.io/hostname</code>, "
                        "<code>kubernetes.io/arch</code>, "
                        "<code>kubernetes.io/os</code>, "
                        "<code>node-role.kubernetes.io/control-plane</code>.",
                        "Three lines of YAML and no expressiveness at all &mdash; which is "
                        "exactly why node affinity exists.",
                    ]
                ),
                note(
                    "n-info",
                    "<code>nodeSelector</code> is not deprecated and never will be. For "
                    "&ldquo;this Pod belongs on that class of machine&rdquo; it is still the "
                    "right, readable answer.",
                ),
            ),
            ratio="1fr 1.2fr",
        ),
        eyebrow="Pinning, the simple way",
        kicker="One map of labels on the Pod, matched against the labels on the node. That is "
        "the whole feature.",
        notes=(
            "Do this live: label a node, watch a Pod land on it, remove the label, watch the "
            "next Pod go Pending. The trap is that removing a label does not move a running Pod "
            "&mdash; scheduling decisions are made once, at bind time, and never revisited. That "
            "surprises people, so state it explicitly."
        ),
        day=4,
    ),
    slide(
        "Node affinity &mdash; the expressive one",
        two(
            term(
                "required vs preferred",
                """affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: disktype
          operator: In
          values: ["ssd","nvme"]
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 80
      preference:
        matchExpressions:
        - key: topology.kubernetes.io/zone
          operator: In
          values: ["eu-west-1a"]""",
                cls="xs",
            ),
            col(
                bul(
                    [
                        "<b>required&hellip;</b> is a hard filter &mdash; same power as "
                        "<code>nodeSelector</code>, but with operators: <code>In</code>, "
                        "<code>NotIn</code>, <code>Exists</code>, <code>DoesNotExist</code>, "
                        "<code>Gt</code>, <code>Lt</code>.",
                        "<b>preferred&hellip;</b> is a scoring hint with a "
                        "<code>weight</code> of 1&ndash;100. If nothing matches, the Pod still "
                        "schedules &mdash; just somewhere less ideal.",
                        "That soft mode is the thing <code>nodeSelector</code> can never do, and "
                        "the reason affinity exists.",
                        "<code>IgnoredDuringExecution</code> means: once bound, the Pod stays "
                        "put even if the node stops matching.",
                    ]
                ),
                note(
                    "n-tip",
                    "The names are long but they parse: "
                    "<b>required</b>-during-<b>scheduling</b>, "
                    "<b>ignored</b>-during-<b>execution</b>. Kubernetes is telling you exactly "
                    "when the rule applies and when it stops caring.",
                ),
            ),
            ratio="1.15fr 1fr",
            gap=30,
        ),
        eyebrow="Soft rules, set operators",
        kicker="Everything <code class=\"i\">nodeSelector</code> does, plus &ldquo;prefer, but do "
        "not insist&rdquo;.",
        notes=(
            "Do not drown them in the YAML &mdash; read the two field names aloud and let the "
            "structure explain itself. The one point that must land is required versus preferred: "
            "required can strand a Pod in Pending, preferred never can. Mention podAffinity and "
            "podAntiAffinity exist for co-locating or separating Pods relative to each other, and "
            "leave it there."
        ),
        day=4,
    ),
    slide(
        "Taints &amp; tolerations",
        two(
            panel(
                "&#128274; Taint &mdash; on the <b>node</b>",
                '<div class="term xs r" style="margin-bottom:14px"><div class="term-bar">'
                '<div class="dots"><i></i><i></i><i></i></div>'
                '<span class="term-label">repel everything</span></div>'
                "<pre><code>kubectl taint node iti-worker2 \\\n"
                "  tier=data:NoSchedule</code></pre></div>"
                + bul(
                    [
                        "&ldquo;Keep out, unless you carry the key.&rdquo;",
                        "The node <b>repels</b> every Pod by default.",
                        "Remove one by re-running the command with a trailing "
                        "<code>-</code>.",
                    ]
                ),
                "t-maroon",
            ),
            panel(
                "&#128273; Toleration &mdash; on the <b>Pod</b>",
                '<div class="term xs r" style="margin-bottom:14px"><div class="term-bar">'
                '<div class="dots"><i></i><i></i><i></i></div>'
                '<span class="term-label">carry the key</span></div>'
                "<pre><code><span class=\"k\">tolerations</span>:\n"
                '- <span class="k">key</span>: tier\n'
                '  <span class="k">operator</span>: Equal\n'
                '  <span class="k">value</span>: data\n'
                '  <span class="k">effect</span>: NoSchedule</code></pre></div>'
                + bul(
                    [
                        "&ldquo;I am allowed past this particular lock.&rdquo;",
                        "A toleration <b>permits</b>, it never <b>attracts</b>.",
                        "<code>operator: Exists</code> tolerates any value of that key.",
                    ]
                ),
                "t-green",
            ),
            ratio="1fr 1fr",
            gap=30,
        )
        + note(
            "n-warn",
            "A toleration is a <b>lock and key</b>, not a magnet. Tolerating a taint does not "
            "send your Pod to that node &mdash; it only stops the node refusing it. If you want "
            "the Pod <i>on</i> that node, you still need <b>nodeSelector or affinity</b> as well. "
            "Taints repel, affinity attracts; real setups use both together.",
            style="margin-top:16px",
        ),
        eyebrow="The lock and the key",
        kicker="Taints are the only mechanism where the <b>node</b> gets a say in what runs on "
        "it.",
        notes=(
            "The lock-and-key metaphor is the whole slide &mdash; draw it if you have a "
            "whiteboard. The universal misconception is that a toleration attracts a Pod to the "
            "tainted node; it does not, it only grants permission. Show them their own control "
            "plane node: it carries a NoSchedule taint out of the box, which is precisely why "
            "their workloads never land there."
        ),
        day=4,
    ),
    slide(
        "The three taint effects",
        table(
            ["Effect", "New Pods", "Pods already running", "Typical use"],
            [
                [
                    "<code>NoSchedule</code>",
                    "<b>Refused</b> unless they tolerate it",
                    "Left alone",
                    "Reserve nodes for a workload class &mdash; the default choice",
                ],
                [
                    "<code>PreferNoSchedule</code>",
                    "Scheduler <b>tries</b> to avoid the node",
                    "Left alone",
                    "A soft hint. Rarely worth reaching for",
                ],
                [
                    "<code>NoExecute</code>",
                    "<b>Refused</b> unless they tolerate it",
                    "<b>Evicted</b> if they do not tolerate it",
                    "Drain a sick node; the built-in not-ready and unreachable taints",
                ],
            ],
            note_after=two(
                bul(
                    [
                        "<code>kubectl cordon</code> adds an <b>unschedulable</b> mark; "
                        "<code>kubectl drain</code> cordons <i>and</i> evicts &mdash; the pair "
                        "you use before patching a node.",
                        "The control plane node ships with "
                        "<code>node-role.kubernetes.io/control-plane:NoSchedule</code>. That is "
                        "why your Pods only land on workers.",
                        "Kubernetes taints nodes automatically on failure: "
                        "<code>node.kubernetes.io/not-ready</code> and "
                        "<code>&hellip;/unreachable</code>, both <code>NoExecute</code>.",
                    ]
                ),
                note(
                    "n-info",
                    "With <code>NoExecute</code> you can add "
                    "<code>tolerationSeconds: 300</code> &mdash; &ldquo;let me stay five more "
                    "minutes, then evict me&rdquo;. That is the default grace window Kubernetes "
                    "gives your Pods when a node goes unreachable.",
                ),
                ratio="1.3fr 1fr",
                gap=28,
            ),
        ),
        eyebrow="Choosing the right hammer",
        kicker="Two effects block scheduling. Only one of them evicts what is already there.",
        notes=(
            "The line to remember is that NoExecute is the only effect that touches running Pods. "
            "Connect it to something they have already seen: when a node goes down, Kubernetes "
            "does not have magic failover logic &mdash; it just taints the node NoExecute and the "
            "Pods get evicted. Cordon and drain are worth ten seconds each; they will use both in "
            "any real job."
        ),
        day=4,
    ),
    lab(
        "Pin the database, repel the rest",
        two(
            term(
                "1 &middot; label and pin db",
                """kubectl label node iti-worker disktype=ssd
kubectl get nodes -L disktype

kubectl patch deploy db -p \\
'{"spec":{"template":{"spec":{"nodeSelector":\\
{"disktype":"ssd"}}}}}'

kubectl rollout status deploy/db
kubectl get pod -l app=db -o wide""",
                cls="xs",
            ),
            term(
                "2 &middot; taint, then tolerate",
                """kubectl taint node iti-worker2 tier=data:NoSchedule

kubectl scale deploy/vote --replicas=6
kubectl get pod -l app=vote -o wide
# nothing lands on iti-worker2

kubectl patch deploy vote -p \\
'{"spec":{"template":{"spec":{"tolerations":\\
[{"key":"tier","operator":"Equal",\\
"value":"data","effect":"NoSchedule"}]}}}}'

kubectl get pod -l app=vote -o wide
# now some do

# clean up: note the trailing dash
kubectl taint node iti-worker2 tier=data:NoSchedule-
kubectl scale deploy/vote --replicas=2""",
                cls="xs",
            ),
            ratio="1fr 1.15fr",
            gap=28,
        )
        + note(
            "n-tip",
            "Between the two steps, run <code>kubectl describe pod</code> on anything that went "
            "<code>Pending</code> and read the Events line: it names the failing predicate and "
            "counts the nodes it rejected &mdash; <i>&ldquo;2 node(s) had untolerated taint&rdquo;</i>. "
            "That single line is how you debug scheduling for the rest of your career.",
            style="margin-top:16px",
        ),
        eyebrow="Lab 26 &middot; Scheduling",
        kicker="Label a node and pin <code class=\"i\">db</code> to it; taint a node and watch "
        "<code class=\"i\">vote</code> avoid it until you hand it the key.",
        notes=(
            "Make them run <code>-o wide</code> before and after each step &mdash; the NODE "
            "column is the entire point of this lab. The moment worth pausing on is after the "
            "taint and before the toleration: read the Pending Pod&rsquo;s Events together. "
            "Remind them about the trailing dash to remove a taint; everyone forgets it and then "
            "wonders why the cluster stays half-full."
        ),
        day=4,
    ),
]

# ============================================================= 4. metrics_hpa
BLOCKS["metrics_hpa"] = [
    slide(
        "metrics-server",
        two(
            col(
                flow(
                    [
                        ("kubelet", "cAdvisor, every node", "t-slate"),
                        ("metrics-server", "scrapes &amp; aggregates", "t-teal"),
                        ("metrics API", "kubectl top &middot; HPA", "t-blue"),
                    ]
                ),
                bul(
                    [
                        "A <b>single Deployment</b> in <code>kube-system</code> that scrapes "
                        "every kubelet every 15s and keeps the numbers <b>in memory</b>.",
                        "It serves one API: <code>metrics.k8s.io</code>. That is the API "
                        "<code>kubectl top</code> and the HPA read.",
                        "It is <b>not</b> monitoring. No history, no graphs, no alerts, nothing "
                        "on disk &mdash; restart it and every number is gone. Prometheus is what "
                        "you want for the other job.",
                        "It is <b>not installed by default</b> on kind, kubeadm or k3s-minus-"
                        "addons. No metrics-server means no <code>top</code> and a permanently "
                        "confused HPA.",
                    ]
                ),
            ),
            col(
                term(
                    "install &middot; kind needs one patch",
                    """kubectl apply -f https://github.com/\\
kubernetes-sigs/metrics-server/releases/\\
latest/download/components.yaml

kubectl patch deploy metrics-server \\
  -n kube-system --type=json -p='[{"op":"add",
  "path":"/spec/template/spec/containers/0/args/-",
  "value":"--kubelet-insecure-tls"}]'""",
                    cls="xs",
                ),
                note(
                    "n-warn",
                    "kind&rsquo;s kubelets serve their metrics endpoint with a "
                    "<b>self-signed certificate</b>. Without "
                    "<code>--kubelet-insecure-tls</code> the metrics-server Pod runs happily and "
                    "reports <b>nothing</b>: <code>kubectl top</code> says <i>metrics not "
                    "available</i> and the HPA sits at <code>&lt;unknown&gt;</code> forever. "
                    "Never use that flag on a real cluster &mdash; fix the certificates instead.",
                ),
            ),
            ratio="1.1fr 1fr",
            gap=30,
        ),
        eyebrow="Where numbers come from",
        kicker="Nothing in Kubernetes knows how busy your Pods are until you install this.",
        notes=(
            "The framing that matters: metrics-server is plumbing for autoscaling, not a "
            "monitoring stack. Students assume Kubernetes tracks CPU natively &mdash; it does "
            "not, and that is why <code>kubectl top</code> errors on a fresh cluster. The "
            "insecure-tls flag is a kind-specific wart; say why it exists so nobody carries it "
            "into production."
        ),
        day=4,
    ),
    slide(
        "kubectl top",
        two(
            term(
                "the two commands",
                """kubectl top nodes

# NAME           CPU    CPU%  MEMORY   MEM%
# iti-control    221m   11%   1244Mi   32%
# iti-worker      94m    4%    612Mi   15%

kubectl top pods
kubectl top pods -n kube-system
kubectl top pods --containers
kubectl top pods -l app=vote --sort-by=cpu""",
                cls="xs",
            ),
            col(
                bul(
                    [
                        "<code>top</code> shows <b>actual usage</b>. "
                        "<code>describe node</code> shows <b>requests</b>. They are different "
                        "numbers and they disagree constantly &mdash; that is normal.",
                        "A node at <b>100% requested</b> and <b>6% used</b> is a node that "
                        "refuses new Pods while looking idle. This is the conversation you will "
                        "have with every developer you ever work with.",
                        "The percentage column is against the node&rsquo;s <b>allocatable</b> "
                        "capacity, which is less than its physical capacity &mdash; the kubelet "
                        "and OS reserve a slice.",
                        "First run after installing usually errors. Wait ~60s for the first "
                        "scrape window.",
                    ]
                ),
                note(
                    "n-tip",
                    "Use <code>top</code> to <b>size your requests honestly</b>: run the app "
                    "under real load, read the number, then set the request just above it. "
                    "Guessing is how clusters end up 90% reserved and 10% busy.",
                ),
            ),
            ratio="1fr 1.15fr",
            gap=30,
        ),
        eyebrow="Actual usage, at last",
        kicker="Two commands. The gap between what they show and what "
        "<code class=\"i\">describe node</code> shows is the lesson.",
        notes=(
            "Run both commands side by side and put the requests-versus-usage gap on screen "
            "&mdash; it is the most useful thing in this block. Students conflate the two "
            "numbers all week; separating them here pays off in the gauntlet when a Pod is "
            "Pending on a node that <code>top</code> says is idle. Mention the 60-second warm-up "
            "so the first error does not derail the room."
        ),
        day=4,
    ),
    slide(
        "The HPA control loop",
        flow(
            [
                ("metrics-server", "current CPU per Pod", "t-teal"),
                ("HPA controller", "every 15 seconds", "t-blue"),
                ("compare", "current vs target %", "t-amber"),
                ("Deployment", "spec.replicas updated", "t-violet"),
                ("more Pods", "load per Pod drops", "t-green"),
            ]
        )
        + two(
            term(
                "hpa.yaml",
                """apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vote
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vote
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50""",
                cls="xs",
            ),
            col(
                bul(
                    [
                        "It is a <b>controller</b>, exactly like the ones from Day 2 &mdash; "
                        "observe, compare to desired, act. Nothing new, new inputs.",
                        "It edits <code>spec.replicas</code> on the Deployment. The Deployment "
                        "then does what it always does.",
                        "It is a loop, not an event: it re-evaluates every 15s whether anything "
                        "changed or not.",
                        "<code>autoscaling/v2</code> is the version you want &mdash; "
                        "<code>v1</code> only understands CPU.",
                    ]
                ),
                note(
                    "n-warn",
                    "Do <b>not</b> set <code>replicas:</code> in a Deployment that an HPA "
                    "manages. Every <code>kubectl apply</code> will reset the count and fight the "
                    "HPA. Delete the field and let the HPA own it.",
                ),
            ),
            ratio="1fr 1.05fr",
            gap=28,
        ),
        eyebrow="Autoscaling, mechanically",
        kicker="A controller that watches a number and writes <code class=\"i\">replicas</code>. "
        "That is genuinely all it is.",
        notes=(
            "Anchor this to the control loop from Day 1 &mdash; they already understand the "
            "shape, the HPA just has a different input. The replicas-in-git conflict is a real "
            "production trap and worth ten seconds: someone will apply a manifest with "
            "<code>replicas: 1</code> during a traffic spike. Insist on autoscaling/v2 so they "
            "are not learning a dead API."
        ),
        day=4,
    ),
    slide(
        "The algorithm, and why it is calm",
        two(
            col(
                panel(
                    "The formula",
                    '<div class="term sm r"><div class="term-bar"><div class="dots">'
                    "<i></i><i></i><i></i></div>"
                    '<span class="term-label">one line of maths</span></div><pre><code>'
                    "desired = ceil( current * ( currentMetric / targetMetric ) )"
                    "</code></pre></div>"
                    + bul(
                        [
                            "4 Pods at <b>80%</b>, target <b>50%</b> &rarr; "
                            "<code>ceil(4 &times; 1.6)</code> = <b>7 Pods</b>.",
                            "<code>currentMetric</code> is the <b>average across all ready "
                            "Pods</b>, expressed as a percentage <b>of the CPU request</b>.",
                            "Inside a <b>10% tolerance</b> of the target, it does nothing at all.",
                        ]
                    ),
                    "t-blue",
                ),
            ),
            col(
                bul(
                    [
                        "<b>Scale up is fast</b> &mdash; it may act on every 15s tick, and can "
                        "double the replica count in one go.",
                        "<b>Scale down is slow</b> &mdash; a <b>5-minute stabilisation "
                        "window</b> by default. It waits for the highest recommendation of the "
                        "last 5 minutes before shrinking.",
                        "That asymmetry is deliberate: over-provisioning costs money, "
                        "under-provisioning costs your users. Flapping costs both.",
                        "Tune it under <code>spec.behavior</code> "
                        "(<code>scaleUp</code> / <code>scaleDown</code> policies) if you must "
                        "&mdash; the defaults are good.",
                    ]
                ),
                note(
                    "n-warn",
                    "<b>An HPA without CPU <code>requests</code> does nothing &mdash; silently.</b> "
                    "Utilisation is a percentage <i>of the request</i>, so with no request there "
                    "is no denominator. The HPA reports "
                    "<code>TARGETS: &lt;unknown&gt;/50%</code>, never scales, and emits no error "
                    "you would notice. Requests are not optional here; they are the input.",
                    title="The #1 HPA failure",
                ),
            ),
            ratio="1fr 1.1fr",
            gap=30,
        ),
        eyebrow="Scaling behaviour",
        kicker="Up quickly, down slowly, and never on a metric it cannot compute.",
        notes=(
            "Work one number through the formula on the board &mdash; abstract, it never sticks. "
            "The up-fast/down-slow asymmetry answers the question they always ask: &ldquo;why is "
            "it still at 8 replicas, the load stopped ages ago?&rdquo; The requests warning is "
            "the single most important sentence in this block; it is confusion #15 from the "
            "review and it fails silently, which is the worst kind."
        ),
        day=4,
    ),
    lab(
        "Install metrics-server and read the numbers",
        two(
            term(
                "1 &middot; install and patch",
                """kubectl apply -f https://github.com/\\
kubernetes-sigs/metrics-server/releases/\\
latest/download/components.yaml

# kind: accept the kubelet's self-signed cert
kubectl patch deploy metrics-server \\
  -n kube-system --type=json -p='[{"op":"add",
  "path":"/spec/template/spec/containers/0/args/-",
  "value":"--kubelet-insecure-tls"}]'

kubectl rollout status deploy/metrics-server \\
  -n kube-system --timeout=120s""",
                cls="xs",
            ),
            col(
                term(
                    "2 &middot; use it",
                    """# wait ~60s for the first scrape
kubectl top nodes
kubectl top pods
kubectl top pods --containers

# usage vs reserved -- compare these two
kubectl top nodes
kubectl describe node iti-worker \\
  | grep -A8 'Allocated resources'""",
                    cls="xs",
                ),
                note(
                    "n-tip",
                    "If <code>top</code> says <i>metrics not available</i>, check the Pod is "
                    "Ready and that your patch actually landed: "
                    "<code>kubectl get deploy metrics-server -n kube-system -o "
                    "jsonpath='{.spec.template.spec.containers[0].args}'</code>.",
                ),
            ),
            ratio="1fr 1fr",
            gap=28,
        ),
        eyebrow="Lab 27 &middot; Metrics",
        kicker="Two commands to install, one flag to make it work on kind, then real numbers.",
        notes=(
            "Everyone must finish this lab &mdash; the HPA lab is dead without it. The single "
            "thing that goes wrong is the patch not applying, so have them verify the args list "
            "rather than trusting it. Use the waiting minute to compare top output against the "
            "node&rsquo;s allocated requests one more time."
        ),
        day=4,
    ),
    lab(
        "Autoscale vote under load",
        two(
            term(
                "1 &middot; create the HPA, then hammer it",
                """# vote already has a CPU request from Lab 24
kubectl get deploy vote -o jsonpath=\\
'{.spec.template.spec.containers[0].resources}{"\\n"}'

kubectl autoscale deploy/vote \\
  --cpu-percent=50 --min=2 --max=10

kubectl get hpa vote
# TARGETS should be 0%/50%, never <unknown>

# second terminal: generate load
kubectl run load --image=busybox:1.36 \\
  --restart=Never -- /bin/sh -c \\
  "while true; do wget -q -O- http://vote; done" """,
                cls="xs",
            ),
            col(
                term(
                    "2 &middot; watch it climb, then settle",
                    """kubectl get hpa vote -w
kubectl get pod -l app=vote -w
kubectl top pods -l app=vote

kubectl describe hpa vote | tail -20

# stop the load -- then be patient
kubectl delete pod load""",
                    cls="xs",
                ),
                note(
                    "n-warn",
                    "After you kill the load generator, replicas will <b>not</b> drop for about "
                    "<b>5 minutes</b>. That is the stabilisation window doing its job, not a "
                    "broken HPA. Do not let anyone &ldquo;fix&rdquo; it by deleting Pods.",
                ),
            ),
            ratio="1.15fr 1fr",
            gap=28,
        ),
        eyebrow="Lab 28 &middot; Scaling",
        kicker="One <code class=\"i\">autoscale</code> command, one busybox loop, and a replica "
        "count that moves on its own.",
        notes=(
            "Check the TARGETS column before generating any load &mdash; if it says unknown, stop "
            "and fix requests or metrics-server, because nothing after this will work. Put "
            "<code>get hpa -w</code> on the projector; watching the percentage rise and the "
            "replica count follow is the payoff of the whole block. Warn about the 5-minute "
            "cooldown before they start asking, and use the time to talk about "
            "<code>describe hpa</code> events."
        ),
        day=4,
    ),
]

# ==================================================================== 5. jobs
BLOCKS["jobs"] = [
    slide(
        "Job &mdash; run it once, then stop",
        two(
            term(
                "job.yaml",
                """apiVersion: batch/v1
kind: Job
metadata: {name: db-init}
spec:
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: psql
        image: postgres:14
        command: ["sh","-c"]
        args: ["psql -h db -U postgres -f /sql/schema.sql"]""",
                cls="xs",
            ),
            col(
                bul(
                    [
                        "A Job creates Pods and keeps creating them until the required number "
                        "<b>exit 0</b>. Then it stops &mdash; permanently.",
                        "The Pod is <b>not deleted</b> when it finishes. That is on purpose: its "
                        "logs are the record of the run. Clean up with "
                        "<code>ttlSecondsAfterFinished</code>.",
                        "<code>restartPolicy</code> must be <code>OnFailure</code> or "
                        "<code>Never</code>. <code>Always</code> is rejected &mdash; a Job that "
                        "always restarts would never complete.",
                        "Status you care about: <code>COMPLETIONS 1/1</code> and "
                        "<code>kubectl logs job/db-init</code>.",
                    ]
                ),
                note(
                    "n-info",
                    "Real uses: database migrations, schema seeding, a one-off batch import, a "
                    "backup, a data-fix script. Anything you would have run once over SSH now "
                    "belongs in a Job &mdash; declarative, logged, and repeatable.",
                ),
            ),
            ratio="1.05fr 1fr",
            gap=30,
        ),
        eyebrow="Workloads that end",
        kicker="Every controller so far kept Pods alive forever. This one wants them to finish.",
        notes=(
            "Frame it against everything they know: a Deployment treats exit 0 as a failure to "
            "correct, a Job treats it as the goal. The rejected <code>restartPolicy: Always</code> "
            "is a good five-second logic puzzle &mdash; ask them why before you tell them. Stress "
            "that finished Pods stick around deliberately; students think the cluster is leaking."
        ),
        day=4,
    ),
    slide(
        "completions, parallelism, backoffLimit",
        table(
            ["Field", "Default", "What it controls", "Example"],
            [
                [
                    "<code>completions</code>",
                    "<code>1</code>",
                    "How many Pods must succeed before the Job is done",
                    "<code>completions: 5</code> &mdash; five successful runs",
                ],
                [
                    "<code>parallelism</code>",
                    "<code>1</code>",
                    "How many Pods may run <b>at the same time</b>",
                    "<code>parallelism: 2</code> &mdash; five runs, two at a time",
                ],
                [
                    "<code>backoffLimit</code>",
                    "<code>6</code>",
                    "How many <b>failures</b> before the Job gives up entirely",
                    "Retries back off 10s, 20s, 40s&hellip; capped at 6 minutes",
                ],
                [
                    "<code>activeDeadlineSeconds</code>",
                    "<i>none</i>",
                    "Hard wall-clock timeout for the whole Job",
                    "Overrides <code>backoffLimit</code> &mdash; kills running Pods",
                ],
                [
                    "<code>ttlSecondsAfterFinished</code>",
                    "<i>none</i>",
                    "Auto-delete the Job (and its Pods) N seconds after it finishes",
                    "<code>ttlSecondsAfterFinished: 600</code>",
                ],
            ],
            note_after=note(
                "n-warn",
                "Your Job&rsquo;s container <b>must be idempotent</b>. Kubernetes guarantees "
                "<i>at least once</i>, never <i>exactly once</i> &mdash; a node can die "
                "mid-run and the Pod is recreated from scratch. Write "
                "<code>CREATE TABLE IF NOT EXISTS</code>, not <code>CREATE TABLE</code>.",
                style="margin-top:18px",
            ),
        ),
        eyebrow="Tuning a Job",
        kicker="Three numbers turn one script into a controlled batch run.",
        notes=(
            "The completions/parallelism pair is easiest with the worked example: five "
            "completions, parallelism two, so it runs two at a time until five have succeeded. "
            "backoffLimit is the one they will meet in anger &mdash; a Job that quietly stops "
            "retrying after six failures looks like nothing happened. The idempotency warning is "
            "the professional point of the slide; do not skip it."
        ),
        day=4,
    ),
    slide(
        "CronJob &mdash; a Job on a schedule",
        two(
            col(
                term(
                    "cronjob.yaml",
                    """apiVersion: batch/v1
kind: CronJob
metadata: {name: tally}
spec:
  schedule: "*/5 * * * *"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers: [...]""",
                    cls="xs",
                ),
                note(
                    "n-info",
                    "A CronJob creates a <b>Job</b>, which creates a <b>Pod</b>. Three objects "
                    "deep &mdash; when something fails, <code>describe</code> all three, starting "
                    "at the bottom.",
                ),
            ),
            col(
                term(
                    "the five fields",
                    """#  min  hour  dom  mon  dow
#   *    *    *    *    *
#   0-59 0-23 1-31 1-12 0-6 (Sun=0)

  "*/5 * * * *"    every 5 minutes
  "0 * * * *"      top of every hour
  "0 2 * * *"      02:00 daily
  "0 3 * * 0"      03:00 Sundays
  "30 1 1 * *"     01:30 on the 1st""",
                    cls="xs",
                ),
                bul(
                    [
                        "<code>concurrencyPolicy</code>: <code>Allow</code> (default), "
                        "<code>Forbid</code> (skip if the last run is still going), "
                        "<code>Replace</code> (kill it and start fresh).",
                        "The history limits are why old Jobs disappear &mdash; that is cleanup, "
                        "not data loss.",
                        "<code>suspend: true</code> pauses the schedule without deleting "
                        "anything.",
                    ]
                ),
            ),
            ratio="1fr 1.05fr",
            gap=28,
        ),
        eyebrow="Scheduled work",
        kicker="Standard cron syntax, in UTC, run by the control plane instead of a box you have "
        "to remember.",
        notes=(
            "Most of the room has written a crontab; the news is the five-field syntax is "
            "identical and the schedule now survives losing a node. Two things to call out: the "
            "schedule is evaluated in the <b>control plane&rsquo;s timezone, UTC by default</b>, "
            "which burns people every daylight-saving change, and <code>Forbid</code> is what you "
            "want for anything touching a database. Draw the CronJob &rarr; Job &rarr; Pod chain."
        ),
        day=4,
    ),
    slide(
        "Job or Deployment?",
        two(
            panel(
                "&#8635; Deployment",
                bul(
                    [
                        "The process should run <b>forever</b>.",
                        "Exit 0 is a <b>failure</b> &mdash; restart it.",
                        "<code>restartPolicy: Always</code>, and nothing else is legal.",
                        "Scale means <b>more concurrent capacity</b>.",
                        "Success = <code>READY 3/3</code> and staying that way.",
                        "<code>vote</code>, <code>result</code>, <code>worker</code>, "
                        "<code>redis</code>, <code>db</code>.",
                    ]
                ),
                "t-blue",
            ),
            panel(
                "&#10004; Job / CronJob",
                bul(
                    [
                        "The process should run <b>to completion</b>.",
                        "Exit 0 is <b>the goal</b> &mdash; stop.",
                        "<code>restartPolicy: OnFailure</code> or <code>Never</code>.",
                        "Scale means <b>more work items finished</b>.",
                        "Success = <code>COMPLETIONS 1/1</code>, then silence.",
                        "Migrations, backups, imports, nightly reports.",
                    ]
                ),
                "t-green",
            ),
            ratio="1fr 1fr",
            gap=30,
        )
        + note(
            "n-tip",
            "The test is one question: <b>should this process ever exit?</b> If yes, it is a Job. "
            "Running a migration as a Deployment is a classic beginner mistake &mdash; it "
            "succeeds, exits, gets restarted, succeeds again, and lands in "
            "<code>CrashLoopBackOff</code> while having worked perfectly every single time.",
            style="margin-top:18px",
        ),
        eyebrow="Picking the right controller",
        kicker="Same Pod spec, opposite definitions of success.",
        notes=(
            "This contrast is the whole reason Jobs exist and it is worth the slide. The "
            "CrashLoopBackOff-on-success story is the one they remember &mdash; a migration that "
            "worked six times and still shows as failing. Ask the room which controller a backup "
            "script needs before you reveal the answer."
        ),
        day=4,
    ),
    lab(
        "A DB-init Job and a tally CronJob",
        two(
            term(
                "1 &middot; initialise the schema, once",
                """cat <<'EOF' | kubectl apply -f -
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
          psql -h db -U postgres -c "CREATE TABLE IF NOT
          EXISTS votes (id VARCHAR(255) NOT NULL UNIQUE,
          vote VARCHAR(255) NOT NULL);"
EOF
kubectl logs job/db-init""",
                cls="xs",
            ),
            term(
                "2 &middot; snapshot the tally every 2 minutes",
                """cat <<'EOF' | kubectl apply -f -
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
            args: ["psql -h db -U postgres -t -c
              'SELECT vote, count(*) FROM votes
              GROUP BY vote;'"]
EOF

kubectl get cronjob tally
kubectl get jobs -w

kubectl logs "$(kubectl get pod \\
  -l batch.kubernetes.io/job-name \\
  --sort-by=.metadata.creationTimestamp \\
  -o name | tail -1)" """,
                cls="xs",
            ),
            ratio="1fr 1fr",
            gap=26,
        )
        ,
        eyebrow="Lab 29 &middot; Batch",
        kicker="One Job that must succeed once, one CronJob that reports forever.",
        notes=(
            "Have them cast votes between CronJob firings so the log output actually changes "
            "&mdash; a static count teaches nothing. Two minutes is a long silence in a "
            "classroom, so fill it by walking through <code>kubectl get jobs</code> and the "
            "history limits. If the Job fails, that is a fine outcome: read the logs together and "
            "let them find the Secret name typo. The Job waits on pg_isready first, the same "
            "trick as the Day-2 init container, which is why it is safe to re-run. db-secret is "
            "the Secret they created on "
            "Day 3, and have them cast votes between CronJob runs so the counts actually move."
        ),
        day=4,
    ),
]

# ================================================================= 6. ingress
BLOCKS["ingress"] = [
    slide(
        "The Ingress Controller is just a Pod",
        two(
            col(
                flow(
                    [
                        ("Internet", ":80 / :443", "t-slate"),
                        ("Controller Pod", "nginx, watching", "t-teal"),
                        ("Service", "ClusterIP", "t-blue"),
                        ("Pods", "your app", "t-green"),
                    ]
                ),
                bul(
                    [
                        "An <b>Ingress</b> object is <b>data, not behaviour</b>. On its own it "
                        "does absolutely nothing &mdash; it is a routing table nobody is reading.",
                        "An <b>Ingress Controller</b> is a normal Deployment running a real proxy "
                        "(nginx, Traefik, HAProxy, Envoy). It <b>watches the API for Ingress "
                        "objects</b> and rewrites its own config to match.",
                        "So the flow is: you write YAML &rarr; the controller notices &rarr; nginx "
                        "reloads &rarr; traffic routes. Same control-loop pattern as everything "
                        "else this week.",
                        "One controller, one external IP, <b>many</b> Services behind it &mdash; "
                        "instead of a cloud load balancer per Service.",
                    ]
                ),
            ),
            col(
                note(
                    "n-warn",
                    "<b>No controller installed means your Ingress silently does nothing.</b> "
                    "<code>kubectl get ingress</code> shows the object, the ADDRESS column stays "
                    "empty forever, and no error is ever printed. This is the number one Ingress "
                    "support question and the answer is always the same: is a controller running?",
                ),
                note(
                    "n-info",
                    "A Service of <code>type: LoadBalancer</code> gives <b>one Service</b> an "
                    "external IP at <b>L4</b> &mdash; it cannot see URLs. Ingress works at "
                    "<b>L7</b>: it reads the <code>Host</code> header and the path, so one IP can "
                    "serve your whole app. In practice the controller <i>itself</i> sits behind a "
                    "single LoadBalancer Service.",
                ),
                note(
                    "n-tip",
                    "k3s ships <b>Traefik</b> already installed. kind ships nothing &mdash; which "
                    "is why the next lab installs ingress-nginx by hand.",
                ),
            ),
            ratio="1.15fr 1fr",
            gap=30,
        ),
        eyebrow="Recap, then the missing half",
        kicker="You met Ingress on Day 1. Here is the part that makes it actually route traffic.",
        notes=(
            "The single idea to land: the Ingress object is inert, the controller is the thing "
            "that works. Students write a perfect Ingress, get nothing, and conclude Kubernetes "
            "is broken &mdash; pre-empt that here. The L4-versus-L7 contrast is also the honest "
            "answer to &ldquo;why not just use LoadBalancer for everything&rdquo;."
        ),
        day=4,
    ),
    slide(
        "Host rules, path rules and TLS",
        two(
            term(
                "one Ingress, both styles",
                """spec:
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
            port:
              number: 80
      - path: /result
        pathType: Prefix
        backend:
          service:
            name: result
            port:
              number: 80
  tls:
  - hosts: ["vote.localtest.me"]
    secretName: vote-tls""",
                cls="xs",
            ),
            col(
                bul(
                    [
                        "<b>Host-based</b> &mdash; routes on the <code>Host</code> header. "
                        "<code>vote.example.com</code> and <code>result.example.com</code> hitting "
                        "one IP. Needs real DNS in production.",
                        "<b>Path-based</b> &mdash; routes on the URL path. <code>/</code> to "
                        "<code>vote</code>, <code>/result</code> to <code>result</code>. No DNS "
                        "changes needed at all.",
                        "<code>pathType</code>: <code>Prefix</code> is what you want. "
                        "<code>Exact</code> matches the whole path, <code>ImplementationSpecific</code> "
                        "hands the decision to the controller.",
                        "Longest matching path wins &mdash; <code>/result</code> beats "
                        "<code>/</code>, so ordering in the file does not matter.",
                    ]
                ),
                note(
                    "n-info",
                    "<b>TLS termination</b> &mdash; awareness only. Put a Secret of type "
                    "<code>kubernetes.io/tls</code> (a cert and a key) in the "
                    "<code>tls:</code> block and the controller serves HTTPS on :443 and talks "
                    "plain HTTP to your Pods. In the real world <b>cert-manager</b> issues and "
                    "renews those certificates from Let&rsquo;s Encrypt automatically. Worth "
                    "knowing the words; out of scope today.",
                    title="TLS",
                ),
            ),
            ratio="1fr 1.15fr",
            gap=30,
        ),
        eyebrow="Writing the rules",
        kicker="Two ways to split traffic, and the block that turns on HTTPS.",
        notes=(
            "Path-based routing is what the next lab uses, because it needs no DNS &mdash; make "
            "that connection explicit. <code>pathType</code> is genuinely required and omitting it "
            "is a common validation error, so point at it. Keep TLS to sixty seconds: name "
            "cert-manager, say it is the standard answer, and move on."
        ),
        day=4,
    ),
    slide(
        "IngressClass, and what usually goes wrong",
        two(
            col(
                panel(
                    "IngressClass &mdash; which controller owns this rule?",
                    bul(
                        [
                            "A cluster can run <b>several</b> controllers: nginx for public "
                            "traffic, another for internal.",
                            "<code>spec.ingressClassName: nginx</code> says which one should pick "
                            "your Ingress up.",
                            "Omit it and only a controller marked as <b>default</b> will act "
                            "&mdash; if none is, nothing happens.",
                            "The old <code>kubernetes.io/ingress.class</code> annotation is "
                            "deprecated. Use the field.",
                        ]
                    ),
                    "t-violet",
                )
                + term(
                    "check",
                    """kubectl get ingressclass
kubectl get ingress
kubectl describe ingress vote""",
                    cls="xs",
                ),
            ),
            col(
                table(
                    ["Symptom", "Real cause"],
                    [
                        [
                            "ADDRESS column stays empty",
                            "No controller running, or wrong "
                            "<code>ingressClassName</code>",
                        ],
                        [
                            "<code>404</code> from nginx itself",
                            "No rule matched &mdash; wrong <code>Host</code> header or path",
                        ],
                        [
                            "<code>503</code> from nginx",
                            "Rule matched, but the backing Service has <b>no ready "
                            "endpoints</b>",
                        ],
                        [
                            "Works by IP, fails by name",
                            "DNS. The <code>Host</code> header is how host rules match",
                        ],
                        [
                            "Service not found",
                            "Ingress can only reference a Service in its <b>own "
                            "namespace</b>",
                        ],
                    ],
                ),
                note(
                    "n-warn",
                    "<code>503</code> is not an Ingress problem. It means routing worked "
                    "perfectly and the Service behind it has nothing Ready to send traffic to "
                    "&mdash; check <code>kubectl get endpoints</code> and your readiness probes "
                    "first.",
                ),
            ),
            ratio="1fr 1.15fr",
            gap=30,
        ),
        eyebrow="After the lab",
        kicker="Five failures that account for nearly every broken Ingress you will meet.",
        notes=(
            "Run this straight after the lab while the object is still on their screens. The "
            "404-versus-503 distinction is the most useful thing here: 404 means your rule is "
            "wrong, 503 means your rule is right and your app is not ready. The "
            "same-namespace restriction catches people who split frontend and backend across "
            "namespaces."
        ),
        day=4,
    ),
]

# ================================================================== 7. netpol
BLOCKS["netpol"] = [
    slide(
        "What a CNI plugin actually does",
        two(
            col(
                steps(
                    [
                        "The kubelet is told to start a Pod. It creates the Pod&rsquo;s "
                        "<b>network namespace</b> &mdash; empty, no interfaces, no address.",
                        "It calls the <b>CNI plugin</b> on that node, handing it the namespace "
                        "and the Pod&rsquo;s identity.",
                        "The plugin <b>allocates an IP</b> from the node&rsquo;s slice of the "
                        "pod CIDR, creates a veth pair, and plugs one end into the Pod.",
                        "The plugin <b>programs routes</b> so that IP is reachable from every "
                        "other node &mdash; via overlay tunnelling or plain routing.",
                    ]
                ),
                note(
                    "n-info",
                    "Kubernetes itself contains <b>no networking implementation</b>. It defines "
                    "a contract and delegates. That is why a fresh cluster with no CNI has all "
                    "its nodes stuck <code>NotReady</code> &mdash; nothing has claimed the job.",
                ),
            ),
            col(
                panel(
                    "The three rules of the Kubernetes network model",
                    bul(
                        [
                            "<b>Every Pod gets its own routable IP.</b> Not a port on the host "
                            "&mdash; a real address of its own.",
                            "<b>Every Pod can reach every other Pod directly</b>, on any node, "
                            "<b>without NAT</b>. The source IP the receiver sees is the "
                            "sender&rsquo;s actual Pod IP.",
                            "<b>Agents on a node</b> (kubelet, system daemons) can reach all Pods "
                            "on that node.",
                        ]
                    ),
                    "t-teal",
                ),
                note(
                    "n-tip",
                    "This is why Kubernetes networking feels simpler than Docker&rsquo;s. No "
                    "port mapping, no <code>-p 8080:80</code>, no port collisions &mdash; two "
                    "Pods can both listen on :80 because they own different IPs. The flat model "
                    "is the whole trick.",
                ),
                note(
                    "n-info",
                    "Common plugins: <b>Calico</b> (policy-first, BGP or VXLAN), <b>Flannel</b> "
                    "(simple overlay, <b>no policy</b>), <b>Cilium</b> (eBPF), <b>kindnet</b> "
                    "(kind&rsquo;s tiny default, <b>no policy</b>), <b>AWS VPC CNI</b> (real VPC "
                    "IPs).",
                ),
            ),
            ratio="1fr 1.05fr",
            gap=30,
        ),
        eyebrow="The layer nobody explains",
        kicker="Kubernetes does not do networking. It writes the spec and hires a plugin.",
        notes=(
            "Start with the fact that surprises everyone: Kubernetes ships zero networking code. "
            "The flat, no-NAT model is worth dwelling on because every Docker habit they have "
            "&mdash; port mapping, published ports &mdash; is unnecessary here. Flag now that two "
            "of the plugins on that list do not implement NetworkPolicy at all; it becomes the "
            "point of the lab in twenty minutes."
        ),
        day=4,
    ),
    slide(
        "Pod to Pod, step by step",
        two(
            term(
                "vote Pod wants to reach a redis Pod",
                """# 1. vote resolves the name
nslookup redis
#    -> CoreDNS answers with the SERVICE IP
#    -> 10.96.71.4  (a virtual IP; nothing owns it)

# 2. vote opens a TCP connection to 10.96.71.4:6379

# 3. leaving the Pod, the packet hits the node's
#    iptables rules programmed by kube-proxy
#    DNAT: 10.96.71.4:6379 -> 192.168.14.7:6379

# 4. that Pod IP is routed by the CNI --
#    same node: local veth
#    other node: overlay tunnel or a route

# 5. redis sees a connection FROM vote's Pod IP.
#    No NAT. The source IP is real and usable.""",
                cls="xs",
            ),
            col(
                bul(
                    [
                        "The <b>Service IP is fiction</b> &mdash; no interface anywhere holds it. "
                        "It only exists as a rewrite rule in every node&rsquo;s kernel.",
                        "You cannot <code>ping</code> a Service IP. It answers on its declared "
                        "ports and nothing else. Half the room will try.",
                        "<b>DNS gives you a Service IP. kube-proxy turns it into a Pod IP. The "
                        "CNI delivers the packet.</b> Three components, one hop.",
                        "Because there is no NAT, the receiver&rsquo;s view of &ldquo;who called "
                        "me&rdquo; is a real Pod IP &mdash; which is exactly what NetworkPolicy "
                        "needs in order to work.",
                    ]
                ),
                table(
                    ["IP kind", "Who owns it", "Lifetime"],
                    [
                        [
                            "<b>Pod IP</b>",
                            "One Pod, assigned by the CNI",
                            "Dies with the Pod. Never reuse it in config",
                        ],
                        [
                            "<b>Service IP</b>",
                            "Nobody &mdash; a virtual IP in iptables",
                            "Stable for the life of the Service",
                        ],
                        [
                            "<b>Node IP</b>",
                            "The machine itself",
                            "Stable. What NodePort listens on",
                        ],
                    ],
                ),
            ),
            ratio="1.1fr 1fr",
            gap=30,
        ),
        eyebrow="One connection, end to end",
        kicker="Follow a single packet from <code class=\"i\">vote</code> to "
        "<code class=\"i\">redis</code> and every networking object falls into place.",
        notes=(
            "Walk the five steps slowly &mdash; this is the slide that ties DNS, Services, "
            "kube-proxy and the CNI into one story. The three-IP table is confusion #8 from the "
            "review; make them say which one they would put in a config file (none of them "
            "&mdash; use a name). Someone always tries to ping a Service IP, so pre-empt it."
        ),
        day=4,
    ),
    slide(
        "kube-proxy: how a Service IP becomes a Pod IP",
        two(
            col(
                flow(
                    [
                        ("Service", "+ its Endpoints", "t-blue"),
                        ("kube-proxy", "on every node", "t-teal"),
                        ("iptables / IPVS", "kernel rules", "t-violet"),
                    ]
                ),
                bul(
                    [
                        "kube-proxy is a <b>DaemonSet</b> &mdash; one Pod per node. It watches "
                        "Services and <b>EndpointSlices</b> through the API server.",
                        "It never touches a packet. It only <b>writes kernel rules</b>; the "
                        "kernel does all the forwarding at full speed.",
                        "<b>iptables mode</b> (default): a chain per Service, with random "
                        "probability rules spreading connections across the ready Pod IPs.",
                        "<b>IPVS mode</b>: a purpose-built kernel load balancer. Scales far "
                        "better past a few thousand Services and offers real algorithms "
                        "(round-robin, least-conn).",
                    ]
                ),
            ),
            col(
                term(
                    "look at the actual rules",
                    """kubectl get endpointslices -l \\
  kubernetes.io/service-name=redis

# the rules kube-proxy wrote, on a node
docker exec iti-worker \\
  iptables -t nat -L KUBE-SERVICES -n | head""",
                    cls="xs",
                ),
                note(
                    "n-info",
                    "Load balancing is <b>per connection</b>, not per request. A client that "
                    "holds one keep-alive TCP connection open will talk to exactly <b>one</b> "
                    "Pod forever &mdash; which is why gRPC and connection-pooling clients look "
                    "unbalanced behind a Service. That is not a bug; it is L4.",
                ),
                note(
                    "n-warn",
                    "Only <b>Ready</b> Pods appear in EndpointSlices. A Service with an empty "
                    "endpoints list is either a selector that matches nothing or a readiness "
                    "probe that never passes &mdash; and both look identical from the outside.",
                ),
            ),
            ratio="1fr 1.05fr",
            gap=30,
        ),
        eyebrow="The load balancer that is not a process",
        kicker="kube-proxy writes rules. The Linux kernel is the load balancer.",
        notes=(
            "The counter-intuitive point is that kube-proxy is not in the data path at all "
            "&mdash; kill it and existing traffic keeps flowing, only new Services stop being "
            "programmed. Keep iptables versus IPVS at the level of &ldquo;same job, IPVS scales "
            "better&rdquo;. The per-connection balancing note answers a question that will come "
            "up the first time someone load-tests a Service."
        ),
        day=4,
    ),
    slide(
        "NetworkPolicy: default allow, until it is not",
        two(
            panel(
                "&#128275; By default: everything talks to everything",
                bul(
                    [
                        "A brand-new cluster is <b>completely flat</b>. Any Pod can open a "
                        "connection to any other Pod, in <b>any namespace</b>, on any port.",
                        "Nothing is filtered. Nothing is logged. There is no implicit boundary "
                        "anywhere.",
                        "Your <code>vote</code> frontend can talk straight to "
                        "<code>db</code> on 5432. So can a compromised sidecar. So can anything "
                        "an attacker manages to run.",
                    ]
                ),
                "t-maroon",
            ),
            panel(
                "&#128274; A policy flips <b>one</b> Pod to deny-by-default",
                bul(
                    [
                        "A NetworkPolicy selects Pods with a <code>podSelector</code>. Only "
                        "<b>those</b> Pods are affected.",
                        "The moment a Pod is selected by <b>any</b> policy, it switches to "
                        "<b>deny by default</b> for the directions that policy names.",
                        "From then on, only traffic explicitly allowed by <b>some</b> policy gets "
                        "through. Multiple policies are <b>additive</b> &mdash; they union, they "
                        "never subtract.",
                        "There is no <code>deny</code> rule in the API. You deny by <b>not "
                        "allowing</b>.",
                    ]
                ),
                "t-green",
            ),
            ratio="1fr 1fr",
            gap=30,
        )
        + note(
            "n-warn",
            "<b>Namespaces are not network isolation.</b> A Pod in <code>dev</code> can reach a "
            "Pod in <code>prod</code> by its FQDN with nothing stopping it. Namespaces separate "
            "<i>names</i>, RBAC and quotas &mdash; never packets. NetworkPolicy is the only "
            "thing in Kubernetes that separates packets.",
            style="margin-top:18px",
        ),
        eyebrow="The default nobody expects",
        kicker="An empty cluster is an open network. Policies do not filter &mdash; they "
        "<b>opt Pods into</b> filtering.",
        notes=(
            "The mental flip to install: a policy is not a firewall rule you add to an existing "
            "firewall, it is the act of switching a Pod from allow-all to deny-all and then "
            "punching holes. That is why an empty policy denies everything. Namespaces-are-not-"
            "isolation is confusion #7 and students genuinely believe the opposite &mdash; they "
            "will prove it themselves in the lab."
        ),
        day=4,
    ),
    slide(
        "The default-deny pattern",
        two(
            term(
                "deny all ingress in this namespace",
                """apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress""",
                cls="sm",
            )
            + note(
                "n-tip",
                "<code>podSelector: {}</code> means <b>every Pod in this namespace</b>. No "
                "<code>ingress:</code> block means <b>no traffic is allowed in</b>. Nine lines, "
                "and the namespace is sealed.",
                style="margin-top:14px",
            ),
            col(
                steps(
                    [
                        "<b>Deny first.</b> Apply default-deny to the namespace. Everything "
                        "breaks &mdash; on purpose, and while you are watching.",
                        "<b>Allow deliberately.</b> Add one policy per legitimate path, each "
                        "naming its source and its port.",
                        "<b>Verify.</b> Confirm the app works <i>and</i> that a probe Pod is "
                        "still refused.",
                    ]
                ),
                bul(
                    [
                        "This is <b>allow-listing</b>: the security model that fails closed. "
                        "Adding rules one by one to an open network fails open, and you will "
                        "never know which hole you missed.",
                        "Scoped to a <b>namespace</b>, because that is what "
                        "<code>podSelector: {}</code> covers. There is no cluster-wide "
                        "NetworkPolicy in core Kubernetes.",
                        "Add <code>- Egress</code> to <code>policyTypes</code> to seal outbound "
                        "too &mdash; then remember to allow <b>DNS to CoreDNS on UDP 53</b> or "
                        "nothing will resolve.",
                    ]
                ),
            ),
            ratio="1fr 1.15fr",
            gap=30,
        ),
        eyebrow="Start closed, open deliberately",
        kicker="Nine lines of YAML that turn a namespace from open to allow-list.",
        notes=(
            "Deny-then-allow is the professional habit; adding allow rules to an open network is "
            "how you end up with a policy set nobody can reason about. The DNS trap is the "
            "classic egress mistake &mdash; someone seals egress, every name lookup fails, and "
            "the app looks like it lost its database. Warn them before they try it at home."
        ),
        day=4,
    ),
    slide(
        "Ingress, egress and the three selectors",
        two(
            term(
                "the shape of a rule",
                """spec:
  podSelector:
    matchLabels:
      app: db
  policyTypes: [Ingress, Egress]
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: worker
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: batch
    - ipBlock:
        cidr: 10.0.0.0/8
        except: [10.0.5.0/24]
    ports:
    - protocol: TCP
      port: 5432
  egress:
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - {protocol: UDP, port: 53}""",
                cls="xs",
            ),
            col(
                bul(
                    [
                        "<b>ingress</b> = who may connect <b>to</b> the selected Pods. "
                        "<b>egress</b> = where the selected Pods may connect <b>out</b> to. "
                        "Direction is always from the selected Pod&rsquo;s point of view.",
                        "<b>podSelector</b> &mdash; Pods by label, <b>in the same namespace</b> "
                        "as the policy.",
                        "<b>namespaceSelector</b> &mdash; every Pod in namespaces matching those "
                        "labels. Every namespace carries "
                        "<code>kubernetes.io/metadata.name</code> automatically.",
                        "<b>ipBlock</b> &mdash; a raw CIDR, for things outside the cluster. Has "
                        "an <code>except:</code> list.",
                    ]
                ),
                note(
                    "n-warn",
                    "Watch the YAML dashes. Separate list items are <b>OR</b>: "
                    "<code>- podSelector</code> then <code>- namespaceSelector</code> means "
                    "either. Two keys under <b>one</b> dash are <b>AND</b>: "
                    "<code>- namespaceSelector&hellip;</code> plus "
                    "<code>podSelector&hellip;</code> means that Pod in that namespace. One "
                    "character of indentation changes the meaning completely.",
                    title="OR vs AND",
                ),
            ),
            ratio="1fr 1.1fr",
            gap=30,
        ),
        eyebrow="Writing real rules",
        kicker="Two directions, three ways to name a peer, and one indentation trap.",
        notes=(
            "Direction is always relative to the selected Pod &mdash; say it twice, because "
            "people write egress rules that describe inbound traffic. The OR-versus-AND dash "
            "trap is subtle, genuinely dangerous, and it is where policy reviews find real bugs: "
            "an accidental OR opens a namespace you never meant to trust. Point at the egress "
            "DNS rule as the one you will copy into every project."
        ),
        day=4,
    ),
    lab(
        "Rebuild the cluster with a CNI that enforces",
        two(
            term(
                "1 &middot; kind without kindnet, plus Calico",
                """kind delete cluster --name iti

cat <<'EOF' > kind-day4.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
  podSubnet: "192.168.0.0/16"
nodes:
- role: control-plane
  extraPortMappings:
  - {containerPort: 80, hostPort: 80}
  - {containerPort: 30080, hostPort: 30080}
- role: worker
- role: worker
EOF

kind create cluster --name iti --config kind-day4.yaml

# EXPECTED: every node NotReady, no CNI yet
kubectl get nodes

kubectl apply -f https://raw.githubusercontent.com/\\
projectcalico/calico/v3.28.0/manifests/calico.yaml

kubectl wait --for=condition=ready pod \\
  -l k8s-app=calico-node -n kube-system --timeout=300s

# now Ready, and Pods get IPs from 192.168.0.0/16
kubectl get nodes
kubectl get pod -A -o wide | head""",
                cls="xs",
            ),
            col(
                '<div class="failbox r"><div class="fb-h">'
                '<span class="fb-badge">WHY</span>'
                '<span class="fb-t">kindnet ignores NetworkPolicy</span></div>'
                "<p>kind&rsquo;s default CNI, <b>kindnet</b>, implements the Pod network and "
                "<b>nothing else</b>. It does not read NetworkPolicy objects at all.</p>"
                '<div class="fb-note">Apply a perfect default-deny policy on stock kind and '
                "<code>kubectl get networkpolicy</code> lists it, <code>describe</code> shows "
                "your rules, no error appears anywhere &mdash; and <b>every packet still gets "
                "through</b>. A policy that looks enforced but is not is far worse than no "
                "policy: you will ship it, and you will believe you are protected.</div></div>",
                bul(
                    [
                        "<code>disableDefaultCNI: true</code> &mdash; do not install kindnet.",
                        "<code>podSubnet: 192.168.0.0/16</code> &mdash; this <b>must</b> match "
                        "Calico&rsquo;s default IP pool. Mismatch it and Pods never get an "
                        "address and sit <code>ContainerCreating</code> forever.",
                        "<b>Checkpoint:</b> nodes <code>Ready</code> and Pods showing "
                        "<code>192.168.x.y</code> in <code>-o wide</code>. Do not go further "
                        "until both are true.",
                    ]
                ),
                note(
                    "n-tip",
                    "You just deleted the cluster and <b>every add-on in it</b> &mdash; ingress-nginx, "
                    "metrics-server and MetalLB all have to go back on. Reinstall them, then "
                    "<code>kubectl apply -f k8s/</code> to rebuild the app. This is precisely "
                    "why manifests and install commands live in git, not in your shell history.",
                ),
            ),
            ratio="1.1fr 1fr",
            gap=28,
        ),
        eyebrow="Lab 33 &middot; Networking",
        kicker="NetworkPolicy is only as real as the plugin enforcing it. kind&rsquo;s default "
        "enforces nothing.",
        notes=(
            "Do not let anyone skip this and go straight to writing policies &mdash; on kindnet "
            "their policies will appear to apply and enforce nothing, which teaches exactly the "
            "wrong lesson. The podSubnet must match Calico&rsquo;s default pool; that one line is "
            "the difference between a working cluster and Pods stuck without IPs. Make the "
            "checkpoint explicit: nodes Ready, Pod IPs in 192.168.x.y, then redeploy the app."
        ),
        day=4,
    ),
    lab(
        "Lock down the data tier",
        two(
            term(
                "1 &middot; prove it is open, then close it",
                """# BEFORE: anything can reach the data tier
kubectl run probe --rm -it --restart=Never \\
  --image=busybox:1.36 -- sh -c \\
  'nc -zv -w2 redis 6379; nc -zv -w2 db 5432'
# both open. that is default-allow.

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
EOF""",
                cls="xs",
            ),
            col(
                term(
                    "2 &middot; verify both directions",
                    """kubectl get networkpolicy

# the app still works -- vote, then check result
kubectl port-forward svc/vote 8080:80

# AFTER: the same probe is now cut off
kubectl run probe --rm -it --restart=Never \\
  --image=busybox:1.36 -- sh -c \\
  'nc -zv -w2 redis 6379 || echo BLOCKED; \\
   nc -zv -w2 db 5432   || echo BLOCKED'

# and a Pod that IS allowed still gets through
kubectl run probe --rm -it --restart=Never \\
  --labels=app=worker --image=busybox:1.36 \\
  -- nc -zv -w2 db 5432""",
                    cls="xs",
                ),
                note(
                    "n-warn",
                    "A blocked connection <b>hangs and times out</b> &mdash; it is not "
                    "&ldquo;connection refused&rdquo;. Policies <b>drop</b> packets silently, so "
                    "there is nobody to send a reset. That two-second wait before "
                    "<code>BLOCKED</code> is the policy working. Always use "
                    "<code>-w2</code> or you will sit there.",
                ),
            ),
            ratio="1.15fr 1fr",
            gap=26,
        ),
        eyebrow="Lab 34 &middot; NetworkPolicy",
        kicker="Only <code class=\"i\">vote</code> and <code class=\"i\">worker</code> may reach "
        "<code class=\"i\">redis</code>; only <code class=\"i\">worker</code> and "
        "<code class=\"i\">result</code> may reach <code class=\"i\">db</code>.",
        notes=(
            "Run the before-probe first &mdash; students need to see it succeed or the after-"
            "probe proves nothing. The third probe is the moment the model clicks: same image, "
            "same command, different label, and it connects. Policy decides on labels: "
            "identity in Kubernetes networking is a label, full stop. Expect confusion about the "
            "timeout versus refused distinction and address it as soon as the first person says "
            "&ldquo;mine is just hanging&rdquo;."
        ),
        day=4,
    ),
]

# ================================================================= 8. lbmetal
BLOCKS["lbmetal"] = [
    lab(
        "Install MetalLB on kind",
        two(
            term(
                "1 &middot; install, then find a free range",
                """kubectl apply -f https://raw.githubusercontent.com/\\
metallb/metallb/v0.14.8/config/manifests/\\
metallb-native.yaml

kubectl wait -n metallb-system --timeout=180s \\
  --for=condition=ready pod -l app=metallb

# which subnet do the kind nodes live on?
docker network inspect kind \\
  -f '{{ (index .IPAM.Config 0).Subnet }}'
# e.g. 172.18.0.0/16

# which addresses are already taken?
kubectl get nodes -o wide""",
                cls="xs",
            ),
            col(
                term(
                    "2 &middot; hand MetalLB a slice of it",
                    """cat <<'EOF' | kubectl apply -f -
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

kubectl get ipaddresspool -n metallb-system""",
                    cls="xs",
                ),
                note(
                    "n-warn",
                    "The pool <b>must be inside the <code>kind</code> Docker network subnet</b> "
                    "and <b>must not overlap the node IPs</b>. Docker hands nodes addresses from "
                    "the bottom of the range, so taking <code>.255.200&ndash;.255.250</code> from "
                    "the top is safe. If <code>docker network inspect</code> shows something "
                    "other than <code>172.18.0.0/16</code>, adjust every number to match yours.",
                ),
                note(
                    "n-info",
                    "<b>L2Advertisement</b> means MetalLB answers ARP for those addresses from "
                    "one node &mdash; a speaker Pod claims the IP and forwards. Simple, no "
                    "router config, and exactly right for a lab. The alternative mode is BGP, "
                    "which peers with real network gear.",
                ),
            ),
            ratio="1fr 1.1fr",
            gap=28,
        ),
        eyebrow="Lab 31 &middot; LoadBalancer",
        kicker="For four days <code class=\"i\">type: LoadBalancer</code> has been a slide. "
        "Twenty lines of YAML and it becomes real.",
        notes=(
            "Explain what has been missing: <code>type: LoadBalancer</code> is a request to a "
            "cloud controller, and kind has none, so the Service just sits Pending forever. "
            "MetalLB <i>is</i> that controller, running in the cluster. The one thing that goes "
            "wrong is the address range &mdash; make every student run the docker inspect command "
            "rather than pasting 172.18 blindly."
        ),
        day=4,
    ),
    lab(
        "A real external IP for vote",
        two(
            term(
                "1 &middot; flip the Service type",
                """kubectl patch svc vote \\
  -p '{"spec":{"type":"LoadBalancer"}}'

# EXTERNAL-IP goes <pending> -> a real address
kubectl get svc vote -w

kubectl get svc vote
# NAME  TYPE           EXTERNAL-IP      PORT(S)
# vote  LoadBalancer   172.18.255.200   80:31421/TCP""",
                cls="xs",
            ),
            col(
                term(
                    "2 &middot; use it",
                    """IP=$(kubectl get svc vote -o jsonpath=\\
'{.status.loadBalancer.ingress[0].ip}')
echo "$IP"

curl -s "http://$IP" | head -n5

# scale up -- the IP never changes
kubectl scale deploy/vote --replicas=4
curl -s "http://$IP" | head -n1

kubectl describe svc vote | tail -6""",
                    cls="xs",
                ),
                bul(
                    [
                        "A LoadBalancer Service is a <b>NodePort plus an external address</b> "
                        "&mdash; look at the <code>80:31421/TCP</code> column, the NodePort is "
                        "still there underneath.",
                        "The address is <b>stable</b> for the life of the Service. Pods churn, "
                        "replicas scale, the IP does not move.",
                        "This is what a cloud provider does for you on EKS or GKE &mdash; only "
                        "there it provisions a real ELB and bills you for it.",
                    ]
                ),
                note(
                    "n-tip",
                    "The <code>172.18.x.x</code> address is routable from the <b>Docker "
                    "host</b>. On a Linux VPS <code>curl</code> just works. On Docker Desktop "
                    "there is no route to that network &mdash; test from inside instead: "
                    "<code>docker exec iti-worker curl -s http://$IP</code>.",
                ),
            ),
            ratio="1fr 1.15fr",
            gap=28,
        ),
        eyebrow="Lab 32 &middot; LoadBalancer",
        kicker="One patch, one external IP, and the last theory-only Service type is finally "
        "hands-on.",
        notes=(
            "Have them run <code>get svc -w</code> before the patch lands so they watch pending "
            "turn into an address &mdash; that transition is the whole lab. Point out the "
            "NodePort still sitting in the PORT(S) column; LoadBalancer builds on NodePort rather "
            "than replacing it. The Docker Desktop caveat matters for anyone not on the class "
            "VPS, so read it out."
        ),
        day=4,
    ),
]

# =================================================================== 9. helm
BLOCKS["helm"] = [
    slide(
        "The problem Helm solves",
        two(
            panel(
                "Without Helm",
                bul(
                    [
                        "<code>k8s/dev/</code>, <code>k8s/staging/</code>, "
                        "<code>k8s/prod/</code> &mdash; three near-identical copies of the same "
                        "twelve manifests.",
                        "The image tag differs. The replica count differs. The hostname differs. "
                        "<b>Everything else is duplicated</b>.",
                        "A change to the Deployment shape means editing it three times, and "
                        "forgetting the third.",
                        "Installing someone else&rsquo;s app means reading their README and "
                        "hand-applying nine files in order.",
                        "&ldquo;What version of this app is running?&rdquo; &mdash; nobody can "
                        "answer. There is no unit called <i>this app</i>.",
                    ]
                ),
                "t-maroon",
            ),
            panel(
                "With Helm",
                bul(
                    [
                        "<b>One templated chart</b> plus a small <code>values-prod.yaml</code> "
                        "holding only what actually differs.",
                        "<code>helm install</code> renders the templates and applies everything "
                        "in dependency order, in one command.",
                        "The result is a <b>release</b>: a named, versioned unit you can "
                        "upgrade, roll back and uninstall as one thing.",
                        "<code>helm rollback myapp 3</code> &mdash; the whole application "
                        "returns to a known-good state, not just one Deployment.",
                        "Public charts exist for almost everything: Postgres, Prometheus, "
                        "ingress-nginx, cert-manager.",
                    ]
                ),
                "t-green",
            ),
            ratio="1fr 1fr",
            gap=30,
        )
        + note(
            "n-info",
            "Helm is often called &ldquo;the package manager for Kubernetes&rdquo;, and that is "
            "half of it. The other half is <b>templating</b> &mdash; and honestly, templating is "
            "the half you will use every day.",
            style="margin-top:18px",
        ),
        eyebrow="Awareness &middot; intro only",
        kicker="Copy-pasting the same YAML per environment stops scaling at about the second "
        "environment.",
        notes=(
            "Sell the problem before the tool &mdash; ask who has already copied a manifest "
            "folder this week. The release concept is the part people underrate: rolling back one "
            "Deployment is easy, rolling back an entire application atomically is not. Keep this "
            "awareness-level; Helm is its own day."
        ),
        day=4,
    ),
    slide(
        "Chart anatomy",
        two(
            term(
                "a chart is a directory",
                """mychart/
  Chart.yaml          # name, version, appVersion
  values.yaml         # DEFAULT values
  templates/
    deployment.yaml   # Go templates
    service.yaml
    ingress.yaml
    _helpers.tpl      # reusable snippets
    NOTES.txt         # printed after install
  charts/             # vendored dependencies""",
                cls="xs",
            ),
            col(
                term(
                    "template + values = manifest",
                    """# templates/deployment.yaml
spec:
  replicas: {{ .Values.replicaCount }}
  ...
      image: "{{ .Values.image.repo }}:\\
{{ .Values.image.tag }}"

# values.yaml
replicaCount: 2
image:
  repo: vote
  tag: "1.0"

# values-prod.yaml -- only the differences
replicaCount: 6
image:
  tag: "1.4" """,
                    cls="xs",
                ),
                bul(
                    [
                        "<code>Chart.yaml</code> &mdash; <b>version</b> is the chart&rsquo;s own "
                        "version; <b>appVersion</b> is the software it ships. Two different "
                        "numbers, and people conflate them constantly.",
                        "<code>values.yaml</code> is the <b>documented API</b> of your chart. "
                        "Anything not exposed there cannot be changed without forking.",
                        "<code>--set</code> and <code>-f</code> override defaults; the last one "
                        "wins.",
                    ]
                ),
            ),
            ratio="1fr 1.15fr",
            gap=28,
        ),
        eyebrow="What is in the box",
        kicker="Three things matter: <code class=\"i\">Chart.yaml</code>, "
        "<code class=\"i\">values.yaml</code>, and <code class=\"i\">templates/</code>.",
        notes=(
            "Show the template and its values side by side &mdash; the substitution is obvious "
            "once seen and abstract until then. The values.yaml-as-API framing is the most useful "
            "idea here: a good chart exposes exactly what should vary and nothing more. Mention "
            "<code>helm template</code> as the way to see the rendered YAML without installing, "
            "because that is how you debug charts."
        ),
        day=4,
    ),
    slide(
        "The commands you will actually use",
        two(
            term(
                "day-to-day Helm",
                """# find and inspect
helm repo add bitnami \\
  https://charts.bitnami.com/bitnami
helm repo update
helm search repo postgres
helm show values bitnami/postgresql | head -40

# install and manage a release
helm install mydb bitnami/postgresql \\
  --namespace data --create-namespace \\
  --set auth.database=votes

helm list -A
helm upgrade mydb bitnami/postgresql \\
  -f values-prod.yaml
helm history mydb
helm rollback mydb 1
helm uninstall mydb -n data

# render without installing -- debug here
helm template mydb ./mychart -f values-prod.yaml""",
                cls="xs",
            ),
            col(
                table(
                    ["Command", "What it does"],
                    [
                        [
                            "<code>repo add</code> / <code>update</code>",
                            "Register a chart repository, refresh its index",
                        ],
                        [
                            "<code>search repo</code>",
                            "Find charts in repos you have added",
                        ],
                        [
                            "<code>show values</code>",
                            "Read a chart&rsquo;s configurable options before installing",
                        ],
                        [
                            "<code>install</code>",
                            "Render + apply as a new named <b>release</b>",
                        ],
                        [
                            "<code>upgrade</code>",
                            "New chart or new values &rarr; a new release revision",
                        ],
                        [
                            "<code>rollback</code>",
                            "Return the whole release to an earlier revision",
                        ],
                        [
                            "<code>uninstall</code>",
                            "Remove every object the release created",
                        ],
                        [
                            "<code>template</code>",
                            "Print the YAML locally. Applies nothing",
                        ],
                    ],
                ),
                note(
                    "n-tip",
                    "Helm 3 keeps release state in a <b>Secret in the release&rsquo;s "
                    "namespace</b> &mdash; no Tiller, no cluster-wide component, nothing extra to "
                    "install. If you read an old tutorial mentioning Tiller, it is Helm 2 and it "
                    "is gone.",
                ),
            ),
            ratio="1fr 1.1fr",
            gap=28,
        ),
        eyebrow="Awareness &middot; the short list",
        kicker="Eight commands cover almost everything you will do with Helm.",
        notes=(
            "If you have five spare minutes, install one public chart live &mdash; seeing a "
            "whole Postgres appear from one command sells Helm better than any slide. Push "
            "<code>helm show values</code> as the habit: read the API before installing a "
            "stranger&rsquo;s chart. The Tiller footnote saves them from following outdated "
            "tutorials."
        ),
        day=4,
    ),
]

# ============================================================== 10. awareness
BLOCKS["awareness"] = [
    slide(
        "DaemonSet &mdash; one Pod per node",
        two(
            col(
                term(
                    "daemonset.yaml",
                    """apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-agent
spec:
  selector:
    matchLabels:
      app: log-agent
  template:
    metadata:
      labels:
        app: log-agent
    spec:
      tolerations:
      - operator: Exists
      containers:
      - name: agent
        image: fluent-bit:2.2""",
                    cls="xs",
                ),
                note(
                    "n-tip",
                    "Note there is <b>no <code>replicas</code> field</b>. The node count "
                    "<i>is</i> the replica count. Add a node and a Pod appears on it "
                    "automatically; drain the node and it goes.",
                ),
            ),
            col(
                bul(
                    [
                        "A DaemonSet guarantees <b>exactly one Pod on every node</b> that "
                        "matches its selector &mdash; or on every node, if there is no selector.",
                        "For work that belongs to the <b>machine</b>, not to the application: "
                        "log shippers, metrics agents, storage drivers, network plugins.",
                        "<code>tolerations: [{operator: Exists}]</code> tolerates <b>every</b> "
                        "taint &mdash; which is how system DaemonSets reach control-plane nodes "
                        "too.",
                        "<b>You already depend on three of them.</b> "
                        "<code>kube-proxy</code> is a DaemonSet. Your CNI, <code>calico-node</code>, "
                        "is a DaemonSet. So is the MetalLB speaker.",
                    ]
                ),
                term(
                    "look at the ones you are running",
                    """kubectl get daemonset -n kube-system
kubectl get pod -n kube-system -o wide \\
  -l k8s-app=kube-proxy""",
                    cls="xs",
                ),
            ),
            ratio="1fr 1.1fr",
            gap=30,
        ),
        eyebrow="Awareness &middot; the fourth controller",
        kicker="Deployment scales by demand. DaemonSet scales by node count.",
        notes=(
            "The callback is the point: they have been running DaemonSets since Day 1 without "
            "knowing the word &mdash; show them kube-proxy and calico-node in kube-system. The "
            "missing replicas field is the detail that makes the concept concrete. Keep it to one "
            "slide; they will not write one today."
        ),
        day=4,
    ),
    slide(
        "RBAC and ServiceAccounts",
        two(
            col(
                flow(
                    [
                        ("Subject", "user / SA / group", "t-slate"),
                        ("RoleBinding", "the link", "t-amber"),
                        ("Role", "verbs on resources", "t-blue"),
                    ]
                ),
                bul(
                    [
                        "<b>Role</b> &mdash; a list of allowed verbs on resources, <b>scoped to "
                        "one namespace</b>. <b>ClusterRole</b> &mdash; the same, cluster-wide or "
                        "for cluster-scoped objects like nodes.",
                        "<b>RoleBinding</b> grants a Role to a subject in a namespace. "
                        "<b>ClusterRoleBinding</b> grants it everywhere.",
                        "RBAC is <b>purely additive</b>. There is no deny rule; permissions only "
                        "ever accumulate.",
                        "Everything is denied until something explicitly allows it.",
                    ]
                ),
            ),
            col(
                term(
                    "a read-only Role, and who am I",
                    """apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: default
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list", "watch"]

---
kubectl auth can-i delete pods
kubectl auth can-i list pods \\
  --as=system:serviceaccount:default:vote""",
                    cls="xs",
                ),
                note(
                    "n-warn",
                    "<b>Every Pod runs as a ServiceAccount</b> &mdash; <code>default</code> if "
                    "you never said otherwise &mdash; and a token for it is mounted at "
                    "<code>/var/run/secrets/kubernetes.io/serviceaccount/</code>. Anyone who can "
                    "<code>exec</code> into your Pod holds that identity. Give workloads their "
                    "own ServiceAccount with the minimum it needs, and set "
                    "<code>automountServiceAccountToken: false</code> when it needs nothing at "
                    "all.",
                ),
            ),
            ratio="1fr 1.1fr",
            gap=30,
        ),
        eyebrow="Awareness &middot; who may do what",
        kicker="Four objects, one sentence: <b>a binding connects a subject to a role</b>.",
        notes=(
            "<code>kubectl auth can-i</code> is the takeaway command &mdash; it answers RBAC "
            "questions in one second and works with <code>--as</code> for impersonation. The "
            "mounted-token point genuinely surprises people: their app has cluster credentials it "
            "never asked for. Additive-only is the other thing to state, because people go "
            "looking for a deny rule."
        ),
        day=4,
    ),
    slide(
        "ResourceQuota and LimitRange",
        two(
            panel(
                "ResourceQuota &mdash; a ceiling for the <b>namespace</b>",
                '<div class="term xs r" style="margin:12px 0"><div class="term-bar">'
                '<div class="dots"><i></i><i></i><i></i></div>'
                '<span class="term-label">quota.yaml</span></div><pre><code>'
                '<span class="k">kind</span>: ResourceQuota\n'
                '<span class="k">spec</span>:\n'
                '  <span class="k">hard</span>:\n'
                '    <span class="k">requests.cpu</span>: "4"\n'
                '    <span class="k">requests.memory</span>: 8Gi\n'
                '    <span class="k">limits.cpu</span>: "8"\n'
                '    <span class="k">pods</span>: "20"\n'
                '    <span class="k">persistentvolumeclaims</span>: "5"'
                "</code></pre></div>"
                + bul(
                    [
                        "Caps the <b>total</b> across every Pod in the namespace.",
                        "Exceed it and the Pod is <b>rejected at creation</b> &mdash; a clear "
                        "error, not a Pending Pod.",
                        "<b>Once a quota exists, every container must declare requests and "
                        "limits</b>, or it is refused outright.",
                    ]
                ),
                "t-blue",
            ),
            panel(
                "LimitRange &mdash; defaults and bounds per <b>container</b>",
                '<div class="term xs r" style="margin:12px 0"><div class="term-bar">'
                '<div class="dots"><i></i><i></i><i></i></div>'
                '<span class="term-label">limitrange.yaml</span></div><pre><code>'
                '<span class="k">kind</span>: LimitRange\n'
                '<span class="k">spec</span>:\n'
                '  <span class="k">limits</span>:\n'
                '  - <span class="k">type</span>: Container\n'
                '    <span class="k">default</span>:\n'
                '      <span class="k">cpu</span>: 500m\n'
                '      <span class="k">memory</span>: 256Mi\n'
                '    <span class="k">defaultRequest</span>:\n'
                '      <span class="k">cpu</span>: 100m\n'
                '      <span class="k">memory</span>: 128Mi\n'
                '    <span class="k">max</span>:\n'
                '      <span class="k">cpu</span>: "2"'
                "</code></pre></div>"
                + bul(
                    [
                        "<b>Injects defaults</b> into containers that declared nothing &mdash; "
                        "no more BestEffort Pods by accident.",
                        "Enforces <code>min</code> and <code>max</code> per container.",
                        "The natural partner to a quota: LimitRange fills the gaps, the quota "
                        "counts the total.",
                    ]
                ),
                "t-green",
            ),
            ratio="1fr 1fr",
            gap=28,
        )
        + note(
            "n-tip",
            "<code>kubectl describe quota -n team-a</code> shows used versus hard, live. When a "
            "developer says &ldquo;my Pod will not create and the error mentions quota&rdquo;, "
            "that is the first and usually the last command you need.",
            style="margin-top:16px",
        ),
        eyebrow="Awareness &middot; multi-tenant hygiene",
        kicker="Requests and limits, enforced from above instead of hoped for.",
        notes=(
            "Tie this straight back to the morning: quotas are how a platform team makes requests "
            "and limits non-optional. The rule that catches people is that adding a quota "
            "retroactively makes every future Pod without resources fail &mdash; a LimitRange is "
            "how you soften that. One minute each, then move on."
        ),
        day=4,
    ),
]

# =========================================================== 11. troubleshoot
BLOCKS["troubleshoot"] = [
    slide(
        "Decision tree: symptom to cause",
        table(
            ["What you see", "Run this first", "Almost always means"],
            [
                [
                    "<code>Pending</code>",
                    "<code>kubectl describe pod</code> &rarr; Events",
                    "No node fits: <b>requests too big</b>, a taint, a nodeSelector, or an "
                    "unbound PVC",
                ],
                [
                    "<code>ImagePullBackOff</code>",
                    "<code>kubectl describe pod</code> &rarr; Events",
                    "Typo in the image name or tag, private registry, or "
                    "<b>image never loaded into kind</b>",
                ],
                [
                    "<code>CrashLoopBackOff</code>",
                    "<code>kubectl logs POD --previous</code>",
                    "The app exits on start: bad config, missing env var, a dependency that is "
                    "not up",
                ],
                [
                    "<code>OOMKilled</code> / exit <code>137</code>",
                    "<code>kubectl describe pod</code> &rarr; Last State",
                    "Memory limit too low, or a genuine leak",
                ],
                [
                    "<code>Running</code> but <code>READY 0/1</code>",
                    "<code>kubectl describe pod</code> &rarr; probe events",
                    "<b>Readiness probe failing</b> &mdash; wrong path, wrong port, or too short "
                    "a delay",
                ],
                [
                    "Service returns nothing",
                    "<code>kubectl get endpoints SVC</code>",
                    "Empty list &rarr; selector does not match the labels, or no Pod is Ready",
                ],
                [
                    "Name will not resolve",
                    "<code>kubectl exec &hellip; -- nslookup NAME</code>",
                    "Wrong Service name, wrong namespace, or CoreDNS is unhealthy",
                ],
                [
                    "Connection hangs, no refusal",
                    "<code>kubectl get networkpolicy</code>",
                    "A policy is dropping the packets &mdash; drops time out, they do not refuse",
                ],
            ],
            note_after=note(
                "n-tip",
                "Notice how many rows start with <code>describe pod</code>. When in doubt, that "
                "is the command &mdash; and the <b>Events</b> at the bottom are where the "
                "cluster tells you, in plain English, exactly what it could not do.",
                style="margin-top:16px",
            ),
        ),
        eyebrow="Troubleshooting",
        kicker="Eight symptoms cover the overwhelming majority of everything that will ever go "
        "wrong.",
        notes=(
            "Tell them to photograph this slide &mdash; it is the single most reusable thing in "
            "the course. Work the middle column, not the right: the skill is knowing which "
            "command to reach for, and the cause then reads itself off the output. The last row "
            "is the one they just met in the NetworkPolicy lab, so point back to it."
        ),
        day=4,
    ),
    slide(
        "The six-step playbook",
        two(
            steps(
                [
                    "<b>Look at the object.</b> <code>kubectl get pod -o wide</code> &mdash; "
                    "STATUS, READY, RESTARTS, AGE and NODE. Four of those five are clues.",
                    "<b>Read the Events.</b> <code>kubectl describe pod POD</code> and go "
                    "straight to the bottom. Scheduling, pulls, mounts and probes all report "
                    "here.",
                    "<b>Read the app&rsquo;s own logs.</b> <code>kubectl logs POD</code>, and "
                    "<code>--previous</code> if it has restarted &mdash; the interesting output "
                    "belongs to the container that <i>died</i>.",
                    "<b>Get inside.</b> <code>kubectl exec -it POD -- sh</code>. Check env vars, "
                    "mounted files, and whether the app answers on localhost.",
                    "<b>Test the network hop by hop.</b> <code>port-forward</code> to the Pod, "
                    "then to the Service. If the Pod works and the Service does not, it is the "
                    "selector or the endpoints.",
                    "<b>Compare to what works.</b> <code>kubectl get pod GOOD -o yaml &gt; a.yaml</code>, "
                    "same for the broken one, then <code>diff</code>. The answer is in the diff.",
                ]
            ),
            col(
                term(
                    "the toolkit",
                    """kubectl get pod -o wide
kubectl describe pod POD
kubectl logs POD --previous
kubectl logs -l app=vote --tail=50 --prefix
kubectl exec -it POD -- sh
kubectl port-forward pod/POD 8080:80
kubectl port-forward svc/vote 8080:80
kubectl get endpoints vote
kubectl get events --sort-by=.lastTimestamp
kubectl top pod
kubectl cp POD:/app/log.txt ./log.txt
kubectl get pod POD -o yaml""",
                    cls="xs",
                ),
                note(
                    "n-warn",
                    "Do not skip steps. The universal failure mode is jumping to step 4, "
                    "rebuilding an image, redeploying twice and losing twenty minutes &mdash; "
                    "when step 2 had the answer printed in English the whole time.",
                ),
            ),
            ratio="1.25fr 1fr",
            gap=28,
        ),
        eyebrow="A method, not a hunch",
        kicker="Same six steps, every time, in this order. Discipline beats intuition here.",
        notes=(
            "The value of a playbook is that it works when you are tired and the outage is loud "
            "&mdash; sell it that way. Step 6, diffing a broken object against a working one, is "
            "the professional trick most beginners have never seen. Make them run the whole "
            "sequence once on a healthy Pod so the commands are in their fingers before the "
            "gauntlet."
        ),
        day=4,
    ),
    slide(
        "Failure states and what they really mean",
        table(
            ["State", "What the cluster is telling you", "The real cause, usually"],
            [
                [
                    "<code>ImagePullBackOff</code><br><code>ErrImagePull</code>",
                    "The kubelet asked the registry and did not get an image",
                    "Typo in name or tag; <code>:latest</code> that no longer exists; private "
                    "registry with no <code>imagePullSecret</code>; <b>on kind, you forgot "
                    "<code>kind load docker-image</code></b>",
                ],
                [
                    "<code>ErrImageNeverPull</code>",
                    "<code>imagePullPolicy: Never</code> and the image is not on that node",
                    "The image exists on your laptop, not inside the node. Load it, or use "
                    "<code>IfNotPresent</code>",
                ],
                [
                    "<code>CrashLoopBackOff</code>",
                    "It started, it died, it started again &mdash; with growing back-off",
                    "App exits on a missing env var or Secret; the DB is not reachable yet; a "
                    "Job written as a Deployment; or a liveness probe that is too aggressive",
                ],
                [
                    "<code>OOMKilled</code> (137)",
                    "SIGKILL from the kernel&rsquo;s OOM killer",
                    "Memory limit below what the app actually needs, or a leak. Nothing appears "
                    "in the app&rsquo;s own logs",
                ],
                [
                    "<code>Pending</code>",
                    "No node passed the filter phase",
                    "Requests larger than any node; an untolerated taint; unsatisfiable "
                    "nodeSelector; a PVC with no matching StorageClass",
                ],
                [
                    "<code>READY 0/1</code>, Running",
                    "The container is up; readiness says do not send traffic",
                    "Probe path, port or scheme wrong; <code>initialDelaySeconds</code> too "
                    "short; the app is genuinely not ready yet",
                ],
                [
                    "Service, no endpoints",
                    "The selector matched zero <b>Ready</b> Pods",
                    "Selector/label mismatch, wrong namespace, or every Pod failing readiness",
                ],
                [
                    "<code>Terminating</code>, stuck",
                    "Something is holding the object open",
                    "A finalizer waiting on a resource; a PVC still mounted; a container "
                    "ignoring SIGTERM",
                ],
            ],
        ),
        eyebrow="The eight you will actually meet",
        kicker="The status is a symptom. This column tells you what the disease usually is.",
        notes=(
            "Emphasise that a status is never a diagnosis &mdash; CrashLoopBackOff means "
            "&lsquo;it keeps dying&rsquo;, not why, and the why is always in the logs of the "
            "previous container. The kind-specific rows, ErrImageNeverPull and the missing "
            "<code>kind load</code>, are the ones that will actually bite in this room. Ask which "
            "of these they have already hit this week; most hands go up for at least three."
        ),
        day=4,
    ),
    slide(
        "Reading Events properly",
        two(
            term(
                "events, four ways",
                """# the bottom of describe -- start here
kubectl describe pod vote-7d9f-x2k4

# every event in the namespace, newest last
kubectl get events --sort-by=.lastTimestamp

# only the bad news
kubectl get events --field-selector \\
  type=Warning --sort-by=.lastTimestamp

# everything about one object
kubectl get events --field-selector \\
  involvedObject.name=vote-7d9f-x2k4

# follow them live during a rollout
kubectl get events -w""",
                cls="xs",
            ),
            col(
                bul(
                    [
                        "Events are written by <b>controllers</b>, not by your app: the "
                        "scheduler, the kubelet, the Deployment controller. Each one is a "
                        "component telling you what it tried and what happened.",
                        "<b>They expire after one hour by default.</b> An empty event list on an "
                        "old failure means nothing &mdash; not that nothing went wrong.",
                        "Read the <code>REASON</code> column first: <code>FailedScheduling</code>, "
                        "<code>Failed</code>, <code>BackOff</code>, <code>Unhealthy</code>, "
                        "<code>Killing</code>, <code>FailedMount</code>.",
                        "<code>kubectl get events</code> is <b>not sorted</b> by default. Always "
                        "pass <code>--sort-by=.lastTimestamp</code> or you will read them in "
                        "arbitrary order and reach the wrong conclusion.",
                    ]
                ),
                note(
                    "n-tip",
                    "Events answer &ldquo;what did <b>Kubernetes</b> do?&rdquo;. Logs answer "
                    "&ldquo;what did <b>my app</b> do?&rdquo;. Almost every wasted debugging hour "
                    "comes from asking one of those questions of the wrong source.",
                ),
            ),
            ratio="1fr 1.15fr",
            gap=30,
        ),
        eyebrow="90% of failures explain themselves here",
        kicker="Events are the cluster narrating its own decisions. Most people never read them.",
        notes=(
            "The events-versus-logs split is the sentence to leave them with, and it is worth "
            "repeating twice. The one-hour expiry catches everyone: a Pod that failed overnight "
            "has no events left, so capture them while the failure is fresh. Make the sort-by "
            "flag a habit now, in class, rather than after they misread an unsorted list in "
            "production."
        ),
        day=4,
    ),
    lab(
        "The troubleshooting gauntlet",
        two(
            col(
                '<div class="failbox r"><div class="fb-h">'
                '<span class="fb-badge">RULES</span>'
                '<span class="fb-t">5 faults &middot; 30 minutes &middot; pairs</span>'
                "</div>"
                "<p>Your partner runs the break script against <b>your</b> cluster and does not "
                "tell you what it did. Then you swap. The Voting App is broken in five "
                "independent ways.</p>"
                '<div class="fb-note">For each fault write down three things: the '
                "<b>symptom</b> you saw, the <b>command</b> that revealed the cause, and the "
                "<b>fix</b> you applied. The write-up is the exercise &mdash; guessing your way "
                "to a green cluster teaches nothing.</div></div>",
                steps(
                    [
                        "Work the <b>playbook in order</b>. Resist the urge to jump to a fix.",
                        "<code>kubectl get pod -o wide</code> across the whole app first &mdash; "
                        "get the shape of the damage before touching anything.",
                        "Fix one fault, confirm it, then move on. Two changes at once and you "
                        "will not know which one worked.",
                        "Done when all five components are <code>Running</code> and "
                        "<code>READY</code>, and a vote you cast appears in the result page.",
                    ]
                ),
            ),
            col(
                term(
                    "break.sh &mdash; your partner runs this",
                    """#!/bin/sh
# 1 image that does not exist
kubectl set image deploy/vote vote=vote:v9-typo

# 2 memory limit far too small
kubectl patch deploy worker -p \\
'{"spec":{"template":{"spec":{"containers":\\
[{"name":"worker","resources":{"limits":\\
{"memory":"8Mi"}}}]}}}}'

# 3 service selector no longer matches
kubectl patch svc redis -p \\
'{"spec":{"selector":{"app":"redis-cache"}}}'

# 4 readiness probe on a path that 404s
kubectl patch deploy result -p \\
'{"spec":{"template":{"spec":{"containers":\\
[{"name":"result","readinessProbe":{"httpGet":\\
{"path":"/healthz","port":80}}}]}}}}'

# 5 requests no node can satisfy
kubectl set resources deploy/db \\
  --requests=cpu=32,memory=64Gi

echo "5 faults planted. good luck."
""",
                    cls="xs",
                ),
                note(
                    "n-warn",
                    "Do <b>not</b> read the script before you start. Five minutes of honest "
                    "diagnosis is worth more than a correct answer you looked up &mdash; and in "
                    "an incident nobody will hand you the script.",
                ),
            ),
            ratio="1fr 1.1fr",
            gap=26,
        ),
        eyebrow="Lab 35 &middot; Troubleshooting",
        kicker="Five planted faults, thirty minutes, one working Voting App at the end.",
        notes=(
            "Time it strictly and hold the room to the playbook &mdash; the discipline is the "
            "skill being trained, not the five specific bugs. Circulate and ask &ldquo;what did "
            "the Events say?&rdquo; rather than giving hints; most pairs are one "
            "<code>describe</code> away. Debrief at the end by walking all five faults and "
            "mapping each back to a row of the decision-tree slide."
        ),
        day=4,
    ),
]

# =========================================================== 12. bestpractice
BLOCKS["bestpractice"] = [
    slide(
        "Production readiness checklist",
        two(
            panel(
                "Before it ships",
                bul(
                    [
                        "<b>Pinned image tags.</b> <code>vote:1.4.2</code>, never "
                        "<code>:latest</code> &mdash; and ideally a digest.",
                        "<b>Requests and limits on every container.</b> Memory limit always; CPU "
                        "request always.",
                        "<b>All three probes considered.</b> Readiness nearly always, liveness "
                        "carefully, startup for slow boots.",
                        "<b>State on a PVC</b>, never in the container filesystem or on "
                        "<code>hostPath</code>.",
                        "<b>Secrets externalised</b> &mdash; out of the image, out of git, "
                        "injected at runtime.",
                        "<b>More than one replica</b> for anything stateless, so a node can die.",
                    ]
                ),
                "t-green",
            ),
            panel(
                "Around it",
                bul(
                    [
                        "<b>Its own namespace</b>, with a ResourceQuota and a LimitRange.",
                        "<b>NetworkPolicy on the data tier</b> at minimum &mdash; nothing "
                        "reaches the database that does not need to.",
                        "<b>HPA</b> wherever load varies, backed by real requests.",
                        "<b>Every manifest in git</b>, applied from CI, never from a laptop.",
                        "<b><code>--record</code> or a CHANGE-CAUSE annotation</b> on rollouts, "
                        "so <code>rollout history</code> is readable.",
                        "<b>A rollback you have actually rehearsed</b>, not one you assume works.",
                    ]
                ),
                "t-blue",
            ),
            ratio="1fr 1fr",
            gap=30,
        )
        + note(
            "n-tip",
            "Run this list against the Voting App you just built. Be honest about which lines you "
            "would fail today &mdash; that gap is your first week&rsquo;s work in any real job.",
            style="margin-top:16px",
        ),
        eyebrow="Best practices",
        kicker="Twelve lines. If you can tick them all, the thing is genuinely production-ready.",
        notes=(
            "Turn this into an exercise, not a reading: put the Voting App manifests up and audit "
            "them line by line against the list. The two students always underestimate are "
            "rehearsed rollbacks and manifests-in-git &mdash; both are process, not YAML, and "
            "both are what actually saves you at 3am."
        ),
        day=4,
    ),
    slide(
        "The top ten mistakes",
        cards(
            [
                (
                    "&#9888;",
                    "1 &middot; No resource requests",
                    "The scheduler assumes zero, packs the node, and everything degrades "
                    "together. Also silently disables your HPA.",
                    "t-maroon",
                ),
                (
                    "&#127991;",
                    "2 &middot; :latest tags",
                    "Two Pods of the same Deployment can run different code. Rollback becomes "
                    "meaningless because there is nothing to roll back to.",
                    "t-amber",
                ),
                (
                    "&#128273;",
                    "3 &middot; Secrets in git",
                    "base64 is not encryption. Once it is in history it is public forever "
                    "&mdash; rotate the credential, do not just delete the commit.",
                    "t-maroon",
                ),
                (
                    "&#128260;",
                    "4 &middot; No readiness probe",
                    "Traffic hits Pods that cannot serve yet. Every rolling update drops "
                    "requests &mdash; the zero-downtime myth from Day 2.",
                    "t-blue",
                ),
                (
                    "&#128163;",
                    "5 &middot; Aggressive liveness probe",
                    "A slow app under load fails the probe, gets restarted, comes back slower. "
                    "A liveness probe can turn a hiccup into an outage.",
                    "t-violet",
                ),
                (
                    "&#128230;",
                    "6 &middot; Bare Pods in production",
                    "Nothing recreates them. The node reboots and your app is simply gone. "
                    "Always a Deployment, StatefulSet, Job or DaemonSet.",
                    "t-teal",
                ),
                (
                    "&#128193;",
                    "7 &middot; Everything in default",
                    "No quotas, no boundaries, no way to delete one app cleanly, and RBAC that "
                    "cannot be scoped to anything useful.",
                    "t-slate",
                ),
                (
                    "&#128220;",
                    "8 &middot; No CHANGE-CAUSE",
                    "<code>rollout history</code> full of &lt;none&gt;. You know a revision 4 "
                    "exists; you have no idea what it changed.",
                    "t-gold",
                ),
                (
                    "&#128190;",
                    "9 &middot; hostPath for app data",
                    "Ties the Pod to one node&rsquo;s disk. Reschedule and the data is on the "
                    "wrong machine. Use a PVC.",
                    "t-green",
                ),
                (
                    "&#128274;",
                    "10 &middot; No NetworkPolicy",
                    "Any compromised Pod anywhere reaches your database directly. Default-allow "
                    "is a choice you are making by not choosing.",
                    "t-maroon",
                ),
            ],
            cols=5,
        ),
        eyebrow="Learn these from other people",
        kicker="Every one of these is common, every one is cheap to avoid, and every one has "
        "caused a real outage.",
        notes=(
            "Go quickly &mdash; one line each, this is a reference slide not a lecture. Ask the "
            "room to vote on which they have personally done; the honesty gets a laugh and makes "
            "it stick. Numbers 1, 4 and 5 are the ones that cause real production incidents, so "
            "spend the extra ten seconds there."
        ),
        day=4,
    ),
    slide(
        "Security basics",
        two(
            term(
                "a sane securityContext",
                """spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    fsGroup: 10001
  containers:
  - name: vote
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
    resources:
      limits:
        memory: 256Mi""",
                cls="xs",
            ),
            col(
                bul(
                    [
                        "<b>Do not run as root.</b> A container escape as UID 0 is a very "
                        "different afternoon from one as UID 10001. Set <code>runAsNonRoot</code> "
                        "and let the cluster refuse the Pod if the image ignores it.",
                        "<b>Drop all capabilities</b>, then add back only what you truly need. "
                        "Almost no web app needs any.",
                        "<b>Read-only root filesystem</b> where you can &mdash; mount an "
                        "<code>emptyDir</code> for scratch space instead.",
                        "<b>No secrets in the image and none in git.</b> Inject at runtime; "
                        "rotate anything that ever leaked.",
                        "<b>Scan your images</b> (<code>trivy image vote:1.4.2</code>) and keep "
                        "base images small &mdash; less installed means less to exploit.",
                    ]
                ),
                note(
                    "n-info",
                    "Clusters increasingly enforce this centrally with <b>Pod Security "
                    "Admission</b> &mdash; label a namespace "
                    "<code>pod-security.kubernetes.io/enforce=restricted</code> and non-compliant "
                    "Pods are rejected at creation. Better to write compliant manifests now than "
                    "to discover it at deploy time.",
                ),
            ),
            ratio="1fr 1.2fr",
            gap=30,
        ),
        eyebrow="The cheap 80%",
        kicker="Five settings that cost nothing and remove most of the easy attacks.",
        notes=(
            "Keep it practical &mdash; this is a hardening checklist, not a security course. The "
            "line that lands is that root inside a container is much closer to root on the node "
            "than people assume. Mention Pod Security Admission so they are not blindsided when a "
            "real cluster rejects their manifest."
        ),
        day=4,
    ),
    slide(
        "Resource and cost hygiene",
        two(
            col(
                bul(
                    [
                        "<b>You pay for requests, not for usage.</b> A cluster 95% requested and "
                        "10% used costs the same as one that is genuinely busy. This is where "
                        "cloud bills go to die.",
                        "<b>Size requests from measurements.</b> Run under real load, read "
                        "<code>kubectl top</code>, set the request just above the observed "
                        "steady state &mdash; then revisit it.",
                        "<b>Memory limits: yes. CPU limits: think.</b> A memory limit protects "
                        "the node from a leak. An aggressive CPU limit just throttles your app "
                        "into latency that looks like a bug.",
                        "<b>Scale to what you need.</b> An HPA with a sane "
                        "<code>minReplicas</code> beats a fixed count guessed at peak.",
                        "<b>Delete what you are not using.</b> Finished Jobs, evicted Pods, "
                        "orphaned PVCs and unattached load balancers all keep costing.",
                    ]
                ),
            ),
            col(
                term(
                    "the hygiene sweep",
                    """# requested vs actually used
kubectl describe node iti-worker \\
  | grep -A8 'Allocated resources'
kubectl top nodes

# clutter that still costs money
kubectl get pod -A \\
  --field-selector status.phase=Failed
kubectl get job -A
kubectl get pvc -A
kubectl get svc -A \\
  --field-selector spec.type=LoadBalancer

# clean up finished work
kubectl delete pod -A \\
  --field-selector status.phase=Succeeded""",
                    cls="xs",
                ),
                note(
                    "n-tip",
                    "Do this sweep monthly and you will find something every single time. The "
                    "usual winners: a forgotten LoadBalancer, a 100Gi PVC nobody mounted since "
                    "March, and a namespace of Evicted Pods from an incident last quarter.",
                ),
            ),
            ratio="1.15fr 1fr",
            gap=30,
        ),
        eyebrow="What it costs to run",
        kicker="The gap between requested and used is real money, on someone&rsquo;s real "
        "invoice.",
        notes=(
            "This is the slide that makes them useful to a business rather than just to a "
            "cluster. The you-pay-for-requests point is the whole argument for sizing honestly, "
            "and it connects the morning&rsquo;s theory to a number a manager cares about. The "
            "cleanup commands are worth running live on the class cluster; there will be junk in "
            "it already."
        ),
        day=4,
    ),
]

# ================================================================== 13. final
BLOCKS["final"] = [
    lab(
        "Final challenge: the Voting App, from scratch",
        two(
            col(
                '<div class="failbox r"><div class="fb-h">'
                '<span class="fb-badge">SPEC</span>'
                '<span class="fb-t">90 minutes &middot; fresh namespace &middot; solo</span>'
                "</div>"
                "<p>Create namespace <code>vote-final</code> and deploy the complete Voting App "
                "into it &mdash; <b>from an empty editor</b>. No copying yesterday&rsquo;s "
                "files. Docs and <code>kubectl explain</code> are allowed; your old manifests "
                "are not.</p>"
                '<div class="fb-note">Done when: you can cast a vote through the Ingress, see it '
                "counted on <code>/result</code>, delete any Pod and watch it recover, and "
                "<b>delete the <code>db</code> Pod without losing a single vote</b>."
                "</div></div>",
                term(
                    "start here",
                    """kubectl create namespace vote-final
kubectl config set-context --current \\
  --namespace=vote-final

# work in files, apply the directory
mkdir final && cd final
kubectl apply -f .

kubectl get all,cm,secret,pvc,ing,hpa,netpol""",
                    cls="xs",
                ),
            ),
            col(
                table(
                    ["#", "Requirement"],
                    [
                        [
                            "1",
                            "<b>5 Deployments</b>: <code>vote</code>, <code>result</code>, "
                            "<code>worker</code>, <code>redis</code>, <code>db</code>. "
                            "<code>vote</code> and <code>result</code> at 2 replicas.",
                        ],
                        [
                            "2",
                            "<b>4 Services.</b> Named exactly <code>vote</code>, "
                            "<code>result</code>, <code>redis</code>, <code>db</code>. "
                            "<code>worker</code> gets none &mdash; know why.",
                        ],
                        [
                            "3",
                            "<b>ConfigMap</b> supplying <code>OPTION_A</code> and "
                            "<code>OPTION_B</code> to <code>vote</code>. Pick your own two "
                            "options.",
                        ],
                        [
                            "4",
                            "<b>Secret</b> supplying <code>POSTGRES_PASSWORD</code> to "
                            "<code>db</code>. No password anywhere in a Deployment.",
                        ],
                        [
                            "5",
                            "<b>PVC</b> for <code>db</code>, mounted at "
                            "<code>/var/lib/postgresql/data</code>. Votes survive a Pod delete.",
                        ],
                        [
                            "6",
                            "<b>Probes</b>: readiness on <code>vote</code> and "
                            "<code>result</code>; an <code>exec</code> "
                            "<code>pg_isready</code> probe on <code>db</code>.",
                        ],
                        [
                            "7",
                            "<b>requests and limits on every container.</b> "
                            "<code>db</code> must come out <b>Guaranteed</b>.",
                        ],
                        [
                            "8",
                            "<b>HPA</b> on <code>vote</code>: min 2, max 8, CPU target 60%.",
                        ],
                        [
                            "9",
                            "<b>Ingress</b>: <code>/</code> &rarr; <code>vote</code>, "
                            "<code>/result</code> &rarr; <code>result</code>.",
                        ],
                        [
                            "10",
                            "<b>NetworkPolicy</b>: only <code>vote</code>+<code>worker</code> "
                            "reach <code>redis</code>; only <code>worker</code>+"
                            "<code>result</code> reach <code>db</code>.",
                        ],
                    ],
                ),
                note(
                    "n-warn",
                    "The Services <b>must</b> be named <code>redis</code> and <code>db</code>. "
                    "The app resolves those hostnames from inside its own code &mdash; call the "
                    "Service <code>postgres</code> and everything comes up green while the app "
                    "quietly does nothing. DNS name equals Service name.",
                ),
            ),
            ratio="1fr 1.35fr",
            gap=28,
        ),
        eyebrow="Lab 36 &middot; Final challenge",
        kicker="Ten requirements, one namespace, everything you have learned in four days.",
        notes=(
            "Insist on the empty editor &mdash; the whole value is in recalling the object shapes "
            "unaided, and <code>kubectl explain</code> is the tool that makes that fair. Read "
            "requirement 2 and the Service-naming warning aloud at the start, because that one "
            "failure is silent and will eat somebody&rsquo;s last twenty minutes. Circulate with "
            "the rubric visible so they know exactly what is being checked."
        ),
        day=4,
    ),
    slide(
        "How it is graded",
        two(
            table(
                ["Area", "Pts", "What earns them"],
                [
                    [
                        "<b>It runs</b>",
                        "30",
                        "All 5 components <code>Running</code> and <code>READY</code>; a vote "
                        "cast in the UI appears on the result page",
                    ],
                    [
                        "<b>Config &amp; Secrets</b>",
                        "15",
                        "ConfigMap feeds the vote options; Secret feeds the DB password; no "
                        "plaintext credential in any Deployment",
                    ],
                    [
                        "<b>Storage</b>",
                        "15",
                        "PVC <code>Bound</code> and mounted; <code>kubectl delete pod -l "
                        "app=db</code> loses zero votes",
                    ],
                    [
                        "<b>Health</b>",
                        "10",
                        "Readiness probes present and passing; the <code>pg_isready</code> exec "
                        "probe on <code>db</code>",
                    ],
                    [
                        "<b>Resources</b>",
                        "10",
                        "Requests and limits on every container; <code>db</code> reports "
                        "<code>qosClass: Guaranteed</code>",
                    ],
                    [
                        "<b>Scaling</b>",
                        "10",
                        "HPA exists and shows a real percentage &mdash; not "
                        "<code>&lt;unknown&gt;</code>",
                    ],
                    [
                        "<b>Networking</b>",
                        "10",
                        "Ingress routes both paths; the two NetworkPolicies block an unlabelled "
                        "probe Pod",
                    ],
                ],
            ),
            col(
                term(
                    "grade yourself in one pass",
                    """kubectl get all -n vote-final
kubectl get cm,secret,pvc,ing,hpa,netpol \\
  -n vote-final

kubectl get pod -n vote-final -o custom-columns=\\
NAME:.metadata.name,QOS:.status.qosClass

kubectl get hpa -n vote-final
# TARGETS must not be <unknown>

# the storage proof
kubectl delete pod -n vote-final -l app=db
# ...then reload /result. votes still there?

# the policy proof
kubectl run probe -n vote-final --rm -it \\
  --restart=Never --image=busybox:1.36 \\
  -- nc -zv -w2 db 5432 || echo BLOCKED""",
                    cls="xs",
                ),
                note(
                    "n-tip",
                    "<b>85+ is a pass.</b> Run this column on yourself before you call me over "
                    "&mdash; every check here is a command you already know, and self-grading is "
                    "the habit that makes you trustworthy on a real team.",
                ),
            ),
            ratio="1.25fr 1fr",
            gap=28,
        ),
        eyebrow="Rubric &middot; 100 points",
        kicker="Seven areas. Every one of them is verifiable with a command, not an opinion.",
        notes=(
            "Show the rubric <i>before</i> they start the challenge, not after &mdash; a hidden "
            "rubric tests luck, a visible one tests skill. Push the self-grading column hard: the "
            "point is that they can prove their own work, which is exactly what a team will "
            "expect. The two proofs at the bottom, storage and policy, are the ones people forget "
            "to actually test."
        ),
        day=4,
    ),
]

# ============================================================= 14. interview4
BLOCKS["interview4"] = [
    slide(
        "Day 4 interview questions",
        two(
            col(
                steps(
                    [
                        "<b>What is the difference between a resource request and a limit?</b> "
                        "<i>Requests are used by the scheduler to place the Pod and are reserved "
                        "on the node; limits are enforced at runtime by the kernel. Requests "
                        "schedule, limits constrain.</i>",
                        "<b>What happens when a container exceeds its CPU limit? Its memory "
                        "limit?</b> <i>CPU is throttled &mdash; it just runs slower. Memory is "
                        "not compressible, so the container is OOMKilled with exit code 137 and "
                        "restarted.</i>",
                        "<b>Name the three QoS classes and how a Pod gets each.</b> "
                        "<i>Guaranteed: every container sets requests == limits for CPU and "
                        "memory. Burstable: something is set but they do not match. BestEffort: "
                        "nothing set. Eviction goes BestEffort first, Guaranteed last.</i>",
                        "<b>Difference between nodeSelector, node affinity, and taints?</b> "
                        "<i>nodeSelector and affinity are Pod-side attraction &mdash; affinity "
                        "adds operators and soft preferences. Taints are node-side repulsion; a "
                        "toleration only grants permission, it does not attract.</i>",
                    ]
                ),
            ),
            col(
                steps(
                    [
                        "<b>Why might an HPA never scale?</b> <i>No metrics-server, or &mdash; "
                        "far more often &mdash; no CPU request on the container. Utilisation is "
                        "a percentage of the request, so with no request there is no metric. It "
                        "shows &lt;unknown&gt; and fails silently.</i>",
                        "<b>Job versus Deployment?</b> <i>A Deployment keeps a process running "
                        "forever and treats exit 0 as a failure. A Job runs to completion and "
                        "treats exit 0 as success. Jobs must use restartPolicy OnFailure or "
                        "Never.</i>",
                        "<b>Do namespaces isolate network traffic?</b> <i>No. Any Pod can reach "
                        "any Pod in any namespace by default. Only a NetworkPolicy &mdash; "
                        "enforced by a CNI that supports it &mdash; restricts traffic.</i>",
                        "<b>How does a NetworkPolicy actually work?</b> <i>It selects Pods with a "
                        "podSelector; those Pods flip to deny-by-default for the directions "
                        "listed, and only explicitly allowed traffic passes. Policies are "
                        "additive and there is no deny rule.</i>",
                    ]
                ),
            ),
            ratio="1fr 1fr",
            gap=28,
        ),
        eyebrow="Eight you will genuinely be asked",
        kicker="Answer each in two sentences. Interviewers are testing the model, not your "
        "vocabulary.",
        notes=(
            "Run this as a cold-call round rather than reading the answers &mdash; they have "
            "done every one of these with their hands today. Questions 1, 2 and 5 come up in "
            "almost every Kubernetes interview, so make sure everybody can say those three "
            "cleanly. Push for the short answer; rambling is what actually loses interviews."
        ),
        day=4,
    ),
    slide(
        "What to study next",
        two(
            cards(
                [
                    (
                        "&#127891;",
                        "CKAD",
                        "Developer-focused. Pods, Deployments, config, storage, probes, Jobs, "
                        "Services &mdash; almost exactly the four days you just did. The natural "
                        "next step, and it is hands-on in a real terminal.",
                        "t-blue",
                    ),
                    (
                        "&#128737;",
                        "CKA",
                        "Administrator-focused. Adds cluster installation with kubeadm, etcd "
                        "backup and restore, upgrades, node maintenance, RBAC and cluster "
                        "networking in depth.",
                        "t-violet",
                    ),
                    (
                        "&#128214;",
                        "The official docs",
                        "<code>kubernetes.io/docs</code> &mdash; genuinely excellent, and the "
                        "only reference allowed during the exams. Learn to navigate it fast; "
                        "that is itself an exam skill.",
                        "t-teal",
                    ),
                ],
                cols=3,
            ),
            col(
                bul(
                    [
                        "<b>Live in <code>kubectl explain</code>.</b> "
                        "<code>kubectl explain deploy.spec.template.spec.containers</code> is "
                        "faster than any search engine and always matches your cluster version.",
                        "<b>Then learn Helm properly</b> &mdash; you saw the shape today; write "
                        "a chart for the Voting App and it will click.",
                        "<b>Then GitOps</b> (Argo CD or Flux): git becomes the only way anything "
                        "reaches the cluster. This is how serious teams deploy.",
                        "<b>Then observability</b> &mdash; Prometheus and Grafana. "
                        "metrics-server told you the numbers exist; these tell you what they "
                        "meant last Tuesday.",
                        "<b>Keep a cluster.</b> kind on your laptop costs nothing. The people who "
                        "get good are the ones who kept breaking one.",
                    ]
                ),
                note(
                    "n-tip",
                    "Rebuild the Voting App from memory once a week for a month. Four "
                    "repetitions and the object shapes stop being something you look up and "
                    "become something you know &mdash; which is precisely the difference an "
                    "interviewer is listening for.",
                ),
            ),
            ratio="1.2fr 1fr",
            gap=30,
        ),
        eyebrow="Where to go from here",
        kicker="You have the foundation. Here is the shortest path from here to hired.",
        notes=(
            "Be concrete about CKAD being the closer match to what they just learned &mdash; "
            "people default to CKA because it sounds more senior and then struggle. The "
            "docs-navigation point is real exam advice: both certifications allow the docs, so "
            "speed of lookup is part of the score. End on the weekly rebuild; it is the single "
            "highest-return habit you can hand them."
        ),
        day=4,
    ),
]
