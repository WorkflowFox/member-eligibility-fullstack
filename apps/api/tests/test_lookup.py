from db import make_engine, make_session_factory
from lookup import MemberCoverage, get_member_coverage
from models import Coverage, Member, Plan
from seed import RESERVED_NOT_FOUND_MEMBER_ID, seed


def _seed_and_open_session(tmp_path):
    db_path = tmp_path / "eligibility.db"
    seed(db_path=db_path)

    engine = make_engine(db_path)
    session_factory = make_session_factory(engine)
    return session_factory()


def test_get_member_coverage_returns_details_for_seeded_member(tmp_path):
    with _seed_and_open_session(tmp_path) as session:
        expected_member = session.get(Member, "M-1001")
        expected_coverage = session.get(Coverage, "M-1001")
        expected_plan = session.get(Plan, expected_coverage.plan_id)

        result = get_member_coverage(session, "M-1001")

    assert result == MemberCoverage(
        member_id="M-1001",
        name=expected_member.name,
        plan_name=expected_plan.name,
        effective_date=expected_coverage.effective_date,
        termination_date=expected_coverage.termination_date,
    )


def test_get_member_coverage_returns_none_for_reserved_not_found_id(tmp_path):
    with _seed_and_open_session(tmp_path) as session:
        result = get_member_coverage(session, RESERVED_NOT_FOUND_MEMBER_ID)

    assert result is None
    assert RESERVED_NOT_FOUND_MEMBER_ID == "M-9999"


def test_get_member_coverage_does_not_raise_for_unknown_id(tmp_path):
    with _seed_and_open_session(tmp_path) as session:
        # No unhandled exception -- a clearly distinguishable None instead.
        result = get_member_coverage(session, "definitely-not-a-real-id")

    assert result is None


def test_get_member_coverage_lookup_is_exact_match_only(tmp_path):
    with _seed_and_open_session(tmp_path) as session:
        assert get_member_coverage(session, "m-1001") is None  # case-sensitive
        assert get_member_coverage(session, "M-100") is None  # no prefix match
        assert get_member_coverage(session, "M-10011") is None  # no substring match
        assert get_member_coverage(session, " M-1001") is None  # no fuzzy/trim match
