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
        "Scheduling, Scaling & Production",
        "Day 4. You can deploy an app. Today you make it survive a real cluster "
        "&mdash; and fix it when it does not.",
        [
            "Requests, limits & QoS",
            "Scheduling: affinity, taints & tolerations",
            "metrics-server, kubectl top & the HPA",
            "Jobs & CronJobs",
            "Ingress, CNI & NetworkPolicy",
            "Helm, RBAC, DaemonSets & quotas",
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
