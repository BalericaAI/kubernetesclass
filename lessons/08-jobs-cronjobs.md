# Lesson 8: Jobs and CronJobs

## Understanding Jobs

**Jobs** create one or more Pods and ensure they successfully complete. Unlike Deployments or StatefulSets that keep Pods running indefinitely, Jobs run to completion.

### Use Cases

- Batch processing
- Data migrations
- Database backups
- Report generation
- One-time setup tasks
- ETL (Extract, Transform, Load) operations

## Basic Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-job
spec:
  template:
    spec:
      containers:
      - name: processor
        image: busybox
        command: ['sh', '-c', 'echo "Processing data..." && sleep 30 && echo "Done!"']
      restartPolicy: Never
  backoffLimit: 4
```

**Key Points:**
- `restartPolicy` must be `Never` or `OnFailure` (not `Always`)
- `backoffLimit`: Max retries before considering job failed (default: 6)

### Running the Job

```bash
# Create job
kubectl apply -f job.yaml

# Check status
kubectl get jobs

# View pods
kubectl get pods

# View logs
kubectl logs <pod-name>

# Check completion
kubectl describe job batch-job
```

## Job Patterns

### 1. Single Job (One Pod)

Default behavior - run one pod to completion.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: single-job
spec:
  template:
    spec:
      containers:
      - name: task
        image: busybox
        command: ['sh', '-c', 'echo "Single task" && sleep 10']
      restartPolicy: Never
```

### 2. Parallel Jobs with Fixed Completion Count

Run multiple pods until N completions.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel-job
spec:
  completions: 10      # Need 10 successful completions
  parallelism: 3       # Run 3 pods at a time
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ['sh', '-c', 'echo "Processing item $RANDOM" && sleep 5']
      restartPolicy: Never
```

**Execution:**
- Starts 3 pods
- When one completes, starts another
- Continues until 10 successful completions

### 3. Work Queue Pattern

Multiple workers processing items from a queue.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: queue-job
spec:
  parallelism: 5       # 5 workers
  template:
    spec:
      containers:
      - name: worker
        image: myworker:1.0
        env:
        - name: QUEUE_URL
          value: "redis://redis-service:6379"
      restartPolicy: Never
```

Workers:
1. Connect to queue
2. Process items until queue empty
3. Exit when done

### 4. Indexed Jobs

Each pod gets a unique index (0, 1, 2, ...).

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: indexed-job
spec:
  completions: 5
  parallelism: 3
  completionMode: Indexed
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command:
        - sh
        - -c
        - echo "Processing index $JOB_COMPLETION_INDEX"
      restartPolicy: Never
```

Access index via `JOB_COMPLETION_INDEX` environment variable.

## Job Completion and Cleanup

### Automatic Cleanup

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: temp-job
spec:
  ttlSecondsAfterFinished: 100  # Delete job 100s after completion
  template:
    spec:
      containers:
      - name: task
        image: busybox
        command: ['sh', '-c', 'echo "Task done"']
      restartPolicy: Never
```

### Manual Cleanup

```bash
# Delete completed job
kubectl delete job batch-job

# Delete all completed jobs
kubectl delete jobs --field-selector status.successful=1
```

## Job Failure Handling

### Restart Policies

```yaml
# OnFailure: Restart container in same pod
spec:
  template:
    spec:
      restartPolicy: OnFailure

# Never: Create new pod on failure
spec:
  template:
    spec:
      restartPolicy: Never
```

### Backoff Limit

```yaml
spec:
  backoffLimit: 3  # Max 3 retries
```

Backoff delay increases exponentially: 10s, 20s, 40s...

### Active Deadline

```yaml
spec:
  activeDeadlineSeconds: 600  # Job must complete within 10 minutes
```

## CronJobs: Scheduled Jobs

**CronJobs** run Jobs on a schedule (like cron in Unix).

### Basic CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-job
spec:
  schedule: "0 2 * * *"  # Every day at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: backup-tool:1.0
            command: ['sh', '-c', 'echo "Running backup at $(date)"']
          restartPolicy: OnFailure
```

### Cron Schedule Format

```
# ┌───────────── minute (0 - 59)
# │ ┌───────────── hour (0 - 23)
# │ │ ┌───────────── day of month (1 - 31)
# │ │ │ ┌───────────── month (1 - 12)
# │ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday)
# │ │ │ │ │
# * * * * *

Examples:
"*/5 * * * *"        # Every 5 minutes
"0 * * * *"          # Every hour
"0 0 * * *"          # Every day at midnight
"0 0 * * 0"          # Every Sunday at midnight
"0 0 1 * *"          # First day of every month
"0 9-17 * * *"       # Every hour from 9 AM to 5 PM
"0 0 1,15 * *"       # 1st and 15th of month
```

### CronJob Options

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: report-generator
spec:
  schedule: "0 8 * * 1"  # Every Monday at 8 AM
  
  # How to handle missed schedules
  concurrencyPolicy: Forbid  # Allow, Forbid, or Replace
  
  # Keep last 3 successful and 1 failed job
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  
  # If job doesn't start within 100s of scheduled time, count as failed
  startingDeadlineSeconds: 100
  
  # Suspend scheduling (for maintenance)
  suspend: false
  
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: report
            image: report-generator:1.0
          restartPolicy: OnFailure
```

### Concurrency Policies

- **Allow** (default): Multiple jobs can run concurrently
- **Forbid**: Skip new run if previous still running
- **Replace**: Cancel current job and start new one

## Real-World Examples

### Example 1: Database Backup

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 7
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: password
            command:
            - sh
            - -c
            - |
              pg_dump -h postgres-service -U admin mydb > /backup/backup-$(date +%Y%m%d).sql
              echo "Backup completed at $(date)"
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

### Example 2: Data Cleanup

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cleanup-old-data
spec:
  schedule: "0 3 * * 0"  # Every Sunday at 3 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: cleanup
            image: mysql:8.0
            env:
            - name: MYSQL_PWD
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: password
            command:
            - sh
            - -c
            - |
              mysql -h mysql-service -u admin mydb <<EOF
              DELETE FROM logs WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
              DELETE FROM temp_data WHERE created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
              EOF
              echo "Cleanup completed"
          restartPolicy: OnFailure
      backoffLimit: 3
      activeDeadlineSeconds: 3600
```

### Example 3: Report Generation

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: weekly-report
spec:
  schedule: "0 9 * * 1"  # Monday 9 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: report
            image: python:3.11
            command:
            - python
            - -c
            - |
              import datetime
              print(f"Generating weekly report for {datetime.date.today()}")
              # Report generation logic here
              print("Report sent via email")
            env:
            - name: SMTP_HOST
              valueFrom:
                configMapKeyRef:
                  name: email-config
                  key: smtp_host
          restartPolicy: Never
```

## Hands-On Exercises

### Exercise 1: Simple Job

```bash
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: pi-calculation
spec:
  template:
    spec:
      containers:
      - name: pi
        image: perl:5.34
        command: ["perl", "-Mbignum=bpi", "-wle", "print bpi(2000)"]
      restartPolicy: Never
  backoffLimit: 2
EOF

# Watch job progress
kubectl get jobs -w

# View result
kubectl logs job/pi-calculation
```

### Exercise 2: Parallel Job

```bash
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel-processing
spec:
  completions: 8
  parallelism: 3
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command:
        - sh
        - -c
        - echo "Worker processing at $(date)" && sleep $((RANDOM % 10 + 5)) && echo "Done"
      restartPolicy: Never
EOF

# Watch pods
kubectl get pods -l job-name=parallel-processing -w

# Check job status
kubectl describe job parallel-processing
```

### Exercise 3: CronJob

```bash
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: CronJob
metadata:
  name: hello
spec:
  schedule: "*/1 * * * *"  # Every minute
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: hello
            image: busybox
            command:
            - sh
            - -c
            - date; echo "Hello from CronJob"
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
EOF

# Wait a few minutes and check
kubectl get cronjobs
kubectl get jobs
kubectl get pods

# View logs from one of the runs
kubectl logs <pod-name>

# Trigger manually (without waiting)
kubectl create job test-run --from=cronjob/hello

# Clean up
kubectl delete cronjob hello
```

### Exercise 4: Indexed Job

```bash
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: indexed-processor
spec:
  completions: 5
  parallelism: 3
  completionMode: Indexed
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: processor
        image: busybox
        command:
        - sh
        - -c
        - |
          echo "Processing batch \$JOB_COMPLETION_INDEX"
          sleep 5
          echo "Batch \$JOB_COMPLETION_INDEX completed"
EOF

# Watch execution
kubectl get pods -l job-name=indexed-processor -w
kubectl logs -l job-name=indexed-processor --prefix=true
```

## Best Practices

1. ✅ **Set resource limits** for Jobs
2. ✅ **Use ttlSecondsAfterFinished** for automatic cleanup
3. ✅ **Set activeDeadlineSeconds** to prevent runaway jobs
4. ✅ **Configure backoffLimit** appropriately
5. ✅ **Use CronJob history limits** to prevent clutter
6. ✅ **Set concurrencyPolicy** for CronJobs
7. ✅ **Monitor job completion** and failures
8. ✅ **Use indexed jobs** for parallelizable tasks with state

## Troubleshooting

```bash
# Check job status
kubectl describe job <name>

# View failed pods
kubectl get pods --field-selector=status.phase=Failed

# View logs from failed job
kubectl logs <pod-name>

# Check CronJob history
kubectl get jobs --sort-by=.metadata.creationTimestamp

# Check when CronJob will run next
kubectl get cronjob <name> -o yaml | grep lastScheduleTime

# Suspend CronJob
kubectl patch cronjob <name> -p '{"spec":{"suspend":true}}'

# Resume CronJob
kubectl patch cronjob <name> -p '{"spec":{"suspend":false}}'
```

## Key Takeaways

1. Jobs run pods to completion, then stop
2. Use Jobs for batch processing and one-time tasks
3. CronJobs schedule Jobs on a timetable
4. Configure parallelism for concurrent processing
5. Set appropriate limits and cleanup policies
6. Monitor job completion and handle failures
7. Use indexed jobs for numbered batch processing

## Course Completion! 🎉

Congratulations! You've completed the Kubernetes Class. You now understand:
- Kubernetes architecture and components
- Pods, Deployments, and workload management
- Services and networking
- Configuration with ConfigMaps and Secrets
- Persistent storage with Volumes
- StatefulSets and DaemonSets for specialized workloads
- Jobs and CronJobs for batch processing

## Next Steps in Your Kubernetes Journey

1. **Practice**: Set up a project using what you learned
2. **Certifications**: Consider CKA, CKAD, or CKS certifications
3. **Advanced Topics**:
   - Operators and Custom Resources
   - Service Meshes (Istio, Linkerd)
   - GitOps (ArgoCD, Flux)
   - Security hardening
   - Multi-cluster management

## Additional Resources

- [Jobs Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [CronJobs Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
- [Crontab Guru](https://crontab.guru/) - Cron schedule helper
