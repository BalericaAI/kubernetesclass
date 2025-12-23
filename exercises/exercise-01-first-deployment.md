# Exercise 1: Deploy Your First Application

## Objective
Deploy a simple web application with multiple replicas and expose it via a Service.

## Prerequisites
- kubectl installed
- Access to a Kubernetes cluster
- Basic understanding of Pods and Deployments

## Steps

### 1. Create a Deployment

Create a file named `nginx-deployment.yaml`:

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
        image: nginx:1.21-alpine
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

Apply it:
```bash
kubectl apply -f nginx-deployment.yaml
```

### 2. Verify Deployment

```bash
# Check deployment
kubectl get deployments

# Check pods
kubectl get pods -l app=nginx

# Get detailed info
kubectl describe deployment nginx-deployment
```

### 3. Create a Service

Create a file named `nginx-service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  type: NodePort
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080
```

Apply it:
```bash
kubectl apply -f nginx-service.yaml
```

### 4. Test the Service

```bash
# Get service info
kubectl get service nginx-service

# If using Minikube
minikube service nginx-service

# Or use port-forward
kubectl port-forward service/nginx-service 8080:80

# Visit http://localhost:8080 in your browser
```

### 5. Scale the Deployment

```bash
# Scale up
kubectl scale deployment nginx-deployment --replicas=5

# Verify
kubectl get pods -l app=nginx

# Scale down
kubectl scale deployment nginx-deployment --replicas=2
```

### 6. Update the Application

```bash
# Update image
kubectl set image deployment/nginx-deployment nginx=nginx:1.22-alpine

# Watch rollout
kubectl rollout status deployment/nginx-deployment

# Check rollout history
kubectl rollout history deployment/nginx-deployment
```

### 7. Rollback if Needed

```bash
# Rollback to previous version
kubectl rollout undo deployment/nginx-deployment

# Rollback to specific revision
kubectl rollout undo deployment/nginx-deployment --to-revision=1
```

## Clean Up

```bash
kubectl delete service nginx-service
kubectl delete deployment nginx-deployment
```

## Challenge Tasks

1. **Add Health Checks**: Add liveness and readiness probes to the deployment
2. **Use ConfigMap**: Create a ConfigMap for nginx configuration
3. **Add Resource Limits**: Experiment with different resource limits
4. **Create Ingress**: Instead of NodePort, expose via Ingress
5. **Multi-Container Pod**: Add a sidecar container for logging

## Expected Output

After completing this exercise, you should have:
- ✅ A running deployment with 3 replicas
- ✅ A service exposing the deployment
- ✅ Ability to access the application
- ✅ Experience scaling and updating deployments
- ✅ Understanding of rollouts and rollbacks

## Troubleshooting Tips

If pods are not starting:
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

If service is not accessible:
```bash
kubectl get endpoints nginx-service
kubectl describe service nginx-service
```

## Next Steps

- Try [Exercise 2: ConfigMaps and Secrets](exercise-02-config-secrets.md)
- Explore [Lesson 4: Services and Networking](../lessons/04-services-networking.md)
