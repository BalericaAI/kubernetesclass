# Exercise 2: Working with ConfigMaps and Secrets

## Objective
Learn to externalize configuration and manage sensitive data using ConfigMaps and Secrets.

## Prerequisites
- Completed Exercise 1
- Understanding of environment variables
- Basic understanding of ConfigMaps and Secrets

## Scenario

You're deploying a web application that needs:
- Configuration settings (non-sensitive)
- Database credentials (sensitive)
- API keys (sensitive)

## Steps

### 1. Create a ConfigMap

Create `app-configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_NAME: "My Awesome App"
  APP_ENV: "development"
  LOG_LEVEL: "debug"
  DATABASE_HOST: "postgres.default.svc.cluster.local"
  DATABASE_PORT: "5432"
  DATABASE_NAME: "myapp"
  CACHE_TTL: "300"
  MAX_CONNECTIONS: "100"
```

Apply it:
```bash
kubectl apply -f app-configmap.yaml
```

### 2. Create a Secret

Create database credentials:

```bash
# Create secret from command line
kubectl create secret generic db-credentials \
  --from-literal=username=admin \
  --from-literal=password=MySecretPassword123 \
  --from-literal=api-key=super-secret-api-key-xyz
```

Or create `db-secret.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
stringData:
  username: admin
  password: MySecretPassword123
  api-key: super-secret-api-key-xyz
```

Apply it:
```bash
kubectl apply -f db-secret.yaml
```

### 3. Create Deployment Using ConfigMap and Secret

Create `app-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: app
        image: nginx:alpine
        
        # Load all ConfigMap keys as env vars
        envFrom:
        - configMapRef:
            name: app-config
        
        # Load specific Secret values
        env:
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: username
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: api-key
        
        ports:
        - containerPort: 80
```

Apply it:
```bash
kubectl apply -f app-deployment.yaml
```

### 4. Verify Environment Variables

```bash
# Get pod name
kubectl get pods -l app=myapp

# Check environment variables
kubectl exec <pod-name> -- env | grep -E 'APP_|DB_|API_'
```

### 5. Mount ConfigMap as Files

Create `app-with-volume.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-with-volume
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp-volume
  template:
    metadata:
      labels:
        app: myapp-volume
    spec:
      containers:
      - name: app
        image: nginx:alpine
        volumeMounts:
        - name: config-volume
          mountPath: /etc/config
        - name: secret-volume
          mountPath: /etc/secrets
          readOnly: true
      volumes:
      - name: config-volume
        configMap:
          name: app-config
      - name: secret-volume
        secret:
          secretName: db-credentials
```

Apply and verify:
```bash
kubectl apply -f app-with-volume.yaml

# Get pod name
kubectl get pods -l app=myapp-volume

# Check mounted files
kubectl exec <pod-name> -- ls -la /etc/config
kubectl exec <pod-name> -- ls -la /etc/secrets

# Read config values
kubectl exec <pod-name> -- cat /etc/config/APP_NAME
kubectl exec <pod-name> -- cat /etc/secrets/username
```

### 6. Update ConfigMap

```bash
# Update ConfigMap
kubectl create configmap app-config \
  --from-literal=APP_NAME="My Awesome App" \
  --from-literal=APP_ENV="production" \
  --from-literal=LOG_LEVEL="info" \
  --from-literal=DATABASE_HOST="postgres.default.svc.cluster.local" \
  --from-literal=DATABASE_PORT="5432" \
  --from-literal=DATABASE_NAME="myapp" \
  --from-literal=CACHE_TTL="600" \
  --from-literal=MAX_CONNECTIONS="200" \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart deployment to pick up changes
kubectl rollout restart deployment/myapp
```

### 7. View Secret Data (Safely)

```bash
# View secret (base64 encoded)
kubectl get secret db-credentials -o yaml

# Decode specific key
kubectl get secret db-credentials -o jsonpath='{.data.username}' | base64 --decode
```

## Clean Up

```bash
kubectl delete deployment myapp myapp-with-volume
kubectl delete configmap app-config
kubectl delete secret db-credentials
```

## Challenge Tasks

1. **Create Config File**: Create a ConfigMap from a file (e.g., nginx.conf)
2. **Use Multiple Secrets**: Create separate secrets for different purposes
3. **Selective Mounting**: Mount only specific keys from ConfigMap
4. **Update Detection**: Create a sidecar that watches for config changes
5. **Sealed Secrets**: Research and try sealed-secrets for GitOps

## Best Practices Learned

- ✅ Never hardcode configuration in images
- ✅ Use ConfigMaps for non-sensitive data
- ✅ Use Secrets for sensitive data
- ✅ Mount secrets as volumes (more secure than env vars)
- ✅ Use meaningful names for ConfigMaps and Secrets
- ✅ Version your ConfigMaps for easier rollback

## Security Notes

⚠️ **Important:**
- Secrets are base64 encoded, NOT encrypted by default
- Enable encryption at rest for production clusters
- Use RBAC to restrict secret access
- Consider external secret management (Vault, AWS Secrets Manager)
- Never commit secrets to version control

## Troubleshooting

If pods can't start:
```bash
kubectl describe pod <pod-name>

# Common issues:
# - ConfigMap/Secret doesn't exist
# - Wrong key names
# - Incorrect volume mount paths
```

## Next Steps

- Try [Exercise 3: Persistent Storage](exercise-03-persistent-storage.md)
- Explore [Lesson 5: ConfigMaps and Secrets](../lessons/05-config-secrets.md)
- Learn about [External Secrets Operator](https://external-secrets.io/)
