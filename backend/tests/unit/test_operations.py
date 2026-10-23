import json


def test_healthz_is_ok(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_checks_the_database(client):
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_request_logs_are_json_and_never_contain_card_content(client, capsys):
    card = client.post(
        "/cards", json={"title": "secret-title", "description": "secret-description"}
    ).json()
    client.patch(f"/cards/{card['id']}/move", json={"column": "done"})

    lines = [
        line for line in capsys.readouterr().out.splitlines() if line.startswith("{")
    ]
    entries = [json.loads(line) for line in lines]

    move = next(e for e in entries if e.get("http.route") == "/cards/{card_id}/move")
    assert move["http.method"] == "PATCH"
    assert move["http.status_code"] == 200
    assert move["card_id"] == card["id"]
    assert "secret" not in "\n".join(lines)
