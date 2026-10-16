# Kubernetes Volumes – what I learned

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037

A container's own filesystem is thrown away every time the container restarts. **Volumes** give a Pod storage that lives outside the container. The big question for each type is: **how long does the data live?**

Every example here is in [`examples/`](examples/), and I ran all of them on my Minikube cluster. Raw output: [`../outputs/01-volumes.txt`](../outputs/01-volumes.txt).

| Type | Data lives as long as... | Shared between |
|---|---|---|
| `emptyDir` | the **Pod** | containers in the same Pod |
| `hostPath` | the **node** | Pods on that same node |
| PV + PVC | the **PersistentVolume** (separate from Pods) | whoever claims it (depends on access mode) |

---

## emptyDir

An empty folder that is created when the Pod starts and **deleted when the Pod is deleted**. A container crash doesn't wipe it, because the Pod is still there. Good for scratch space, caches, or passing files between containers in one Pod.

[`examples/01-emptydir.yaml`](examples/01-emptydir.yaml): a `writer` container adds the date every 5 seconds, and a `reader` container reads the same file.
```text
$ kubectl exec -n s13 emptydir-demo -c reader -- cat /shared/log.txt
Fri Oct 16 18:50:25 UTC 2026
Fri Oct 16 18:50:30 UTC 2026
Fri Oct 16 18:50:35 UTC 2026

# after deleting and re-creating the Pod:
$ kubectl exec -n s13 emptydir-demo -c reader -- cat /shared/log.txt
Fri Oct 16 18:51:07 UTC 2026          <- old lines are gone, a fresh empty folder
```
Tip: `emptyDir: { medium: Memory }` uses RAM (tmpfs) instead of disk.

## hostPath

Mounts a folder **from the node's own disk** into the Pod. The data survives Pod deletion, but **only on that one node**. If the Pod moves to another node, it sees a different, empty folder. It also gives the Pod access to the node's files, which is a security risk. It is mostly used by system agents like log collectors, not by normal apps.

[`examples/02-hostpath.yaml`](examples/02-hostpath.yaml):
```text
# after creating, deleting and re-creating the Pod:
$ kubectl exec -n s13 hostpath-demo -- cat /node-data/notes.txt
written by hostpath-demo at Fri Oct 16 18:51:08 UTC 2026      <- first Pod
written by hostpath-demo at Fri Oct 16 18:51:39 UTC 2026      <- second Pod

$ minikube ssh -- cat /tmp/s13-hostpath/notes.txt       # the same file on the node itself
written by hostpath-demo at Fri Oct 16 18:51:08 UTC 2026
written by hostpath-demo at Fri Oct 16 18:51:39 UTC 2026
```

## PersistentVolume (PV)

A piece of storage in the cluster, such as an AWS EBS disk, an NFS share, or (in Minikube) a folder on the node. It is a **cluster-wide** object, not inside a namespace, and it exists on its own, apart from any Pod.

Important fields:
- `capacity` – size, for example `200Mi`
- `accessModes`:
  - `ReadWriteOnce` (RWO) – one node can mount it read-write
  - `ReadOnlyMany` (ROX) – many nodes, read-only
  - `ReadWriteMany` (RWX) – many nodes read-write, which needs something like NFS or EFS
  - `ReadWriteOncePod` – one Pod only
- `persistentVolumeReclaimPolicy` – what happens when the claim is deleted:
  - `Retain` – keep the data; an admin must clean it up
  - `Delete` – delete the real storage too

## PersistentVolumeClaim (PVC)

A **request** for storage by an app: "I need 100Mi, RWO, of class X". It lives in a namespace. Kubernetes **binds** it to a matching PV, and the Pod then mounts the PVC by name. It never needs to know which disk is behind it.

**Static example** – [`examples/03-static-pv.yaml`](examples/03-static-pv.yaml): I made the PV by hand (200Mi, class `manual`, `Retain`), then a 100Mi claim:
```text
NAME            CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM              STORAGECLASS
s13-manual-pv   200Mi      RWO            Retain           Bound    s13/manual-claim   manual

NAME           STATUS   VOLUME          CAPACITY   ACCESS MODES   STORAGECLASS
manual-claim   Bound    s13-manual-pv   200Mi      RWO            manual
```
The claim asked for 100Mi but got the whole 200Mi PV. **A PV binds to exactly one PVC.**

## StorageClass

A StorageClass describes a **type** of storage and **which provisioner creates it**. My cluster has one built in:
```text
$ kubectl get sc
NAME                 PROVISIONER                RECLAIMPOLICY   VOLUMEBINDINGMODE
standard (default)   k8s.io/minikube-hostpath   Delete          Immediate
```
Fields:
- `provisioner` – the driver, for example `ebs.csi.aws.com` on EKS, or `k8s.io/minikube-hostpath` here
- `parameters` – driver options, like the disk type `gp3`
- `reclaimPolicy` – default `Delete`
- `volumeBindingMode`:
  - `Immediate` – make the volume right away
  - `WaitForFirstConsumer` – wait until a Pod is scheduled, so the disk is created in the same zone as the Pod. This is the right choice on EKS.
- `allowVolumeExpansion` – whether a PVC can be grown later

If a PVC doesn't name a class, the one marked `(default)` is used.

## Dynamic provisioning

With dynamic provisioning **nobody writes a PV by hand**. The PVC names a StorageClass, the provisioner creates real storage plus a PV, and binds them.

[`examples/04-storageclass-dynamic.yaml`](examples/04-storageclass-dynamic.yaml) creates the class `s13-fast`, a claim `dynamic-claim`, and a Pod that uses both claims:
```text
$ kubectl get pvc -n s13
NAME            STATUS   VOLUME                                     CAPACITY   STORAGECLASS
dynamic-claim   Bound    pvc-f7ade0c6-170b-46bf-8cdb-8634e09e5840   100Mi      s13-fast      <- PV made for me
manual-claim    Bound    s13-manual-pv                              200Mi      manual

$ kubectl describe pvc dynamic-claim -n s13
  Normal  Provisioning           External provisioner is provisioning volume for claim "s13/dynamic-claim"
  Normal  ProvisioningSucceeded  Successfully provisioned volume pvc-f7ade0c6-170b-46bf-8cdb-8634e09e5840
```
**Data survives the Pod:**
```text
$ kubectl exec -n s13 pvc-user -- sh -c "echo loan-record-001 > /data/records.txt; echo hello-manual > /manual/hello.txt"
$ kubectl delete pod pvc-user -n s13 && kubectl apply -f examples/04-storageclass-dynamic.yaml
$ kubectl exec -n s13 pvc-user -- cat /data/records.txt /manual/hello.txt
loan-record-001
hello-manual
```
**Reclaim policies in action.** When I deleted the namespace (and so both PVCs):
```text
$ kubectl get pv
NAME            CAPACITY   RECLAIM POLICY   STATUS     CLAIM
s13-manual-pv   200Mi      Retain           Released   s13/manual-claim
```
- The dynamic PV (`Delete`) disappeared with its claim.
- The manual PV (`Retain`) stayed as `Released`, with its data still there, until I deleted it myself.

One note from my lab: I first set my StorageClass to `WaitForFirstConsumer`. Minikube's simple hostpath provisioner can't handle that mode (`storage-provisioner cannot get resource "nodes"`), so I used `Immediate`, the same as Minikube's default class.

## Putting it together

```text
Pod --mounts--> PVC "dynamic-claim" --bound to--> PV "pvc-f7ad..." --made by--> StorageClass "s13-fast" --> real disk
     (app side)        (namespace)                    (cluster)                     (provisioner)
```
Developers only write the PVC. Admins (or the cloud) take care of StorageClasses and PVs.
