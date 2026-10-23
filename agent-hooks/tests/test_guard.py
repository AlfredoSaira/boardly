"""Run guard.py the way Claude Code does: a subprocess with the event on stdin."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

GUARD = Path(__file__).resolve().parent.parent / "guard.py"
ROOT = GUARD.parent.parent


def run_guard(tool_name: str, **tool_input) -> subprocess.CompletedProcess:
    event = {"tool_name": tool_name, "tool_input": tool_input}
    return subprocess.run(
        [sys.executable, str(GUARD)], input=json.dumps(event), capture_output=True, text=True
    )


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf backend",
        "git push --force origin main",
        "git reset --hard HEAD~3",
        "kubectl delete namespace boardly-prod",
        "docker compose down -v",
        "psql -c 'DROP TABLE cards'",
        "cat .env",
    ],
)
def test_blocks_destructive_or_secret_commands(command):
    result = run_guard("Bash", command=command)
    assert result.returncode == 2
    assert "Blocked by agent-hooks/guard.py" in result.stderr


@pytest.mark.parametrize(
    "command",
    ["uv run pytest -q", "git status", "npm test", "docker compose ps", "rm build.log"],
)
def test_allows_everyday_commands(command):
    assert run_guard("Bash", command=command).returncode == 0


def test_blocks_reading_secrets():
    assert run_guard("Read", file_path=str(ROOT / "backend/.env")).returncode == 2
    assert run_guard("Read", file_path=str(ROOT / "backend/.env.production")).returncode == 2
    assert run_guard("Read", file_path=str(ROOT / "backend/.env.example")).returncode == 0


def test_blocks_editing_incident_evidence_but_allows_reading_it():
    path = str(ROOT / "incident-response/incidents/x/answer.json")
    assert run_guard("Edit", file_path=path).returncode == 2
    assert run_guard("Read", file_path=path).returncode == 0


def test_contract_edits_need_the_review_marker():
    marker = ROOT / "agent-hooks/.contract-reviewed"
    marker.unlink(missing_ok=True)
    assert run_guard("Edit", file_path=str(ROOT / "openapi.yaml")).returncode == 2
    marker.write_text("reviewed\n")
    try:
        assert run_guard("Edit", file_path=str(ROOT / "openapi.yaml")).returncode == 0
    finally:
        marker.unlink()


def test_allows_normal_code_edits():
    path = str(ROOT / "backend/src/boardly_backend/store.py")
    assert run_guard("Edit", file_path=path).returncode == 0


def test_bad_input_never_breaks_the_agent():
    result = subprocess.run([sys.executable, str(GUARD)], input="not json", text=True)
    assert result.returncode == 0
