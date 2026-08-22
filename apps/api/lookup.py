"""Member and coverage lookup (data-access layer).

Queries the database seeded by `seed.py` (#3) for a member's coverage,
using the SQLAlchemy models from `models.py` -- no raw SQL strings.

Deciding ELIGIBLE/NOT_YET_ELIGIBLE/INELIGIBLE from the returned dates is out
of scope here (see `eligibility.py`, #4), as is exposing this lookup as an
HTTP endpoint (see #6).
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Coverage, Member, Plan


@dataclass(frozen=True)
class MemberCoverage:
    """A member's coverage details, as returned by `get_member_coverage`."""

    member_id: str
    name: str
    plan_name: str
    effective_date: datetime.date
    termination_date: datetime.date | None


def get_member_coverage(session: Session, member_id: str) -> MemberCoverage | None:
    """Look up a member's coverage by exact member ID.

    Args:
        session: An open SQLAlchemy session.
        member_id: The member ID to look up. Matched exactly against
            `Member.member_id` -- no partial or case-insensitive matching.

    Returns:
        A `MemberCoverage` with the member's name, plan name, coverage
        effective date, and coverage termination date, if a member with
        that exact ID exists and has a coverage record. `None` if no such
        member (or no matching coverage) exists -- never partially-filled
        data and never an unhandled exception for a missing member.
    """
    row = session.execute(
        select(Member, Coverage, Plan)
        .join(Coverage, Coverage.member_id == Member.member_id)
        .join(Plan, Plan.plan_id == Coverage.plan_id)
        .where(Member.member_id == member_id)
    ).first()

    if row is None:
        return None

    member, coverage, plan = row

    return MemberCoverage(
        member_id=member.member_id,
        name=member.name,
        plan_name=plan.name,
        effective_date=coverage.effective_date,
        termination_date=coverage.termination_date,
    )
