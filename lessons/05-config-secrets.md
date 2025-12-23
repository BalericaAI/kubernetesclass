# Lesson 5: ConfigMaps and Secrets

## Configuration Management in Kubernetes

Modern applications require external configuration to:
- Work in different environments (dev, staging, prod)
- Change behavior without rebuilding images
- Store sensitive data securely

Kubernetes provides two resources for this:
- **ConfigMaps**: Non-sensitive configuration data
- **Secrets**: Sensitive data (passwords, tokens, keys)

## ConfigMaps

ConfigMaps store configuration as key-value pairs.

### Creating ConfigMaps

#### From Literal Values

```bash
kubectl create configmap app-config \
  --from-literal=database_host=mysql.example.com \
  --from-literal=database_port=3306 \
  --from-literal=log_level=info
```

#### From Files

```bash
# Create config file
cat > app.properties <<EOF
database.host=mysql.example.com
database.port=3306
log.level=info
EOF

# Create ConfigMap from file
kubectl create configmap app-config --from-file=app.properties
```

#### From YAML

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database_host: "mysql.example.com"
  database_port: "3306"
  log_level: "info"
  app.properties: |
    database.host=mysql.example.com
    database.port=3306
    log.level=info
```

### Using ConfigMaps in Pods

#### As Environment Variables

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:1.0
    env:
    - name: DATABASE_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database_host
    - name: DATABASE_PORT
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database_port
```

#### All Keys as Environment Variables

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:1.0
    envFrom:
    - configMapRef:
        name: app-config
```

#### As Volume Mounts

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:1.0
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config
  volumes:
  - name: config-volume
    configMap:
      name: app-config
```

Now `/etc/config/` contains files for each key in the ConfigMap.

## Secrets

Secrets store sensitive data (base64 encoded).

### Types of Secrets

- **generic**: Arbitrary user-defined data
- **docker-registry**: Docker registry credentials
- **tls**: TLS certificate and key

### Creating Secrets

#### From Literal Values

```bash
kubectl create secret generic db-secret \
  --from-literal=username=admin \
  --from-literal=password=secretpassword123
```

#### From Files

```bash
echo -n 'admin' > username.txt
echo -n 'secretpassword123' > password.txt

kubectl create secret generic db-secret \
  --from-file=username=username.txt \
  --from-file=password=password.txt
```

#### From YAML

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  username: YWRtaW4=           # base64 encoded "admin"
  password: c2VjcmV0cGFzc3dvcmQxMjM=  # base64 encoded "secretpassword123"
```

Encode/decode base64:
```bash
echo -n 'admin' | base64
echo 'YWRtaW4=' | base64 --decode
```

#### Docker Registry Secret

```bash
kubectl create secret docker-registry regcred \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=myuser \
  --docker-password=mypassword \
  --docker-email=myemail@example.com
```

### Using Secrets in Pods

#### As Environment Variables

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:1.0
    env:
    - name: DB_USERNAME
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: username
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: password
```

#### As Volume Mounts

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:1.0
    volumeMounts:
    - name: secret-volume
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secret-volume
    secret:
      secretName: db-secret
```

#### For Image Pull

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: private-image-pod
spec:
  containers:
  - name: app
    image: myregistry.com/private/myapp:1.0
  imagePullSecrets:
  - name: regcred
```

## Best Practices

### ConfigMaps

1. ✅ **Separate config from code**: Never hardcode configuration
2. ✅ **Use per-environment ConfigMaps**: `app-config-dev`, `app-config-prod`
3. ✅ **Keep ConfigMaps small**: Large ConfigMaps slow down pod startup
4. ✅ **Use volume mounts for large configs**: Better than env vars for files
5. ✅ **Document all keys**: Make it clear what each setting does

### Secrets

1. 🔒 **Never commit secrets to Git**: Use secret management tools
2. 🔒 **Enable encryption at rest**: Encrypt etcd data
3. 🔒 **Use RBAC**: Limit who can read secrets
4. 🔒 **Rotate secrets regularly**: Change passwords/keys periodically
5. 🔒 **Use external secret managers**: Vault, AWS Secrets Manager, etc.
6. 🔒 **Don't log secrets**: Be careful with error messages
7. 🔒 **Use volume mounts over env vars**: More secure (not visible in describe)

## Hands-On Exercises

### Exercise 1: Application Configuration

```bash
# Create ConfigMap for web app
kubectl create configmap webapp-config \
  --from-literal=api_url=https://api.example.com \
  --from-literal=cache_ttl=300 \
  --from-literal=max_connections=100

# Create deployment using ConfigMap
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        envFrom:
        - configMapRef:
            name: webapp-config
EOF

# Verify environment variables
kubectl exec deployment/webapp -- env | grep -E 'api_url|cache_ttl|max_connections'

# Update ConfigMap
kubectl create configmap webapp-config \
  --from-literal=api_url=https://api.example.com \
  --from-literal=cache_ttl=600 \
  --from-literal=max_connections=200 \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart deployment to pick up changes
kubectl rollout restart deployment/webapp
```

### Exercise 2: Database Credentials with Secrets

```bash
# Create secret for database
kubectl create secret generic mysql-secret \
  --from-literal=root-password=MySecretRootPass123 \
  --from-literal=database=myappdb \
  --from-literal=username=appuser \
  --from-literal=password=AppUserPass456

# Deploy MySQL with secret
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
spec:
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
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: root-password
        - name: MYSQL_DATABASE
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: database
        - name: MYSQL_USER
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: username
        - name: MYSQL_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: password
        ports:
        - containerPort: 3306
EOF

# Verify (secrets won't be visible in describe)
kubectl describe deployment mysql
kubectl get secret mysql-secret -o yaml
```

### Exercise 3: Configuration Files as Volumes

```bash
# Create nginx config
cat > nginx.conf <<EOF
server {
    listen 80;
    server_name example.com;
    
    location / {
        root /usr/share/nginx/html;
        index index.html;
    }
    
    location /api {
        proxy_pass http://backend:8080;
    }
}
EOF

# Create ConfigMap from file
kubectl create configmap nginx-config --from-file=nginx.conf

# Deploy with mounted config
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-custom
spec:
  selector:
    matchLabels:
      app: nginx-custom
  template:
    metadata:
      labels:
        app: nginx-custom
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        volumeMounts:
        - name: config
          mountPath: /etc/nginx/conf.d
      volumes:
      - name: config
        configMap:
          name: nginx-config
EOF

# Verify configuration
kubectl exec deployment/nginx-custom -- cat /etc/nginx/conf.d/nginx.conf
```

## ConfigMap and Secret Updates

⚠️ **Important**: Updates don't automatically trigger pod restarts!

### Update Strategies

1. **Rolling restart**:
```bash
kubectl rollout restart deployment/myapp
```

2. **Use a sidecar** to watch for changes and reload

3. **Change ConfigMap/Secret name** and update deployment:
```yaml
# Version your ConfigMaps
app-config-v1 → app-config-v2
```

## External Secret Management

For production, consider external tools:

### HashiCorp Vault
```bash
# Example using Vault Agent Injector
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "myapp"
  vault.hashicorp.com/agent-inject-secret-database: "database/creds/myapp"
```

### AWS Secrets Manager
```bash
# External Secrets Operator
kubectl apply -f https://raw.githubusercontent.com/external-secrets/external-secrets/main/deploy/crds/bundle.yaml
```

### Sealed Secrets
Encrypt secrets for Git storage:
```bash
# Install kubeseal
kubeseal --format yaml < secret.yaml > sealed-secret.yaml
# Safe to commit sealed-secret.yaml
```

## Troubleshooting

```bash
# View ConfigMap contents
kubectl get configmap app-config -o yaml

# View Secret (base64 encoded)
kubectl get secret db-secret -o yaml

# Decode secret value
kubectl get secret db-secret -o jsonpath='{.data.password}' | base64 --decode

# Check if ConfigMap/Secret is mounted in pod
kubectl exec <pod-name> -- ls -la /etc/config
kubectl exec <pod-name> -- cat /etc/config/key-name

# Check environment variables
kubectl exec <pod-name> -- env
```

## Key Takeaways

1. Use ConfigMaps for non-sensitive configuration
2. Use Secrets for sensitive data
3. Secrets are base64 encoded, not encrypted by default
4. Updates don't auto-restart pods
5. Volume mounts are better than env vars for large configs
6. Consider external secret management for production
7. Never commit secrets to version control

## Next Steps

Learn about persistent storage for stateful applications!

[Continue to Lesson 6: Volumes and Persistent Storage →](06-volumes-storage.md)

## Additional Resources

- [ConfigMaps Documentation](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [Secrets Documentation](https://kubernetes.io/docs/concepts/configuration/secret/)
- [External Secrets Operator](https://external-secrets.io/)
