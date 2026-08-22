import datetime

from fastapi.testclient import TestClient

from db import make_engine, make_session_factory
from main import app, get_session
from seed import RESERVED_NOT_FOUND_MEMBER_ID, seed

TODAY = datetime.date.today()


def _client_with_seeded_db(tmp_path):
    """Build a TestClient whose `get_session` dependency points at a
    freshly-seeded temporary database, per #3's seed data."""
    db_path = tmp_path / "eligibility.db"
    seed(db_path=db_path)

    engine = make_engine(db_path)
    session_factory = make_session_factory(engine)

    def override_get_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    return client


def _clear_overrides():
    app.dependency_overrides.clear()


def test_eligible_member_returns_200_with_full_details(tmp_path):
    client = _client_with_seeded_db(tmp_path)
    try:
        response = client.get(
            "/api/v1/eligibility",
            params={"memberId": "M-1001", "checkDate": TODAY.isoformat()},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    body = response.json()

    assert body["memberId"] == "M-1001"
    assert body["memberName"] == "Jordan Testcase"
    assert body["planName"] is not None
    assert body["coverageEffectiveDate"] is not None
    assert body["coverageTerminationDate"] is None
    assert body["checkCoverageOnDate"] == TODAY.isoformat()
    assert body["eligibilityStatus"] == "ELIGIBLE"
    assert body["eligibilityReason"] == f"Coverage is active on {TODAY}."
    assert set(body.keys()) == {
        "memberId",
        "memberName",
        "planName",
        "coverageEffectiveDate",
        "coverageTerminationDate",
        "checkCoverageOnDate",
        "eligibilityStatus",
        "eligibilityReason",
    }


def test_not_yet_eligible_member_returns_200(tmp_path):
    client = _client_with_seeded_db(tmp_path)
    try:
        response = client.get(
            "/api/v1/eligibility",
            params={"memberId": "M-1002", "checkDate": TODAY.isoformat()},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    body = response.json()

    assert body["memberId"] == "M-1002"
    assert body["memberName"] == "Riley Sampleton"
    assert body["planName"] is not None
    effective_date = body["coverageEffectiveDate"]
    assert effective_date is not None
    assert body["eligibilityStatus"] == "NOT_YET_ELIGIBLE"
    assert body["eligibilityReason"] == f"Coverage does not begin until {effective_date}."


def test_ineligible_member_returns_200(tmp_path):
    client = _client_with_seeded_db(tmp_path)
    try:
        response = client.get(
            "/api/v1/eligibility",
            params={"memberId": "M-1003", "checkDate": TODAY.isoformat()},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    body = response.json()

    assert body["memberId"] == "M-1003"
    assert body["memberName"] == "Morgan Placeholder"
    assert body["planName"] is not None
    termination_date = body["coverageTerminationDate"]
    assert termination_date is not None
    assert body["eligibilityStatus"] == "INELIGIBLE"
    assert body["eligibilityReason"] == f"Coverage ended on {termination_date}."


def test_member_not_found_returns_200_not_404(tmp_path):
    client = _client_with_seeded_db(tmp_path)
    try:
        response = client.get(
            "/api/v1/eligibility",
            params={
                "memberId": RESERVED_NOT_FOUND_MEMBER_ID,
                "checkDate": TODAY.isoformat(),
            },
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    body = response.json()

    assert body == {
        "memberId": RESERVED_NOT_FOUND_MEMBER_ID,
        "memberName": None,
        "planName": None,
        "coverageEffectiveDate": None,
        "coverageTerminationDate": None,
        "checkCoverageOnDate": TODAY.isoformat(),
        "eligibilityStatus": "MEMBER_NOT_FOUND",
        "eligibilityReason": f"No member found with ID {RESERVED_NOT_FOUND_MEMBER_ID}.",
    }


def test_eligibility_route_is_on_the_single_app_instance(tmp_path):
    # The endpoint is reachable through the same `app` that serves /health,
    # not a separately-mounted app.
    client = _client_with_seeded_db(tmp_path)
    try:
        health_response = client.get("/health")
        eligibility_response = client.get(
            "/api/v1/eligibility",
            params={"memberId": "M-1001", "checkDate": TODAY.isoformat()},
        )
    finally:
        _clear_overrides()

    assert health_response.status_code == 200
    assert eligibility_response.status_code == 200
