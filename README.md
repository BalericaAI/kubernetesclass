# Kubernetes Class - Thursday Night Fun 🚀

Welcome to the Kubernetes Class! This repository contains comprehensive learning materials, hands-on exercises, and practical examples to help you master Kubernetes container orchestration.

## 📚 Course Overview

This course is designed to take you from Kubernetes basics to advanced concepts through practical, hands-on learning. Each lesson includes theory, examples, and exercises to reinforce your understanding.

## 🎯 Prerequisites

- Basic understanding of containerization (Docker)
- Familiarity with command-line interfaces
- Basic YAML syntax knowledge
- A computer with administrator/sudo access for local setup

## 📖 Course Structure

### Module 1: Foundations
1. **[Introduction to Kubernetes](lessons/01-introduction.md)**
   - What is Kubernetes?
   - Why use container orchestration?
   - Kubernetes ecosystem overview

2. **[Kubernetes Architecture](lessons/02-architecture.md)**
   - Control plane components
   - Worker node components
   - etcd and the cluster state

### Module 2: Core Concepts
3. **[Pods and Deployments](lessons/03-pods-deployments.md)**
   - Understanding Pods
   - Creating and managing Deployments
   - Rolling updates and rollbacks

4. **[Services and Networking](lessons/04-services-networking.md)**
   - Service types (ClusterIP, NodePort, LoadBalancer)
   - Ingress controllers
   - Network policies

### Module 3: Configuration and Storage
5. **[ConfigMaps and Secrets](lessons/05-config-secrets.md)**
   - Externalizing configuration
   - Managing sensitive data
   - Environment variables and volumes

6. **[Volumes and Persistent Storage](lessons/06-volumes-storage.md)**
   - Volume types
   - PersistentVolumes and PersistentVolumeClaims
   - Storage classes

### Module 4: Advanced Workloads
7. **[StatefulSets and DaemonSets](lessons/07-statefulsets-daemonsets.md)**
   - Stateful applications in Kubernetes
   - DaemonSets for cluster-wide services
   - Headless services

8. **[Jobs and CronJobs](lessons/08-jobs-cronjobs.md)**
   - Running batch workloads
   - Scheduled tasks
   - Job patterns and best practices

## 🛠️ Getting Started

### Local Development Setup

Choose one of the following options for your local Kubernetes environment:

1. **Minikube** (Recommended for beginners)
   ```bash
   # Install minikube
   curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
   sudo install minikube-linux-amd64 /usr/local/bin/minikube
   
   # Start cluster
   minikube start
   ```

2. **Kind (Kubernetes in Docker)**
   ```bash
   # Install kind
   curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
   chmod +x ./kind
   sudo mv ./kind /usr/local/bin/kind
   
   # Create cluster
   kind create cluster
   ```

3. **Docker Desktop** (For macOS/Windows)
   - Enable Kubernetes in Docker Desktop settings

### Installing kubectl

```bash
# Download latest release
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Install kubectl
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Verify installation
kubectl version --client
```

## 📁 Repository Structure

```
kubernetesclass/
├── lessons/              # Detailed lesson content
├── exercises/            # Hands-on exercises with solutions
├── examples/             # Example YAML manifests
├── resources/            # Additional resources and references
└── setup/                # Setup guides and scripts
```

## 🎓 How to Use This Course

1. **Read the lessons** in order, as they build upon each other
2. **Try the examples** in each lesson - apply them to your cluster
3. **Complete the exercises** to reinforce your learning
4. **Experiment** with modifications to understand behavior
5. **Join discussions** and ask questions in the Issues section

## 🤝 Contributing

This is a learning repository! Contributions are welcome:
- Found a typo or error? Open an issue or PR
- Have a great example? Share it!
- Want to add a lesson? Propose it in an issue first

## 📚 Additional Resources

- [Official Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kubernetes GitHub Repository](https://github.com/kubernetes/kubernetes)
- [CNCF Kubernetes Tutorials](https://www.cncf.io/certification/training/)

## 📝 License

This educational content is provided for learning purposes. Feel free to use, modify, and share!

---

**Happy Learning! 🎉** Let's master Kubernetes together!
