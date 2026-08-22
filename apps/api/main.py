"""FastAPI application entrypoint for the api service.

This module holds the single FastAPI app instance. Run locally with:

    uvicorn main:app --reload
"""

import datetime
from typing import Generator, Literal

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import DEFAULT_DB_PATH, make_engine, make_session_factory
from eligibility import check_eligibility
from lookup import get_member_coverage

app = FastAPI(title="Member Eligibility API")

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


@app.get("/api/v1/eligibility")
def get_eligibility(
    memberId: str,
    checkDate: datetime.date,
    session: Session = Depends(get_session),
) -> EligibilityResponse:
    """Look up a member's coverage and decide eligibility on `checkDate`.

    Wires together the lookup (#5) and the pure decision function (#4) --
    no eligibility logic is duplicated here. Every outcome, including a
    member that cannot be found, returns HTTP 200 (see #6 acceptance
    criteria); validating malformed input is out of scope (see #7).
    """
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
