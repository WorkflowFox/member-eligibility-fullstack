"""FastAPI application entrypoint for the api service.

This module holds the single FastAPI app instance. Run locally with:

    uvicorn main:app --reload
"""

import datetime
import os
from typing import Annotated, Generator, Literal

from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db import DEFAULT_DB_PATH, make_engine, make_session_factory
from eligibility import check_eligibility
from lookup import get_member_coverage

app = FastAPI(title="Member Eligibility API")

DEFAULT_ALLOWED_ORIGINS = ["http://localhost:3000"]


def _get_allowed_origins() -> list[str]:
    """Read allowed CORS origins from `ALLOWED_ORIGINS` (comma-separated).

    Defaults to `http://localhost:3000` -- matching the `web` service's
    host-published port in #15's docker-compose setup -- if the env var is
    unset or blank, so local dev works out of the box without any code or
    compose change. Per #21.
    """
    raw = os.environ.get("ALLOWED_ORIGINS")
    if not raw:
        return DEFAULT_ALLOWED_ORIGINS
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or DEFAULT_ALLOWED_ORIGINS


app.add_middleware(CORSMiddleware, allow_origins=_get_allowed_origins())

_engine = make_engine(DEFAULT_DB_PATH)
_session_factory = make_session_factory(_engine)


def get_session() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session bound to the api's default database.

    Overridden in tests via `app.dependency_overrides` to point at a
    seeded temporary database instead.
    """
    session = _session_factory()
    try:
        yield session
    finally:
        session.close()


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check. Does not depend on the database."""
    return {"status": "ok"}


EligibilityStatus = Literal[
    "ELIGIBLE", "NOT_YET_ELIGIBLE", "INELIGIBLE", "MEMBER_NOT_FOUND"
]


class EligibilityResponse(BaseModel):
    """Response contract for `GET /api/v1/eligibility`.

    Field names and shape per `_docs/outdated/architecture.md` §5.
    """

    memberId: str
    memberName: str | None
    planName: str | None
    coverageEffectiveDate: datetime.date | None
    coverageTerminationDate: datetime.date | None
    checkCoverageOnDate: datetime.date
    eligibilityStatus: EligibilityStatus
    eligibilityReason: str


class EligibilityQueryParams(BaseModel):
    """Query parameters for `GET /api/v1/eligibility`.

    Declared as a Pydantic model -- rather than manual `if` checks in the
    route handler -- so FastAPI's native query validation rejects bad
    input before the handler ever runs. A missing/blank `memberId` or a
    missing/malformed `checkDate` (not a valid ISO `YYYY-MM-DD` date) both
    produce a `422` with FastAPI/Pydantic's default `detail` shape. Per #7.
    """

    memberId: str = Field(min_length=1)
    checkDate: datetime.date


@app.get("/api/v1/eligibility")
def get_eligibility(
    params: Annotated[EligibilityQueryParams, Query()],
    session: Session = Depends(get_session),
) -> EligibilityResponse:
    """Look up a member's coverage and decide eligibility on `checkDate`.

    Wires together the lookup (#5) and the pure decision function (#4) --
    no eligibility logic is duplicated here. Every outcome, including a
    member that cannot be found, returns HTTP 200 (see #6 acceptance
    criteria). Malformed input is rejected with a 422 by
    `EligibilityQueryParams` before this body runs, and any unexpected
    failure below is turned into a generic 500 by the app-wide exception
    handler (see #7).
    """
    memberId = params.memberId
    checkDate = params.checkDate

    coverage = get_member_coverage(session, memberId)

    if coverage is None:
        return EligibilityResponse(
            memberId=memberId,
            memberName=None,
            planName=None,
            coverageEffectiveDate=None,
            coverageTerminationDate=None,
            checkCoverageOnDate=checkDate,
            eligibilityStatus="MEMBER_NOT_FOUND",
            eligibilityReason=f"No member found with ID {memberId}.",
        )

    status = check_eligibility(
        coverage.effective_date, coverage.termination_date, checkDate
    )

    reasons: dict[str, str] = {
        "ELIGIBLE": f"Coverage is active on {checkDate}.",
        "NOT_YET_ELIGIBLE": f"Coverage does not begin until {coverage.effective_date}.",
        "INELIGIBLE": f"Coverage ended on {coverage.termination_date}.",
    }

    return EligibilityResponse(
        memberId=coverage.member_id,
        memberName=coverage.name,
        planName=coverage.plan_name,
        coverageEffectiveDate=coverage.effective_date,
        coverageTerminationDate=coverage.termination_date,
        checkCoverageOnDate=checkDate,
        eligibilityStatus=status,
        eligibilityReason=reasons[status],
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Turn any unhandled exception into a generic, non-technical 500.

    No exception message, stack trace, or other internal detail is ever
    included in the response body -- per #7 / `_docs/outdated/architecture.md`
    §10 ("no internal details exposed"). The body shape is fixed per the
    grooming decision on #7 so the frontend can key off one `detail` field
    for every non-200 response.
    """
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."},
    )
