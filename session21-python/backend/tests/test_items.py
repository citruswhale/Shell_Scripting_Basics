"""Item CRUD, validation, search and filters."""
from sqlalchemy import select

from app.models import Item


def test_create_and_get_item(client):
    resp = client.post(
        "/api/items",
        json={
            "name": "Rode VideoMic",
            "category": "audio",
            "serial_number": "RODE-001",
            "condition": "fair",
            "notes": "Comes with a dead cat windshield",
        },
    )
    assert resp.status_code == 201
    item = resp.json()
    assert item["id"] > 0
    assert item["status"] == "available"
    assert item["condition"] == "fair"
    assert item["created_at"] and item["updated_at"]

    fetched = client.get(f"/api/items/{item['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["serial_number"] == "RODE-001"


def test_create_item_validation_errors(client):
    bad_payloads = [
        {"category": "camera"},  # no name
        {"name": "A", "category": "camera"},  # name too short
        {"name": "x" * 101, "category": "camera"},  # name too long
        {"name": "Drone", "category": "drone"},  # unknown category
        {"name": "Tripod", "category": "tripod", "condition": "broken"},
        {"name": "Tripod", "category": "tripod", "status": "on_loan"},  # can't create on loan
    ]
    for payload in bad_payloads:
        resp = client.post("/api/items", json=payload)
        assert resp.status_code == 422, payload


def test_serial_number_must_be_unique(client, make_item):
    make_item(serial_number="SN-123")
    resp = client.post(
        "/api/items", json={"name": "Second", "category": "camera", "serial_number": "SN-123"}
    )
    assert resp.status_code == 409
    # an empty serial is treated as "none", so several items can leave it blank
    make_item(name="No serial 1", serial_number="")
    make_item(name="No serial 2", serial_number="")


def test_update_item(client, make_item):
    item = make_item()
    resp = client.put(
        f"/api/items/{item['id']}",
        json={"name": "Canon EOS R50 Kit", "condition": "fair", "status": "maintenance"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Canon EOS R50 Kit"
    assert body["condition"] == "fair"
    assert body["status"] == "maintenance"
    assert body["category"] == "camera"  # untouched field keeps its value

    assert client.put(f"/api/items/{item['id']}", json={"name": "x"}).status_code == 422
    assert client.put(f"/api/items/{item['id']}", json={"status": "on_loan"}).status_code == 409


def test_missing_item_returns_404(client):
    assert client.get("/api/items/9999").status_code == 404
    assert client.put("/api/items/9999", json={"name": "Nope"}).status_code == 404
    assert client.delete("/api/items/9999").status_code == 404


def test_delete_item(client, make_item):
    item = make_item()
    assert client.delete(f"/api/items/{item['id']}").status_code == 204
    assert client.get(f"/api/items/{item['id']}").status_code == 404


def test_search_and_filters(client, make_item):
    make_item(name="Sony A7 III", category="camera", serial_number="SONY-7")
    make_item(name="MacBook Air", category="laptop")
    make_item(name="Godox LED panel", category="lighting", notes="needs sony battery")
    lamp = make_item(name="Softbox", category="lighting")
    client.put(f"/api/items/{lamp['id']}", json={"status": "maintenance"})

    names = lambda resp: sorted(i["name"] for i in resp.json())  # noqa: E731

    # search is case-insensitive and also looks at serial number and notes
    assert names(client.get("/api/items", params={"search": "SONY"})) == [
        "Godox LED panel",
        "Sony A7 III",
    ]
    assert names(client.get("/api/items", params={"category": "lighting"})) == [
        "Godox LED panel",
        "Softbox",
    ]
    assert names(client.get("/api/items", params={"status": "maintenance"})) == ["Softbox"]
    assert names(
        client.get("/api/items", params={"category": "lighting", "status": "available"})
    ) == ["Godox LED panel"]
    assert len(client.get("/api/items").json()) == 4
    assert client.get("/api/items", params={"category": "spaceship"}).status_code == 422


def test_items_persist_across_sessions(client, make_item, db_session):
    item = make_item(name="Zoom H5 Recorder", category="audio")
    # read it back with a brand new session, straight from the database
    stored = db_session.scalars(select(Item).where(Item.id == item["id"])).one()
    assert stored.name == "Zoom H5 Recorder"
    assert stored.status == "available"
