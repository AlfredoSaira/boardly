"""Collect the evidence behind a Boardly alert.

Every query here is read-only and scoped to the board API. A failure in any
one backend (Prometheus, Loki, Tempo) is recorded, not raised, so a partial
telemetry outage never blocks the other two.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import httpx

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100")
TEMPO_URL = os.getenv("TEMPO_URL", "http://localhost:3200")
SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "boardly-backend")
LOOKBACK_MINUTES = int(os.getenv("EVIDENCE_LOOKBACK_MINUTES", "15"))
MAX_LOGS = int(os.getenv("EVIDENCE_MAX_LOGS", "50"))
MAX_TRACES = int(os.getenv("EVIDENCE_MAX_TRACES", "5"))


@dataclass
class Evidence:
    window_start: str
    window_end: str
    requests_by_route_status: dict
    error_logs: list
    error_trace_ids: list
    failing_routes: list
    errors: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "service": SERVICE_NAME,
            "window": {"start": self.window_start, "end": self.window_end},
            "requests_by_route_status_last_window": self.requests_by_route_status,
            "error_logs": self.error_logs,
            "error_trace_ids": self.error_trace_ids,
            "failing_routes": self.failing_routes,
            "collection_errors": self.errors,
        }


def _safe(errors: list, source: str, func, *args):
    try:
        return func(*args)
    except (httpx.HTTPError, ValueError, KeyError) as error:
        errors.append(f"{source}: {type(error).__name__}: {error}")
        return None


def _query_prometheus(client: httpx.Client, end: datetime) -> dict:
    query = (
        "sum by (http_route, http_status_code) "
        f"(increase(boardly_http_requests_total[{LOOKBACK_MINUTES}m]))"
    )
    response = client.get(
        f"{PROMETHEUS_URL}/api/v1/query", params={"query": query, "time": end.timestamp()}
    )
    response.raise_for_status()
    counts: dict = {}
    for r in response.json()["data"]["result"]:
        route = r["metric"].get("http_route", "?")
        status = r["metric"].get("http_status_code", "?")
        counts.setdefault(route, {})[status] = round(float(r["value"][1]), 2)
    return counts


def _query_loki_errors(client: httpx.Client, start: datetime, end: datetime) -> list:
    query = f'{{service_name="{SERVICE_NAME}"}} | http_status_code=~"5.."'
    response = client.get(
        f"{LOKI_URL}/loki/api/v1/query_range",
        params={
            "query": query,
            "start": int(start.timestamp() * 1e9),
            "end": int(end.timestamp() * 1e9),
            "limit": MAX_LOGS,
            "direction": "backward",
        },
    )
    response.raise_for_status()
    entries = []
    for stream in response.json()["data"]["result"]:
        labels = stream["stream"]
        for ts, line in stream["values"]:
            entries.append(
                {
                    "timestamp": datetime.fromtimestamp(int(ts) / 1e9, timezone.utc).isoformat(),
                    "line": line,
                    "http_method": labels.get("http_method"),
                    "http_route": labels.get("http_route"),
                    "http_status_code": labels.get("http_status_code"),
                    "card_id": labels.get("card_id"),
                    "trace_id": labels.get("trace_id"),
                }
            )
    return entries


def _query_tempo_error_traces(client: httpx.Client, start: datetime, end: datetime) -> list:
    response = client.get(
        f"{TEMPO_URL}/api/search",
        params={
            "q": f'{{ resource.service.name="{SERVICE_NAME}" && status=error }}',
            "start": int(start.timestamp()),
            "end": int(end.timestamp()),
            "limit": MAX_TRACES,
        },
    )
    response.raise_for_status()
    return [t["traceID"] for t in response.json().get("traces", [])]


def collect(now: datetime | None = None, client: httpx.Client | None = None) -> Evidence:
    now = now or datetime.now(timezone.utc)
    start = now - timedelta(minutes=LOOKBACK_MINUTES)
    client = client or httpx.Client(timeout=10)
    errors: list = []

    requests_by_route_status = _safe(errors, "prometheus", _query_prometheus, client, now) or {}
    error_logs = _safe(errors, "loki", _query_loki_errors, client, start, now) or []
    error_trace_ids = _safe(errors, "tempo", _query_tempo_error_traces, client, start, now) or []
    failing_routes = sorted(
        {f"{e['http_method']} {e['http_route']}" for e in error_logs if e.get("http_route")}
    )

    return Evidence(
        window_start=start.isoformat(),
        window_end=now.isoformat(),
        requests_by_route_status=requests_by_route_status,
        error_logs=error_logs,
        error_trace_ids=error_trace_ids,
        failing_routes=failing_routes,
        errors=errors,
    )


def render_markdown(evidence: Evidence) -> str:
    lines = [
        f"Service: {SERVICE_NAME}",
        f"Window: {evidence.window_start} to {evidence.window_end}",
        "",
        f"Requests by route and status code (last {LOOKBACK_MINUTES}m):",
    ]
    if evidence.requests_by_route_status:
        for route, statuses in sorted(evidence.requests_by_route_status.items()):
            counts = ", ".join(f"{s}: {c}" for s, c in sorted(statuses.items()))
            lines.append(f"- {route} -> {counts}")
    else:
        lines.append("- (no data)")

    lines.append("")
    lines.append(f"Routes seen failing in logs: {', '.join(evidence.failing_routes) or '(none found)'}")

    lines.append("")
    lines.append("Error log lines:")
    if evidence.error_logs:
        for entry in evidence.error_logs[:20]:
            lines.append(
                f"- {entry['timestamp']} {entry.get('http_method')} {entry.get('http_route')} "
                f"-> {entry.get('http_status_code')} card_id={entry.get('card_id')} "
                f"trace_id={entry.get('trace_id')}: {entry['line']}"
            )
    else:
        lines.append("- (none)")

    lines.append("")
    lines.append(f"Error trace IDs (Tempo): {', '.join(evidence.error_trace_ids) or '(none)'}")

    if evidence.errors:
        lines.append("")
        lines.append("Evidence collection problems (non-fatal):")
        lines += [f"- {err}" for err in evidence.errors]

    return "\n".join(lines)
