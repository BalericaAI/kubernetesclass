import os
import sys
import json
from collections import defaultdict
from datetime import datetime

import requests

# ==========================================
# CONFIG
# ==========================================

TELEMETRY_DIR = os.environ.get(
    "TELEMETRY_DIR",
    "/opt/ai-soc/incoming"
)

CORRELATED_OUTPUT = os.environ.get(
    "CORRELATED_OUTPUT",
    "/opt/ai-soc/correlated/correlated_findings.json"
)

# ==========================================
# MCP GATEWAY (Zero Trust entry point)
# ==========================================
# The agent does not talk to the MCP server directly.
# It authenticates through the mTLS gateway by presenting
# a client certificate signed by the trusted client CA.

MCP_GATEWAY_URL = os.environ.get(
    "MCP_GATEWAY_URL",
    "https://mcp-gateway.mcp-gateway.svc.cluster.local"
)

MCP_CLIENT_CERT = os.environ.get(
    "MCP_CLIENT_CERT",
    "/etc/mcp/certs/tls.crt"
)

MCP_CLIENT_KEY = os.environ.get(
    "MCP_CLIENT_KEY",
    "/etc/mcp/certs/tls.key"
)

# Optional: CA bundle to verify the gateway's server cert.
# The lab uses a self-signed server cert whose SAN does not
# match the in-cluster DNS name, so verification is off by
# default. In production, issue a proper cert and set this.
MCP_SERVER_CA = os.environ.get("MCP_SERVER_CA", "")

VERIFY = MCP_SERVER_CA if MCP_SERVER_CA else False

if not VERIFY:
    requests.packages.urllib3.disable_warnings()

# ==========================================
# STEP 1 - AUTHENTICATE VIA THE MCP SERVER
# ==========================================
# Machine identity, proven cryptographically:
# if this call succeeds, the gateway validated our
# client certificate and the MCP server trusts us.


def authenticate_with_mcp():

    print("=== MCP AUTHENTICATION ===")
    print(f"Gateway: {MCP_GATEWAY_URL}")

    try:

        response = requests.get(
            f"{MCP_GATEWAY_URL}/tools",
            cert=(MCP_CLIENT_CERT, MCP_CLIENT_KEY),
            verify=VERIFY,
            timeout=10
        )

        response.raise_for_status()

        tools = response.json().get("tools", [])

        print("Authentication: SUCCESS")
        print(f"MCP tools available: {tools}\n")

        return tools

    except requests.exceptions.SSLError as e:

        print("Authentication: FAILED (TLS handshake rejected)")
        print(f"Details: {e}")
        sys.exit(1)

    except Exception as e:

        print("Authentication: FAILED")
        print(f"Details: {e}")
        sys.exit(1)


def mcp_tool(name, payload=None):
    """Call an MCP tool through the authenticated mTLS channel."""

    response = requests.post(
        f"{MCP_GATEWAY_URL}/tool/{name}",
        json=payload or {},
        cert=(MCP_CLIENT_CERT, MCP_CLIENT_KEY),
        verify=VERIFY,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


tools = authenticate_with_mcp()

# ==========================================
# RISK SCORING
# ==========================================

RISK_SCORES = {
    "critical_cve": 40,
    "shell_spawn": 35,
    "tls_failure": 15,
    "cert_expiring": 10,
    "policy_violation": 20
}

# ==========================================
# STEP 2 - LOAD EVENTS
# ==========================================

student_findings = defaultdict(list)

for root, dirs, files in os.walk(TELEMETRY_DIR):

    # ConfigMap volume mounts expose the real files a second time
    # under hidden ..data / ..<timestamp> dirs -- skip those so
    # each event is only counted once.
    dirs[:] = [d for d in dirs if not d.startswith("..")]

    for file in files:

        if not file.endswith(".json"):
            continue

        path = os.path.join(root, file)

        try:

            with open(path, "r") as f:

                event = json.load(f)

                student_id = event.get(
                    "student_id",
                    "unknown"
                )

                student_findings[student_id].append(
                    event
                )

        except Exception as e:

            print(
                f"Failed to process {path}: {e}"
            )

# ==========================================
# STEP 3 - CORRELATION
# ==========================================

results = []

for student_id, events in student_findings.items():

    risk_score = 0

    event_summary = []

    for event in events:

        event_type = event.get(
            "event_type",
            ""
        )

        score = RISK_SCORES.get(
            event_type,
            0
        )

        risk_score += score

        event_summary.append(event_type)

    # ======================================
    # RISK LEVEL
    # ======================================

    if risk_score >= 81:
        level = "CRITICAL"

    elif risk_score >= 51:
        level = "HIGH"

    elif risk_score >= 21:
        level = "MEDIUM"

    else:
        level = "LOW"

    result = {
        "student_id": student_id,
        "timestamp": str(datetime.utcnow()),
        "risk_score": risk_score,
        "risk_level": level,
        "events": event_summary
    }

    results.append(result)

# ==========================================
# STEP 4 - ENRICH VIA MCP (live cluster state)
# ==========================================
# Uses the authenticated session to attach a snapshot
# of running pods to the correlated findings.

cluster_snapshot = ""

if "get_pods" in tools:

    try:

        cluster_snapshot = mcp_tool("get_pods").get(
            "pods",
            ""
        )

    except Exception as e:

        print(f"MCP get_pods failed: {e}")

report = {
    "generated_at": str(datetime.utcnow()),
    "mcp_gateway": MCP_GATEWAY_URL,
    "findings": results,
    "cluster_snapshot": cluster_snapshot
}

# ==========================================
# OUTPUT RESULTS
# ==========================================

os.makedirs(
    os.path.dirname(CORRELATED_OUTPUT),
    exist_ok=True
)

with open(CORRELATED_OUTPUT, "w") as f:

    json.dump(report, f, indent=2)

print("\n=== CORRELATED FINDINGS ===\n")

for result in results:

    print(json.dumps(result, indent=2))
