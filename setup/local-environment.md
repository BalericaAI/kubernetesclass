# Setup Guide: Local Kubernetes Environment

This guide helps you set up a local Kubernetes environment for learning and development.

## Prerequisites

- A computer with at least 4GB RAM (8GB+ recommended)
- Administrator/sudo access
- Internet connection
- Basic command-line knowledge

## Option 1: Minikube (Recommended for Beginners)

Minikube runs a single-node Kubernetes cluster in a VM or container.

### Installation

#### Linux

```bash
# Download minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64

# Install
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Verify installation
minikube version
```

#### macOS

```bash
# Using Homebrew
brew install minikube

# Or download directly
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-darwin-amd64
sudo install minikube-darwin-amd64 /usr/local/bin/minikube
```

#### Windows

```powershell
# Using Chocolatey
choco install minikube

# Or download installer from:
# https://minikube.sigs.k8s.io/docs/start/
```

### Start Minikube

```bash
# Start with default settings
minikube start

# Start with specific resources
minikube start --cpus=2 --memory=4096 --disk-size=20g

# Start with specific driver
minikube start --driver=docker
# or --driver=virtualbox, --driver=hyperv, etc.
```

### Useful Minikube Commands

```bash
# Check status
minikube status

# Stop cluster
minikube stop

# Delete cluster
minikube delete

# SSH into cluster
minikube ssh

# Open Kubernetes dashboard
minikube dashboard

# Enable addons
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons list

# Get service URL
minikube service <service-name>
```

## Option 2: Kind (Kubernetes in Docker)

Kind runs Kubernetes clusters using Docker containers as nodes.

### Installation

#### Linux/macOS

```bash
# Download kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64

# Make executable
chmod +x ./kind

# Move to PATH
sudo mv ./kind /usr/local/bin/kind
```

#### macOS with Homebrew

```bash
brew install kind
```

#### Windows

```powershell
# Using Chocolatey
choco install kind

# Or download from releases
# https://github.com/kubernetes-sigs/kind/releases
```

### Create Cluster

```bash
# Create single-node cluster
kind create cluster

# Create multi-node cluster
cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
EOF

# Create with custom name
kind create cluster --name dev-cluster
```

### Useful Kind Commands

```bash
# List clusters
kind get clusters

# Delete cluster
kind delete cluster

# Load image into cluster (for local development)
kind load docker-image myimage:tag

# Get kubeconfig
kind get kubeconfig --name dev-cluster
```

## Option 3: Docker Desktop

Easiest option for macOS and Windows users.

### Installation

1. Download Docker Desktop:
   - **macOS**: https://www.docker.com/products/docker-desktop
   - **Windows**: https://www.docker.com/products/docker-desktop

2. Install Docker Desktop

3. Enable Kubernetes:
   - Open Docker Desktop settings
   - Go to Kubernetes tab
   - Check "Enable Kubernetes"
   - Click "Apply & Restart"

4. Wait for Kubernetes to start (green indicator)

### Verify

```bash
kubectl cluster-info
kubectl get nodes
```

## Option 4: K3s (Lightweight Kubernetes)

Perfect for resource-constrained environments.

### Installation (Linux)

```bash
# Install K3s
curl -sfL https://get.k3s.io | sh -

# Check status
sudo systemctl status k3s

# Get kubeconfig
sudo cat /etc/rancher/k3s/k3s.yaml

# Use with kubectl
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
```

## Installing kubectl

kubectl is the command-line tool for Kubernetes.

### Linux

```bash
# Download latest release
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Install
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Verify
kubectl version --client
```

### macOS

```bash
# Using Homebrew
brew install kubectl

# Or download directly
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

### Windows

```powershell
# Using Chocolatey
choco install kubernetes-cli

# Or using Scoop
scoop install kubectl
```

## Verify Installation

```bash
# Check kubectl version
kubectl version --client

# Check cluster connection
kubectl cluster-info

# List nodes
kubectl get nodes

# Check all system pods
kubectl get pods -n kube-system
```

## Shell Completion (Optional but Recommended)

### Bash

```bash
# Add to ~/.bashrc
echo 'source <(kubectl completion bash)' >>~/.bashrc
echo 'alias k=kubectl' >>~/.bashrc
echo 'complete -o default -F __start_kubectl k' >>~/.bashrc
```

### Zsh

```bash
# Add to ~/.zshrc
echo 'source <(kubectl completion zsh)' >>~/.zshrc
echo 'alias k=kubectl' >>~/.zshrc
```

## Install Helpful Tools

### kubectx and kubens

Switch between contexts and namespaces easily.

```bash
# macOS
brew install kubectx

# Linux
sudo git clone https://github.com/ahmetb/kubectx /opt/kubectx
sudo ln -s /opt/kubectx/kubectx /usr/local/bin/kubectx
sudo ln -s /opt/kubectx/kubens /usr/local/bin/kubens
```

### k9s

Terminal UI for Kubernetes.

```bash
# macOS
brew install k9s

# Linux
curl -sS https://webinstall.dev/k9s | bash
```

### Helm

Kubernetes package manager.

```bash
# macOS
brew install helm

# Linux
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

## Troubleshooting

### Minikube won't start

```bash
# Try different driver
minikube start --driver=docker

# Delete and recreate
minikube delete
minikube start

# Check logs
minikube logs
```

### kubectl can't connect

```bash
# Check config
kubectl config view

# Check current context
kubectl config current-context

# List contexts
kubectl config get-contexts

# Switch context
kubectl config use-context minikube
```

### Resource constraints

```bash
# Increase resources (Minikube)
minikube delete
minikube start --cpus=4 --memory=8192

# Check resource usage
kubectl top nodes
kubectl top pods --all-namespaces
```

## Next Steps

1. ✅ Verify installation: `kubectl get nodes`
2. ✅ Deploy test application: `kubectl create deployment nginx --image=nginx`
3. ✅ Explore the cluster: `kubectl get all --all-namespaces`
4. ✅ Start with [Lesson 1](../lessons/01-introduction.md)

## Quick Reference Card

```bash
# Cluster info
kubectl cluster-info
kubectl get nodes

# Create deployment
kubectl create deployment nginx --image=nginx

# Expose deployment
kubectl expose deployment nginx --port=80 --type=NodePort

# View resources
kubectl get all

# Delete deployment
kubectl delete deployment nginx

# Get help
kubectl --help
kubectl <command> --help
```

## Recommended Resources

- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [Kind Documentation](https://kind.sigs.k8s.io/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Interactive Tutorial](https://kubernetes.io/docs/tutorials/kubernetes-basics/)

Happy Learning! 🚀
