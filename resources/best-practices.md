# Kubernetes Best Practices and Troubleshooting Guide

## Best Practices

### 1. Resource Management

#### Always Set Resource Requests and Limits

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

**Why?**
- Prevents resource starvation
- Enables proper scheduling
- Protects against runaway processes

#### Use Namespace Resource Quotas

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: dev
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
```

### 2. High Availability

#### Use Multiple Replicas

```yaml
spec:
  replicas: 3  # Minimum for HA
```

#### Configure Pod Disruption Budgets

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: app-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: myapp
```

#### Implement Health Probes

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

### 3. Security

#### Run as Non-Root User

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 2000
```

#### Use Read-Only Root Filesystem

```yaml
securityContext:
  readOnlyRootFilesystem: true
```

#### Limit Capabilities

```yaml
securityContext:
  capabilities:
    drop:
    - ALL
    add:
    - NET_BIND_SERVICE
```

#### Never Store Secrets in Code

```yaml
# ❌ Bad
env:
- name: PASSWORD
  value: "mypassword"

# ✅ Good
env:
- name: PASSWORD
  valueFrom:
    secretKeyRef:
      name: db-secret
      key: password
```

#### Use Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

### 4. Configuration Management

#### Use ConfigMaps and Secrets

```yaml
# Don't hardcode configuration
envFrom:
- configMapRef:
    name: app-config
```

#### Version Your ConfigMaps

```yaml
# Version them in names
app-config-v1
app-config-v2
```

### 5. Labels and Annotations

#### Use Consistent Labels

```yaml
metadata:
  labels:
    app: myapp
    version: "1.0"
    environment: production
    team: backend
    component: api
```

#### Recommended Labels

```yaml
app.kubernetes.io/name: myapp
app.kubernetes.io/instance: myapp-prod
app.kubernetes.io/version: "1.0.0"
app.kubernetes.io/component: api
app.kubernetes.io/part-of: ecommerce
app.kubernetes.io/managed-by: helm
```

### 6. Image Management

#### Use Specific Tags

```yaml
# ❌ Bad
image: nginx:latest

# ✅ Good
image: nginx:1.21.6-alpine
```

#### Specify Image Pull Policy

```yaml
imagePullPolicy: IfNotPresent  # or Always, Never
```

### 7. Logging and Monitoring

#### Structured Logging

Log in JSON format for better parsing:

```json
{"level":"info","timestamp":"2024-01-01T12:00:00Z","message":"Request processed","duration_ms":45}
```

#### Export Metrics

Expose Prometheus metrics:

```yaml
ports:
- name: metrics
  containerPort: 9090
```

### 8. Deployment Strategies

#### Use Rolling Updates

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

#### Implement Graceful Shutdown

```yaml
lifecycle:
  preStop:
    exec:
      command: ["/bin/sh", "-c", "sleep 15"]
```

Set appropriate termination grace period:

```yaml
terminationGracePeriodSeconds: 30
```

## Troubleshooting Guide

### Pod Issues

#### Pod Stuck in Pending

**Symptoms:**
```bash
NAME                   READY   STATUS    RESTARTS   AGE
myapp-7b4f5d8c-xyz12   0/1     Pending   0          2m
```

**Diagnosis:**
```bash
kubectl describe pod myapp-7b4f5d8c-xyz12
kubectl get events --sort-by='.lastTimestamp'
```

**Common Causes:**
1. **Insufficient resources**
   - Check: `kubectl describe nodes`
   - Solution: Scale down other apps or add nodes

2. **PVC not bound**
   - Check: `kubectl get pvc`
   - Solution: Check StorageClass and PV availability

3. **Node selector mismatch**
   - Check: Pod spec's `nodeSelector` vs node labels
   - Solution: Update nodeSelector or add labels to nodes

#### CrashLoopBackOff

**Symptoms:**
```bash
NAME                   READY   STATUS             RESTARTS   AGE
myapp-7b4f5d8c-xyz12   0/1     CrashLoopBackOff   5          5m
```

**Diagnosis:**
```bash
kubectl logs myapp-7b4f5d8c-xyz12
kubectl logs myapp-7b4f5d8c-xyz12 --previous
kubectl describe pod myapp-7b4f5d8c-xyz12
```

**Common Causes:**
1. **Application error**
   - Check logs for error messages
   - Verify environment variables

2. **Liveness probe too aggressive**
   - Increase `initialDelaySeconds`
   - Increase `failureThreshold`

3. **Missing dependencies**
   - Check ConfigMaps and Secrets exist
   - Verify volumes are mounted

#### ImagePullBackOff

**Symptoms:**
```bash
NAME                   READY   STATUS             RESTARTS   AGE
myapp-7b4f5d8c-xyz12   0/1     ImagePullBackOff   0          1m
```

**Diagnosis:**
```bash
kubectl describe pod myapp-7b4f5d8c-xyz12
```

**Common Causes:**
1. **Image doesn't exist**
   - Verify image name and tag
   - Check registry

2. **Authentication required**
   - Create imagePullSecret
   - Add to pod spec

3. **Network issues**
   - Check node connectivity
   - Verify DNS resolution

### Service Issues

#### Service Not Reachable

**Diagnosis:**
```bash
# Check service
kubectl get service myapp

# Check endpoints
kubectl get endpoints myapp

# Should show pod IPs
kubectl describe service myapp
```

**Common Causes:**
1. **No endpoints**
   - Verify selector matches pod labels
   - Check pods are ready (readiness probe)

2. **Wrong port**
   - Verify targetPort matches container port

3. **Network policy blocking**
   - Check network policies
   - Test with policy disabled

**Test connectivity:**
```bash
# From inside cluster
kubectl run test --image=busybox --rm -it --restart=Never -- wget -qO- http://myapp

# Port forward
kubectl port-forward service/myapp 8080:80
curl http://localhost:8080
```

### Storage Issues

#### PVC Stuck in Pending

**Diagnosis:**
```bash
kubectl describe pvc my-pvc
kubectl get pv
kubectl get storageclass
```

**Common Causes:**
1. **No matching PV**
   - Check accessMode matches
   - Check storage size requested

2. **StorageClass doesn't exist**
   - Create StorageClass or use existing
   - Specify correct storageClassName

3. **Dynamic provisioning failed**
   - Check provisioner logs
   - Verify cloud permissions

### Node Issues

#### Node NotReady

**Diagnosis:**
```bash
kubectl get nodes
kubectl describe node <node-name>
kubectl get events --field-selector involvedObject.name=<node-name>
```

**Common Causes:**
1. **Kubelet not running**
   - SSH to node: `systemctl status kubelet`

2. **Network plugin issues**
   - Check network plugin pods

3. **Disk pressure**
   - Check disk usage: `df -h`

### Ingress Issues

#### Ingress Not Working

**Diagnosis:**
```bash
kubectl get ingress
kubectl describe ingress myapp
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx <controller-pod>
```

**Common Causes:**
1. **Ingress controller not running**
   - Install/enable ingress controller

2. **Wrong host/path**
   - Check ingress rules
   - Verify DNS/hosts file

3. **Service backend doesn't exist**
   - Verify service name and port

## Debugging Techniques

### Interactive Debugging

```bash
# Execute shell in pod
kubectl exec -it myapp-7b4f5d8c-xyz12 -- /bin/sh

# Run debug container
kubectl debug myapp-7b4f5d8c-xyz12 -it --image=busybox

# Copy files from pod
kubectl cp myapp-7b4f5d8c-xyz12:/var/log/app.log ./app.log
```

### Network Debugging

```bash
# Run network tools
kubectl run netdebug --image=nicolaka/netshoot --rm -it --restart=Never

# DNS debugging
kubectl run dnstest --image=busybox --rm -it --restart=Never -- nslookup kubernetes.default

# Test service
kubectl run curl --image=curlimages/curl --rm -it --restart=Never -- curl http://myapp
```

### Resource Monitoring

```bash
# Top nodes
kubectl top nodes

# Top pods
kubectl top pods
kubectl top pods --all-namespaces --sort-by=memory

# Describe resource usage
kubectl describe node <node-name>
```

## Common kubectl Commands Reference

```bash
# Get resources
kubectl get pods
kubectl get pods -o wide
kubectl get pods --all-namespaces
kubectl get all

# Describe resource
kubectl describe pod <name>

# Logs
kubectl logs <pod-name>
kubectl logs <pod-name> -c <container-name>
kubectl logs <pod-name> --previous
kubectl logs -f <pod-name>  # Follow

# Edit resource
kubectl edit deployment <name>

# Scale
kubectl scale deployment <name> --replicas=5

# Delete
kubectl delete pod <name>
kubectl delete -f manifest.yaml

# Apply/Create
kubectl apply -f manifest.yaml
kubectl create deployment nginx --image=nginx

# Port forward
kubectl port-forward pod/<name> 8080:80

# Exec
kubectl exec <pod-name> -- command
kubectl exec -it <pod-name> -- /bin/sh

# Events
kubectl get events --sort-by='.lastTimestamp'
kubectl get events --watch

# Resource usage
kubectl top nodes
kubectl top pods
```

## When to Ask for Help

If you've tried troubleshooting and still stuck:

1. **Gather information:**
   ```bash
   kubectl get all
   kubectl describe pod <name>
   kubectl logs <pod-name>
   kubectl get events
   ```

2. **Check documentation:**
   - Official Kubernetes docs
   - Relevant tool documentation

3. **Search for errors:**
   - Google error messages
   - Check GitHub issues

4. **Ask the community:**
   - Kubernetes Slack
   - Stack Overflow
   - Reddit r/kubernetes

## Additional Resources

- [Official Kubernetes Documentation](https://kubernetes.io/docs/)
- [Troubleshooting Guide](https://kubernetes.io/docs/tasks/debug/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Kubernetes Patterns Book](https://www.oreilly.com/library/view/kubernetes-patterns/9781492050278/)
