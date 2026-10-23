def test_board_starts_empty_with_four_columns(client):
    response = client.get("/board")
    assert response.status_code == 200
    body = response.json()
    assert [c["id"] for c in body["columns"]] == ["new", "todo", "in_progress", "done"]
    assert body["cards"] == []


def test_create_card_defaults_to_new_column(client):
    response = client.post("/cards", json={"title": "Write specs"})
    assert response.status_code == 201
    card = response.json()
    assert card["title"] == "Write specs"
    assert card["description"] == ""
    assert card["column"] == "new"
    assert card["id"]


def test_create_card_rejects_empty_title(client):
    response = client.post("/cards", json={"title": ""})
    assert response.status_code == 422


def test_created_card_appears_on_the_board(client):
    client.post("/cards", json={"title": "Task A"})
    client.post("/cards", json={"title": "Task B", "column": "done"})

    board = client.get("/board").json()
    titles = {c["title"]: c["column"] for c in board["cards"]}
    assert titles == {"Task A": "new", "Task B": "done"}


def test_update_card_title_and_description(client):
    card = client.post("/cards", json={"title": "Original"}).json()

    response = client.patch(
        f"/cards/{card['id']}",
        json={"title": "Updated", "description": "More detail"},
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["title"] == "Updated"
    assert updated["description"] == "More detail"
    assert updated["column"] == "new"


def test_update_missing_card_returns_404(client):
    response = client.patch("/cards/does-not-exist", json={"title": "x"})
    assert response.status_code == 404


def test_move_card_to_another_column(client):
    card = client.post("/cards", json={"title": "Task"}).json()

    response = client.patch(f"/cards/{card['id']}/move", json={"column": "in_progress"})
    assert response.status_code == 200
    assert response.json()["column"] == "in_progress"


def test_move_card_to_every_column(client):
    card = client.post("/cards", json={"title": "Task"}).json()

    for column in ["todo", "in_progress", "done", "new"]:
        response = client.patch(f"/cards/{card['id']}/move", json={"column": column})
        assert response.status_code == 200
        assert response.json()["column"] == column


def test_move_missing_card_returns_404(client):
    response = client.patch("/cards/does-not-exist/move", json={"column": "done"})
    assert response.status_code == 404


def test_delete_card(client):
    card = client.post("/cards", json={"title": "Task"}).json()

    response = client.delete(f"/cards/{card['id']}")
    assert response.status_code == 204

    board = client.get("/board").json()
    assert board["cards"] == []


def test_delete_missing_card_returns_404(client):
    response = client.delete("/cards/does-not-exist")
    assert response.status_code == 404
