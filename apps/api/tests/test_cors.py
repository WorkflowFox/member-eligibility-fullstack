"""Tests for CORS middleware configuration on the FastAPI `app`. Per #21.

Covers: allowed-origin preflight and actual requests get
`Access-Control-Allow-Origin`; disallowed-origin requests don't; and the
`ALLOWED_ORIGINS` env var (not a hardcoded value) controls which origin(s)
are allowed.
"""

import datetime
import importlib

from fastapi.testclient import TestClient

import main as main_module
from db import make_engine, make_session_factory
from seed import seed

TODAY = datetime.date.today()
DEFAULT_ORIGIN = "http://localhost:3000"
DISALLOWED_ORIGIN = "http://evil.example.com"


def _seeded_client(app, get_session, tmp_path) -> TestClient:
    """Build a TestClient for `app` whose `get_session` dependency points at
    a freshly-seeded temporary database, per #3's seed data (mirrors the
    helper in test_eligibility_endpoint.py, parameterized over `app` /
    `get_session` so it also works with a reloaded `main` module)."""
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
    return TestClient(app)


def test_preflight_from_allowed_origin_gets_success_with_header(tmp_path):
    client = _seeded_client(main_module.app, main_module.get_session, tmp_path)
    try:
        response = client.options(
            "/api/v1/eligibility",
            headers={
                "Origin": DEFAULT_ORIGIN,
                "Access-Control-Request-Method": "GET",
            },
        )
    finally:
        main_module.app.dependency_overrides.clear()

    assert response.status_code in (200, 204)
    assert response.headers.get("access-control-allow-origin") == DEFAULT_ORIGIN


def test_actual_get_from_allowed_origin_receives_header(tmp_path):
    client = _seeded_client(main_module.app, main_module.get_session, tmp_path)
    try:
        response = client.get(
            "/api/v1/eligibility",
            params={"memberId": "M-1001", "checkDate": TODAY.isoformat()},
            headers={"Origin": DEFAULT_ORIGIN},
        )
    finally:
        main_module.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == DEFAULT_ORIGIN


def test_disallowed_origin_does_not_receive_allow_origin_header(tmp_path):
    client = _seeded_client(main_module.app, main_module.get_session, tmp_path)
    try:
        preflight = client.options(
            "/api/v1/eligibility",
            headers={
                "Origin": DISALLOWED_ORIGIN,
                "Access-Control-Request-Method": "GET",
            },
        )
        actual = client.get(
            "/api/v1/eligibility",
            params={"memberId": "M-1001", "checkDate": TODAY.isoformat()},
            headers={"Origin": DISALLOWED_ORIGIN},
        )
    finally:
        main_module.app.dependency_overrides.clear()

    assert "access-control-allow-origin" not in preflight.headers
    assert "access-control-allow-origin" not in actual.headers


def test_allowed_origins_env_var_is_not_hardcoded(monkeypatch, tmp_path):
    """Setting `ALLOWED_ORIGINS` to a different value changes which origin
    is accepted -- confirming the allow-list is read from the env var
    rather than hardcoded. `main` is reloaded so the module-level
    `app.add_middleware(...)` call picks up the new env var."""
    custom_origin = "https://custom.example.com"
    monkeypatch.setenv("ALLOWED_ORIGINS", custom_origin)
    reloaded = importlib.reload(main_module)

    try:
        client = _seeded_client(reloaded.app, reloaded.get_session, tmp_path)

        custom_response = client.options(
            "/api/v1/eligibility",
            headers={
                "Origin": custom_origin,
                "Access-Control-Request-Method": "GET",
            },
        )
        default_response = client.options(
            "/api/v1/eligibility",
            headers={
                "Origin": DEFAULT_ORIGIN,
                "Access-Control-Request-Method": "GET",
            },
        )
    finally:
        reloaded.app.dependency_overrides.clear()
        # Restore the env var and reload again so later tests (in this file
        # or others, if collected after this one) see the default-config app.
        monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
        importlib.reload(main_module)

    assert custom_response.headers.get("access-control-allow-origin") == custom_origin
    assert "access-control-allow-origin" not in default_response.headers


def test_allowed_origins_env_var_supports_comma_separated_list(monkeypatch, tmp_path):
    """Multiple origins can be allowed at once via a comma-separated
    `ALLOWED_ORIGINS`."""
    other_origin = "https://other.example.com"
    monkeypatch.setenv("ALLOWED_ORIGINS", f"{DEFAULT_ORIGIN},{other_origin}")
    reloaded = importlib.reload(main_module)

    try:
        client = _seeded_client(reloaded.app, reloaded.get_session, tmp_path)

        first = client.options(
            "/api/v1/eligibility",
            headers={
                "Origin": DEFAULT_ORIGIN,
                "Access-Control-Request-Method": "GET",
            },
        )
        second = client.options(
            "/api/v1/eligibility",
            headers={
                "Origin": other_origin,
                "Access-Control-Request-Method": "GET",
            },
        )
    finally:
        reloaded.app.dependency_overrides.clear()
        monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
        importlib.reload(main_module)

    assert first.headers.get("access-control-allow-origin") == DEFAULT_ORIGIN
    assert second.headers.get("access-control-allow-origin") == other_origin


def test_no_allowed_origins_env_var_defaults_to_localhost_3000(monkeypatch, tmp_path):
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    reloaded = importlib.reload(main_module)

    try:
        client = _seeded_client(reloaded.app, reloaded.get_session, tmp_path)

        response = client.options(
            "/api/v1/eligibility",
            headers={
                "Origin": DEFAULT_ORIGIN,
                "Access-Control-Request-Method": "GET",
            },
        )
    finally:
        reloaded.app.dependency_overrides.clear()
        importlib.reload(main_module)

    assert response.headers.get("access-control-allow-origin") == DEFAULT_ORIGIN
