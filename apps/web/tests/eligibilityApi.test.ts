import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { getEligibility } from "../src/lib/eligibilityApi";

const API_URL = "http://api.test";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("getEligibility", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_URL = API_URL;
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("builds the query string and calls the endpoint via fetch", async () => {
    const mockFetch = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        memberId: "M-1001",
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

    await getEligibility("M-1001", "2026-08-22");

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toBe(
      `${API_URL}/api/v1/eligibility?memberId=M-1001&checkDate=2026-08-22`,
    );
  });

  it("returns a success result with the parsed body on HTTP 200", async () => {
    const responseBody = {
      memberId: "M-1001",
      memberName: "Jane Doe",
      planName: "Gold Plan",
      coverageEffectiveDate: "2024-01-01",
      coverageTerminationDate: null,
      checkCoverageOnDate: "2026-08-22",
      eligibilityStatus: "ELIGIBLE",
      eligibilityReason: "Coverage is active on 2026-08-22.",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(200, responseBody)),
    );

    const result = await getEligibility("M-1001", "2026-08-22");

    expect(result.type).toBe("success");
    if (result.type === "success") {
      expect(result.data).toEqual(responseBody);
    }
  });

  it("returns a validationError result, distinct from success, on HTTP 422", async () => {
    const detail = [
      {
        type: "string_too_short",
        loc: ["query", "memberId"],
        msg: "String should have at least 1 character",
      },
    ];
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(422, { detail })),
    );

    const result = await getEligibility("", "2026-08-22");

    expect(result.type).toBe("validationError");
    expect(result.type).not.toBe("success");
    if (result.type === "validationError") {
      expect(result.detail).toEqual(detail);
    }
  });

  it("returns an unavailable result, distinct from the others, on HTTP 500", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(500, {
          detail: "An unexpected error occurred. Please try again.",
        }),
      ),
    );

    const result = await getEligibility("M-1001", "2026-08-22");

    expect(result.type).toBe("unavailable");
    expect(result.type).not.toBe("success");
    expect(result.type).not.toBe("validationError");
    if (result.type === "unavailable") {
      expect(result.detail).toBe(
        "An unexpected error occurred. Please try again.",
      );
    }
  });

  it("returns an unavailable result when fetch itself throws (network failure)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    );

    const result = await getEligibility("M-1001", "2026-08-22");

    expect(result.type).toBe("unavailable");
    if (result.type === "unavailable") {
      expect(typeof result.detail).toBe("string");
    }
  });
});
