"""Seed a SQLite database with synthetic Member/Plan/Coverage data.

The schema is created from the SQLAlchemy models in `models.py` (no
hand-written SQL) and is safe to run repeatedly: seeding is idempotent and
does not create duplicate rows.

The seed data is designed so every eligibility outcome can be demonstrated
against today's date:

- `M-1001` (Jordan Testcase) -- coverage effective well in the past with no
  termination date -- evaluates to `ELIGIBLE`, and also demonstrates an
  open-ended active coverage (`termination_date IS NULL`).
- `M-1002` (Riley Sampleton) -- coverage effective in the future -- evaluates
  to `NOT_YET_ELIGIBLE`.
- `M-1003` (Morgan Placeholder) -- coverage terminated in the past --
  evaluates to `INELIGIBLE`.

`M-9999` is RESERVED and is never present in the seed data. It exists so
demos and tests can deterministically look up a non-existent member and
observe `MEMBER_NOT_FOUND`, without depending on an arbitrary/unlucky ID.

All member, plan, and organization names below are fictional placeholder
names (per `_docs/outdated/plan.md` §10) and do not refer to real people or
companies.

Usage:

    python seed.py [--db-path PATH]

or, from Python:

    from seed import seed
    seed(db_path="/tmp/eligibility.db")
"""

from __future__ import annotations

import argparse
import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from db import DEFAULT_DB_PATH, create_schema, make_engine, make_session_factory
from models import Coverage, Member, Plan

# Reserved and intentionally never seeded -- see module docstring.
RESERVED_NOT_FOUND_MEMBER_ID = "M-9999"


def _upsert_member(session: Session, member_id: str, name: str) -> Member:
    member = session.get(Member, member_id)
    if member is None:
        member = Member(member_id=member_id, name=name)
        session.add(member)
    else:
        member.name = name
    return member


def _upsert_plan(session: Session, plan_id: str, name: str) -> Plan:
    plan = session.get(Plan, plan_id)
    if plan is None:
        plan = Plan(plan_id=plan_id, name=name)
        session.add(plan)
    else:
        plan.name = name
    return plan


def _upsert_coverage(
    session: Session,
    member_id: str,
    plan_id: str,
    effective_date: datetime.date,
    termination_date: datetime.date | None,
) -> Coverage:
    coverage = session.get(Coverage, member_id)
    if coverage is None:
        coverage = Coverage(
            member_id=member_id,
            plan_id=plan_id,
            effective_date=effective_date,
            termination_date=termination_date,
        )
        session.add(coverage)
    else:
        coverage.plan_id = plan_id
        coverage.effective_date = effective_date
        coverage.termination_date = termination_date
    return coverage


def _synthetic_records(today: datetime.date) -> list[dict]:
    """Synthetic member/plan/coverage records, built relative to `today`."""
    return [
        {
            "member_id": "M-1001",
            "member_name": "Jordan Testcase",
            "plan_id": "PLAN-ACME",
            "plan_name": "Acme Health Plan",
            # Effective long ago, no termination date -> ELIGIBLE and
            # open-ended active coverage.
            "effective_date": today - datetime.timedelta(days=400),
            "termination_date": None,
        },
        {
            "member_id": "M-1002",
            "member_name": "Riley Sampleton",
            "plan_id": "PLAN-GLOBEX",
            "plan_name": "Globex Wellness Plan",
            # Effective in the future -> NOT_YET_ELIGIBLE.
            "effective_date": today + datetime.timedelta(days=30),
            "termination_date": None,
        },
        {
            "member_id": "M-1003",
            "member_name": "Morgan Placeholder",
            "plan_id": "PLAN-INITECH",
            "plan_name": "Initech Care Plan",
            # Terminated in the past -> INELIGIBLE.
            "effective_date": today - datetime.timedelta(days=400),
            "termination_date": today - datetime.timedelta(days=10),
        },
    ]


def seed(db_path: str | Path = DEFAULT_DB_PATH) -> Path:
    """Create the schema (if needed) and idempotently seed synthetic data.

    Returns the resolved path of the database file that was seeded.
    """
    db_path = Path(db_path)
    engine = make_engine(db_path)
    create_schema(engine)

    session_factory = make_session_factory(engine)
    today = datetime.date.today()

    with session_factory() as session:
        for record in _synthetic_records(today):
            assert record["member_id"] != RESERVED_NOT_FOUND_MEMBER_ID

            _upsert_member(session, record["member_id"], record["member_name"])
            _upsert_plan(session, record["plan_id"], record["plan_name"])
            _upsert_coverage(
                session,
                member_id=record["member_id"],
                plan_id=record["plan_id"],
                effective_date=record["effective_date"],
                termination_date=record["termination_date"],
            )

        session.commit()

    return db_path.resolve()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db-path",
        default=DEFAULT_DB_PATH,
        help=f"Path to the SQLite database to seed (default: {DEFAULT_DB_PATH})",
    )
    args = parser.parse_args()

    resolved_path = seed(db_path=args.db_path)

    print(f"Seeded synthetic data into {resolved_path}")
    print(
        f"Note: member ID {RESERVED_NOT_FOUND_MEMBER_ID} is reserved and is "
        "intentionally never present -- use it to demonstrate MEMBER_NOT_FOUND."
    )


if __name__ == "__main__":
    main()
