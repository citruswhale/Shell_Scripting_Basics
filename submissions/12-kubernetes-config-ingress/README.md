# Session 12 – Kubernetes Ingress, ConfigMaps & Secrets

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037 · **Batch:** B

Everything here ran on my Minikube cluster (`devops-lab`, Kubernetes v1.37) in the namespace `s12`. I used names from my capstone idea, **GearLoan** (an equipment lending app), so the config values look like a real app.

- [`ingress-vs-ingress-controller/README.md`](ingress-vs-ingress-controller/README.md) – Task 4
- [`outputs/`](outputs/) – raw output of every command

```bash
kubectl apply -f namespace.yaml
```

---

## Task 1 – ConfigMap

[`01-configmap/configmap.yaml`](01-configmap/configmap.yaml) stores 4 simple settings and 1 whole file:
```yaml
data:
  APP_NAME: "GearLoan"
  APP_ENV: "staging"
  LOG_LEVEL: "info"
  MAX_LOAN_DAYS: "14"
  settings.ini: |
    [loans]
    max_items_per_person = 3
    overdue_reminder_hours = 24
```

[`01-configmap/pod.yaml`](01-configmap/pod.yaml) uses it in three ways:
- `env` + `configMapKeyRef` → one key as one variable
- `envFrom` + `configMapRef` → every key as a variable
- a `configMap` **volume** → `settings.ini` becomes the file `/etc/app/settings.ini`

**Verify inside the container**
```text
$ kubectl exec -n s12 config-demo -- sh -c 'env | grep -E "^(APP_NAME|APP_ENV|LOG_LEVEL|MAX_LOAN_DAYS)=" | sort'
APP_ENV=staging
APP_NAME=GearLoan
LOG_LEVEL=info
MAX_LOAN_DAYS=14

$ kubectl exec -n s12 config-demo -- cat /etc/app/settings.ini
[loans]
max_items_per_person = 3
overdue_reminder_hours = 24
```

**What happens when I change the ConfigMap?** I patched `LOG_LEVEL` to `debug` and `max_items_per_person` to `5`, without touching the Pod:
```text
--- mounted file:            (updated by itself after about 90 seconds)
[loans]
max_items_per_person = 5
overdue_reminder_hours = 12
--- env var:                 (still the old value)
LOG_LEVEL=info

# after deleting and re-creating the Pod:
LOG_LEVEL=debug
```
- **Mounted files update automatically.** The kubelet syncs them, which took about 90 s for me. That's why the file is a symlink to `..data/`: the kubelet swaps the link in one step.
- **Environment variables are read only once, when the container starts.** You have to restart the Pod to get new values.

Full log: [`outputs/01-configmap.txt`](outputs/01-configmap.txt)

---

## Task 2 – Secret

[`02-secret/secret.yaml`](02-secret/secret.yaml) holds a demo database user and password. I used `stringData` so I could write plain text; Kubernetes stores it base64-encoded.

> These values are made up, only for this lab. In a real project I would **not** commit a Secret file at all (see below).

```text
$ kubectl describe secret db-credentials -n s12
Type:  Opaque
Data
====
DB_PASSWORD:  21 bytes
DB_USER:      12 bytes
```
`describe` doesn't show the values, only their sizes. But anyone who can **read** the Secret can decode it:
```text
$ kubectl get secret db-credentials -n s12 -o jsonpath='{.data.DB_USER}'
Z2VhcmxvYW5fYXBw
$ ... | base64 -d
gearloan_app
```

[`02-secret/pod.yaml`](02-secret/pod.yaml) injects it as env vars (`secretKeyRef`) **and** as files in `/etc/creds`.

**Verify inside the container, without printing the password**
```text
$ kubectl exec -n s12 secret-demo -- sh -c 'echo DB_USER=$DB_USER; echo DB_PASSWORD is set: ${#DB_PASSWORD} characters, starts with ${DB_PASSWORD:0:3}***'
DB_USER=gearloan_app
DB_PASSWORD is set: 21 characters, starts with lab***

$ kubectl exec -n s12 secret-demo -- ls -l /etc/creds/..data/
-r--------    1 root     root            21 Oct 16 18:32 DB_PASSWORD
-r--------    1 root     root            12 Oct 16 18:32 DB_USER

$ kubectl exec -n s12 secret-demo -- sh -c 'mount | grep /etc/creds'
tmpfs on /etc/creds type tmpfs (ro,relatime,size=12232784k,noswap)

$ kubectl exec -n s12 secret-demo -- sh -c '[ "$(cat /etc/creds/DB_PASSWORD)" = "$DB_PASSWORD" ] && echo file and env var match'
file and env var match
```
- The files are mode `0400` (owner can read, nobody else).
- They sit on a `tmpfs`, which is in memory and never written to the node's disk.

### Why Secrets should not be committed to Git
- **Base64 is not encryption.** As shown above, `base64 -d` gives the value back in one command.
- **Git remembers forever.** Even if you delete the file later, the password is still in the history, and a public repo can be cloned or scraped by bots within minutes.
- **Everyone with repo access gets production passwords**, and you can't revoke a copy someone already cloned. A leaked secret has to be **rotated** (changed), not just deleted.

**Better ways:**
- `kubectl create secret generic db-credentials --from-literal=DB_PASSWORD=...` from a terminal or a CI secret.
- **Sealed Secrets** (encrypted file, safe to commit).
- **External Secrets** with AWS Secrets Manager or Vault.

Also turn on encryption at rest in etcd and limit who can `get secrets` with RBAC.

Full log: [`outputs/02-secret.txt`](outputs/02-secret.txt)

---

## Task 3 – Ingress

**Setup:** I enabled the ingress-nginx controller (Minikube addon) and deployed 3 small apps, each with a ClusterIP Service: `frontend`, `api` and `admin`.
```bash
minikube addons enable ingress -p devops-lab
kubectl apply -f 03-ingress/frontend.yaml -f 03-ingress/api.yaml -f 03-ingress/admin.yaml
kubectl apply -f 03-ingress/ingress.yaml
```
```text
NAME              CONTROLLER             PARAMETERS   AGE
nginx (default)   k8s.io/ingress-nginx   <none>       3m28s

NAME               TYPE        CLUSTER-IP       PORT(S)
service/admin      ClusterIP   10.111.162.91    80/TCP
service/api        ClusterIP   10.110.181.92    80/TCP
service/frontend   ClusterIP   10.105.152.180   80/TCP
```

[`03-ingress/ingress.yaml`](03-ingress/ingress.yaml) does **path-based** and **host-based** routing:
```text
$ kubectl get ingress gearloan -n s12
NAME       CLASS   HOSTS                                 ADDRESS        PORTS   AGE
gearloan   nginx   gearloan.local,admin.gearloan.local   192.168.49.2   80      51s

$ kubectl describe ingress gearloan -n s12
  Host                  Path  Backends
  gearloan.local
                        /api   api:80 (10.244.0.100:8080,10.244.0.99:8080)
                        /      frontend:80 (10.244.0.97:8080,10.244.0.98:8080)
  admin.gearloan.local
                        /   admin:80 (10.244.0.101:8080,10.244.0.102:8080)
```

**Access it.** On macOS with the docker driver I can't reach the node IP directly, so I port-forwarded the controller and set the `Host` header:
```bash
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8088:80
```
```text
$ curl -H "Host: gearloan.local" http://127.0.0.1:8088/
GearLoan frontend (home page)
$ curl -H "Host: gearloan.local" http://127.0.0.1:8088/api
GearLoan API - list of items
$ curl -H "Host: gearloan.local" http://127.0.0.1:8088/api/items/42
GearLoan API - list of items
$ curl -H "Host: gearloan.local" http://127.0.0.1:8088/some/page
GearLoan frontend (home page)
$ curl -H "Host: admin.gearloan.local" http://127.0.0.1:8088/
GearLoan admin site
$ curl -H "Host: something-else.local" http://127.0.0.1:8088/
unknown host -> HTTP 404
```

**Verify the routing.** The controller's access log shows which Service and which Pod got each request:
```text
"GET / HTTP/1.1" 200 ... [s12-frontend-80] [] 10.244.0.97:8080
"GET /api HTTP/1.1" 200 ... [s12-api-80] [] 10.244.0.100:8080
"GET /api/items/42 HTTP/1.1" 200 ... [s12-api-80] [] 10.244.0.99:8080
"GET /some/page HTTP/1.1" 200 ... [s12-frontend-80] [] 10.244.0.98:8080
"GET / HTTP/1.1" 200 ... [s12-admin-80] [] 10.244.0.101:8080
```
- `pathType: Prefix` with `/api` matches `/api` and everything under it.
- The longest matching path wins, so `/api/...` beats `/`.
- A host that isn't in any rule gets the controller's default 404.

Full log: [`outputs/03-ingress.txt`](outputs/03-ingress.txt)

---

## Task 4 – Ingress vs Ingress Controller

See [`ingress-vs-ingress-controller/README.md`](ingress-vs-ingress-controller/README.md).

---

## Task 5 – Troubleshooting

### Issue 1 – "Password is correct, but the database says it's wrong"

This is the instructor's `troubleshooting/secret-base64-gotcha` case. I recreated it with a real PostgreSQL:
- [`postgres.yaml`](04-troubleshooting/postgres.yaml) – the database, with password `labPass123`
- [`broken-client-secret.yaml`](04-troubleshooting/broken-client-secret.yaml) – the app's copy of the password, made with `echo "labPass123" | base64`
- [`client-job.yaml`](04-troubleshooting/client-job.yaml) – an "app" that logs in with `psql`

**1. Identify the problem**
```text
$ kubectl get job,pods -n s12 -l job-name=db-client
job.batch/db-client   Failed   0/1           3s
pod/db-client-6ctjw   0/1     Error    0          3s

$ kubectl logs -n s12 job/db-client
psql: error: connection to server at "postgres" (10.111.9.104), port 5432 failed: FATAL:  password authentication failed for user "gearloan"
```

**2. Run troubleshooting commands.** The database log agrees: a login attempt reached it, so networking and DNS are fine.
```text
$ kubectl logs -n s12 postgres --tail=3
... FATAL:  password authentication failed for user "gearloan"
```
Both Secrets "contain labPass123", so I compared them byte by byte:
```text
$ kubectl get secret pg-server -n s12 -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d | xxd
00000000: 6c61 6250 6173 7331 3233                 labPass123

$ kubectl get secret pg-client -n s12 -o jsonpath='{.data.PGPASSWORD}' | base64 -d | xxd
00000000: 6c61 6250 6173 7331 3233 0a              labPass123.
```

**3. Root cause.** The client's password has an extra byte, **`0a`, which is a newline (`\n`)**. `echo` adds a newline by default, and `base64` encodes it too:
```text
$ echo "labPass123" | base64        ->  bGFiUGFzczEyMwo=     (11 bytes, wrong)
$ echo -n "labPass123" | base64     ->  bGFiUGFzczEyMw==     (10 bytes, right)
```
A quick hint is that the encoded value ends in `o=` instead of `==`.

**4. Fix.** Re-create the value with `echo -n`. That's [`fixed-client-secret.yaml`](04-troubleshooting/fixed-client-secret.yaml). Then run the job again:
```bash
kubectl apply -f 04-troubleshooting/fixed-client-secret.yaml
kubectl delete job db-client -n s12 && kubectl apply -f 04-troubleshooting/client-job.yaml
```

**5. After**
```text
$ kubectl get secret pg-client -n s12 -o jsonpath='{.data.PGPASSWORD}' | base64 -d | xxd
00000000: 6c61 6250 6173 7331 3233                 labPass123

$ kubectl get job -n s12 db-client
job.batch/db-client   Complete   1/1           3s

$ kubectl logs -n s12 job/db-client
 current_user |                    version
--------------+---------------------------------------------------
 gearloan     | PostgreSQL 17.11 on aarch64-unknown-linux-musl, ...
(1 row)
```
**Lesson:** use `stringData`, or `kubectl create secret --from-literal`, so you never hand-encode base64. If you must, always use `echo -n` or `printf '%s'`.

Full log: [`outputs/04-troubleshooting-secret-newline.txt`](outputs/04-troubleshooting-secret-newline.txt)

### Issue 2 – Pod stuck in `CreateContainerConfigError`

[`missing-config-pod.yaml`](04-troubleshooting/missing-config-pod.yaml) reads the key `FEATURE_FLAGS` from `app-config`.

| Step | Command | Result |
|---|---|---|
| Identify | `kubectl get pod missing-config -n s12` | `0/1  CreateContainerConfigError` |
| Investigate | `kubectl describe pod missing-config -n s12` | `Error: couldn't find key FEATURE_FLAGS in ConfigMap s12/app-config` |
| Investigate | `kubectl get configmap app-config -n s12 -o jsonpath='{.data}'` | Keys are `APP_ENV, APP_NAME, LOG_LEVEL, MAX_LOAN_DAYS, settings.ini`. No `FEATURE_FLAGS` |
| Root cause | | The Pod needs a key the ConfigMap doesn't have. The image is fine; the kubelet just can't build the container's environment |
| Fix | `kubectl patch configmap app-config -n s12 --type merge -p '{"data":{"FEATURE_FLAGS":"late-fees,email-reminders"}}'` | |
| Verify | `kubectl get pod` / `kubectl logs` | `1/1 Running`, `FEATURE_FLAGS=late-fees,email-reminders` |

I didn't have to restart anything; the kubelet kept retrying and started the container once the key existed. Another fix is `optional: true` on the `configMapKeyRef`, if the app can run without the value.

Full log: [`outputs/05-troubleshooting-missing-config.txt`](outputs/05-troubleshooting-missing-config.txt)

---

## Cleanup
```bash
kubectl delete namespace s12
minikube addons disable ingress -p devops-lab     # optional
```
