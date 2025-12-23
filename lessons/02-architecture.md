# Lesson 2: Kubernetes Architecture

## Overview

Understanding Kubernetes architecture is crucial for effectively working with the platform. Kubernetes follows a master-worker architecture where the control plane manages the cluster, and worker nodes run your applications.

## Cluster Architecture

A Kubernetes cluster consists of:
- **Control Plane** (Master Node): Manages the cluster
- **Worker Nodes**: Run containerized applications
- **Add-ons**: Optional components for additional functionality

```
┌─────────────────────────────────────────────────────────────┐
│                     CONTROL PLANE                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ API Server   │  │  Scheduler   │  │  Controller  │     │
│  │              │  │              │  │   Manager    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                                                    │
│  ┌──────────────┐                                          │
│  │     etcd     │                                          │
│  │  (data store)│                                          │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼───────┐  ┌───────▼───────┐  ┌───────▼───────┐
│  Worker Node  │  │  Worker Node  │  │  Worker Node  │
│ ┌───────────┐ │  │ ┌───────────┐ │  │ ┌───────────┐ │
│ │  kubelet  │ │  │ │  kubelet  │ │  │ │  kubelet  │ │
│ └───────────┘ │  │ └───────────┘ │  │ └───────────┘ │
│ ┌───────────┐ │  │ ┌───────────┐ │  │ ┌───────────┐ │
│ │kube-proxy │ │  │ │kube-proxy │ │  │ │kube-proxy │ │
│ └───────────┘ │  │ └───────────┘ │  │ └───────────┘ │
│ ┌───────────┐ │  │ ┌───────────┐ │  │ ┌───────────┐ │
│ │Container  │ │  │ │Container  │ │  │ │Container  │ │
│ │ Runtime   │ │  │ │ Runtime   │ │  │ │ Runtime   │ │
│ └───────────┘ │  │ └───────────┘ │  │ └───────────┘ │
│  [Pods/Apps]  │  │  [Pods/Apps]  │  │  [Pods/Apps]  │
└───────────────┘  └───────────────┘  └───────────────┘
```

## Control Plane Components

The control plane makes global decisions about the cluster and detects/responds to cluster events.

### 1. API Server (kube-apiserver)

**What it does:**
- Front-end for the Kubernetes control plane
- Exposes the Kubernetes API
- Processes REST requests and updates etcd

**Key Responsibilities:**
- Authentication and authorization
- Validation of API objects
- Communication hub for all components

**Example Interaction:**
```bash
# When you run this command:
kubectl get pods

# You're actually making an HTTP request to the API server
# GET /api/v1/namespaces/default/pods
```

### 2. Scheduler (kube-scheduler)

**What it does:**
- Watches for newly created Pods with no assigned node
- Selects the best node for each Pod to run on

**Scheduling Factors:**
- Resource requirements (CPU, memory)
- Hardware/software constraints
- Affinity and anti-affinity rules
- Data locality
- Taints and tolerations

**Decision Process:**
1. Filter nodes (remove unsuitable ones)
2. Score remaining nodes
3. Select highest-scoring node
4. Bind Pod to node

### 3. Controller Manager (kube-controller-manager)

**What it does:**
- Runs controller processes that regulate the state of the cluster

**Key Controllers:**
- **Node Controller**: Monitors node health
- **Replication Controller**: Maintains correct number of Pods
- **Endpoints Controller**: Populates Endpoints objects
- **Service Account Controller**: Creates default accounts for new namespaces

**How Controllers Work:**
```
┌─────────────────────────────────────┐
│  Watch for changes in cluster state │
│                 │                    │
│                 ▼                    │
│  Compare current state vs desired   │
│                 │                    │
│                 ▼                    │
│  Take action to reconcile           │
│                 │                    │
│                 └──────► repeat      │
└─────────────────────────────────────┘
```

### 4. etcd

**What it is:**
- Consistent and highly-available key-value store
- Kubernetes' backing store for all cluster data

**What it stores:**
- Cluster configuration
- Resource definitions
- State of all objects
- Secrets and ConfigMaps

**Key Characteristics:**
- Distributed consensus using Raft algorithm
- Strong consistency guarantees
- Watch functionality for real-time updates

**⚠️ Important:** etcd is critical - always back it up!

## Worker Node Components

These components run on every worker node to maintain running pods.

### 1. Kubelet

**What it does:**
- Primary node agent
- Ensures containers are running in Pods
- Reports node and Pod status to control plane

**Responsibilities:**
- Pulls container images
- Starts/stops containers
- Monitors container health
- Mounts volumes
- Reports metrics

**PodSpec:**
The kubelet takes a set of PodSpecs and ensures the containers described in them are running and healthy.

### 2. Kube-proxy

**What it does:**
- Network proxy that runs on each node
- Maintains network rules for Pod communication

**Responsibilities:**
- Implement Service abstraction
- Load balance traffic across Pod backends
- Enable service discovery

**Modes:**
- **iptables mode** (default): Uses iptables rules
- **IPVS mode**: More efficient for large clusters
- **userspace mode**: Legacy mode

### 3. Container Runtime

**What it is:**
- Software responsible for running containers

**Supported Runtimes:**
- **containerd** (most common)
- **CRI-O**
- **Docker** (deprecated in K8s 1.24+, but still works via containerd)

**Container Runtime Interface (CRI):**
Allows Kubernetes to work with different container runtimes without code changes.

## Add-ons

Optional components that provide cluster features:

### DNS (CoreDNS)
- Provides DNS-based service discovery
- Required add-on for most clusters

### Dashboard
- Web-based UI for managing clusters

### Monitoring
- Metrics Server: Collects resource metrics
- Prometheus: Full monitoring solution

### Logging
- Cluster-level logging (EFK/ELK stack)

## Communication Flow

### Example: Creating a Deployment

```
1. User runs: kubectl create deployment nginx --image=nginx
               │
               ▼
2. kubectl sends request to API Server
               │
               ▼
3. API Server validates and stores in etcd
               │
               ▼
4. Controller Manager detects new Deployment
               │
               ▼
5. Controller Manager creates ReplicaSet
               │
               ▼
6. ReplicaSet creates Pod specifications
               │
               ▼
7. Scheduler assigns Pod to a Node
               │
               ▼
8. Kubelet on that Node pulls image and starts container
               │
               ▼
9. Status updates flow back through API Server to etcd
```

## High Availability Considerations

### Control Plane HA
- Multiple API server instances (load balanced)
- Clustered etcd (minimum 3 nodes)
- Multiple controller managers (leader election)
- Multiple schedulers (leader election)

### Worker Node HA
- Multiple worker nodes
- Pods distributed across nodes
- Automatic rescheduling on node failure

## Kubernetes Distributions

Different ways to run Kubernetes:

### Managed Services
- **EKS** (AWS)
- **GKE** (Google Cloud)
- **AKS** (Azure)

### Self-Managed
- **kubeadm**: Official cluster bootstrapping tool
- **kops**: Production-grade cluster management

### Local Development
- **minikube**: Single-node cluster
- **kind**: Kubernetes in Docker
- **k3s**: Lightweight Kubernetes

## Practice Exercises

### Exercise 1: Explore Your Cluster

```bash
# View control plane components
kubectl get pods -n kube-system

# Check API server version
kubectl version

# View nodes with detailed info
kubectl get nodes -o wide

# Describe a node to see its components
kubectl describe node <node-name>
```

### Exercise 2: Understand Component Logs

```bash
# View API server logs (if using Docker Desktop or similar)
kubectl logs -n kube-system kube-apiserver-<node-name>

# View scheduler logs
kubectl logs -n kube-system kube-scheduler-<node-name>

# View controller manager logs
kubectl logs -n kube-system kube-controller-manager-<node-name>
```

### Exercise 3: Check etcd

```bash
# If using minikube, you can access etcd
minikube ssh

# Then inside the node:
sudo etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/var/lib/minikube/certs/etcd/ca.crt \
  --cert=/var/lib/minikube/certs/etcd/server.crt \
  --key=/var/lib/minikube/certs/etcd/server.key \
  member list
```

## Key Takeaways

1. **Control Plane** manages the cluster; **Worker Nodes** run applications
2. **API Server** is the central communication hub
3. **etcd** stores all cluster data - back it up!
4. **Scheduler** assigns Pods to nodes intelligently
5. **Controllers** continuously work to maintain desired state
6. **Kubelet** ensures containers run on nodes
7. All components work together through the API Server

## Common Interview Questions

1. **Q: What happens if the control plane goes down?**
   A: Existing Pods continue running, but you can't create new ones or make changes.

2. **Q: What's the difference between kubelet and kube-proxy?**
   A: Kubelet manages Pod lifecycle; kube-proxy handles network routing.

3. **Q: Can you run Pods on the master node?**
   A: By default, no (tainted), but you can remove the taint in dev environments.

## Next Steps

Now that you understand the architecture, let's get hands-on with Pods and Deployments!

[Continue to Lesson 3: Pods and Deployments →](03-pods-deployments.md)

## Additional Resources

- [Kubernetes Components Documentation](https://kubernetes.io/docs/concepts/overview/components/)
- [Understanding Kubernetes Architecture](https://kubernetes.io/docs/concepts/architecture/)
- [etcd Documentation](https://etcd.io/docs/)
