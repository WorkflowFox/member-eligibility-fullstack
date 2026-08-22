/**
 * Typed client for `GET /api/v1/eligibility` (see
 * `_docs/outdated/architecture.md` §5 for the endpoint's request/response
 * contract and status-code mapping).
 *
 * The backend base URL comes from the `NEXT_PUBLIC_API_URL` build-time
 * environment variable rather than being hardcoded, because this call runs
 * in the browser (architecture.md §3: "the browser calls the FastAPI
 * service directly") and Next.js only exposes `NEXT_PUBLIC_`-prefixed
 * variables to client-side code. That also means the value is inlined at
 * build time, not read at container runtime.
 */

/** One of the four business eligibility outcomes the backend can report. */
export type EligibilityStatus =
  | "ELIGIBLE"
  | "NOT_YET_ELIGIBLE"
  | "INELIGIBLE"
  | "MEMBER_NOT_FOUND";

/**
 * Successful (HTTP 200) response body shape, per
 * `_docs/outdated/architecture.md` §5. All four eligibility outcomes,
 * including `MEMBER_NOT_FOUND`, are `200`s -- they're business results,
 * not errors.
 */
export interface EligibilityResponse {
  memberId: string;
  memberName: string | null;
  planName: string | null;
  coverageEffectiveDate: string | null;
  coverageTerminationDate: string | null;
  checkCoverageOnDate: string;
  eligibilityStatus: EligibilityStatus;
  eligibilityReason: string;
}

/** HTTP 200: the lookup/eligibility decision succeeded. */
export interface EligibilitySuccessResult {
  type: "success";
  data: EligibilityResponse;
}

/**
 * HTTP 422: the request itself was invalid (blank member ID or a malformed
 * `checkDate`). `detail` carries FastAPI/Pydantic's default validation
 * error body (a list of per-field error objects) verbatim.
 */
export interface EligibilityValidationErrorResult {
  type: "validationError";
  detail: unknown;
}

/**
 * HTTP 500, or the `fetch` call itself failing (network error). Both are
 * "the backend is unavailable right now" from the frontend's point of
 * view, and are represented the same way here so callers have a single
 * case to handle for "try again later".
 */
export interface EligibilityUnavailableResult {
  type: "unavailable";
  detail: string;
}

/**
 * Discriminated union of every outcome `getEligibility` can return.
 * Callers branch on `result.type`, never on error message strings.
 */
export type EligibilityResult =
  | EligibilitySuccessResult
  | EligibilityValidationErrorResult
  | EligibilityUnavailableResult;

const DEFAULT_UNAVAILABLE_MESSAGE =
  "An unexpected error occurred. Please try again.";

/**
 * Look up a member's eligibility as of `checkDate` by calling
 * `GET /api/v1/eligibility` on the backend.
 *
 * Never throws: every failure mode (validation error, server error,
 * network failure) is represented as a typed member of the returned
 * discriminated union instead.
 */
export async function getEligibility(
  memberId: string,
  checkDate: string,
): Promise<EligibilityResult> {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
  const query = new URLSearchParams({ memberId, checkDate }).toString();
  const url = `${baseUrl}/api/v1/eligibility?${query}`;

  let response: Response;
  try {
    response = await fetch(url);
  } catch {
    return { type: "unavailable", detail: DEFAULT_UNAVAILABLE_MESSAGE };
  }

  if (response.status === 200) {
    const data = (await response.json()) as EligibilityResponse;
    return { type: "success", data };
  }

  if (response.status === 422) {
    const detail = await readDetail(response);
    return { type: "validationError", detail: detail ?? null };
  }

  const detail = await readDetail(response);
  return {
    type: "unavailable",
    detail: typeof detail === "string" ? detail : DEFAULT_UNAVAILABLE_MESSAGE,
  };
}

/** Best-effort read of a JSON response body's `detail` field. */
async function readDetail(response: Response): Promise<unknown> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    return body?.detail;
  } catch {
    return undefined;
  }
}
