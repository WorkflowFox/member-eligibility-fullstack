"""Pure eligibility decision logic.

Implements the eligibility rule from `_docs/outdated/plan.md` §7 (and the
open-ended-coverage clarification in §10) as a pure function with no I/O.

Looking up a member's coverage dates from the database is out of scope here
(see #5), as is wiring this function into the REST endpoint (see #6). The
`MEMBER_NOT_FOUND` outcome from plan.md §7 is a lookup-layer concern and is
never returned by this function.

Boundary rules (see issue #4 grooming notes):
    - The check date is compared against the coverage's active window.
    - `NOT_YET_ELIGIBLE`: check date is strictly before the effective date.
    - `ELIGIBLE`: check date is on/after the effective date and, when a
      termination date exists, on/before the termination date (i.e. the
      effective date and termination date are both inside the active
      window, not the first/last excluded day).
    - `INELIGIBLE`: check date is strictly after the termination date.
    - A `None` termination date means coverage is open-ended: any check
      date on or after the effective date is `ELIGIBLE`.
"""

import datetime
from typing import Final, Literal

EligibilityStatus = Literal["ELIGIBLE", "NOT_YET_ELIGIBLE", "INELIGIBLE"]

ELIGIBLE: Final[EligibilityStatus] = "ELIGIBLE"
NOT_YET_ELIGIBLE: Final[EligibilityStatus] = "NOT_YET_ELIGIBLE"
INELIGIBLE: Final[EligibilityStatus] = "INELIGIBLE"


def check_eligibility(
    effective_date: datetime.date,
    termination_date: datetime.date | None,
    check_date: datetime.date,
) -> EligibilityStatus:
    """Determine eligibility for a single coverage segment.

    Pure function: no database, file, or network access. Inputs and output
    are plain `date` values (or `EligibilityStatus` for the output), so it
    is importable and testable without fixtures or mocks.

    Args:
        effective_date: The date coverage became active.
        termination_date: The date coverage ended, or `None` if coverage is
            open-ended (still active).
        check_date: The "check coverage on" date to evaluate.

    Returns:
        `NOT_YET_ELIGIBLE` if `check_date` is before `effective_date`;
        `INELIGIBLE` if `termination_date` is set and `check_date` is after
        it; `ELIGIBLE` otherwise.
    """
    if check_date < effective_date:
        return NOT_YET_ELIGIBLE

    if termination_date is not None and check_date > termination_date:
        return INELIGIBLE

    return ELIGIBLE
