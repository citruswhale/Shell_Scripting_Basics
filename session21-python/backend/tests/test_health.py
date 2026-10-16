"""Health, readiness, info and metrics endpoints."""


def test_health_is_ok(client):
    for path in ("/health", "/api/health"):
        resp = client.get(path)
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


def test_ready_checks_database(client):
    for path in ("/ready", "/api/ready"):
        resp = client.get(path)
        assert resp.status_code == 200
        assert resp.json() == {"status": "ready"}


def test_ready_returns_503_when_db_is_down(client, monkeypatch):
    import app.main as main

    class BrokenEngine:
        def connect(self):
            raise ConnectionError("database is down")

    monkeypatch.setattr(main, "engine", BrokenEngine())
    resp = client.get("/ready")
    assert resp.status_code == 503
    assert resp.json() == {"status": "unavailable"}
    # liveness must not depend on the database
    assert client.get("/health").status_code == 200


def test_info_shows_name_and_version(client):
    body = client.get("/api/info").json()
    assert body["name"] == "GearLoan"
    assert body["version"]


def test_metrics_use_route_templates(client, make_item, make_loan):
    item = make_item()
    client.get(f"/api/items/{item['id']}")
    make_loan(item["id"])

    resp = client.get("/metrics")
    assert resp.status_code == 200
    text = resp.text
    assert "http_requests_total" in text
    assert "http_request_duration_seconds_bucket" in text
    assert "gearloan_loans_created_total" in text
    assert "gearloan_loans_returned_total" in text
    # the label is the template, not the real id
    assert 'path="/api/items/{item_id}"' in text
    assert f'path="/api/items/{item["id"]}"' not in text
    assert client.get("/api/metrics").status_code == 200


def test_loan_counters_go_up(client, make_item, make_loan):
    from app import metrics

    created_before = metrics.LOANS_CREATED._value.get()
    returned_before = metrics.LOANS_RETURNED._value.get()

    loan = make_loan(make_item()["id"]).json()
    client.post(f"/api/loans/{loan['id']}/return", json={})

    assert metrics.LOANS_CREATED._value.get() == created_before + 1
    assert metrics.LOANS_RETURNED._value.get() == returned_before + 1
