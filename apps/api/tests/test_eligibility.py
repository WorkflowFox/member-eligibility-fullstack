import datetime

from eligibility import ELIGIBLE, INELIGIBLE, NOT_YET_ELIGIBLE, check_eligibility

EFFECTIVE = datetime.date(2024, 1, 1)
TERMINATION = datetime.date(2024, 12, 31)


def test_before_effective_date_is_not_yet_eligible():
    check_date = EFFECTIVE - datetime.timedelta(days=1)

    result = check_eligibility(EFFECTIVE, TERMINATION, check_date)

    assert result == NOT_YET_ELIGIBLE


def test_on_effective_date_is_eligible():
    result = check_eligibility(EFFECTIVE, TERMINATION, EFFECTIVE)

    assert result == ELIGIBLE


def test_mid_coverage_is_eligible():
    check_date = datetime.date(2024, 6, 15)

    result = check_eligibility(EFFECTIVE, TERMINATION, check_date)

    assert result == ELIGIBLE


def test_on_termination_date_is_eligible():
    result = check_eligibility(EFFECTIVE, TERMINATION, TERMINATION)

    assert result == ELIGIBLE


def test_day_after_termination_date_is_ineligible():
    check_date = TERMINATION + datetime.timedelta(days=1)

    result = check_eligibility(EFFECTIVE, TERMINATION, check_date)

    assert result == INELIGIBLE


def test_no_termination_date_is_eligible_on_or_after_effective_date():
    far_future = EFFECTIVE + datetime.timedelta(days=10_000)

    assert check_eligibility(EFFECTIVE, None, EFFECTIVE) == ELIGIBLE
    assert check_eligibility(EFFECTIVE, None, far_future) == ELIGIBLE


def test_no_termination_date_before_effective_date_is_not_yet_eligible():
    check_date = EFFECTIVE - datetime.timedelta(days=1)

    result = check_eligibility(EFFECTIVE, None, check_date)

    assert result == NOT_YET_ELIGIBLE


def test_never_returns_member_not_found():
    possible_results = {
        check_eligibility(EFFECTIVE, TERMINATION, EFFECTIVE - datetime.timedelta(days=1)),
        check_eligibility(EFFECTIVE, TERMINATION, EFFECTIVE),
        check_eligibility(EFFECTIVE, TERMINATION, TERMINATION),
        check_eligibility(EFFECTIVE, TERMINATION, TERMINATION + datetime.timedelta(days=1)),
        check_eligibility(EFFECTIVE, None, EFFECTIVE),
    }

    assert "MEMBER_NOT_FOUND" not in possible_results
    assert possible_results <= {ELIGIBLE, NOT_YET_ELIGIBLE, INELIGIBLE}
