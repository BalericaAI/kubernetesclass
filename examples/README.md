# Example: Simple Web Application

This example demonstrates a complete web application deployment with:
- Deployment with multiple replicas
- ConfigMap for configuration
- Secret for credentials
- Service for internal access
- Ingress for external access

## Files

- `configmap.yaml` - Application configuration
- `secret.yaml` - Database credentials
- `deployment.yaml` - Web application deployment
- `service.yaml` - Service to expose the deployment
- `ingress.yaml` - Ingress for external access

## Deploy

```bash
# Create namespace
kubectl create namespace webapp

# Apply all resources
kubectl apply -f configmap.yaml -n webapp
kubectl apply -f secret.yaml -n webapp
kubectl apply -f deployment.yaml -n webapp
kubectl apply -f service.yaml -n webapp
kubectl apply -f ingress.yaml -n webapp

# Check status
kubectl get all -n webapp

# Test the application
kubectl port-forward -n webapp service/webapp 8080:80
# Visit http://localhost:8080
```

## Clean Up

```bash
kubectl delete namespace webapp
```
