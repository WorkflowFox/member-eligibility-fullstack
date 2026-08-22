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
 * Result panel for a successful (200) eligibility lookup, per
 * `_docs/outdated/plan.md` §6 (fields to show) and §8 ("start another
 * inquiry"). Rendering for the `MEMBER_NOT_FOUND` outcome (also a 200, per
 * `_docs/outdated/architecture.md` §5) is deferred to issue #13 alongside
 * the other non-success states.
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

  const isSubmitDisabled = memberId.trim().length === 0;

  function handleMemberIdChange(event: ChangeEvent<HTMLInputElement>) {
    setMemberId(event.target.value);
  }

  function handleCheckDateChange(event: ChangeEvent<HTMLInputElement>) {
    setCheckDate(event.target.value);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const outcome = await getEligibility(memberId, checkDate);
    setResult(outcome);
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
    </>
  );
}
