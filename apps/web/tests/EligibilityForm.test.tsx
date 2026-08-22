import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import EligibilityForm, {
  getTodayIsoDate,
} from "../src/components/EligibilityForm";

const API_URL = "http://api.test";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  process.env.NEXT_PUBLIC_API_URL = API_URL;
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("EligibilityForm", () => {
  it("defaults the Check Coverage On date field to today's date", () => {
    render(<EligibilityForm />);

    const dateInput = screen.getByLabelText(
      "Check Coverage On",
    ) as HTMLInputElement;

    expect(dateInput.value).toBe(getTodayIsoDate());
  });

  it("updates the member ID field's value as the user types", () => {
    render(<EligibilityForm />);

    const memberIdInput = screen.getByLabelText(
      "Member ID",
    ) as HTMLInputElement;

    fireEvent.change(memberIdInput, { target: { value: "M12345" } });

    expect(memberIdInput.value).toBe("M12345");
  });

  it("disables the submit button when member ID is empty, and enables it once text is entered", () => {
    render(<EligibilityForm />);

    const memberIdInput = screen.getByLabelText(
      "Member ID",
    ) as HTMLInputElement;
    const submitButton = screen.getByRole("button", {
      name: "Check Eligibility",
    }) as HTMLButtonElement;

    expect(submitButton.disabled).toBe(true);

    fireEvent.change(memberIdInput, { target: { value: "M12345" } });

    expect(submitButton.disabled).toBe(false);
  });

  it("calls the eligibility API with the form's values on submit, instead of the old stub", async () => {
    const mockFetch = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        memberId: "M12345",
        memberName: "Jane Doe",
        planName: "Gold Plan",
        coverageEffectiveDate: "2024-01-01",
        coverageTerminationDate: null,
        checkCoverageOnDate: "2026-08-22",
        eligibilityStatus: "ELIGIBLE",
        eligibilityReason: "Coverage is active on 2026-08-22.",
      }),
    );
    vi.stubGlobal("fetch", mockFetch);

    render(<EligibilityForm />);

    const memberIdInput = screen.getByLabelText(
      "Member ID",
    ) as HTMLInputElement;
    const dateInput = screen.getByLabelText(
      "Check Coverage On",
    ) as HTMLInputElement;
    const submitButton = screen.getByRole("button", {
      name: "Check Eligibility",
    });

    fireEvent.change(memberIdInput, { target: { value: "M12345" } });
    fireEvent.change(dateInput, { target: { value: "2026-08-22" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toBe(
      `${API_URL}/api/v1/eligibility?memberId=M12345&checkDate=2026-08-22`,
    );
  });
});
