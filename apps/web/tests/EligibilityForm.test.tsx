import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import EligibilityForm, {
  getTodayIsoDate,
} from "../src/components/EligibilityForm";

afterEach(() => {
  cleanup();
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
});
