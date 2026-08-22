"use client";

import { useState, type ChangeEvent, type FormEvent } from "react";

import {
  getEligibility,
  type EligibilityResponse,
  type EligibilityResult,
  type EligibilityStatus,
} from "../lib/eligibilityApi";

/**
 * Today's date in the browser's local timezone, formatted as the ISO
 * YYYY-MM-DD date the API's `checkDate` param expects
 * (see `_docs/outdated/architecture.md` §5).
 */
export function getTodayIsoDate(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/**
 * Human-readable text label for each eligibility status, per plan.md §6/§7.
 * Always shown as text (never color alone) so the outcome is distinguishable
 * at a glance -- see the accessibility requirement in issue #19.
 */
const STATUS_LABELS: Record<EligibilityStatus, string> = {
  ELIGIBLE: "Eligible",
  NOT_YET_ELIGIBLE: "Not Yet Eligible",
  INELIGIBLE: "Ineligible",
  MEMBER_NOT_FOUND: "Member Not Found",
};

const FALLBACK_VALUE = "Not available";
const NO_TERMINATION_DATE_LABEL = "No termination date on file";

/**
 * Fixed message copy for the non-success states, per issue #13's
 * acceptance criteria (a PM decision -- wording is not left ambiguous).
 */
const MEMBER_NOT_FOUND_MESSAGE =
  "We couldn't find a member with that ID. Double-check the member ID and try again.";
const VALIDATION_ERROR_FALLBACK_MESSAGE =
  "Please check the member ID and date and try again.";
const UNAVAILABLE_MESSAGE =
  "The service is temporarily unavailable. Please try again.";

/**
 * Extracts a human-readable message from a `validationError` result's
 * `detail` (see `eligibilityApi.ts`): either a plain string, or FastAPI's
 * default Pydantic validation shape (a list of `{ msg: string, ... }`
 * objects, per issue #7). Falls back to a generic message when `detail`
 * doesn't match either shape, since #7's `msg` text is already the
 * human-readable message the backend produced for display -- not raw
 * internal error text.
 */
function extractValidationMessage(detail: unknown): string {
  if (typeof detail === "string" && detail.trim().length > 0) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) =>
        item !== null &&
        typeof item === "object" &&
        "msg" in item &&
        typeof (item as { msg: unknown }).msg === "string"
          ? (item as { msg: string }).msg
          : null,
      )
      .filter((msg): msg is string => msg !== null);

    if (messages.length > 0) {
      return messages.join(" ");
    }
  }

  return VALIDATION_ERROR_FALLBACK_MESSAGE;
}

/**
 * Rendered in place of the result panel for the `MEMBER_NOT_FOUND` business
 * outcome (a `200` response, per `_docs/outdated/architecture.md` §5) --
 * distinct from `EligibilitySuccessPanel`'s `<dl>` layout so the outcome
 * reads as visually distinct at a glance.
 */
function MemberNotFoundPanel() {
  return (
    <section aria-label="Member not found">
      <p>{MEMBER_NOT_FOUND_MESSAGE}</p>
    </section>
  );
}

/**
 * Rendered for a `422` validation-error result. Uses `role="alert"` (unlike
 * `MemberNotFoundPanel`, which reports a business outcome rather than an
 * error) so it's visually and semantically distinct from both the success
 * panel and the not-found panel.
 */
function ValidationErrorPanel({ detail }: { detail: unknown }) {
  return (
    <section aria-label="Validation error" role="alert">
      <p>{extractValidationMessage(detail)}</p>
    </section>
  );
}

/**
 * Rendered for a `500`/network-failure result. Ignores the result's raw
 * `detail` text in favor of the fixed message issue #13 specifies, and
 * offers a "Retry" action that resubmits the same inquiry.
 */
function UnavailablePanel({ onRetry }: { onRetry: () => void }) {
  return (
    <section aria-label="Service unavailable" role="alert">
      <p>{UNAVAILABLE_MESSAGE}</p>
      <button type="button" onClick={onRetry}>
        Retry
      </button>
    </section>
  );
}

/**
 * Result panel for a successful (200) eligibility lookup with a non-
 * `MEMBER_NOT_FOUND` status, per `_docs/outdated/plan.md` §6 (fields to
 * show) and §8 ("start another inquiry"). The `MEMBER_NOT_FOUND` outcome
 * (also a 200, per `_docs/outdated/architecture.md` §5) renders via
 * `MemberNotFoundPanel` instead, per issue #13.
 */
function EligibilitySuccessPanel({
  data,
  onStartAnotherInquiry,
}: {
  data: EligibilityResponse;
  onStartAnotherInquiry: () => void;
}) {
  return (
    <section aria-label="Eligibility result">
      <dl>
        <dt>Member ID</dt>
        <dd>{data.memberId}</dd>

        <dt>Member Name</dt>
        <dd>{data.memberName ?? FALLBACK_VALUE}</dd>

        <dt>Plan Name</dt>
        <dd>{data.planName ?? FALLBACK_VALUE}</dd>

        <dt>Coverage Effective Date</dt>
        <dd>{data.coverageEffectiveDate ?? FALLBACK_VALUE}</dd>

        <dt>Coverage Termination Date</dt>
        <dd>{data.coverageTerminationDate ?? NO_TERMINATION_DATE_LABEL}</dd>

        <dt>Check Coverage On</dt>
        <dd>{data.checkCoverageOnDate}</dd>

        <dt>Eligibility Status</dt>
        <dd>{STATUS_LABELS[data.eligibilityStatus]}</dd>

        <dt>Eligibility Reason</dt>
        <dd>{data.eligibilityReason}</dd>
      </dl>
      <button type="button" onClick={onStartAnotherInquiry}>
        Start another inquiry
      </button>
    </section>
  );
}

export default function EligibilityForm() {
  const [memberId, setMemberId] = useState("");
  const [checkDate, setCheckDate] = useState(getTodayIsoDate);
  const [result, setResult] = useState<EligibilityResult | null>(null);
  /**
   * The member ID and check date used for the most recent lookup, kept
   * separate from the (possibly since-edited) form fields so "Retry" always
   * resubmits the exact same inquiry that produced the current result, per
   * issue #13.
   */
  const [lastSubmitted, setLastSubmitted] = useState<{
    memberId: string;
    checkDate: string;
  } | null>(null);

  const isSubmitDisabled = memberId.trim().length === 0;

  function handleMemberIdChange(event: ChangeEvent<HTMLInputElement>) {
    setMemberId(event.target.value);
  }

  function handleCheckDateChange(event: ChangeEvent<HTMLInputElement>) {
    setCheckDate(event.target.value);
  }

  async function runLookup(memberIdToSubmit: string, checkDateToSubmit: string) {
    setLastSubmitted({
      memberId: memberIdToSubmit,
      checkDate: checkDateToSubmit,
    });
    const outcome = await getEligibility(memberIdToSubmit, checkDateToSubmit);
    setResult(outcome);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runLookup(memberId, checkDate);
  }

  async function handleRetry() {
    if (!lastSubmitted) {
      return;
    }
    await runLookup(lastSubmitted.memberId, lastSubmitted.checkDate);
  }

  function handleStartAnotherInquiry() {
    setResult(null);
    setMemberId("");
    setCheckDate(getTodayIsoDate());
  }

  return (
    <>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="memberId">Member ID</label>
          <input
            id="memberId"
            name="memberId"
            type="text"
            value={memberId}
            onChange={handleMemberIdChange}
          />
        </div>
        <div>
          <label htmlFor="checkDate">Check Coverage On</label>
          <input
            id="checkDate"
            name="checkDate"
            type="date"
            value={checkDate}
            onChange={handleCheckDateChange}
          />
        </div>
        <button type="submit" disabled={isSubmitDisabled}>
          Check Eligibility
        </button>
      </form>
      {result?.type === "success" &&
        result.data.eligibilityStatus !== "MEMBER_NOT_FOUND" && (
          <EligibilitySuccessPanel
            data={result.data}
            onStartAnotherInquiry={handleStartAnotherInquiry}
          />
        )}
      {result?.type === "success" &&
        result.data.eligibilityStatus === "MEMBER_NOT_FOUND" && (
          <MemberNotFoundPanel />
        )}
      {result?.type === "validationError" && (
        <ValidationErrorPanel detail={result.detail} />
      )}
      {result?.type === "unavailable" && (
        <UnavailablePanel onRetry={handleRetry} />
      )}
    </>
  );
}
