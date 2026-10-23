"""Integration tests: a real uvicorn process, a real database, real HTTP.

By default the server gets a fresh SQLite file per test module. Set
INTEGRATION_DATABASE_URL (CI does, pointing at a Postgres service) to run
the same journey against Postgres instead.
"""

import os
import socket
import subprocess
import sys
import time

import httpx
import pytest


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Server:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.port = _free_port()
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.process: subprocess.Popen | None = None

    def start(self) -> None:
        env = {
            **os.environ,
            "DATABASE_URL": self.database_url,
            "APP_ENV": "test",
        }
        env.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "boardly_backend.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
            ],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                if httpx.get(f"{self.base_url}/readyz", timeout=1).status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(0.2)
        self.stop()
        raise RuntimeError("server did not become ready")

    def stop(self) -> None:
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=10)
            self.process = None


@pytest.fixture
def database_url(tmp_path):
    url = os.getenv("INTEGRATION_DATABASE_URL")
    if url:
        yield url
        # Leave Postgres clean for the next test.
        from sqlalchemy import create_engine, text

        engine = create_engine(url)
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM cards"))
        engine.dispose()
    else:
        yield f"sqlite:///{tmp_path / 'boardly.db'}"


@pytest.fixture
def server(database_url):
    srv = Server(database_url)
    srv.start()
    yield srv
    srv.stop()


def test_full_card_lifecycle_over_http(server):
    with httpx.Client(base_url=server.base_url, timeout=5) as api:
        created = api.post("/cards", json={"title": "Ship it", "description": "v1"})
        assert created.status_code == 201
        card_id = created.json()["id"]

        assert (
            api.patch(f"/cards/{card_id}", json={"title": "Ship it now"}).status_code
            == 200
        )
        moved = api.patch(f"/cards/{card_id}/move", json={"column": "in_progress"})
        assert moved.json()["column"] == "in_progress"

        board = api.get("/board").json()
        assert [(c["title"], c["column"]) for c in board["cards"]] == [
            ("Ship it now", "in_progress")
        ]

        assert api.delete(f"/cards/{card_id}").status_code == 204
        assert api.get("/board").json()["cards"] == []


def test_cards_survive_a_server_restart(server):
    with httpx.Client(base_url=server.base_url, timeout=5) as api:
        card_id = api.post("/cards", json={"title": "Persist me"}).json()["id"]
        api.patch(f"/cards/{card_id}/move", json={"column": "done"})

    server.stop()
    server.start()

    with httpx.Client(base_url=server.base_url, timeout=5) as api:
        cards = api.get("/board").json()["cards"]
    assert [(c["id"], c["column"]) for c in cards] == [(card_id, "done")]


def test_cors_allows_the_dev_frontend(server):
    response = httpx.options(
        f"{server.base_url}/board",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert (
        response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    )
