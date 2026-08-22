import datetime

from sqlalchemy import select

from db import make_engine, make_session_factory
from models import Coverage, Member
from seed import RESERVED_NOT_FOUND_MEMBER_ID, seed


def _seed_and_open_session(tmp_path):
    db_path = tmp_path / "eligibility.db"
    seed(db_path=db_path)

    engine = make_engine(db_path)
    session_factory = make_session_factory(engine)
    return session_factory()


def test_seed_creates_member_demonstrating_eligible(tmp_path):
    today = datetime.date.today()

    with _seed_and_open_session(tmp_path) as session:
        member = session.get(Member, "M-1001")
        assert member is not None

        coverage = session.get(Coverage, "M-1001")
        assert coverage is not None
        assert coverage.effective_date <= today
        assert coverage.termination_date is None or coverage.termination_date >= today


def test_seed_creates_member_demonstrating_not_yet_eligible(tmp_path):
    today = datetime.date.today()

    with _seed_and_open_session(tmp_path) as session:
        member = session.get(Member, "M-1002")
        assert member is not None

        coverage = session.get(Coverage, "M-1002")
        assert coverage is not None
        assert coverage.effective_date > today


def test_seed_creates_member_demonstrating_ineligible(tmp_path):
    today = datetime.date.today()

    with _seed_and_open_session(tmp_path) as session:
        member = session.get(Member, "M-1003")
        assert member is not None

        coverage = session.get(Coverage, "M-1003")
        assert coverage is not None
        assert coverage.termination_date is not None
        assert coverage.termination_date < today


def test_seed_includes_member_with_null_termination_date(tmp_path):
    with _seed_and_open_session(tmp_path) as session:
        open_ended = session.scalars(
            select(Coverage).where(Coverage.termination_date.is_(None))
        ).all()
        assert len(open_ended) >= 1


def test_seed_never_includes_reserved_not_found_member(tmp_path):
    with _seed_and_open_session(tmp_path) as session:
        assert session.get(Member, RESERVED_NOT_FOUND_MEMBER_ID) is None
        assert RESERVED_NOT_FOUND_MEMBER_ID == "M-9999"


def test_seed_member_ids_follow_expected_format(tmp_path):
    with _seed_and_open_session(tmp_path) as session:
        members = session.scalars(select(Member)).all()
        assert members, "expected seed data to include members"
        for member in members:
            prefix, _, digits = member.member_id.partition("-")
            assert prefix == "M"
            assert digits.isdigit()
            assert len(digits) == 4


def test_seeding_twice_is_idempotent(tmp_path):
    db_path = tmp_path / "eligibility.db"

    seed(db_path=db_path)
    seed(db_path=db_path)

    engine = make_engine(db_path)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        members = session.scalars(select(Member)).all()
        member_ids = [m.member_id for m in members]

        # No duplicate rows -- same member should not appear twice, and the
        # set of members should match a single seed run.
        assert len(member_ids) == len(set(member_ids))
        assert sorted(member_ids) == ["M-1001", "M-1002", "M-1003"]

        coverages = session.scalars(select(Coverage)).all()
        assert len(coverages) == len(members)
