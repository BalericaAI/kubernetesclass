
# Telemetry Correlation Agent — Authenticating via the MCP Server

This walkthru deploys the telemetry-correlation-agent so that it
authenticates FIRST through the MCP gateway before doing any work.

The authentication is mutual TLS:

        Agent  --(client cert)-->  mcp-gateway (nginx, verifies cert)
                                        |
                                        v
                                   mcp-server

If the agent cannot prove its identity cryptographically, the gateway
rejects the connection and the agent exits — Zero Trust, machine edition.

Prerequisite: the MCP gateway stack from mcp/walkthru.md is running,
including the mcp-client-ca secret (that CA signs agent certificates).


Step 1 — Issue a client certificate for the agent

Sign it with the SAME client CA the gateway trusts (ca.crt / ca.key
from mcp/walkthru.md Step 3):

        openssl req -newkey rsa:2048 -nodes \
          -keyout telemetry-agent.key \
          -out telemetry-agent.csr \
          -subj "/CN=telemetry-correlation-agent"

        openssl x509 -req \
          -in telemetry-agent.csr \
          -CA ca.crt -CAkey ca.key -CAcreateserial \
          -out telemetry-agent.crt \
          -days 90

The CN becomes the agent's identity — the gateway forwards it to the
MCP server as the X-Client-DN header.


Step 2 — Store the identity as a secret

        kubectl apply -f telemetry-agent.yaml   # creates the ai-agents namespace

        kubectl create secret tls telemetry-agent-client-cert \
          --cert=telemetry-agent.crt \
          --key=telemetry-agent.key \
          -n ai-agents


Step 3 — Build and push the agent image

        mkdir -p /tmp/telemetry-build
        cp docker/telemetry_agent /tmp/telemetry-build/Dockerfile
        cp python/telemetry-correlation-agent.py /tmp/telemetry-build/
        docker build -t gcr.io/PROJECT_ID/telemetry-agent:lab1c /tmp/telemetry-build
        docker push gcr.io/PROJECT_ID/telemetry-agent:lab1c

Then replace PROJECT_ID in telemetry-agent.yaml.


Step 4 — Deploy

        kubectl apply -f telemetry-sample-events.yaml
        kubectl apply -f telemetry-agent.yaml

The CronJob runs every 5 minutes. To run it immediately:

        kubectl create job telemetry-now \
          --from=cronjob/telemetry-correlation-agent \
          -n ai-agents


Step 5 — Validate

        kubectl logs -n ai-agents job/telemetry-now

Expected output:

        === MCP AUTHENTICATION ===
        Gateway: https://mcp-gateway.mcp-gateway.svc.cluster.local
        Authentication: SUCCESS
        MCP tools available: ['get_logs', 'restart_deployment', 'get_pods']

        === CORRELATED FINDINGS ===
        ... risk-scored findings per student ...

The findings JSON also embeds a live cluster snapshot fetched through
the authenticated MCP session (the get_pods tool).


Step 6 — Prove the Zero Trust part

Delete the cert secret and run the job again:

        kubectl delete secret telemetry-agent-client-cert -n ai-agents

The pod fails to start (missing identity). Recreate the secret with a
cert signed by a DIFFERENT CA and the gateway rejects the handshake:

        Authentication: FAILED (TLS handshake rejected)

No valid machine identity, no MCP access.
