"""Lending rules, returns, overdue logic and stats."""
from datetime import date, timedelta

from sqlalchemy import update

from app.models import Loan
from tests.conftest import in_days


def test_lend_item_marks_it_on_loan(client, make_item, make_loan):
    item = make_item()
    resp = make_loan(item["id"], email="Asha@College.EDU")
    assert resp.status_code == 201
    loan = resp.json()
    assert loan["status"] == "active"
    assert loan["item_name"] == "Canon EOS R50"
    assert loan["borrower_email"] == "asha@college.edu"  # stored in lower case
    assert loan["returned_at"] is None

    assert client.get(f"/api/items/{item['id']}").json()["status"] == "on_loan"
    assert client.get(f"/api/loans/{loan['id']}").json()["id"] == loan["id"]


def test_loan_validation(client, make_item):
    item = make_item()
    base = {"item_id": item["id"], "borrower_name": "Ravi", "borrower_email": "ravi@x.edu"}
    cases = [
        {**base, "borrower_email": "not-an-email", "due_date": in_days(3)},
        {**base, "due_date": in_days(-1)},  # in the past
        {**base, "due_date": in_days(31)},  # more than 30 days ahead
        {**base, "borrower_name": "", "due_date": in_days(3)},
        {"item_id": item["id"], "borrower_email": "ravi@x.edu", "due_date": in_days(3)},
    ]
    for payload in cases:
        assert client.post("/api/loans", json=payload).status_code == 422, payload
    # edge values that are allowed: today and exactly 30 days out
    assert client.post("/api/loans", json={**base, "due_date": in_days(0)}).status_code == 201
    other = make_item(name="Spare camera")
    edge = {**base, "item_id": other["id"], "due_date": in_days(30)}
    assert client.post("/api/loans", json=edge).status_code == 201


def test_loan_for_missing_item_is_404(client, make_loan):
    assert make_loan(4242).status_code == 404
    assert client.get("/api/loans/4242").status_code == 404


def test_cannot_lend_item_twice(client, make_item, make_loan):
    item = make_item()
    assert make_loan(item["id"]).status_code == 201
    resp = make_loan(item["id"], email="someone@else.edu")
    assert resp.status_code == 409


def test_cannot_lend_item_in_maintenance(client, make_item, make_loan):
    item = make_item(status="maintenance")
    resp = make_loan(item["id"])
    assert resp.status_code == 409
    assert "maintenance" in resp.json()["detail"]


def test_borrower_limited_to_three_active_loans(client, make_item, make_loan):
    items = [make_item(name=f"Tripod {n}", category="tripod") for n in range(4)]
    for item in items[:3]:
        assert make_loan(item["id"], email="busy@college.edu").status_code == 201

    # fourth one is refused, even with different capitalisation of the email
    resp = make_loan(items[3]["id"], email="BUSY@college.edu")
    assert resp.status_code == 409
    assert client.get(f"/api/items/{items[3]['id']}").json()["status"] == "available"

    # after returning one, they can borrow again
    first = client.get("/api/loans", params={"borrower_email": "busy@college.edu"}).json()[0]
    client.post(f"/api/loans/{first['id']}/return", json={"condition": "good"})
    assert make_loan(items[3]["id"], email="busy@college.edu").status_code == 201


def test_return_flow(client, make_item, make_loan):
    item = make_item()
    loan = make_loan(item["id"]).json()

    resp = client.post(f"/api/loans/{loan['id']}/return", json={"condition": "fair"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "returned"
    assert body["returned_at"] is not None
    assert body["return_condition"] == "fair"

    item_now = client.get(f"/api/items/{item['id']}").json()
    assert item_now["status"] == "available"
    assert item_now["condition"] == "fair"

    # returning twice is a conflict
    assert client.post(f"/api/loans/{loan['id']}/return", json={}).status_code == 409
    # and the item can be lent again
    assert make_loan(item["id"], email="next@college.edu").status_code == 201


def test_damaged_return_sends_item_to_maintenance(client, make_item, make_loan):
    item = make_item()
    loan = make_loan(item["id"]).json()
    client.post(f"/api/loans/{loan['id']}/return", json={"condition": "damaged"})
    item_now = client.get(f"/api/items/{item['id']}").json()
    assert item_now["status"] == "maintenance"
    assert item_now["condition"] == "damaged"
    assert make_loan(item["id"]).status_code == 409


def test_cannot_delete_item_with_active_loan(client, make_item, make_loan):
    item = make_item()
    loan = make_loan(item["id"]).json()
    assert client.delete(f"/api/items/{item['id']}").status_code == 409

    client.post(f"/api/loans/{loan['id']}/return", json={})
    assert client.delete(f"/api/items/{item['id']}").status_code == 204


def test_delete_loan_only_when_returned(client, make_item, make_loan):
    loan = make_loan(make_item()["id"]).json()
    assert client.delete(f"/api/loans/{loan['id']}").status_code == 409
    client.post(f"/api/loans/{loan['id']}/return", json={})
    assert client.delete(f"/api/loans/{loan['id']}").status_code == 204
    assert client.get(f"/api/loans/{loan['id']}").status_code == 404


def test_overdue_status_and_filters(client, make_item, make_loan, db_session):
    on_time = make_loan(make_item(name="Laptop A", category="laptop")["id"], email="a@x.edu").json()
    late = make_loan(make_item(name="Laptop B", category="laptop")["id"], email="b@x.edu").json()
    done = make_loan(make_item(name="Laptop C", category="laptop")["id"], email="a@x.edu").json()
    client.post(f"/api/loans/{done['id']}/return", json={})

    # Pretend the "late" loan was due three days ago. The API refuses past
    # due dates, so we change it straight in the database.
    db_session.execute(
        update(Loan).where(Loan.id == late["id"]).values(due_date=date.today() - timedelta(days=3))
    )
    db_session.commit()

    assert client.get(f"/api/loans/{late['id']}").json()["status"] == "overdue"

    ids = lambda params: [l["id"] for l in client.get("/api/loans", params=params).json()]  # noqa: E731,E741
    assert ids({"status": "overdue"}) == [late["id"]]
    assert ids({"status": "active"}) == [on_time["id"]]
    assert ids({"status": "returned"}) == [done["id"]]
    assert sorted(ids({"borrower_email": "A@x.edu"})) == sorted([on_time["id"], done["id"]])
    assert client.get("/api/loans", params={"status": "lost"}).status_code == 422

    # an overdue loan can still be returned
    resp = client.post(f"/api/loans/{late['id']}/return", json={"condition": "good"})
    assert resp.json()["status"] == "returned"


def test_stats(client, make_item, make_loan, db_session):
    empty = client.get("/api/stats").json()
    assert empty == {
        "items_total": 0,
        "available": 0,
        "on_loan": 0,
        "maintenance": 0,
        "active_loans": 0,
        "overdue_loans": 0,
    }

    a = make_item(name="Cam A")
    b = make_item(name="Cam B")
    make_item(name="Cam C")
    make_item(name="Old light", category="lighting", status="maintenance")
    make_loan(a["id"], email="p@x.edu")
    late = make_loan(b["id"], email="q@x.edu").json()
    db_session.execute(
        update(Loan).where(Loan.id == late["id"]).values(due_date=date.today() - timedelta(days=1))
    )
    db_session.commit()

    stats = client.get("/api/stats").json()
    assert stats == {
        "items_total": 4,
        "available": 1,
        "on_loan": 2,
        "maintenance": 1,
        "active_loans": 2,  # everything still out, overdue included
        "overdue_loans": 1,
    }
