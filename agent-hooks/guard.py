"""PreToolUse guardrail for coding agents working in this repo.

Reads the hook event JSON on stdin. Exit 2 blocks the tool call and the
message on stderr goes back to the agent; exit 0 lets it through. Every
decision is appended to agent-hooks/logs/audit.jsonl.

Blocks:
- reading or writing secrets (.env files, kubeconfig, private keys)
- editing openapi.yaml without the contract review marker
  (agent-hooks/.contract-reviewed, written by the review-api-change skill)
- editing the incident evidence the on-call agent produced
- destructive shell commands (rm -rf, force push, kubectl delete, dropping volumes)
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT_LOG = ROOT / "agent-hooks" / "logs" / "audit.jsonl"
CONTRACT_MARKER = ROOT / "agent-hooks" / ".contract-reviewed"

# .env.example files are templates without values, so agents may read them.
SECRET_PATH = re.compile(r"(^|/)(\.env(\.(?!example$)[^/]*)?|kubeconfig|id_rsa|id_ed25519|.*\.pem)$")
EVIDENCE_PATH = re.compile(r"(^|/)incident-response/incidents/")
DESTRUCTIVE_COMMANDS = [
    (re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r"), "rm -rf"),
    (re.compile(r"\bgit\s+push\b.*(--force|-f\b)"), "force push"),
    (re.compile(r"\bgit\s+reset\s+--hard\b"), "git reset --hard"),
    (re.compile(r"\bkubectl\s+delete\b"), "kubectl delete"),
    (re.compile(r"\bdocker\s+compose\s+down\b.*(-v\b|--volumes)"), "dropping Compose volumes"),
    (re.compile(r"\bdrop\s+(table|database)\b", re.IGNORECASE), "DROP TABLE/DATABASE"),
]
SECRET_IN_COMMAND = re.compile(r"(^|[\s/'\"])\.env(\.[\w-]+)?($|[\s'\"])")


def audit(event: dict, decision: str, reason: str) -> None:
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    tool_input = event.get("tool_input", {})
    entry = {
        "at": datetime.now(timezone.utc).isoformat(),
        "tool": event.get("tool_name"),
        "target": tool_input.get("file_path") or tool_input.get("command", "")[:200],
        "decision": decision,
        "reason": reason,
    }
    with AUDIT_LOG.open("a") as log:
        log.write(json.dumps(entry) + "\n")


def relative(path: str) -> str:
    try:
        return Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return Path(path).as_posix()


def check(event: dict) -> str | None:
    """Return a reason to block, or None to allow."""
    tool = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    if tool in {"Read", "Edit", "Write", "MultiEdit"}:
        path = relative(tool_input.get("file_path", ""))
        if SECRET_PATH.search(path):
            return f"{path} holds secrets; agents never read or write it"
        if tool != "Read":
            if EVIDENCE_PATH.search(path):
                return f"{path} is incident evidence; it is append-only for the responder"
            if path == "openapi.yaml" and not CONTRACT_MARKER.exists():
                return (
                    "openapi.yaml is the frontend/backend contract. Run the review-api-change "
                    "skill first (it records the review in agent-hooks/.contract-reviewed)"
                )

    if tool == "Bash":
        command = tool_input.get("command", "")
        for pattern, label in DESTRUCTIVE_COMMANDS:
            if pattern.search(command):
                return f"destructive command blocked ({label}); ask the human to run it"
        if SECRET_IN_COMMAND.search(command):
            return "commands that touch .env files are blocked; secrets stay out of agent context"

    return None


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # not our event shape; never break the agent on a parsing problem
    reason = check(event)
    if reason:
        audit(event, "block", reason)
        print(f"Blocked by agent-hooks/guard.py: {reason}", file=sys.stderr)
        return 2
    audit(event, "allow", "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
