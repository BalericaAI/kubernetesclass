# Lesson 4: Services and Networking

## Why Services?

Pods are ephemeral - they come and go. When a Pod restarts, it gets a new IP address. **Services** provide:
- Stable IP addresses
- DNS names for service discovery
- Load balancing across Pods
- External access to applications

## Service Types

### 1. ClusterIP (Default)

Exposes service on an internal cluster IP. Only reachable within the cluster.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  type: ClusterIP
  selector:
    app: nginx
  ports:
  - port: 80        # Service port
    targetPort: 80  # Container port
```

**Use case:** Internal microservices communication

### 2. NodePort

Exposes service on each Node's IP at a static port (30000-32767).

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-nodeport-service
spec:
  type: NodePort
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080  # Optional, will be auto-assigned if omitted
```

**Access:** `<NodeIP>:30080`

**Use case:** Development, testing, or when you need direct node access

### 3. LoadBalancer

Creates an external load balancer (cloud provider dependent).

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-loadbalancer
spec:
  type: LoadBalancer
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
```

**Use case:** Production external access (requires cloud provider)

### 4. ExternalName

Maps service to a DNS name.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-db
spec:
  type: ExternalName
  externalName: database.example.com
```

## Service Discovery

### DNS-Based Discovery

Every Service gets a DNS name: `<service-name>.<namespace>.svc.cluster.local`

```bash
# From within a Pod:
curl http://my-service.default.svc.cluster.local
# or simply:
curl http://my-service
```

### Environment Variables

Kubernetes injects service information as environment variables:

```bash
MY_SERVICE_SERVICE_HOST=10.0.0.1
MY_SERVICE_SERVICE_PORT=80
```

## Endpoints

Services route traffic to Pods via **Endpoints**.

```bash
# View service endpoints
kubectl get endpoints my-service

# Describe service (includes endpoints)
kubectl describe service my-service
```

Endpoints are automatically created/updated when:
- Pods matching the selector are created/deleted
- Pods pass/fail readiness probes

## Ingress

**Ingress** provides HTTP/HTTPS routing to services based on rules.

### Why Ingress?

- Single entry point for multiple services
- Path-based routing
- Host-based routing
- SSL/TLS termination
- Cost-effective (one LoadBalancer instead of many)

### Ingress Controller

Ingress resources need an Ingress Controller (not included by default):
- **NGINX Ingress Controller** (most popular)
- **Traefik**
- **HAProxy**
- **Cloud provider controllers** (ALB, GCE)

### Installing NGINX Ingress Controller

```bash
# For minikube
minikube addons enable ingress

# For generic Kubernetes
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
```

### Basic Ingress Example

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: simple-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

### Path-Based Routing

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: path-based-ingress
spec:
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8080
      - path: /web
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

### Host-Based Routing

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: host-based-ingress
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8080
  - host: www.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

### TLS/SSL with Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tls-ingress
spec:
  tls:
  - hosts:
    - myapp.example.com
    secretName: tls-secret
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

Create TLS secret:
```bash
kubectl create secret tls tls-secret \
  --cert=path/to/cert.pem \
  --key=path/to/key.pem
```

## Network Policies

Control traffic between Pods (firewall rules for Kubernetes).

### Default Behavior

By default, all Pods can communicate with all Pods.

### Deny All Traffic

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

### Allow Specific Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

### Allow Specific Egress

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns-egress
spec:
  podSelector:
    matchLabels:
      app: myapp
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53
```

## Hands-On Exercises

### Exercise 1: Create and Test Services

```bash
# Create a deployment
kubectl create deployment nginx --image=nginx:alpine --replicas=3

# Create ClusterIP service
kubectl expose deployment nginx --port=80 --type=ClusterIP

# Test from within cluster
kubectl run test-pod --image=busybox --rm -it --restart=Never -- wget -qO- http://nginx

# Create NodePort service
kubectl expose deployment nginx --port=80 --type=NodePort --name=nginx-nodeport

# Get NodePort
kubectl get service nginx-nodeport

# Access via minikube (if using minikube)
minikube service nginx-nodeport
```

### Exercise 2: Full Application with Ingress

Create `app-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: myapp.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

```bash
# Apply configuration
kubectl apply -f app-deployment.yaml

# Check resources
kubectl get deployments,services,ingress

# Add to /etc/hosts (if testing locally)
echo "$(minikube ip) myapp.local" | sudo tee -a /etc/hosts

# Test
curl http://myapp.local
```

### Exercise 3: Network Policies

```bash
# Create two deployments
kubectl create deployment frontend --image=nginx:alpine
kubectl create deployment backend --image=nginx:alpine

# Expose backend
kubectl expose deployment backend --port=80

# Test connectivity (should work)
kubectl run test --image=busybox --rm -it --restart=Never -- wget -qO- http://backend

# Apply deny-all policy
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-backend
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
EOF

# Test again (should fail)
kubectl run test --image=busybox --rm -it --restart=Never -- wget -qO- http://backend

# Allow from frontend
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
EOF
```

## Service Mesh

For complex microservices, consider a service mesh:

### What is a Service Mesh?

Infrastructure layer for service-to-service communication providing:
- Traffic management
- Security (mTLS)
- Observability
- Resilience

### Popular Service Meshes
- **Istio** (most feature-rich)
- **Linkerd** (lightweight)
- **Consul Connect**

## Best Practices

1. **Use ClusterIP** for internal services
2. **Use LoadBalancer** for production external access
3. **Use Ingress** for HTTP/HTTPS routing
4. **Implement Network Policies** for security
5. **Use meaningful service names** (they become DNS names)
6. **Set readiness probes** so unhealthy pods don't receive traffic
7. **Consider service mesh** for complex microservices

## Troubleshooting

### Service Not Reachable

```bash
# Check service exists
kubectl get service <name>

# Check endpoints (should list pod IPs)
kubectl get endpoints <name>

# Verify selector matches pods
kubectl get pods --show-labels
kubectl describe service <name>

# Test DNS resolution
kubectl run test --image=busybox --rm -it --restart=Never -- nslookup <service-name>

# Check network policies
kubectl get networkpolicies
```

### Ingress Not Working

```bash
# Check ingress controller is running
kubectl get pods -n ingress-nginx

# Check ingress resource
kubectl describe ingress <name>

# Check ingress controller logs
kubectl logs -n ingress-nginx <controller-pod>

# Verify DNS/hosts file
cat /etc/hosts
```

## Key Takeaways

1. Services provide stable endpoints for ephemeral Pods
2. ClusterIP for internal, LoadBalancer for external access
3. Ingress provides HTTP/HTTPS routing to multiple services
4. Network Policies control Pod-to-Pod communication
5. Service discovery works via DNS or environment variables
6. Readiness probes prevent traffic to unhealthy pods

## Next Steps

Learn how to manage configuration and sensitive data!

[Continue to Lesson 5: ConfigMaps and Secrets →](05-config-secrets.md)

## Additional Resources

- [Service Documentation](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Ingress Documentation](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
