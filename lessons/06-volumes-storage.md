# Lesson 6: Volumes and Persistent Storage

## The Problem: Container Storage is Ephemeral

By default, container filesystems are temporary:
- Data is lost when container restarts
- Can't share data between containers
- No persistence across pod rescheduling

**Solution:** Kubernetes Volumes provide persistent storage.

## Volume Types Overview

### Ephemeral Volumes
Data exists only during Pod lifetime:
- `emptyDir`: Empty directory for Pod
- `configMap`: Mount ConfigMap as files
- `secret`: Mount Secret as files

### Persistent Volumes
Data persists beyond Pod lifetime:
- `hostPath`: Mount directory from host (single node)
- `nfs`: Network File System
- `persistentVolumeClaim`: Abstract storage claim
- Cloud provider volumes: `awsElasticBlockStore`, `gcePersistentDisk`, `azureDisk`

## EmptyDir Volume

Temporary storage shared between containers in a Pod.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-emptydir
spec:
  containers:
  - name: writer
    image: busybox
    command: ['sh', '-c', 'echo "Hello from writer" > /data/message.txt && sleep 3600']
    volumeMounts:
    - name: shared-data
      mountPath: /data
  
  - name: reader
    image: busybox
    command: ['sh', '-c', 'cat /data/message.txt && sleep 3600']
    volumeMounts:
    - name: shared-data
      mountPath: /data
  
  volumes:
  - name: shared-data
    emptyDir: {}
```

**Use cases:**
- Temporary scratch space
- Sharing data between sidecar containers
- Cache that can be rebuilt

## HostPath Volume

Mounts a file or directory from the host node.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-hostpath
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: host-volume
      mountPath: /usr/share/nginx/html
  volumes:
  - name: host-volume
    hostPath:
      path: /data/web
      type: DirectoryOrCreate
```

⚠️ **Warning:** 
- Only works on single-node clusters
- Pods may not find data if rescheduled to different node
- Security risk - pod can access host filesystem

**Use cases:**
- Development/testing
- DaemonSets that need host access
- Node-level monitoring

## Persistent Volumes (PV) and Claims (PVC)

The proper way to handle persistent storage in Kubernetes.

### Architecture

```
Developer creates:        Cluster Admin provisions:
    ┌──────┐                  ┌──────────┐
    │ PVC  │ ────claims───>   │    PV    │
    └──────┘                  └──────────┘
        │                          │
        └─────── bound ────────────┘
```

### Persistent Volume (PV)

Cluster resource provisioned by admin or dynamically.

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-data
spec:
  capacity:
    storage: 10Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: /mnt/data
```

**Access Modes:**
- `ReadWriteOnce (RWO)`: Mount by single node (read-write)
- `ReadOnlyMany (ROX)`: Mount by multiple nodes (read-only)
- `ReadWriteMany (RWX)`: Mount by multiple nodes (read-write)

**Reclaim Policies:**
- `Retain`: Keep data after PVC deletion (manual cleanup)
- `Delete`: Delete storage after PVC deletion
- `Recycle`: Deprecated (use dynamic provisioning)

### Persistent Volume Claim (PVC)

Request for storage by a user.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-data
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: manual
```

### Using PVC in Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-pvc
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: persistent-storage
      mountPath: /usr/share/nginx/html
  volumes:
  - name: persistent-storage
    persistentVolumeClaim:
      claimName: pvc-data
```

## Storage Classes

Enable dynamic provisioning of PVs.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/gce-pd
parameters:
  type: pd-ssd
  replication-type: regional-pd
```

### Dynamic Provisioning

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dynamic-pvc
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 20Gi
```

Kubernetes automatically creates PV when PVC is created!

### Common StorageClass Provisioners

- **AWS**: `kubernetes.io/aws-ebs`
- **GCP**: `kubernetes.io/gce-pd`
- **Azure**: `kubernetes.io/azure-disk`
- **NFS**: `kubernetes.io/nfs`
- **Local**: `kubernetes.io/no-provisioner`

## Volume Expansion

Some storage classes support volume expansion:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: expandable-storage
provisioner: kubernetes.io/aws-ebs
allowVolumeExpansion: true
```

Expand volume:
```bash
kubectl patch pvc pvc-data -p '{"spec":{"resources":{"requests":{"storage":"20Gi"}}}}'
```

## StatefulSet with Persistent Storage

For stateful applications requiring stable storage:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
spec:
  serviceName: mysql
  replicas: 3
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        volumeMounts:
        - name: data
          mountPath: /var/lib/mysql
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: "fast-ssd"
      resources:
        requests:
          storage: 10Gi
```

Each pod gets its own PVC: `data-mysql-0`, `data-mysql-1`, `data-mysql-2`

## Hands-On Exercises

### Exercise 1: EmptyDir for Shared Storage

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: shared-volume-demo
spec:
  containers:
  - name: producer
    image: busybox
    command: ['sh', '-c', 'while true; do date >> /data/log.txt; sleep 5; done']
    volumeMounts:
    - name: shared-data
      mountPath: /data
  
  - name: consumer
    image: busybox
    command: ['sh', '-c', 'tail -f /data/log.txt']
    volumeMounts:
    - name: shared-data
      mountPath: /data
  
  volumes:
  - name: shared-data
    emptyDir: {}
EOF

# View consumer logs
kubectl logs shared-volume-demo -c consumer -f
```

### Exercise 2: PV and PVC

```bash
# Create PV
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolume
metadata:
  name: my-pv
spec:
  capacity:
    storage: 1Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: /tmp/data
EOF

# Create PVC
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: manual
  resources:
    requests:
      storage: 500Mi
EOF

# Check binding
kubectl get pv,pvc

# Use in pod
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-pv
spec:
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: storage
      mountPath: /usr/share/nginx/html
  volumes:
  - name: storage
    persistentVolumeClaim:
      claimName: my-pvc
EOF

# Write data
kubectl exec pod-with-pv -- sh -c 'echo "Hello PV!" > /usr/share/nginx/html/index.html'

# Delete pod
kubectl delete pod pod-with-pv

# Recreate pod - data persists!
kubectl apply -f pod.yaml
kubectl exec pod-with-pv -- cat /usr/share/nginx/html/index.html
```

### Exercise 3: Dynamic Provisioning (Minikube)

```bash
# Check available storage classes
kubectl get storageclass

# Create PVC (will auto-provision PV)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dynamic-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF

# Check PV was auto-created
kubectl get pv,pvc

# Use in deployment
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-persistent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
        volumeMounts:
        - name: data
          mountPath: /usr/share/nginx/html
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: dynamic-pvc
EOF
```

## Best Practices

1. ✅ **Use PVC, not direct PV**: Abstract storage from application
2. ✅ **Use StorageClasses**: Enable dynamic provisioning
3. ✅ **Set resource requests**: Prevent over-provisioning
4. ✅ **Choose correct access mode**: RWO for databases, RWX for shared data
5. ✅ **Backup important data**: PVs are not backups!
6. ✅ **Use StatefulSets for stateful apps**: Stable storage identity
7. ✅ **Monitor storage usage**: Prevent full disks

## Common Issues

### PVC Stuck in Pending

```bash
# Check PVC events
kubectl describe pvc <name>

# Common causes:
# - No matching PV available
# - No StorageClass found
# - Insufficient storage
# - Access mode mismatch
```

### Pod Stuck in ContainerCreating

```bash
kubectl describe pod <name>

# Look for volume mount errors:
# - PVC doesn't exist
# - Node can't access storage
# - Permission issues
```

## Volume Snapshots

Create point-in-time copies of volumes:

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: my-snapshot
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: my-pvc
```

## Key Takeaways

1. Volumes provide persistent storage for containers
2. emptyDir for temporary shared storage within pod
3. PV/PVC separate storage provisioning from usage
4. StorageClasses enable dynamic provisioning
5. Choose appropriate access mode for use case
6. StatefulSets provide stable storage identity
7. Always backup critical data

## Next Steps

Learn about StatefulSets and DaemonSets for specialized workloads!

[Continue to Lesson 7: StatefulSets and DaemonSets →](07-statefulsets-daemonsets.md)

## Additional Resources

- [Volumes Documentation](https://kubernetes.io/docs/concepts/storage/volumes/)
- [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/)
