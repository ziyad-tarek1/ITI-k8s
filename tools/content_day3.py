#!/usr/bin/env python3
"""Day 3 content — Configuration, Storage & Health.

Blocks map name -> list of rendered <section> strings, all stamped day=3.
Every lab runs against the Voting App in the `vote` namespace and assumes the
Day-2 state: five Deployments (vote, result, worker, redis, db) whose
Deployment name, container name and `app=` label all match the component name.

App facts these labs depend on (verified against voting-app/):
  vote/app.py            os.getenv('OPTION_A', "Cats") / OPTION_B -> ConfigMap demo
  worker/Worker.java     redis list key "votes", table votes(id, vote)
  result + worker        patched to read DB_HOST / DB_USER / DB_PASSWORD from env
"""
from deck import cards, col, divider, hl, lab, note, slide, steps, table, term, two

D = 3

# =========================================================== day3open (1)
day3open = [
    divider(
        "03",
        "Configuration, Storage &amp; Health",
        "Yesterday the app ran. Today it gets configurable, durable and honest about "
        "whether it is actually ready to serve.",
        [
            "ConfigMaps &mdash; config out of the image",
            "Secrets &mdash; and why base64 is not encryption",
            "Volumes, PVCs and what survives what",
            "StatefulSets &mdash; a first look",
            "Liveness, readiness and startup probes",
        ],
        notes=(
            "Frame the day as making yesterday&rsquo;s app production-shaped. Three "
            "promises: you will change the vote options without rebuilding an image, "
            "you will kill the database Pod and keep the tally, and you will finally "
            "make the zero-downtime claim from Day 2 true. Tell them the last lab is "
            "the one they will remember."
        ),
        day=D,
    )
]

# =========================================================== configmap (7)
configmap = [
    # ---- teach 1: what and why
    slide(
        "ConfigMaps &mdash; take config out of the image",
        cards(
            [
                (
                    "&#128230;",
                    "One image, many environments",
                    "The same <code>vote</code> image runs in dev, staging and prod. "
                    "Only the <b>configuration</b> differs &mdash; so it must not live "
                    "inside the image.",
                    "t-slate",
                ),
                (
                    "&#128273;",
                    "Key/value, plain text",
                    "A ConfigMap is a namespaced object holding string key/value pairs. "
                    "Values can be a word, a number, or a whole file.",
                    "t-blue",
                ),
                (
                    "&#128260;",
                    "Change config, not code",
                    "Edit the ConfigMap and roll the Deployment. No rebuild, no new tag, "
                    "no <code>docker push</code>.",
                    "t-green",
                ),
                (
                    "&#128465;",
                    "Decoupled lifecycle",
                    "The ConfigMap outlives the Pods that read it. Delete every Pod &mdash; "
                    "the config is still there for the replacements.",
                    "t-teal",
                ),
                (
                    "&#128203;",
                    "Two ways in",
                    "Injected as <b>environment variables</b>, or projected as "
                    "<b>files</b> in a mounted volume. Same object, two delivery paths.",
                    "t-violet",
                ),
                (
                    "&#9888;",
                    "Not for secrets",
                    "ConfigMap data is stored and displayed in the clear. Passwords, "
                    "tokens and keys belong in a <b>Secret</b> &mdash; next section.",
                    "t-maroon",
                ),
            ]
        )
        + note(
            "n-why",
            "Our <code>vote</code> app already reads <code>OPTION_A</code> and "
            "<code>OPTION_B</code> from the environment with defaults of &ldquo;Cats&rdquo; "
            "and &ldquo;Dogs&rdquo;. That is a <b>12-factor</b> app: config comes from the "
            "environment, so the same artifact ships everywhere.",
            style="margin-top:18px",
        ),
        eyebrow="18 &middot; Configuration",
        kicker="Anything that changes between environments belongs outside the image.",
        notes=(
            "Start with the pain: baking a hostname or a feature flag into an image means "
            "a rebuild per environment, and images that are no longer identical. Point at "
            "vote/app.py on screen &mdash; it already reads OPTION_A from the environment, "
            "so nothing here is contrived. Say clearly that ConfigMaps are plain text and "
            "are not a security boundary; that sets up the Secrets section."
        ),
        day=D,
    ),
    # ---- teach 2: three creation styles
    slide(
        "Three ways to create one",
        two(
            term(
                "imperative &middot; literals and files",
                """# 1) from literals -- quickest, good for a demo
kubectl create configmap vote-config -n vote \\
  --from-literal=OPTION_A=Tea \\
  --from-literal=OPTION_B=Coffee

# 2) from a file -- the KEY is the filename,
#    the VALUE is the whole file content
cat > banner.txt <<'EOF'
ITI DevOps 2026 -- vote responsibly
EOF
kubectl create configmap vote-banner -n vote \\
  --from-file=banner.txt

# from a whole directory (one key per file)
kubectl create configmap app-conf -n vote \\
  --from-file=./conf.d/

# read it back
kubectl get configmap vote-config -n vote -o yaml""",
                cls="xs",
            ),
            col(
                term(
                    "declarative &middot; the YAML you commit",
                    """apiVersion: v1
kind: ConfigMap
metadata:
  name: vote-config
  namespace: vote
data:
  # simple key/value -> good for env vars
  OPTION_A: "Tea"
  OPTION_B: "Coffee"
  LOG_LEVEL: "info"

  # a key whose value is a whole file
  banner.txt: |
    ITI DevOps 2026
    vote responsibly""",
                    cls="xs",
                ),
                note(
                    "n-tip",
                    "The imperative form is for the classroom. In real life you commit the "
                    "YAML &mdash; or generate it and diff it first: "
                    "<code>kubectl create cm x --from-literal=k=v --dry-run=client -o yaml</code>.",
                ),
            ),
            ratio="1.05fr 1fr",
            gap=30,
        ),
        eyebrow="Creation",
        kicker="<code>--from-literal</code>, <code>--from-file</code>, or a YAML manifest &mdash; "
        "the resulting object is identical.",
        notes=(
            "Emphasise the one rule students forget: with --from-file the key is the "
            "filename and the value is the entire file. Show the --dry-run=client -o yaml "
            "trick and tell them it is how you write manifests without memorising schemas. "
            "Also mention binaryData exists for non-UTF8 content, but they will not need it."
        ),
        day=D,
    ),
    # ---- teach 3: as env vars
    slide(
        "Injecting a ConfigMap as environment variables",
        two(
            term(
                "one key at a time &middot; configMapKeyRef",
                """spec:
  containers:
  - name: vote
    image: vote:v1
    env:
    - name: OPTION_A            # env var name in the container
      valueFrom:
        configMapKeyRef:
          name: vote-config     # which ConfigMap
          key: OPTION_A         # which key inside it
          # optional: true      # tolerate a missing key
    - name: OPTION_B
      valueFrom:
        configMapKeyRef:
          name: vote-config
          key: OPTION_B""",
                cls="xs",
            ),
            col(
                term(
                    "every key at once &middot; envFrom",
                    """spec:
  containers:
  - name: vote
    image: vote:v1
    envFrom:
    - configMapRef:
        name: vote-config
      # every key becomes an env var
      # with the SAME name as the key
    # optional prefix to avoid collisions:
    - configMapRef:
        name: db-config
      prefix: DB_""",
                    cls="xs",
                ),
                note(
                    "n-info",
                    "<b>configMapKeyRef</b> renames &mdash; the env var name and the "
                    "ConfigMap key are independent. <b>envFrom</b> does not: your keys must "
                    "already be valid env var names, or Kubernetes silently skips them and "
                    "records an event.",
                ),
            ),
            ratio="1fr 1fr",
            gap=30,
        ),
        eyebrow="Path 1 &middot; environment",
        kicker="Two shapes: pick individual keys with <code>configMapKeyRef</code>, or dump them "
        "all in with <code>envFrom</code>.",
        notes=(
            "Draw the mapping out loud: name is what the container sees, key is what the "
            "ConfigMap calls it. envFrom is convenient but blunt &mdash; a key like "
            "&ldquo;my.setting&rdquo; is not a legal env var name and gets skipped without "
            "an error in the Pod. Tell them to check with kubectl describe pod when an env "
            "var they expected is missing."
        ),
        day=D,
    ),
    # ---- teach 4: as mounted files
    slide(
        "Injecting a ConfigMap as mounted files",
        two(
            term(
                "volume + volumeMounts",
                """spec:
  containers:
  - name: vote
    image: vote:v1
    volumeMounts:
    - name: conf              # matches a volume below
      mountPath: /etc/vote    # directory in the container
      readOnly: true
  volumes:
  - name: conf
    configMap:
      name: vote-config
      # optional: project only some keys,
      # and rename them on the way in
      items:
      - key: banner.txt
        path: banner.txt""",
                cls="xs",
            ),
            col(
                term(
                    "what the container actually sees",
                    """kubectl exec deploy/vote -n vote -- ls -l /etc/vote
# banner.txt -> ..data/banner.txt   (a symlink)
# ..data     -> ..2026_07_19_10_31.1234  (atomic swap)

kubectl exec deploy/vote -n vote -- cat /etc/vote/banner.txt
# ITI DevOps 2026 -- vote responsibly""",
                    cls="xs",
                ),
                note(
                    "n-warn",
                    "Mounting at <code>mountPath</code> <b>replaces</b> the whole directory. "
                    "Mount over <code>/etc</code> and you have just deleted "
                    "<code>/etc/passwd</code> as far as that container is concerned. Mount "
                    "into a dedicated directory, or use <code>subPath</code> to place a "
                    "single file &mdash; but note <code>subPath</code> files "
                    "<b>never</b> auto-update.",
                ),
            ),
            ratio="1fr 1fr",
            gap=30,
        ),
        eyebrow="Path 2 &middot; files",
        kicker="Each key becomes a file; each value becomes that file&rsquo;s contents.",
        notes=(
            "This is the path for anything that is genuinely a config file &mdash; nginx.conf, "
            "application.yaml, a certificate bundle. Show the symlink dance: the kubelet writes "
            "a new timestamped directory and flips the ..data symlink, which is how updates are "
            "atomic. Hammer the two traps: mounting over a real directory, and subPath freezing "
            "the file forever."
        ),
        day=D,
    ),
    # ---- teach 5: the two injection paths, contrasted
    slide(
        "env vars vs mounted files &mdash; pick deliberately",
        two(
            col(
                cards(
                    [
                        (
                            "&#128221;",
                            "As environment variables",
                            "ConfigMap &rarr; <code>env</code> &rarr; the process environment, "
                            "read <b>once at container start</b>.",
                            "t-amber",
                        )
                    ],
                    cols=1,
                )
                + table(
                    ["", "Behaviour"],
                    [
                        ["Read when", "Container starts &mdash; once"],
                        ["On CM change", "<b>Nothing.</b> Stale until restart"],
                        ["Refresh with", "<code>kubectl rollout restart</code>"],
                        ["Best for", "Flags, hostnames, log levels, ports"],
                        ["Watch out", "Leaks into <code>printenv</code>, crash dumps, child processes"],
                    ],
                ),
            ),
            col(
                cards(
                    [
                        (
                            "&#128193;",
                            "As mounted files",
                            "ConfigMap &rarr; volume &rarr; files on disk, re-read whenever "
                            "<b>the app</b> chooses to.",
                            "t-teal",
                        )
                    ],
                    cols=1,
                )
                + table(
                    ["", "Behaviour"],
                    [
                        ["Read when", "Whenever the app opens the file"],
                        ["On CM change", "kubelet updates the file (~1 min)"],
                        ["Refresh with", "Nothing &mdash; <i>if</i> the app re-reads"],
                        ["Best for", "Real config files, certs, large blobs"],
                        ["Watch out", "<code>subPath</code> mounts never update"],
                    ],
                ),
            ),
            ratio="1fr 1fr",
            gap=30,
        )
        + note(
            "n-warn",
            "The file on disk updating is <b>not</b> the same as the app noticing. Most apps "
            "read their config once at boot. A mounted ConfigMap that changes still needs a "
            "<code>rollout restart</code> unless the app watches the file itself.",
            title="The half-truth",
            style="margin-top:16px",
        ),
        eyebrow="Diagram &middot; two injection paths",
        kicker="Same object, two delivery mechanisms &mdash; and very different update behaviour.",
        notes=(
            "This is the slide to point back at all day. Left column is frozen at container "
            "start; right column is live on disk but only useful if the app re-reads it. Ask the "
            "room which one the vote app uses &mdash; env, so a ConfigMap edit alone will do "
            "nothing, which is exactly the next lab."
        ),
        day=D,
    ),
    # ---- lab 1: vote options via ConfigMap (env)
    lab(
        "Vote options from a ConfigMap &mdash; and watch them go stale",
        two(
            term(
                "1 &middot; create and wire",
                """# vote/app.py: os.getenv('OPTION_A', "Cats")
kubectl create configmap vote-config -n vote \\
  --from-literal=OPTION_A=Tea \\
  --from-literal=OPTION_B=Coffee

# wire every key in as env vars
kubectl set env deployment/vote -n vote \\
  --from=configmap/vote-config
kubectl rollout status deployment/vote -n vote

# see what that actually wrote
kubectl get deployment vote -n vote \\
  -o jsonpath='{.spec.template.spec.containers[0].env}' | tr ',' '\\n'

# see the UI: http://localhost:8080
kubectl port-forward svc/vote 8080:80 -n vote""",
                cls="xs",
            ),
            col(
                term(
                    "2 &middot; change it and be disappointed",
                    """# edit the ConfigMap in place
kubectl create configmap vote-config -n vote \\
  --from-literal=OPTION_A=Vim \\
  --from-literal=OPTION_B=Emacs \\
  --dry-run=client -o yaml \\
  | kubectl apply -f -

kubectl get configmap vote-config -n vote -o yaml
# data says Vim / Emacs

# refresh the browser -- STILL Tea / Coffee
kubectl exec deploy/vote -n vote -- printenv OPTION_A
# Tea      <- the Pod never heard about it

# the only cure: new Pods
kubectl rollout restart deployment/vote -n vote
kubectl rollout status deployment/vote -n vote
# refresh -> Vim vs Emacs""",
                    cls="xs",
                ),
                note(
                    "n-warn",
                    "<b>Editing a ConfigMap does not restart anything.</b> Env vars are copied "
                    "into the container at start and are frozen for its lifetime. "
                    "<code>kubectl rollout restart</code> is the answer, and it is why "
                    "config-change deploys are still deploys.",
                    title="Confusion #6",
                ),
            ),
            ratio="1fr 1.05fr",
            gap=28,
        ),
        eyebrow="Lab 16 &middot; ConfigMap as env",
        kicker="Change two words in a ConfigMap and change what 25 students see on screen.",
        notes=(
            "Make them do step 2 before you explain it &mdash; the disappointment is the lesson. "
            "Everyone will assume the UI updates; it does not, and printenv proves why. Then "
            "rollout restart and let the room see Vim vs Emacs appear. Note that `set env "
            "--from=configmap` writes configMapKeyRef entries, not envFrom &mdash; show them "
            "the jsonpath output so the YAML from the teach slide is recognisable."
        ),
        day=D,
    ),
    # ---- lab 2: mounted file
    lab(
        "Mount a ConfigMap as a file &mdash; and watch it update itself",
        two(
            term(
                "1 &middot; create and mount",
                """cat > banner.txt <<'EOF'
ITI DevOps 2026 -- vote responsibly
EOF
kubectl create configmap vote-banner -n vote \\
  --from-file=banner.txt

# strategic merge: containers are matched BY NAME,
# so the container name must be exactly `vote`
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
kubectl rollout status deployment/vote -n vote""",
                cls="xs",
            ),
            col(
                term(
                    "2 &middot; read it, change it, re-read it",
                    """kubectl exec deploy/vote -n vote -- ls -l /etc/vote
# banner.txt -> ..data/banner.txt

kubectl exec deploy/vote -n vote -- cat /etc/vote/banner.txt
# ITI DevOps 2026 -- vote responsibly

# change the ConfigMap -- do NOT restart anything
kubectl edit configmap vote-banner -n vote
#   ... change the text, save, quit

# wait up to ~60s (kubelet sync period), then:
kubectl exec deploy/vote -n vote -- cat /etc/vote/banner.txt
# the new text -- same Pod, no restart""",
                    cls="xs",
                ),
                note(
                    "n-tip",
                    "Same Pod, same container, new file contents. Contrast this out loud with "
                    "the previous lab: <b>mounted files update, env vars do not</b>. Neither "
                    "makes the application re-read its config &mdash; that part is the "
                    "app&rsquo;s job.",
                ),
            ),
            ratio="1fr 1fr",
            gap=28,
        ),
        eyebrow="Lab 16b &middot; ConfigMap as a volume",
        kicker="The other injection path, and the other half of the update story.",
        notes=(
            "Check the Pod name before and after so nobody claims it restarted. The wait is "
            "real &mdash; the kubelet syncs on its own cadence, up to about a minute, so use "
            "the time to answer questions. If someone asks why the mount is a symlink, that is "
            "how the kubelet swaps the whole directory atomically."
        ),
        day=D,
    ),
]

# ============================================================== secret (7)
secret = [
    # ---- teach 1: what a Secret is
    slide(
        "Secrets &mdash; ConfigMaps with better manners",
        two(
            col(
                cards(
                    [
                        (
                            "&#128274;",
                            "Same shape, different handling",
                            "Key/value, namespaced, injected as env or files &mdash; identical "
                            "mechanics to a ConfigMap.",
                            "t-slate",
                        ),
                        (
                            "&#128065;",
                            "Kept out of casual view",
                            "Values are base64 in the API and are not printed by "
                            "<code>describe</code>. That is discretion, not defence.",
                            "t-amber",
                        ),
                        (
                            "&#128190;",
                            "Never written to node disk",
                            "The kubelet holds Secret volumes in <code>tmpfs</code> &mdash; RAM, "
                            "not disk &mdash; and drops them when the Pod dies.",
                            "t-blue",
                        ),
                        (
                            "&#128683;",
                            "RBAC is the real control",
                            "Anyone who can <code>get secrets</code> in a namespace can read "
                            "every secret in it. Lock down the verb, not the encoding.",
                            "t-maroon",
                        ),
                    ],
                    cols=2,
                )
            ),
            col(
                term(
                    "create and inspect",
                    """kubectl create secret generic db-secret -n vote \\
  --from-literal=POSTGRES_USER=postgres \\
  --from-literal=POSTGRES_PASSWORD='S3cure-ITI-2026'

kubectl describe secret db-secret -n vote
# Data
# ====
# POSTGRES_PASSWORD:  15 bytes
# POSTGRES_USER:      8 bytes
#          ^ lengths only, no values""",
                    cls="xs",
                ),
                note(
                    "n-tip",
                    "Writing Secret YAML by hand? Use <code>stringData:</code> instead of "
                    "<code>data:</code> and Kubernetes does the base64 for you. It never shows "
                    "up in the stored object.",
                ),
            ),
            ratio="1.15fr 1fr",
            gap=30,
        ),
        eyebrow="19 &middot; Configuration",
        kicker="A Secret is a ConfigMap that the platform agrees to be quieter about.",
        notes=(
            "Set expectations early: a Secret is not a vault. What you gain is that values stay "
            "out of describe output and logs, volumes live in tmpfs, and access is a separate "
            "RBAC verb. What you do not gain is encryption &mdash; that is the very next slide "
            "and the single biggest misconception in this whole course."
        ),
        day=D,
    ),
    # ---- teach 2: types
    slide(
        "Secret types &mdash; three you will actually meet",
        table(
            ["<code>type</code>", "Created with", "What it holds", "Consumed by"],
            [
                [
                    "<code>Opaque</code>",
                    "<code>create secret generic</code>",
                    "Arbitrary key/value &mdash; the default, and 90% of what you write",
                    "Your Pods, via env or volume",
                ],
                [
                    "<code>kubernetes.io/dockerconfigjson</code>",
                    "<code>create secret docker-registry</code>",
                    "Registry host, username, password &mdash; stored as a Docker "
                    "<code>config.json</code>",
                    "The kubelet, via <code>imagePullSecrets</code>",
                ],
                [
                    "<code>kubernetes.io/tls</code>",
                    "<code>create secret tls</code>",
                    "Exactly two keys: <code>tls.crt</code> and <code>tls.key</code>",
                    "Ingress controllers, for HTTPS",
                ],
                [
                    "<code>kubernetes.io/service-account-token</code>",
                    "The control plane",
                    "A ServiceAccount JWT for talking to the API server",
                    "Mounted automatically into Pods",
                ],
            ],
        )
        + term(
            "the two you will type most",
            """# pull from a private registry
kubectl create secret docker-registry regcred -n vote \\
  --docker-server=registry.example.com \\
  --docker-username=iti --docker-password='...'
# then in the Pod spec:  imagePullSecrets: [{name: regcred}]

# TLS for an Ingress (Day 4)
kubectl create secret tls vote-tls -n vote \\
  --cert=tls.crt --key=tls.key""",
            cls="xs",
        ),
        eyebrow="Types",
        kicker="The <code>type</code> field is a contract: it tells Kubernetes which keys must exist.",
        notes=(
            "The type is not decoration &mdash; a kubernetes.io/tls Secret is rejected unless it "
            "has exactly tls.crt and tls.key, and imagePullSecrets only accepts a "
            "dockerconfigjson. Mention the ServiceAccount token so they recognise the one Secret "
            "they never created. On modern clusters those tokens are projected, not stored, but "
            "they will still see the type."
        ),
        day=D,
    ),
    # ---- teach 3: base64 is not encryption
    slide(
        "base64 is an <i>encoding</i>, not encryption",
        two(
            term(
                "prove it in five seconds",
                """kubectl get secret db-secret -n vote -o yaml
# data:
#   POSTGRES_PASSWORD: UzNjdXJlLUlUSS0yMDI2

echo 'UzNjdXJlLUlUSS0yMDI2' | base64 -d
# S3cure-ITI-2026

# no key. no password. no permission beyond `get`.
echo -n 'S3cure-ITI-2026' | base64
# UzNjdXJlLUlUSS0yMDI2   <- round trip""",
                cls="xs",
            ),
            col(
                cards(
                    [
                        (
                            "&#10060;",
                            "What base64 is not",
                            "It has no key, no algorithm choice and no secret. It exists so "
                            "binary data survives a text field &mdash; nothing more.",
                            "t-maroon",
                        ),
                        (
                            "&#128193;",
                            "So: never commit Secret YAML",
                            "A base64 blob in git is a plaintext password in git. Use Sealed "
                            "Secrets, SOPS, or an external store (Vault, AWS Secrets Manager).",
                            "t-amber",
                        ),
                        (
                            "&#128273;",
                            "What actually protects it",
                            "RBAC on <code>get secrets</code>, encryption at rest in etcd, and "
                            "not putting the value on a laptop in the first place.",
                            "t-green",
                        ),
                    ],
                    cols=1,
                )
            ),
            ratio="1fr 1fr",
            gap=30,
        )
        + note(
            "n-warn",
            "If you remember one thing from this section: <b>base64 is not security</b>. "
            "Every student decodes a password themselves in the lab &mdash; because being told "
            "and doing it are not the same lesson.",
            title="Confusion #3",
            style="margin-top:16px",
        ),
        eyebrow="The big misconception",
        kicker="Everyone assumes the blob is protected. It is a reversible text transform with "
        "no key at all.",
        notes=(
            "Do not let this be a slide they nod along to. In the lab they decode a real "
            "password with one command. Ask afterwards who would have committed that YAML to "
            "git &mdash; hands go up, and the point lands. Then name the real answers: RBAC, "
            "encryption at rest, and an external secret store."
        ),
        day=D,
    ),
    # ---- teach 4: as env vars
    slide(
        "Consuming a Secret as environment variables",
        two(
            term(
                "secretKeyRef &mdash; and renaming on the way in",
                """spec:
  containers:
  - name: result
    image: result:v1
    env:
    - name: DB_HOST
      value: db                    # a plain literal
    - name: DB_USER                # what the app reads
      valueFrom:
        secretKeyRef:
          name: db-secret          # which Secret
          key: POSTGRES_USER       # what the Secret calls it
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: POSTGRES_PASSWORD

    # or take every key at once:
    envFrom:
    - secretRef: {name: db-secret}""",
                cls="xs",
            ),
            col(
                note(
                    "n-info",
                    "Note the rename: the Secret stores <code>POSTGRES_USER</code> because that "
                    "is what the <code>postgres</code> image needs, while <code>result</code> "
                    "and <code>worker</code> read <code>DB_USER</code>. "
                    "<b>One Secret, three consumers, three vocabularies.</b>",
                ),
                note(
                    "n-warn",
                    "Environment variables are the leakiest path. They show up in "
                    "<code>printenv</code>, in <code>kubectl describe pod</code> as a reference, "
                    "in crash dumps, and are inherited by every child process the container "
                    "spawns. For high-value secrets, prefer a mounted volume.",
                ),
                note(
                    "n-tip",
                    "A missing key fails the Pod at start with "
                    "<code>CreateContainerConfigError</code> &mdash; not a silent empty string. "
                    "Add <code>optional: true</code> only when you genuinely mean it.",
                ),
            ),
            ratio="1.05fr 1fr",
            gap=30,
        ),
        eyebrow="Path 1 &middot; environment",
        kicker="Identical to <code>configMapKeyRef</code> &mdash; only the field name changes.",
        notes=(
            "Once they have seen ConfigMap env injection, this slide is two minutes. Spend the "
            "time instead on the rename idea &mdash; the key name and the env var name are "
            "independent, which is exactly how one db-secret feeds postgres, result and worker "
            "at once. Then warn honestly that env vars leak; CreateContainerConfigError is the "
            "error they will actually hit."
        ),
        day=D,
    ),
    # ---- teach 5: as volume + etcd at rest
    slide(
        "Consuming a Secret as a mounted volume",
        two(
            term(
                "volume &middot; tmpfs, mode 0400",
                """spec:
  containers:
  - name: app
    volumeMounts:
    - name: creds
      mountPath: /etc/creds
      readOnly: true
  volumes:
  - name: creds
    secret:
      secretName: db-secret
      defaultMode: 0400        # owner read only
      items:                   # project a subset
      - key: POSTGRES_PASSWORD
        path: password""",
                cls="xs",
            ),
            col(
                cards(
                    [
                        (
                            "&#128190;",
                            "tmpfs, never the node disk",
                            "Secret volumes are RAM-backed. The Pod dies, the memory goes &mdash; "
                            "nothing left on the node to forensically recover.",
                            "t-blue",
                        ),
                        (
                            "&#128260;",
                            "Updates propagate",
                            "Like ConfigMap volumes, the file is refreshed within about a minute. "
                            "Env vars still will not budge.",
                            "t-teal",
                        ),
                    ],
                    cols=1,
                ),
                note(
                    "n-info",
                    "<b>Encryption at rest &mdash; awareness only.</b> By default etcd stores "
                    "Secret values as plain base64 on the control-plane disk. A cluster admin "
                    "enables an <code>EncryptionConfiguration</code> (AES-CBC or a KMS provider) "
                    "so the API server encrypts before writing. Managed clusters (EKS, GKE, AKS) "
                    "offer this as a checkbox &mdash; it is off unless someone turned it on.",
                    title="etcd",
                ),
            ),
            ratio="1fr 1.1fr",
            gap=30,
        ),
        eyebrow="Path 2 &middot; files",
        kicker="The safer path: files on a RAM disk, readable by the process and nobody else.",
        notes=(
            "Give them the rule of thumb: env vars for convenience, volumes for anything you "
            "would be embarrassed to see in a log. Then the etcd point &mdash; base64 in the API "
            "means base64 on the control-plane disk unless encryption at rest is configured. "
            "This is awareness level; they are not enabling it today, but they should ask about "
            "it on any cluster they inherit."
        ),
        day=D,
    ),
    # ---- lab 1: move the password into a Secret
    lab(
        "Move <code>POSTGRES_PASSWORD</code> into a Secret",
        two(
            term(
                "1 &middot; create it, feed the database",
                """kubectl create secret generic db-secret -n vote \\
  --from-literal=POSTGRES_USER=postgres \\
  --from-literal=POSTGRES_PASSWORD='S3cure-ITI-2026'

# the postgres image wants POSTGRES_* -- exact key match,
# so envFrom-style injection is enough here
kubectl set env deployment/db -n vote --from=secret/db-secret
kubectl rollout status deployment/db -n vote

kubectl describe deployment db -n vote | grep -A3 Environment
# POSTGRES_PASSWORD:  <set to the key ... in secret db-secret>
#                     ^ a reference, never the value""",
                cls="xs",
            ),
            col(
                term(
                    "2 &middot; feed the two clients (renamed keys)",
                    """# result + worker read DB_HOST / DB_USER / DB_PASSWORD
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
kubectl logs deploy/worker -n vote | tail -5   # Connected to db""",
                    cls="xs",
                ),
            ),
            ratio="1fr 1.2fr",
            gap=26,
        )
        + note(
            "n-warn",
            "<code>POSTGRES_PASSWORD</code> is only applied when the data directory is "
            "<b>initialised</b>. Right now <code>db</code> has no persistent volume, so the "
            "replacement Pod runs <code>initdb</code> fresh and picks up the new password. Once "
            "it has a PVC (two labs from now), changing this variable does nothing &mdash; you "
            "would need <code>ALTER USER</code> inside the database.",
            title="Real-world gotcha",
            style="margin-top:14px",
        ),
        eyebrow="Lab 17 &middot; Secrets",
        kicker="One Secret, three consumers &mdash; and the whole app follows the change.",
        notes=(
            "This is the lab that makes Secrets feel real rather than decorative: change the "
            "value and vote, result and worker all move together. Point out the key rename "
            "&mdash; POSTGRES_USER in the Secret becomes DB_USER in the container. The initdb "
            "warning is the one that will bite them in a real job, so say it twice."
        ),
        day=D,
    ),
    # ---- lab 2: prove base64 is not encryption
    lab(
        "Prove it yourself: decode the password",
        two(
            term(
                "1 &middot; three ways to read a &lsquo;secret&rsquo;",
                """# the raw object
kubectl get secret db-secret -n vote -o yaml

# decode by hand
kubectl get secret db-secret -n vote \\
  -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d; echo
# S3cure-ITI-2026

# or let kubectl do it for you
kubectl get secret db-secret -n vote \\
  -o go-template='{{ .data.POSTGRES_PASSWORD | base64decode }}'; echo

# or just ask the running container
kubectl exec deploy/result -n vote -- printenv DB_PASSWORD""",
                cls="xs",
            ),
            col(
                term(
                    "2 &middot; and the one thing that does help",
                    """# who can read secrets in this namespace?
kubectl auth can-i get secrets -n vote
kubectl auth can-i get secrets -n vote \\
  --as=system:serviceaccount:vote:default

# describe stays quiet -- lengths only, no values
kubectl describe secret db-secret -n vote

# a Secret volume is RAM, not disk
kubectl exec deploy/result -n vote -- df -h /etc/creds 2>/dev/null \\
  || echo 'no secret volume mounted on result (env only)'""",
                    cls="xs",
                ),
                note(
                    "n-warn",
                    "You just read a production-shaped password with one command and no "
                    "credentials beyond <code>get</code>. <b>base64 is encoding, not "
                    "encryption.</b> The protections that matter are RBAC, encryption at rest, "
                    "and keeping Secret YAML out of git.",
                    title="Confusion #3",
                ),
            ),
            ratio="1fr 1fr",
            gap=28,
        ),
        eyebrow="Lab 17b &middot; base64 &ne; encryption",
        kicker="Two minutes that permanently fix the most common Kubernetes misconception.",
        notes=(
            "Everyone runs the base64 -d themselves &mdash; do not demo it from the front. Then "
            "ask: who was about to commit a Secret manifest to git this week? That is the moment "
            "the lesson sticks. Close with kubectl auth can-i, because RBAC is the control they "
            "should actually be reaching for."
        ),
        day=D,
    ),
]

# ========================================================= emptydir_lab (2)
emptydir_lab = [
    lab(
        "emptyDir &mdash; cast votes, kill the Pod, lose the data",
        two(
            term(
                "1 &middot; give redis a scratch volume, then queue votes",
                """kubectl patch deployment redis -n vote --type=strategic -p "$(cat <<'EOF'
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

# stop the drain so votes PILE UP in redis
kubectl scale deployment/worker -n vote --replicas=0

# now cast 5-6 votes in the UI
kubectl port-forward svc/vote 8080:80 -n vote""",
                cls="xs",
            ),
            col(
                term(
                    "2 &middot; watch them vanish",
                    """kubectl exec deploy/redis -n vote -- redis-cli LLEN votes
# (integer) 6      <- queued, not yet in postgres

kubectl delete pod -l app=redis -n vote
kubectl rollout status deployment/redis -n vote

kubectl exec deploy/redis -n vote -- redis-cli LLEN votes
# (integer) 0      <- gone. every queued vote.

# put the drain back
kubectl scale deployment/worker -n vote --replicas=1""",
                    cls="xs",
                ),
                note(
                    "n-warn",
                    "<b>An <code>emptyDir</code> lives and dies with the Pod, not the "
                    "container.</b> Crash the container and the data is still there; delete the "
                    "Pod and the directory is deleted with it. Scratch space, cache, sidecar "
                    "hand-off &mdash; never your only copy of anything.",
                    title="Confusion #12",
                ),
            ),
            ratio="1.1fr 1fr",
            gap=28,
        ),
        eyebrow="Lab 18 &middot; Ephemeral storage",
        kicker="Six votes in, one <code>delete pod</code>, zero votes out.",
        notes=(
            "Scaling worker to zero is the trick that makes this visible &mdash; otherwise the "
            "worker drains redis into postgres and there is nothing to lose. Do not skip the "
            "rollout status before the second LLEN or you will query the old terminating Pod and "
            "confuse everyone. If someone asks about container vs Pod, kill PID 1 in the "
            "container and show the data surviving that."
        ),
        day=D,
    ),
    slide(
        "What survives what",
        table(
            ["Storage", "Container crash", "Pod deleted", "Node lost", "Use it for"],
            [
                [
                    "Container filesystem",
                    "&#10060; gone",
                    "&#10060; gone",
                    "&#10060; gone",
                    "Nothing you care about",
                ],
                [
                    "<code>emptyDir</code>",
                    "&#9989; survives",
                    "&#10060; gone",
                    "&#10060; gone",
                    "Cache, scratch, sidecar hand-off",
                ],
                [
                    "<code>hostPath</code>",
                    "&#9989; survives",
                    "&#9989; survives",
                    "&#10060; gone &mdash; and stuck to one node",
                    "Node agents, log shippers",
                ],
                [
                    "<b>PVC</b> (PersistentVolume)",
                    "&#9989; survives",
                    "&#9989; survives",
                    "&#9989; reattached elsewhere",
                    "Databases, uploads, anything real",
                ],
            ],
        )
        + note(
            "n-why",
            "The Pod is the unit of scheduling and therefore the unit of disposal. Anything "
            "whose lifetime must be longer than a Pod&rsquo;s has to be stored <b>outside</b> the "
            "Pod and attached to it &mdash; which is exactly what a PersistentVolumeClaim is.",
            style="margin-top:16px",
        )
        + note(
            "n-tip",
            "Read the table as a ladder. You just fell off rung two live in front of the room. "
            "The next section climbs to rung four and gives Postgres a disk that outlives it.",
        ),
        eyebrow="Why PersistentVolumes exist",
        kicker="Four storage options, four different answers to &ldquo;is my data still there?&rdquo;",
        notes=(
            "Put this straight after the emptyDir loss while the sting is fresh. Walk the "
            "columns left to right and make them predict each cell before you reveal it. The "
            "hostPath row is the trap that looks durable in a one-node kind cluster and destroys "
            "data the moment a Pod reschedules &mdash; call that out explicitly."
        ),
        day=D,
    ),
]

# ========================================================= storage_extra (2)
storage_extra = [
    slide(
        "accessModes &mdash; who may mount this volume",
        table(
            ["Mode", "Short", "Meaning", "Typical backing"],
            [
                [
                    "<code>ReadWriteOnce</code>",
                    "RWO",
                    "Mounted read-write by <b>one node</b>. Several Pods <i>on that node</i> may "
                    "share it &mdash; this is the one everyone misreads",
                    "AWS EBS, GCE PD, local-path",
                ],
                [
                    "<code>ReadOnlyMany</code>",
                    "ROX",
                    "Mounted read-only by many nodes at once",
                    "NFS, pre-populated content volumes",
                ],
                [
                    "<code>ReadWriteMany</code>",
                    "RWX",
                    "Mounted read-write by many nodes at once &mdash; genuine shared storage",
                    "NFS, CephFS, EFS, Azure Files",
                ],
                [
                    "<code>ReadWriteOncePod</code>",
                    "RWOP",
                    "Exactly <b>one Pod</b> in the whole cluster. K8s 1.29+, CSI only",
                    "CSI drivers that support it",
                ],
            ],
        )
        + note(
            "n-warn",
            "<b>RWO means one <i>node</i>, not one <i>Pod</i>.</b> Two Pods scheduled to the same "
            "node can both mount an RWO volume and happily corrupt each other&rsquo;s data. If "
            "you need real single-writer exclusivity, that is what <code>ReadWriteOncePod</code> "
            "was invented for.",
            title="The classic misread",
            style="margin-top:16px",
        )
        + note(
            "n-info",
            "accessModes is a <b>matching hint</b>, not an enforcement layer. The scheduler uses "
            "it to bind a PVC to a PV and to place Pods; the storage backend is what actually "
            "does or does not support concurrent mounts. Ask for RWX on EBS and the PVC simply "
            "never binds.",
        ),
        eyebrow="21 &middot; Storage",
        kicker="Four modes, and the most common misreading in all of Kubernetes storage.",
        notes=(
            "Spend your time on RWO. Everyone reads it as one Pod; it is one node, and that "
            "difference is why a rolling update of a database can silently run two writers "
            "against one disk. That is also why the PVC lab sets strategy Recreate. RWX is the "
            "one people want and rarely have &mdash; EBS cannot do it, NFS and EFS can."
        ),
        day=D,
    ),
    slide(
        "Reclaim policy, binding modes, and the Pending PVC",
        two(
            col(
                table(
                    ["<code>persistentVolumeReclaimPolicy</code>", "When the PVC is deleted"],
                    [
                        [
                            "<code>Delete</code>",
                            "The PV <b>and the real disk</b> are destroyed. Default for "
                            "dynamically provisioned volumes",
                        ],
                        [
                            "<code>Retain</code>",
                            "The PV stays, marked <code>Released</code>, data intact. An admin "
                            "must clean it up by hand before it is reusable",
                        ],
                    ],
                ),
                note(
                    "n-warn",
                    "Default StorageClasses usually reclaim with <code>Delete</code>. "
                    "<code>kubectl delete pvc pgdata</code> can therefore delete a production "
                    "database in one keystroke. Set <code>Retain</code> on anything you would "
                    "miss.",
                ),
            ),
            col(
                table(
                    ["<code>volumeBindingMode</code>", "When the PV is created"],
                    [
                        [
                            "<code>Immediate</code>",
                            "As soon as the PVC exists &mdash; possibly in a zone where your Pod "
                            "cannot be scheduled",
                        ],
                        [
                            "<code>WaitForFirstConsumer</code>",
                            "Only when a Pod actually needs it, so the volume lands where the Pod "
                            "does. kind&rsquo;s default",
                        ],
                    ],
                ),
                note(
                    "n-warn",
                    "<b>A PVC sitting in <code>Pending</code> with no Pod is normal</b> under "
                    "<code>WaitForFirstConsumer</code> &mdash; that is the design, not a fault. "
                    "It is only a bug when a Pod <i>is</i> waiting on it. "
                    "<code>kubectl describe pvc</code> tells you which case you are in.",
                    title="Confusion #10",
                ),
            ),
            ratio="1fr 1fr",
            gap=30,
        )
        + term(
            "the three commands that diagnose every storage problem",
            """kubectl get sc                       # which classes exist, which is default
kubectl get pvc,pv -n vote           # bound? pending? released?
kubectl describe pvc pgdata -n vote  # the Events tail says WHY""",
            cls="xs",
        ),
        eyebrow="Lifecycle",
        kicker="Two settings that decide whether your data outlives the claim &mdash; and why "
        "Pending is not always broken.",
        notes=(
            "Reclaim policy is a career-saver: tell them the story of deleting a namespace and "
            "taking the database with it, because Delete is the default. Then WaitForFirstConsumer "
            "&mdash; students panic at a Pending PVC, but with no Pod referencing it Pending is "
            "correct behaviour. Drill the three diagnostic commands; they reappear in the planted "
            "failure at the end of the day."
        ),
        day=D,
    ),
]

# ============================================================== vapvc (2)
vapvc = [
    lab(
        "Give Postgres a PersistentVolumeClaim",
        two(
            term(
                "1 &middot; claim a disk",
                """kubectl get sc
# NAME                 PROVISIONER             ...
# standard (default)   rancher.io/local-path   ...

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
# STATUS: Pending -- correct, nothing consumes it yet""",
                cls="xs",
            ),
            col(
                term(
                    "2 &middot; mount it into db",
                    """kubectl patch deployment db -n vote --type=strategic -p "$(cat <<'EOF'
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
kubectl get pvc pgdata -n vote      # now Bound""",
                    cls="xs",
                ),
                note(
                    "n-info",
                    "Two deliberate details. <code>strategy: Recreate</code> because an RWO "
                    "volume cannot follow a rolling update across nodes. "
                    "<code>PGDATA</code> points at a <b>subdirectory</b> because some volume "
                    "types hand you a non-empty root and <code>initdb</code> refuses to run in "
                    "one.",
                ),
            ),
            ratio="1fr 1.15fr",
            gap=26,
        ),
        eyebrow="Lab 19 &middot; PVC",
        kicker="Supply and demand: the PVC asks, the StorageClass provisions, the Pod mounts.",
        notes=(
            "Have them run get pvc between the two steps so they see Pending, then Bound &mdash; "
            "that is WaitForFirstConsumer doing exactly what the previous slide described. "
            "Explain Recreate and PGDATA rather than letting them copy blindly; both are the "
            "kind of detail that separates a working manifest from a mysterious CrashLoopBackOff."
        ),
        day=D,
    ),
    lab(
        "Kill the database Pod &mdash; keep the votes",
        two(
            term(
                "1 &middot; vote, then verify the tally",
                """# the db just re-initialised on a fresh disk,
# so cast a handful of NEW votes now
kubectl port-forward svc/vote 8080:80 -n vote
# ... vote a few times, then Ctrl-C

kubectl exec deploy/db -n vote -- \\
  psql -U postgres -c 'select vote, count(*) from votes group by vote;'
#  vote | count
# ------+-------
#  a    |     4
#  b    |     2""",
                cls="xs",
            ),
            col(
                term(
                    "2 &middot; delete it and prove durability",
                    """kubectl get pod -l app=db -n vote -o wide

kubectl delete pod -l app=db -n vote
kubectl wait --for=condition=ready pod -l app=db -n vote --timeout=180s

kubectl get pod -l app=db -n vote
# a NEW Pod name, a NEW IP, the SAME PVC

kubectl exec deploy/db -n vote -- \\
  psql -U postgres -c 'select vote, count(*) from votes group by vote;'
#  a | 4
#  b | 2      <- survived

kubectl get pvc pgdata -n vote     # still Bound""",
                    cls="xs",
                ),
                note(
                    "n-tip",
                    "Run the same thing against <code>redis</code> for contrast: kill the redis "
                    "Pod and the queue is still gone. Same cluster, same command, different "
                    "storage &mdash; that is the whole point of the last hour.",
                ),
            ),
            ratio="1fr 1.15fr",
            gap=26,
        ),
        eyebrow="Lab 19b &middot; Durability",
        kicker="New Pod, new IP, same data. The claim outlived the thing that mounted it.",
        notes=(
            "Make them note the old Pod name before deleting, so the new name is unmistakable. "
            "The psql works without a password because the official image trusts local socket "
            "connections inside the container &mdash; worth one sentence so nobody thinks the "
            "Secret failed. End by contrasting with redis: identical command, opposite outcome."
        ),
        day=D,
    ),
]

# ========================================================== statefulset (2)
statefulset = [
    slide(
        "Why <code>db</code> is not like the others",
        two(
            col(
                cards(
                    [
                        (
                            "&#9851;",
                            "Deployment &mdash; interchangeable",
                            "Pods are cattle: random names, random IPs, any order, any node. "
                            "Perfect for <code>vote</code>, <code>result</code>, "
                            "<code>worker</code>.",
                            "t-slate",
                        ),
                        (
                            "&#128290;",
                            "StatefulSet &mdash; identity matters",
                            "Pods are <code>db-0</code>, <code>db-1</code>, <code>db-2</code>: "
                            "stable names, stable storage, deterministic order.",
                            "t-violet",
                        ),
                    ],
                    cols=1,
                ),
                table(
                    ["", "Deployment", "StatefulSet"],
                    [
                        ["Pod names", "<code>db-7f9c-x2k</code>", "<code>db-0</code>, <code>db-1</code>"],
                        ["Identity across restarts", "New name each time", "Same name, same disk"],
                        ["Start / stop order", "All at once", "Ordinal: 0, then 1, then 2"],
                        ["Storage", "One shared PVC (or none)", "One PVC <b>per replica</b>"],
                        ["DNS", "Via the Service only", "Per-Pod DNS name"],
                    ],
                ),
            ),
            col(
                term(
                    "the two fields that make it a StatefulSet",
                    """apiVersion: apps/v1
kind: StatefulSet
metadata: {name: db}
spec:
  serviceName: db-headless   # the paired headless Service
  replicas: 3
  selector:
    matchLabels: {app: db}
  template:
    metadata:
      labels: {app: db}
    spec:
      containers:
      - name: db
        image: postgres:14
        volumeMounts:
        - {name: pgdata, mountPath: /var/lib/postgresql/data}
  volumeClaimTemplates:      # one PVC PER replica,
  - metadata: {name: pgdata} # created automatically
    spec:
      accessModes: [ReadWriteOnce]
      resources: {requests: {storage: 1Gi}}""",
                    cls="xs",
                )
            ),
            ratio="1fr 1.05fr",
            gap=30,
        ),
        eyebrow="22 &middot; StatefulSets",
        kicker="Awareness level &mdash; enough to recognise one and know why a database wants it.",
        notes=(
            "Keep this at recognition level; a real StatefulSet deep-dive is a course of its own. "
            "The single sentence they must leave with: a Deployment gives you interchangeable "
            "Pods, a StatefulSet gives you Pods with names and disks that stick. Note that we "
            "keep db as a Deployment today because one replica plus a PVC is simpler for the lab."
        ),
        day=D,
    ),
    slide(
        "Stable identity needs a headless Service",
        two(
            term(
                "headless: clusterIP is None",
                """apiVersion: v1
kind: Service
metadata: {name: db-headless}
spec:
  clusterIP: None        # <- headless: no virtual IP
  selector: {app: db}
  ports:
  - {port: 5432, targetPort: 5432}""",
                cls="xs",
            ),
            col(
                table(
                    ["Query", "Normal ClusterIP Service", "Headless Service"],
                    [
                        [
                            "<code>nslookup db</code>",
                            "One virtual IP, load balanced",
                            "Every Pod IP, no balancing",
                        ],
                        [
                            "<code>nslookup db-0.db-headless</code>",
                            "&#10060; does not exist",
                            "&#9989; that exact Pod&rsquo;s IP",
                        ],
                    ],
                ),
                note(
                    "n-info",
                    "The per-Pod DNS name is "
                    "<code>&lt;pod&gt;.&lt;service&gt;.&lt;ns&gt;.svc.cluster.local</code>. "
                    "That is how a replica set of databases finds its own peers &mdash; "
                    "<code>db-1</code> can address <code>db-0</code> directly and follow it, "
                    "which a load-balanced ClusterIP could never allow.",
                ),
                note(
                    "n-tip",
                    "Rule of thumb: <b>stateless &rarr; Deployment + ClusterIP</b>; "
                    "<b>clustered stateful &rarr; StatefulSet + headless Service</b>. Every "
                    "Postgres, Kafka, Cassandra and Elasticsearch Helm chart you will ever "
                    "install is built exactly this way.",
                ),
            ),
            ratio="0.85fr 1.15fr",
            gap=30,
        ),
        eyebrow="The pairing",
        kicker="A ClusterIP hides which Pod you reached. Replication needs the opposite.",
        notes=(
            "Explain why load balancing is actively wrong here: a replica must connect to one "
            "specific primary, not to whichever Pod the Service picked. clusterIP: None turns "
            "the Service into pure DNS, and the StatefulSet then guarantees the names are stable. "
            "Tell them they have now seen the shape of every stateful Helm chart."
        ),
        day=D,
    ),
]

# ============================================================== probes (8)
probes = [
    # ---- teach 1: what each probe fixes
    slide(
        "Three probes, three different failures",
        cards(
            [
                (
                    "&#128137;",
                    "Liveness &mdash; is it alive?",
                    "<b>Fixes:</b> a process that is running but wedged &mdash; deadlocked "
                    "thread pool, infinite loop, stuck event loop.<br>"
                    "<b>On failure:</b> the kubelet <b>kills and restarts the container</b>.",
                    "t-maroon",
                ),
                (
                    "&#128994;",
                    "Readiness &mdash; can it serve?",
                    "<b>Fixes:</b> traffic arriving before the app can answer &mdash; warmup, "
                    "migrations, a lost downstream dependency.<br>"
                    "<b>On failure:</b> the Pod is <b>removed from Service endpoints</b>. No "
                    "restart.",
                    "t-green",
                ),
                (
                    "&#8987;",
                    "Startup &mdash; has it booted yet?",
                    "<b>Fixes:</b> a slow starter being murdered by its own liveness probe "
                    "&mdash; JVM warmup, big migrations.<br>"
                    "<b>On failure:</b> restarts, but liveness and readiness are "
                    "<b>suspended</b> until it first succeeds.",
                    "t-blue",
                ),
            ]
        )
        + note(
            "n-warn",
            "<b>Liveness restarts. Readiness removes from traffic.</b> Say it back to yourself "
            "before writing any probe. Getting these two backwards is the single most common "
            "probe bug in production, and it turns a brief blip into a cluster-wide restart "
            "storm.",
            title="Confusion #4",
            style="margin-top:16px",
        )
        + note(
            "n-why",
            "Without probes, Kubernetes only knows whether the <b>process</b> is running. It has "
            "no idea whether the <b>application</b> works. Probes are how you teach the platform "
            "what healthy means for your app.",
        ),
        eyebrow="23 &middot; Health",
        kicker="All three are optional. All three are how Kubernetes finds out whether your app "
        "is actually working.",
        notes=(
            "Anchor everything on what each probe FIXES, not on its definition &mdash; that is "
            "what makes them memorable. Ask the room what happens to a Java service whose thread "
            "pool deadlocks: the process is up, the port is open, the container looks perfect, "
            "and every request hangs. Only a liveness probe catches that. Then flip it: a Pod "
            "that is fine but temporarily cannot reach its database should be pulled from "
            "traffic, not restarted."
        ),
        day=D,
    ),
    # ---- teach 2: the timeline
    slide(
        "The probe timeline",
        two(
            col(
                steps(
                    [
                        "<b>t=0 &middot; container starts.</b> With no probes at all the Pod is "
                        "marked <code>Ready</code> right now and traffic arrives immediately "
                        "&mdash; whether or not anything is listening.",
                        "<b>Startup probe runs.</b> Liveness and readiness are held back. It may "
                        "fail up to <code>failureThreshold</code> times "
                        "(&times; <code>periodSeconds</code>) &mdash; that is your entire boot "
                        "budget.",
                        "<b>Startup succeeds &rarr; it never runs again.</b> Liveness and "
                        "readiness now both begin.",
                        "<b>Readiness gates traffic, continuously.</b> Pass &rarr; the Pod is in "
                        "the Service&rsquo;s endpoint list. Fail &rarr; it is pulled out, and "
                        "put back the moment it passes again.",
                        "<b>Liveness watches for wedging, continuously.</b> "
                        "<code>failureThreshold</code> consecutive failures &rarr; the container "
                        "is killed and restarted, and <code>RESTARTS</code> ticks up.",
                    ]
                )
            ),
            col(
                table(
                    ["Probe fails", "What Kubernetes does", "Pod status"],
                    [
                        [
                            "<b>Startup</b>",
                            "Restart the container",
                            "<code>0/1</code>, restarts climbing",
                        ],
                        [
                            "<b>Readiness</b>",
                            "Remove from Service endpoints",
                            "<code>Running 0/1</code>, <b>no</b> restarts",
                        ],
                        [
                            "<b>Liveness</b>",
                            "Kill and restart the container",
                            "<code>RESTARTS</code> increments",
                        ],
                    ],
                ),
                note(
                    "n-tip",
                    "That <code>READY 0/1</code> column students keep asking about is the "
                    "<b>readiness</b> result: <i>containers passing readiness</i> / <i>containers "
                    "in the Pod</i>. A Pod can be <code>Running</code> and <code>0/1</code> "
                    "forever &mdash; running is not ready.",
                ),
                note(
                    "n-warn",
                    "Readiness is not one-shot. It is re-evaluated for the whole life of the Pod, "
                    "which is exactly what lets a Pod quietly leave the load balancer during a "
                    "GC pause and rejoin afterwards.",
                ),
            ),
            ratio="1.05fr 1fr",
            gap=30,
        ),
        eyebrow="Diagram &middot; timeline",
        kicker="startup gates liveness &middot; readiness gates traffic &middot; liveness gates "
        "the container&rsquo;s life.",
        notes=(
            "Draw this on the board as a horizontal line while you talk. The beat that matters "
            "most is step 1: with no probes, Ready means the container process started, nothing "
            "more. That is precisely the bug the payoff lab exposes later. Use the right-hand "
            "table to finally answer the READY 1/1 question from Day 1."
        ),
        day=D,
    ),
    # ---- teach 3: probe types
    slide(
        "Three ways to ask &ldquo;are you healthy?&rdquo;",
        two(
            term(
                "httpGet &middot; exec &middot; tcpSocket",
                """# 1) httpGet -- the default choice for web apps
readinessProbe:
  httpGet:
    path: /healthz
    port: 80
    httpHeaders:
    - {name: X-Probe, value: kubelet}
# healthy = any 2xx or 3xx status code

# 2) exec -- run a command, exit 0 means healthy
readinessProbe:
  exec:
    command: ["pg_isready", "-U", "postgres", "-h", "127.0.0.1"]

# 3) tcpSocket -- can the port be opened at all?
livenessProbe:
  tcpSocket:
    port: 6379
# healthy = the TCP handshake completes""",
                cls="xs",
            ),
            col(
                table(
                    ["Type", "Best for", "Cost", "Catches"],
                    [
                        [
                            "<code>httpGet</code>",
                            "HTTP services &mdash; <code>vote</code>, <code>result</code>",
                            "Cheap",
                            "App-level health, if the endpoint is honest",
                        ],
                        [
                            "<code>exec</code>",
                            "Databases and non-HTTP &mdash; <code>db</code>",
                            "Expensive: forks a process each time",
                            "Anything you can script",
                        ],
                        [
                            "<code>tcpSocket</code>",
                            "Plain TCP &mdash; <code>redis</code>",
                            "Cheapest",
                            "Only that something is listening",
                        ],
                        [
                            "<code>grpc</code>",
                            "gRPC services (1.24+)",
                            "Cheap",
                            "The standard gRPC health protocol",
                        ],
                    ],
                ),
                note(
                    "n-warn",
                    "A <code>/healthz</code> that returns 200 unconditionally is decoration. A "
                    "useful one checks what the request path actually needs. But keep dependency "
                    "checks in <b>readiness</b> only &mdash; a liveness probe that fails because "
                    "the database is down will restart every replica you own while the database "
                    "is already struggling.",
                ),
                note(
                    "n-tip",
                    "<code>exec</code> probes fork a process on every period. On a 1-second "
                    "period across hundreds of Pods that is real CPU. Prefer "
                    "<code>httpGet</code> where you have the choice.",
                ),
            ),
            ratio="0.95fr 1.05fr",
            gap=30,
        ),
        eyebrow="Probe types",
        kicker="Same three types available to liveness, readiness and startup alike.",
        notes=(
            "Map each type onto our own app so it is concrete: vote and result get httpGet, db "
            "gets a pg_isready exec, redis could take a tcpSocket. Then the deep point &mdash; a "
            "health endpoint that always returns 200 tells you nothing, but one that checks "
            "downstream dependencies must never be wired to liveness, or one slow database "
            "restarts your entire fleet."
        ),
        day=D,
    ),
    # ---- teach 4: tuning
    slide(
        "Tuning &mdash; the five numbers that matter",
        table(
            ["Field", "Default", "What it means", "How to choose it"],
            [
                [
                    "<code>initialDelaySeconds</code>",
                    "<code>0</code>",
                    "Wait this long after the container starts before the first probe",
                    "Roughly your boot time &mdash; or use a startup probe instead",
                ],
                [
                    "<code>periodSeconds</code>",
                    "<code>10</code>",
                    "How often to probe",
                    "Readiness: short (2&ndash;5s). Liveness: long (10&ndash;30s)",
                ],
                [
                    "<code>timeoutSeconds</code>",
                    "<code>1</code>",
                    "A probe taking longer than this counts as a failure",
                    "Raise it &mdash; 1s is brutal for a loaded app",
                ],
                [
                    "<code>failureThreshold</code>",
                    "<code>3</code>",
                    "Consecutive failures before Kubernetes acts",
                    "Liveness: be generous. Readiness: be quick",
                ],
                [
                    "<code>successThreshold</code>",
                    "<code>1</code>",
                    "Consecutive passes before it counts as healthy again",
                    "Must be <code>1</code> for liveness and startup",
                ],
            ],
        )
        + two(
            col(
                term(
                    "a startup probe buys 5 minutes safely",
                    """startupProbe:
  httpGet: {path: /healthz, port: 80}
  failureThreshold: 30      # 30 x 10s = 300s of boot budget
  periodSeconds: 10
livenessProbe:
  httpGet: {path: /healthz, port: 80}
  periodSeconds: 10
  failureThreshold: 3       # once up, 30s to react""",
                    cls="xs",
                )
            ),
            col(
                note(
                    "n-info",
                    "Worst-case detection time is "
                    "<code>failureThreshold &times; periodSeconds</code> (plus up to one "
                    "<code>timeoutSeconds</code>). With the defaults that is about 30 seconds "
                    "before a wedged container is restarted.",
                ),
                note(
                    "n-tip",
                    "Prefer a <b>startup probe</b> over a large <code>initialDelaySeconds</code>. "
                    "A fixed delay is dead time on every single start; a startup probe finishes "
                    "as soon as the app is genuinely up.",
                ),
            ),
            ratio="1.05fr 1fr",
            gap=26,
        ),
        eyebrow="Tuning",
        kicker="Defaults are a starting point, not a recommendation &mdash; especially "
        "<code>timeoutSeconds: 1</code>.",
        notes=(
            "The default nobody expects is timeoutSeconds: 1. A perfectly healthy JVM under load "
            "will blow past that and get restarted, which is how a traffic spike becomes an "
            "outage. Teach the arithmetic &mdash; failureThreshold times periodSeconds is your "
            "detection window &mdash; and push startup probes over initialDelaySeconds every "
            "time."
        ),
        day=D,
    ),
    # ---- teach 5: liveness vs readiness contrast
    slide(
        "Liveness or readiness? A decision you make once per symptom",
        two(
            col(
                table(
                    ["Symptom", "Right probe", "Why"],
                    [
                        [
                            "App is warming up a cache",
                            "<b>Readiness</b>",
                            "It will be fine shortly. Do not restart it &mdash; just hold traffic",
                        ],
                        [
                            "Database is unreachable",
                            "<b>Readiness</b> only",
                            "Restarting will not fix someone else&rsquo;s outage",
                        ],
                        [
                            "Thread pool deadlocked",
                            "<b>Liveness</b>",
                            "Only a restart clears it",
                        ],
                        [
                            "Memory leak, gradual slowdown",
                            "<b>Liveness</b>",
                            "A restart genuinely recovers it (while you fix the leak)",
                        ],
                        [
                            "JVM takes 90s to boot",
                            "<b>Startup</b>",
                            "Protects a slow start from an impatient liveness probe",
                        ],
                        [
                            "Draining before shutdown",
                            "<b>Readiness</b>",
                            "Fail readiness first so the endpoint is removed before the process "
                            "exits",
                        ],
                    ],
                )
            ),
            col(
                note(
                    "n-why",
                    "The whole decision reduces to one question: <b>would restarting this "
                    "container fix it?</b> Yes &rarr; liveness. No, it just needs to be left "
                    "alone for a moment &rarr; readiness.",
                ),
                note(
                    "n-warn",
                    "<b>Never point a liveness probe at a dependency.</b> If "
                    "<code>/healthz</code> checks the database and the database hiccups, every "
                    "replica of every service restarts simultaneously &mdash; you have converted "
                    "a small problem into a cascading outage.",
                    title="The cascade",
                ),
                note(
                    "n-tip",
                    "Sensible default for a normal web service: <b>readiness always</b>, "
                    "<b>liveness only when you can name the wedge it fixes</b>, startup only for "
                    "genuinely slow starters. No liveness probe at all beats a bad one.",
                ),
            ),
            ratio="1.15fr 1fr",
            gap=30,
        ),
        eyebrow="Choosing",
        kicker="&ldquo;Would a restart fix this?&rdquo; is the entire decision procedure.",
        notes=(
            "Read the symptom table as a quiz &mdash; cover the middle column and make them "
            "answer. The row that changes behaviour is the database one: instinct says restart, "
            "and restarting is exactly what turns a database blip into a full outage. Leave them "
            "with the default: readiness always, liveness only when you can name the wedge."
        ),
        day=D,
    ),
    # ---- teach 6: the classic mistake
    slide(
        "The classic mistake: an over-aggressive liveness probe",
        two(
            col(
                term(
                    "what a restart loop looks like",
                    """livenessProbe:
  httpGet: {path: /healthz, port: 80}
  initialDelaySeconds: 1     # app needs 8s to boot
  periodSeconds: 2
  timeoutSeconds: 1          # slow under load
  failureThreshold: 1        # zero tolerance""",
                    cls="xs",
                ),
                term(
                    "the symptom",
                    """kubectl get pod -l app=vote -n vote
# NAME         READY   STATUS             RESTARTS
# vote-x2k9d   0/1     CrashLoopBackOff   7 (20s ago)

kubectl describe pod vote-x2k9d -n vote | tail -12
# Warning  Unhealthy  Liveness probe failed: ... connection refused
# Normal   Killing    Container failed liveness probe, restarting""",
                    cls="xs",
                ),
            ),
            col(
                steps(
                    [
                        "The container starts. The app needs 8 seconds; the probe begins after 1.",
                        "Three probes fail before the app has bound its port.",
                        "<code>failureThreshold: 1</code> is reached instantly &mdash; the "
                        "kubelet kills the container.",
                        "It restarts&hellip; and the timer resets. <b>The app is never given "
                        "long enough to become healthy.</b>",
                        "<code>CrashLoopBackOff</code>, forever. The application was fine all "
                        "along &mdash; the probe was the outage.",
                    ]
                ),
                note(
                    "n-warn",
                    "<b>A bad liveness probe is a self-inflicted outage.</b> Look at the "
                    "<code>Killing</code> events in <code>describe</code>: if they say "
                    "&ldquo;failed liveness probe&rdquo;, suspect the probe before the app.",
                ),
                note(
                    "n-tip",
                    "The fix is almost always the same three moves: add a "
                    "<b>startupProbe</b> to cover boot, raise <b>timeoutSeconds</b> to something "
                    "humane, and raise <b>failureThreshold</b> to 3. Then ask whether you needed "
                    "liveness at all.",
                ),
            ),
            ratio="1fr 1.05fr",
            gap=30,
        ),
        eyebrow="Failure mode",
        kicker="A probe that is stricter than the application can ever satisfy makes a healthy "
        "app permanently unhealthy.",
        notes=(
            "This is the failure they will personally cause within a month of leaving the course. "
            "Walk the five steps and let them see the loop is self-sustaining &mdash; each "
            "restart resets the clock the app needed. Tie it back to Day 1 troubleshooting: "
            "CrashLoopBackOff plus Unhealthy events in describe means read the probe, not the "
            "application logs."
        ),
        day=D,
    ),
    # ---- lab 1: add probes to the app
    lab(
        "Add probes to <code>vote</code>, <code>result</code> and <code>db</code>",
        two(
            term(
                "1 &middot; httpGet readiness on the two web apps",
                """for d in vote result; do
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
kubectl rollout status deployment/result -n vote""",
                cls="xs",
            ),
            col(
                term(
                    "2 &middot; exec probe on db, then break one on purpose",
                    """kubectl patch deployment db -n vote --type=strategic -p "$(cat <<'EOF'
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

# endpoints = the Pods readiness currently allows
kubectl get endpoints vote -n vote

# now point readiness at a path that does not exist
kubectl patch deployment vote -n vote --type=json -p \\
  '[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/path","value":"/nope"}]'

kubectl get pod -l app=vote -n vote      # READY 0/1, RESTARTS 0
kubectl get endpoints vote -n vote       # <none> -- pulled from traffic

# put it back
kubectl patch deployment vote -n vote --type=json -p \\
  '[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/path","value":"/"}]'""",
                    cls="xs",
                ),
            ),
            ratio="0.85fr 1.25fr",
            gap=24,
        )
        + note(
            "n-tip",
            "The whole lesson is in two columns of one command: <code>READY 0/1</code> with "
            "<code>RESTARTS 0</code>. Readiness removed the Pod from the Service and did "
            "<b>not</b> restart it &mdash; exactly the opposite of what liveness would have done.",
            style="margin-top:14px",
        ),
        eyebrow="Lab 20 &middot; Probes",
        kicker="Add readiness, then break it deliberately and watch the endpoint list empty out.",
        notes=(
            "Insist they run get endpoints before and after &mdash; that object is the proof "
            "that readiness is wired into Service routing, and most students have never looked "
            "at it. Point out RESTARTS staying at 0: readiness never restarts anything. The JSON "
            "patch is also their first look at replacing one field surgically."
        ),
        day=D,
    ),
    # ---- lab 2: the payoff lab
    lab(
        "&#11088; The payoff: zero downtime, proven",
        two(
            term(
                "round 1 &middot; NO readiness probe",
                """# one replica, no readiness, and a 10s warmup
# (real apps warm up: JVM, migrations, caches)
kubectl scale deployment/vote -n vote --replicas=1
kubectl patch deployment vote -n vote --type=json -p \\
  '[{"op":"remove","path":"/spec/template/spec/containers/0/readinessProbe"}]'
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

# TERMINAL A -- continuous load from inside the cluster
kubectl run load -n vote --rm -it --restart=Never \\
  --image=curlimages/curl -- sh -c \\
  'n=0; f=0; while true; do n=$((n+1));
     curl -sf -m 2 -o /dev/null http://vote/ || { f=$((f+1)); echo "FAIL $f  (request $n)"; };
     sleep 0.2; done'

# TERMINAL B -- roll it
kubectl rollout restart deployment/vote -n vote""",
                cls="xs",
            ),
            col(
                term(
                    "round 2 &middot; readiness probe added",
                    """# Terminal A output in round 1:
# FAIL 1  (request 43)
# FAIL 2  (request 44)
#  ... ~50 failures across the 10s warmup window

# now tell Kubernetes what "ready" means
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

# TERMINAL B -- roll it again, same load running
kubectl rollout restart deployment/vote -n vote

# Terminal A: no new FAIL lines. Zero.""",
                    cls="xs",
                ),
                note(
                    "n-warn",
                    "Round 1 is not a bug in Kubernetes. Without a readiness probe a Pod joins "
                    "the Service the moment its <b>container process</b> starts &mdash; not when "
                    "the <b>application</b> can serve. Those dropped requests are the honest "
                    "default behaviour.",
                    title="Confusion #11",
                ),
                note(
                    "n-tip",
                    "<code>maxUnavailable: 0</code> is the other half. It forces the new Pod to "
                    "be genuinely Ready before the old one is allowed to go &mdash; readiness "
                    "supplies the truth, the strategy acts on it.",
                ),
            ),
            ratio="1fr 1.05fr",
            gap=26,
        )
        + note(
            "n-info",
            "On Day 2 we hedged: a rolling update keeps <b>capacity</b>, but only a readiness "
            "probe makes it truly <b>zero downtime</b>. You just measured both halves of that "
            "sentence. Clean up with "
            "<code>kubectl patch deployment vote -n vote --type=json -p "
            "'[{\"op\":\"remove\",\"path\":\"/spec/template/spec/containers/0/command\"}]'</code>.",
            style="margin-top:12px",
        ),
        eyebrow="Lab 21 &middot; &#11088; the payoff",
        kicker="The same rollout, twice. Once it drops ~50 requests. Once it drops none.",
        notes=(
            "This is the most important lab of the course &mdash; give it real time and run it "
            "yourself on the projector first. The 10-second sleep is deliberate and you should "
            "say so: it makes a slow warmup visible in a lab-sized app instead of hoping to catch "
            "a one-second window. Do not explain round 1 before they see the FAIL lines scroll. "
            "Then add readiness plus maxUnavailable: 0, roll again, and let the silence in "
            "terminal A be the lesson."
        ),
        day=D,
    ),
]

# ============================================================= day3end (3)
day3end = [
    lab(
        "Planted failure: a PVC that will never bind",
        two(
            term(
                "1 &middot; break it",
                """kubectl apply -n vote -f - <<'EOF'
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
# NAME     STATUS    VOLUME   CAPACITY   STORAGECLASS
# broken   Pending                       fast-ssd""",
                cls="xs",
            ),
            col(
                term(
                    "2 &middot; diagnose, then fix",
                    """kubectl describe pvc broken -n vote | tail -8
# Events:
#   Warning  ProvisioningFailed
#   storageclass.storage.k8s.io "fast-ssd" not found

# what classes DO exist?
kubectl get sc
# standard (default)   rancher.io/local-path

# storageClassName is IMMUTABLE -- recreate it
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
# STATUS: Pending  <- still! and this time it is CORRECT
kubectl delete pvc broken -n vote""",
                    cls="xs",
                ),
                note(
                    "n-warn",
                    "Two different <code>Pending</code> states, one word. The first has a "
                    "<code>ProvisioningFailed</code> event and never resolves. The second is "
                    "<code>WaitForFirstConsumer</code> waiting for a Pod &mdash; entirely normal. "
                    "<b><code>describe</code> is what tells them apart.</b>",
                    title="Confusion #10",
                ),
            ),
            ratio="0.9fr 1.15fr",
            gap=26,
        ),
        eyebrow="Lab 23 &middot; Troubleshooting",
        kicker="Same symptom, two completely different causes &mdash; and only one of them is a bug.",
        notes=(
            "Do not tell them the class name is wrong &mdash; hand them the Pending PVC and let "
            "them find it. Ninety percent will run get pvc, stare, and stop; push them to "
            "describe and read the Events tail, which is the habit this whole day is building. "
            "The second Pending is the real payoff: they must learn that Pending alone means "
            "nothing without the events."
        ),
        day=D,
    ),
    slide(
        "You are here &mdash; end of Day 3",
        cards(
            [
                (
                    "&#128203;",
                    "vote",
                    "Deployment + Service, options from a <b>ConfigMap</b>, "
                    "<b>readiness probe</b> gating traffic.",
                    "t-blue",
                ),
                (
                    "&#128202;",
                    "result",
                    "Deployment + Service, DB credentials from a <b>Secret</b>, "
                    "<b>readiness probe</b>.",
                    "t-green",
                ),
                (
                    "&#9881;",
                    "worker",
                    "No Service, no inbound traffic &mdash; credentials from the same "
                    "<b>Secret</b>.",
                    "t-amber",
                ),
                (
                    "&#128220;",
                    "redis",
                    "ClusterIP + <code>emptyDir</code>. Deliberately ephemeral &mdash; you "
                    "watched it lose data.",
                    "t-slate",
                ),
                (
                    "&#128190;",
                    "db",
                    "<b>PVC</b> for the data, <b>Secret</b> for the password, "
                    "<code>pg_isready</code> exec probe.",
                    "t-violet",
                ),
                (
                    "&#128273;",
                    "Configuration",
                    "ConfigMaps and Secrets, injected as env vars <i>and</i> as mounted files.",
                    "t-teal",
                ),
                (
                    "&#128421;",
                    "Storage",
                    "emptyDir vs PVC, accessModes, reclaim policy, "
                    "<code>WaitForFirstConsumer</code>.",
                    "t-gold",
                ),
                (
                    "&#128137;",
                    "Health",
                    "Liveness restarts, readiness removes from traffic, startup protects slow "
                    "boots. Zero downtime is now <b>true</b>.",
                    "t-maroon",
                ),
            ],
            cols=4,
        )
        + note(
            "n-tip",
            "Day 2 left the app <i>working</i>. Day 3 left it <b>configurable, durable and "
            "honest</b> &mdash; it now tells Kubernetes when it can serve instead of being "
            "assumed healthy. Tomorrow: how much CPU and memory it may use, where it is allowed "
            "to run, and how it scales itself.",
            style="margin-top:18px",
        ),
        eyebrow="Recap",
        kicker="The same Voting App as yesterday, with four new Kubernetes objects wired into it.",
        notes=(
            "Walk component by component and ask what changed for each &mdash; they should be "
            "able to answer without you. The single sentence to send them home with: the app now "
            "tells Kubernetes when it is ready instead of Kubernetes assuming it. Point at redis "
            "as deliberately still broken; it is the hook into Day 4."
        ),
        day=D,
    ),
    slide(
        "Interview questions &mdash; Day 3",
        cards(
            [
                (
                    "1",
                    "ConfigMap vs Secret",
                    "<b>Q:</b> What is the actual difference?<br><b>A:</b> Mechanically almost "
                    "none &mdash; both are key/value, both inject as env or files. Secrets are "
                    "base64 in the API, hidden from <code>describe</code>, held in "
                    "<code>tmpfs</code>, and gated by their own RBAC verb.",
                    "t-slate",
                ),
                (
                    "2",
                    "Are Secrets encrypted?",
                    "<b>Q:</b> Is a Secret encrypted?<br><b>A:</b> No. base64 is encoding, not "
                    "encryption. Encryption at rest in etcd is an opt-in "
                    "<code>EncryptionConfiguration</code> the cluster admin enables.",
                    "t-maroon",
                ),
                (
                    "3",
                    "Config hot reload",
                    "<b>Q:</b> I changed a ConfigMap &mdash; why did nothing happen?<br>"
                    "<b>A:</b> Env vars are fixed at container start; mounted files refresh in "
                    "about a minute. Either way run <code>kubectl rollout restart</code> unless "
                    "the app re-reads the file.",
                    "t-amber",
                ),
                (
                    "4",
                    "emptyDir lifetime",
                    "<b>Q:</b> When is an <code>emptyDir</code> deleted?<br><b>A:</b> When the "
                    "<b>Pod</b> is removed from the node &mdash; not when a container restarts. "
                    "It is scratch space, never storage.",
                    "t-blue",
                ),
                (
                    "5",
                    "ReadWriteOnce",
                    "<b>Q:</b> Can two Pods mount an RWO volume?<br><b>A:</b> Yes &mdash; if they "
                    "are on the <b>same node</b>. RWO restricts nodes, not Pods. Use "
                    "<code>ReadWriteOncePod</code> for true exclusivity.",
                    "t-green",
                ),
                (
                    "6",
                    "PVC stuck Pending",
                    "<b>Q:</b> My PVC is Pending. Why?<br><b>A:</b> <code>describe pvc</code> and "
                    "read the events: no matching StorageClass, no PV that satisfies the size or "
                    "accessMode &mdash; or it is <code>WaitForFirstConsumer</code> and simply has "
                    "no Pod yet.",
                    "t-teal",
                ),
                (
                    "7",
                    "Liveness vs readiness",
                    "<b>Q:</b> Difference between the two?<br><b>A:</b> Liveness failure restarts "
                    "the container; readiness failure removes the Pod from Service endpoints with "
                    "no restart. Never point liveness at a dependency.",
                    "t-violet",
                ),
                (
                    "8",
                    "Rollouts and readiness",
                    "<b>Q:</b> Does a rolling update guarantee zero downtime?<br><b>A:</b> Not on "
                    "its own. Without readiness a Pod joins the Service the moment the process "
                    "starts. Readiness plus <code>maxUnavailable: 0</code> is what makes it true.",
                    "t-gold",
                ),
            ],
            cols=2,
        ),
        eyebrow="Wrap",
        kicker="Eight questions that come up in almost every Kubernetes interview.",
        notes=(
            "Run this as a cold-call round rather than reading it out &mdash; they have done "
            "every one of these with their hands today. Questions 2, 5 and 8 are the ones "
            "candidates most often get wrong, and each maps to a lab they just ran. Tell them to "
            "answer with the lab, not the definition: &ldquo;I decoded one myself&rdquo; is a far "
            "better answer than &ldquo;base64 is not encryption&rdquo;."
        ),
        day=D,
    ),
]

# ================================================================== exports
BLOCKS = {
    "day3open": day3open,
    "configmap": configmap,
    "secret": secret,
    "emptydir_lab": emptydir_lab,
    "storage_extra": storage_extra,
    "vapvc": vapvc,
    "statefulset": statefulset,
    "probes": probes,
    "day3end": day3end,
}


if __name__ == "__main__":
    for name, secs in BLOCKS.items():
        for i, s in enumerate(secs):
            assert s.startswith("<section"), f"{name}[{i}] does not start with <section"
            assert s.endswith("</section>"), f"{name}[{i}] does not end with </section>"
            assert 'data-day="3"' in s, f"{name}[{i}] is missing data-day=3"
    print({k: len(v) for k, v in BLOCKS.items()})
    print("total", sum(len(v) for v in BLOCKS.values()))
