"""PostToolUse hook: format the file an agent just edited and report leftover lint.

Python files under backend/, incident-response/ or mcp-server/ get
`ruff format` + `ruff check --fix` with the backend's ruff. Remaining lint
errors are sent back to the agent (exit 2 + stderr) so it fixes them in the
same turn instead of leaving them for CI.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON_DIRS = ("backend/", "incident-response/", "mcp-server/")


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    file_path = event.get("tool_input", {}).get("file_path", "")
    try:
        rel = Path(file_path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return 0
    if not rel.endswith(".py") or not rel.startswith(PYTHON_DIRS):
        return 0

    ruff = ["uv", "run", "--directory", "backend", "--quiet", "ruff"]
    target = str(ROOT / rel)
    subprocess.run([*ruff, "format", "--quiet", target], capture_output=True)
    result = subprocess.run(
        [*ruff, "check", "--fix", "--quiet", target], capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"ruff found problems in {rel}:\n{result.stdout}{result.stderr}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
