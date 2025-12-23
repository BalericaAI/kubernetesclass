# Lesson 7: StatefulSets and DaemonSets

## StatefulSets: For Stateful Applications

While Deployments are great for stateless apps, some applications need:
- Stable network identities
- Stable persistent storage
- Ordered deployment and scaling
- Ordered rolling updates

**StatefulSets** provide these guarantees.

## StatefulSet vs Deployment

| Feature | Deployment | StatefulSet |
|---------|-----------|-------------|
| Pod names | Random suffix | Ordinal index (0,1,2...) |
| Network identity | Changes on restart | Stable DNS name |
| Storage | Shared or none | Dedicated per pod |
| Scaling | Parallel | Sequential |
| Updates | Any order | Ordered |
| Use case | Stateless apps | Databases, queues |

## StatefulSet Components

### 1. Headless Service

Required for network identity:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mysql
spec:
  clusterIP: None  # Headless!
  selector:
    app: mysql
  ports:
  - port: 3306
    name: mysql
```

### 2. StatefulSet

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
        ports:
        - containerPort: 3306
          name: mysql
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: password
        volumeMounts:
        - name: data
          mountPath: /var/lib/mysql
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

## Stable Network Identity

Each pod gets a predictable DNS name:

```
<statefulset-name>-<ordinal>.<service-name>.<namespace>.svc.cluster.local

Examples:
mysql-0.mysql.default.svc.cluster.local
mysql-1.mysql.default.svc.cluster.local
mysql-2.mysql.default.svc.cluster.local
```

### Accessing Pods

```bash
# From within cluster
mysql -h mysql-0.mysql.default.svc.cluster.local -p

# Each pod has stable identity even after restart!
```

## Ordered Operations

### Scaling Up
Pods created sequentially: 0 → 1 → 2

```bash
kubectl scale statefulset mysql --replicas=5
# Creates: mysql-3, then mysql-4
```

### Scaling Down
Pods terminated in reverse: N → N-1 → ... → 0

```bash
kubectl scale statefulset mysql --replicas=2
# Deletes: mysql-4, then mysql-3
```

### Rolling Updates
Updates in reverse ordinal order with delay between each:

```bash
kubectl set image statefulset/mysql mysql=mysql:8.0.30
# Updates: mysql-2, waits, then mysql-1, waits, then mysql-0
```

## Partition Updates

Update only pods with ordinal >= partition:

```yaml
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2
```

Now only `mysql-2`, `mysql-3`, etc. will be updated. Useful for canary deployments!

## Persistent Storage

### Volume Claim Templates

Each pod gets its own PVC:

```yaml
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

Creates:
- `data-mysql-0` → used by `mysql-0`
- `data-mysql-1` → used by `mysql-1`
- `data-mysql-2` → used by `mysql-2`

### PVC Lifecycle

⚠️ **Important**: PVCs are NOT deleted when StatefulSet is deleted!

```bash
# Delete StatefulSet (keeps PVCs)
kubectl delete statefulset mysql

# Recreate - pods rebind to existing PVCs!
kubectl apply -f mysql-statefulset.yaml

# Manually delete PVCs if needed
kubectl delete pvc data-mysql-0 data-mysql-1 data-mysql-2
```

## StatefulSet Patterns

### 1. Leader Election

```yaml
# Pod mysql-0 is typically the primary/leader
# Pods mysql-1, mysql-2, ... are replicas

apiVersion: v1
kind: ConfigMap
metadata:
  name: mysql-config
data:
  primary.cnf: |
    [mysqld]
    log-bin
  replica.cnf: |
    [mysqld]
    super-read-only
```

### 2. MongoDB Replica Set

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb
spec:
  serviceName: mongodb
  replicas: 3
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:6.0
        command:
        - mongod
        - "--replSet"
        - rs0
        - "--bind_ip_all"
        ports:
        - containerPort: 27017
        volumeMounts:
        - name: data
          mountPath: /data/db
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 5Gi
```

## DaemonSets: One Pod Per Node

Ensures a pod runs on every node (or selected nodes).

### Use Cases

- **Logging agents** (Fluentd, Filebeat)
- **Monitoring agents** (Prometheus Node Exporter)
- **Network plugins** (Calico, Weave)
- **Storage daemons** (Ceph, GlusterFS)

### Basic DaemonSet

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  namespace: kube-system
spec:
  selector:
    matchLabels:
      name: fluentd
  template:
    metadata:
      labels:
        name: fluentd
    spec:
      containers:
      - name: fluentd
        image: fluentd:v1.14
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
```

## Node Selection for DaemonSets

### Node Selector

Run only on specific nodes:

```yaml
spec:
  template:
    spec:
      nodeSelector:
        disk: ssd
```

### Node Affinity

More flexible node selection:

```yaml
spec:
  template:
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/os
                operator: In
                values:
                - linux
```

### Tolerations

Run on tainted nodes:

```yaml
spec:
  template:
    spec:
      tolerations:
      - key: node-role.kubernetes.io/master
        effect: NoSchedule
```

## DaemonSet Update Strategies

### RollingUpdate (Default)

```yaml
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
```

### OnDelete

Manual updates - pods updated only when manually deleted:

```yaml
spec:
  updateStrategy:
    type: OnDelete
```

## Hands-On Exercises

### Exercise 1: Deploy a StatefulSet

```bash
# Create headless service
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: nginx-headless
spec:
  clusterIP: None
  selector:
    app: nginx-stateful
  ports:
  - port: 80
    name: web
EOF

# Create StatefulSet
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: nginx-headless
  replicas: 3
  selector:
    matchLabels:
      app: nginx-stateful
  template:
    metadata:
      labels:
        app: nginx-stateful
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
          name: web
        volumeMounts:
        - name: www
          mountPath: /usr/share/nginx/html
  volumeClaimTemplates:
  - metadata:
      name: www
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
EOF

# Watch pods being created sequentially
kubectl get pods -w

# Check stable network identity
for i in 0 1 2; do
  kubectl exec web-$i -- hostname
done

# Write unique data to each pod
for i in 0 1 2; do
  kubectl exec web-$i -- sh -c "echo 'Hello from web-$i' > /usr/share/nginx/html/index.html"
done

# Test persistence - delete a pod
kubectl delete pod web-0

# Check data persisted
kubectl exec web-0 -- cat /usr/share/nginx/html/index.html

# Scale down
kubectl scale statefulset web --replicas=1

# Check PVCs still exist
kubectl get pvc
```

### Exercise 2: DaemonSet for Monitoring

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: default
spec:
  selector:
    matchLabels:
      name: node-exporter
  template:
    metadata:
      labels:
        name: node-exporter
    spec:
      hostNetwork: true
      hostPID: true
      containers:
      - name: node-exporter
        image: prom/node-exporter:latest
        ports:
        - containerPort: 9100
          hostPort: 9100
        volumeMounts:
        - name: proc
          mountPath: /host/proc
          readOnly: true
        - name: sys
          mountPath: /host/sys
          readOnly: true
      volumes:
      - name: proc
        hostPath:
          path: /proc
      - name: sys
        hostPath:
          path: /sys
EOF

# Check pods on each node
kubectl get pods -o wide

# Check metrics from a pod
kubectl exec node-exporter-<pod-suffix> -- wget -qO- http://localhost:9100/metrics | head -20
```

### Exercise 3: StatefulSet with Init Container

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: cassandra
spec:
  clusterIP: None
  selector:
    app: cassandra
  ports:
  - port: 9042
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: cassandra
spec:
  serviceName: cassandra
  replicas: 3
  selector:
    matchLabels:
      app: cassandra
  template:
    metadata:
      labels:
        app: cassandra
    spec:
      initContainers:
      - name: init-config
        image: busybox
        command: ['sh', '-c', 'echo "Initialized at $(date)" > /data/init.txt']
        volumeMounts:
        - name: data
          mountPath: /data
      containers:
      - name: cassandra
        image: cassandra:4.0
        ports:
        - containerPort: 9042
        env:
        - name: CASSANDRA_SEEDS
          value: cassandra-0.cassandra.default.svc.cluster.local
        - name: MAX_HEAP_SIZE
          value: 512M
        - name: HEAP_NEWSIZE
          value: 100M
        volumeMounts:
        - name: data
          mountPath: /var/lib/cassandra
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 2Gi
EOF

# Watch pods come up
kubectl get pods -l app=cassandra -w
```

## Best Practices

### StatefulSets
1. ✅ Always use a headless service
2. ✅ Set pod disruption budgets
3. ✅ Use init containers for setup
4. ✅ Implement proper readiness probes
5. ✅ Plan storage capacity carefully
6. ✅ Consider backup strategies
7. ✅ Use partition updates for canary deployments

### DaemonSets
1. ✅ Set resource limits (affects all nodes!)
2. ✅ Use tolerations carefully
3. ✅ Implement proper logging
4. ✅ Monitor resource usage per node
5. ✅ Consider update strategy impact

## Troubleshooting

```bash
# StatefulSet pod stuck
kubectl describe statefulset <name>
kubectl describe pod <pod-name>
kubectl get events --sort-by='.lastTimestamp'

# Check PVC binding
kubectl get pvc

# Check pod logs
kubectl logs <pod-name>

# DaemonSet not scheduling
kubectl describe daemonset <name>
kubectl describe nodes
kubectl get nodes --show-labels
```

## Key Takeaways

1. StatefulSets provide stable identity and storage for stateful apps
2. Pods are created/deleted sequentially with predictable names
3. Each pod gets its own persistent volume
4. DaemonSets ensure pods run on every (or selected) nodes
5. Use StatefulSets for databases, queues, clustered apps
6. Use DaemonSets for node-level services (monitoring, logging)

## Next Steps

Learn about Jobs and CronJobs for batch workloads!

[Continue to Lesson 8: Jobs and CronJobs →](08-jobs-cronjobs.md)

## Additional Resources

- [StatefulSets Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [DaemonSets Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/)
- [Running Cassandra on Kubernetes](https://kubernetes.io/docs/tutorials/stateful-application/cassandra/)
