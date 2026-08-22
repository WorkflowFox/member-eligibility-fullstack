"use client";

import { useState, type ChangeEvent, type FormEvent } from "react";

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
 * Stubbed submit handler. #11 will replace this with a real call to the
 * eligibility API; for now it intentionally does nothing with the values.
 */
function submitEligibilityInquiry(memberId: string, checkDate: string): void {
  void memberId;
  void checkDate;
}

export default function EligibilityForm() {
  const [memberId, setMemberId] = useState("");
  const [checkDate, setCheckDate] = useState(getTodayIsoDate);

  const isSubmitDisabled = memberId.trim().length === 0;

  function handleMemberIdChange(event: ChangeEvent<HTMLInputElement>) {
    setMemberId(event.target.value);
  }

  function handleCheckDateChange(event: ChangeEvent<HTMLInputElement>) {
    setCheckDate(event.target.value);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    submitEligibilityInquiry(memberId, checkDate);
  }

  return (
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
  );
}
