import pytest
from fastapi.testclient import TestClient

from app.fees import MAX_FEE, late_fee
from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_version_has_app_and_commit():
    body = client.get("/version").json()
    assert body["app"] == "s17-loan-calculator"
    assert "commit" in body


def test_fee_normal_case():
    # 5 days late, 1 grace day -> 4 chargeable days * 20
    body = client.get("/fee", params={"days_late": 5, "daily_rate": 20}).json()
    assert body["fee"] == 80.0
    assert body["capped"] is False


def test_fee_inside_grace_period_is_zero():
    body = client.get("/fee", params={"days_late": 1, "daily_rate": 50}).json()
    assert body["fee"] == 0.0


def test_fee_is_capped():
    body = client.get("/fee", params={"days_late": 300, "daily_rate": 100}).json()
    assert body["fee"] == MAX_FEE
    assert body["capped"] is True


@pytest.mark.parametrize(
    "params",
    [
        {"days_late": -1, "daily_rate": 10},
        {"days_late": 5, "daily_rate": 0},
        {"days_late": 5, "daily_rate": -3},
        {"days_late": "abc", "daily_rate": 10},
        {"days_late": 5},
    ],
)
def test_fee_rejects_bad_input(params):
    res = client.get("/fee", params=params)
    assert res.status_code == 422


def test_late_fee_function_rejects_negative_days():
    with pytest.raises(ValueError):
        late_fee(-2, 10)


def test_late_fee_rounds_to_two_decimals():
    assert late_fee(4, 3.333) == 10.0
