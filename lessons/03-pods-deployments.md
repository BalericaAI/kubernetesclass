# Lesson 3: Pods and Deployments

## Understanding Pods

A **Pod** is the smallest deployable unit in Kubernetes. It represents a single instance of a running process in your cluster.

### Key Characteristics

- **One or more containers**: Usually one, but can have multiple tightly-coupled containers
- **Shared storage**: Containers in a Pod share volumes
- **Shared network**: Containers share IP address and port space
- **Ephemeral**: Pods are designed to be disposable and replaceable

### Pod Lifecycle

```
Pending → Running → Succeeded/Failed
                 ↓
              Unknown (node communication lost)
```

**Phases:**
- **Pending**: Pod accepted but not yet running
- **Running**: Pod bound to node, at least one container running
- **Succeeded**: All containers terminated successfully
- **Failed**: All containers terminated, at least one failed
- **Unknown**: Pod state cannot be obtained

## Creating Your First Pod

### Simple Pod YAML

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
  labels:
    app: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.21
    ports:
    - containerPort: 80
```

### Apply the Pod

```bash
# Create from YAML file
kubectl apply -f nginx-pod.yaml

# Check Pod status
kubectl get pods

# Get detailed information
kubectl describe pod nginx-pod

# View Pod logs
kubectl logs nginx-pod

# Execute command in Pod
kubectl exec -it nginx-pod -- /bin/bash
```

## Multi-Container Pods

Sometimes you need multiple containers working together in a single Pod.

### Common Patterns

#### 1. Sidecar Pattern
Helper container that enhances the main container.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-sidecar
spec:
  containers:
  - name: main-app
    image: myapp:1.0
    ports:
    - containerPort: 8080
  
  - name: log-forwarder
    image: fluentd:latest
    volumeMounts:
    - name: logs
      mountPath: /var/log
  
  volumes:
  - name: logs
    emptyDir: {}
```

#### 2. Ambassador Pattern
Proxy container for external connections.

#### 3. Adapter Pattern
Standardizes output from main container.

## Container Probes

Kubernetes can check container health using probes.

### Types of Probes

1. **Liveness Probe**: Is the container alive?
2. **Readiness Probe**: Is the container ready to serve traffic?
3. **Startup Probe**: Has the container started? (for slow-starting apps)

### Example with Probes

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-probes
spec:
  containers:
  - name: webapp
    image: mywebapp:1.0
    ports:
    - containerPort: 8080
    
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
      initialDelaySeconds: 10
      periodSeconds: 5
    
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 3
    
    startupProbe:
      httpGet:
        path: /startup
        port: 8080
      failureThreshold: 30
      periodSeconds: 10
```

## Deployments: Production-Ready Pods

While Pods are the basic unit, you rarely create them directly. Instead, use **Deployments**.

### Why Deployments?

- ✅ Self-healing: Automatically replaces failed Pods
- ✅ Scaling: Easy to scale up/down
- ✅ Rolling updates: Zero-downtime updates
- ✅ Rollback: Revert to previous versions
- ✅ Declarative: Describe desired state

### Deployment Architecture

```
Deployment
    │
    ├─► ReplicaSet (v1)
    │      ├─► Pod 1
    │      ├─► Pod 2
    │      └─► Pod 3
    │
    └─► ReplicaSet (v2) [after update]
           ├─► Pod 1
           ├─► Pod 2
           └─► Pod 3
```

## Creating a Deployment

### Basic Deployment YAML

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 3
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
        image: nginx:1.21
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
```

### Deployment Commands

```bash
# Create deployment
kubectl apply -f nginx-deployment.yaml

# View deployments
kubectl get deployments

# View ReplicaSets
kubectl get rs

# View Pods
kubectl get pods

# Scale deployment
kubectl scale deployment nginx-deployment --replicas=5

# View deployment history
kubectl rollout history deployment nginx-deployment
```

## Resource Requests and Limits

### Requests vs Limits

- **Requests**: Minimum resources guaranteed to container
- **Limits**: Maximum resources container can use

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"      # 250 millicores = 0.25 CPU
  limits:
    memory: "512Mi"
    cpu: "500m"      # 500 millicores = 0.5 CPU
```

### Resource Units

**CPU:**
- `1` = 1 CPU core
- `100m` = 0.1 CPU core (100 millicores)

**Memory:**
- `Mi` = Mebibyte (1024² bytes)
- `Gi` = Gibibyte (1024³ bytes)
- `M` = Megabyte (1000² bytes)

## Rolling Updates

One of Deployment's most powerful features.

### Update Strategy

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1         # Max pods above desired count
      maxUnavailable: 0   # Max pods below desired count
```

### Performing an Update

```bash
# Update image
kubectl set image deployment/nginx-deployment \
  nginx=nginx:1.22

# Watch rollout status
kubectl rollout status deployment/nginx-deployment

# Pause rollout (if issues detected)
kubectl rollout pause deployment/nginx-deployment

# Resume rollout
kubectl rollout resume deployment/nginx-deployment
```

## Rollback

If an update causes issues, rollback quickly.

```bash
# View rollout history
kubectl rollout history deployment/nginx-deployment

# View specific revision
kubectl rollout history deployment/nginx-deployment --revision=2

# Rollback to previous version
kubectl rollout undo deployment/nginx-deployment

# Rollback to specific revision
kubectl rollout undo deployment/nginx-deployment --to-revision=2
```

## Labels and Selectors

Labels are key/value pairs attached to objects.

### Labels Example

```yaml
metadata:
  labels:
    app: nginx
    environment: production
    tier: frontend
    version: "1.21"
```

### Using Selectors

```bash
# Select by single label
kubectl get pods -l app=nginx

# Multiple labels (AND)
kubectl get pods -l app=nginx,environment=production

# Label-based selection (OR)
kubectl get pods -l 'environment in (production, staging)'

# Not equal
kubectl get pods -l app!=nginx
```

## Hands-On Exercises

### Exercise 1: Create and Manage a Pod

```bash
# Create a simple nginx pod
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: my-nginx
spec:
  containers:
  - name: nginx
    image: nginx:alpine
    ports:
    - containerPort: 80
EOF

# Check status
kubectl get pod my-nginx

# Access pod logs
kubectl logs my-nginx

# Execute command in pod
kubectl exec my-nginx -- nginx -v

# Port forward to access locally
kubectl port-forward pod/my-nginx 8080:80

# Visit http://localhost:8080 in browser

# Clean up
kubectl delete pod my-nginx
```

### Exercise 2: Create a Deployment

```bash
# Create deployment imperatively
kubectl create deployment web --image=nginx:alpine --replicas=3

# Expose as service (we'll cover services next lesson)
kubectl expose deployment web --port=80 --type=NodePort

# Get service details
kubectl get service web

# Scale deployment
kubectl scale deployment web --replicas=5

# Update image
kubectl set image deployment/web nginx=nginx:1.21-alpine

# Check rollout status
kubectl rollout status deployment/web

# View history
kubectl rollout history deployment/web

# Rollback
kubectl rollout undo deployment/web

# Clean up
kubectl delete deployment web
kubectl delete service web
```

### Exercise 3: Deployment with Resource Limits

Create file `resource-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resource-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: demo
  template:
    metadata:
      labels:
        app: demo
    spec:
      containers:
      - name: app
        image: nginx:alpine
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 5
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 3
```

```bash
kubectl apply -f resource-deployment.yaml
kubectl get pods -l app=demo
kubectl describe pod <pod-name>
```

## Best Practices

1. **Always use Deployments**, not bare Pods
2. **Set resource requests and limits** for predictability
3. **Use health probes** for production workloads
4. **Use meaningful labels** for organization
5. **Keep container images small** for faster pulls
6. **Don't use :latest tag** in production
7. **One process per container** (generally)
8. **Store configuration externally** (ConfigMaps/Secrets)

## Common Issues and Troubleshooting

### Pod Stuck in Pending
- Check node resources: `kubectl describe nodes`
- Check events: `kubectl describe pod <name>`
- Verify image exists and is pullable

### Pod CrashLoopBackOff
- Check logs: `kubectl logs <pod-name>`
- Check previous logs: `kubectl logs <pod-name> --previous`
- Verify liveness/readiness probes aren't too aggressive

### ImagePullBackOff
- Verify image name and tag
- Check image registry authentication
- Ensure network connectivity

## Key Takeaways

1. Pods are the basic unit, but use Deployments in practice
2. Deployments provide self-healing, scaling, and updates
3. Always set resource requests and limits
4. Use probes to ensure application health
5. Rolling updates enable zero-downtime deployments
6. Labels and selectors organize and select resources
7. Rollbacks provide safety net for bad updates

## Next Steps

Now that you can deploy and manage applications, let's learn how to expose them to users!

[Continue to Lesson 4: Services and Networking →](04-services-networking.md)

## Additional Resources

- [Pod Documentation](https://kubernetes.io/docs/concepts/workloads/pods/)
- [Deployment Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Resource Management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
