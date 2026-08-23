# Cloud-Native Member Eligibility
## Product and Technical Specification — MVP v1.0

**Document type:** Combined Product and Technical Specification  
**Status:** Draft for review  
**Product source:** [`_docs/outdated/plan.md`](../_docs/outdated/plan.md), v0.1  
**Technical source:** [`_docs/outdated/architecture.md`](../_docs/outdated/architecture.md), v0.2, Approved  
**Implementation trace:** [`_docs/outdated/tasks.md`](../_docs/outdated/tasks.md), v0.2, Approved

This specification defines the deliberately narrow MVP and provides sufficient product, UX, API, and architecture detail to guide implementation and a high-fidelity frontend prototype. Product behavior follows the product plan; technical decisions follow the approved architecture.

Source note: the referenced source documents currently exist under `_docs/outdated/`, not directly under `_docs/`. The plan is marked “Draft for approval,” while the derived architecture and backlog are marked “Approved.” This specification uses the plan as the requested product source without changing its product behavior.

Architecture consistency note: architecture §7 first says both workflows run on push/pull request to `main`, but its detailed workflow descriptions and the approved backlog specify CI on pull requests and CD after merge to `main`. This specification preserves the detailed behavior and records the inconsistency rather than silently combining the two statements.

## 1. Product Summary

Cloud-Native Member Eligibility is a small, read-only enterprise healthcare application for checking whether a synthetic member has active coverage on a selected date.

A service representative enters a member ID and a **Check Coverage On** date. The application returns one of four deterministic business outcomes, the relevant coverage details, and a plain-language reason. The showcase demonstrates production-oriented, specification-driven enterprise application engineering without expanding into a broader healthcare administration system.

## 2. Problem / Context

Eligibility information is often distributed across systems or interpreted through manual steps. A service representative may take too long to answer a basic coverage question, and inconsistent interpretation of effective and termination dates can produce errors.

The MVP provides one clear, repeatable workflow using synthetic data. It is intended for a short public demonstration and as a production-quality reference implementation, not for processing real member data.

## 3. Goals

1. Let a service representative complete a date-specific eligibility inquiry without training.
2. Return a consistent decision using explicit, testable date rules.
3. Display the decision, supporting coverage details, and a plain-language reason in an easy-to-scan format.
4. Demonstrate every supported business outcome with synthetic data.
5. Handle invalid input, unknown members, network failures, and backend failures without exposing technical details.
6. Demonstrate a minimal cloud-native architecture with independently deployable web and API services.
7. Keep the showcase inexpensive to operate, read-only, and deliberately narrow.

## 4. Non-Goals

The MVP is not a system of record and does not update member or coverage data. It does not provide member search, workflow history, broader healthcare administration, enterprise identity, analytics, or AI-assisted product functionality. The complete exclusion list is in §19.

## 5. Primary User

**Service Representative**

The representative receives an eligibility question from a member or provider and needs a fast, consistent answer. The representative is expected to know the exact member ID; discovering a member by name or other attributes is not supported.

## 6. Core User Flow

```text
Member ID + Check Coverage On date
        ↓
Check Eligibility
        ↓
Eligibility result and reason
        ↓
Start Another Inquiry
```

1. The representative opens the application.
2. The representative enters a member ID.
3. **Check Coverage On** defaults to the current date and may be changed.
4. The representative selects **Check Eligibility**.
5. The application validates the input and sends the eligibility inquiry.
6. The application displays a business outcome and reason, or a friendly validation/technical error.
7. The representative may select **Start Another Inquiry** to return to a clean inquiry state.

## 7. Functional Requirements

### 7.1 Eligibility inquiry

- The application shall expose one eligibility inquiry form on a single page.
- The form shall accept exactly two business inputs: member ID and **Check Coverage On** date.
- The application shall perform a read-only inquiry; no user action shall create, update, or delete member, plan, or coverage data.
- Submitting valid input shall call the FastAPI eligibility endpoint directly from the browser.
- The same database state and input values shall always return the same business outcome.

### 7.2 Input fields

| Field | Control | Required | Behavior |
|---|---|---:|---|
| Member ID | Text input | Yes | Accepts the exact synthetic member identifier. Blank input is invalid. No partial-name or fuzzy search is performed. |
| Check Coverage On | Date input | Yes | Defaults to the current date, may be changed, and is sent to the API as an ISO `YYYY-MM-DD` date. |

No additional healthcare, member, provider, plan, or contact fields shall be added.

### 7.3 Eligibility outcomes

The application shall support exactly four business outcomes:

| Outcome | Meaning |
|---|---|
| `ELIGIBLE` | Coverage is active on the selected date. |
| `NOT_YET_ELIGIBLE` | The selected date is before coverage becomes effective. |
| `INELIGIBLE` | The selected date is after coverage terminates. |
| `MEMBER_NOT_FOUND` | No member matches the submitted member ID. |

All four are business results returned with HTTP `200`. `MEMBER_NOT_FOUND` shall not be represented as HTTP `404`.

### 7.4 Result display

For a found member, the result panel shall display:

| Field | Display requirement |
|---|---|
| Eligibility status | Highest-priority element, shown as readable text and a status badge; never communicated by color alone. |
| Eligibility reason | Plain-language sentence immediately beneath or beside the status. |
| Member ID | Labeled value. |
| Member name | Labeled value. |
| Plan name | Labeled value. |
| Coverage effective date | Labeled, human-readable date. |
| Coverage termination date | Labeled, human-readable date; show “No termination date” when the API value is `null`. |
| Check Coverage On date | Labeled, human-readable date. |

The UI may format dates for readability, but it shall not change their calendar values. It shall not display raw JSON, internal codes without readable labels, stack traces, database details, or infrastructure details.

### 7.5 Start another inquiry

- Every completed business-result state shall provide a clearly labeled **Start Another Inquiry** action.
- The action shall clear the previous result and any result-level message and return the page to the inquiry form.
- The form shall again present the current-date default for **Check Coverage On**.

### 7.6 Validation

- Both fields shall have persistent visible labels.
- The frontend shall prevent submission when the member ID is blank or the date is missing/invalid and shall show a concise field-level message.
- The API remains authoritative and shall return HTTP `422` for a missing/blank member ID or a missing/malformed date.
- A `422` response shall be translated into a friendly, non-technical message near the relevant form field or in a form-level validation summary.
- The raw FastAPI/Pydantic validation payload shall not be shown directly to the user.
- No member ID pattern, length rule, case conversion, or fuzzy matching is required beyond the existing non-blank exact-match behavior.

### 7.7 Loading behavior

- After a valid submission, the primary button shall enter a visible loading state such as **Checking eligibility…**.
- Duplicate submissions shall be prevented while the request is pending.
- Existing form values shall remain visible while the request is pending.
- Any previous result or technical-error state shall be cleared when a new request starts.
- The loading state shall end on a business response, validation response, network failure, or technical failure.
- Motion shall be minimal; a simple progress indicator is sufficient and shall respect reduced-motion preferences.

### 7.8 Member-not-found behavior

- `MEMBER_NOT_FOUND` shall be displayed as a completed business outcome, not as a broken-page or system-error state.
- The result shall show the submitted member ID, selected check date, status, and plain-language reason.
- Member name, plan, and coverage dates are `null` in the API response and shall not be rendered as empty or misleading data rows.
- The result shall offer **Start Another Inquiry**.

### 7.9 Technical/system-error behavior

- HTTP `500`, an unreachable API, a timeout, or another network failure shall produce one generic unavailable-service state.
- The message shall be non-technical, for example: “The eligibility service is temporarily unavailable. Please try again.”
- The state shall provide a **Try Again** action that repeats the inquiry using the unchanged form values.
- Technical details, exception messages, stack traces, SQL text, file paths, service names, and internal identifiers shall not be exposed in the UI or API error body.

## 8. UX Requirements

### 8.1 Experience principles

The application shall feel like a modern internal enterprise healthcare tool: professional, minimal, calm, trustworthy, accessible, and easy to scan. It is primarily desktop-oriented.

### 8.2 Page composition

- Use one page with a restrained application header and a centered main workspace.
- The header shall identify the product as **Member Eligibility** or **Cloud-Native Member Eligibility**. It shall not resemble a marketing hero.
- The inquiry form shall be the initial visual focus.
- On common desktop widths, member ID and date may share one row; the primary action shall be visually obvious.
- The result shall appear in the same workspace below the form or replace its primary content without navigating to a dashboard or a second application area.
- Use clear grouping, generous but restrained spacing, short labels, and a strong status hierarchy.
- Do not add navigation items that imply unsupported features.

### 8.3 Visual system

Use the approved WorkflowFox-inspired palette:

| Role | Color |
|---|---|
| Primary text / application header | Deep Navy `#0F172A` |
| Primary action / focus accents | Enterprise Blue `#2563EB` |
| Eligible success accent | Emerald `#10B981` |
| Surfaces | White and light-neutral backgrounds |

Neutral grays may be used for borders, secondary text, and inactive surfaces. Any semantic warning/error accent shall be used sparingly and must meet contrast requirements. Status text and supporting language shall carry meaning independently of color.

Avoid marketing-site styling, excessive gradients, glassmorphism, decorative animation, illustrations, dashboards, sidebars, AI imagery, oversized hero text, or decorative data visualizations.

### 8.4 Prototype/demo data

All prototype and implementation data shall be synthetic. The existing repository seed identifiers provide deterministic demonstrations:

| Member ID | Default-date demonstration |
|---|---|
| `M-1001` | `ELIGIBLE` |
| `M-1002` | `NOT_YET_ELIGIBLE` |
| `M-1003` | `INELIGIBLE` |
| `M-9999` | `MEMBER_NOT_FOUND`; this ID is intentionally absent |

The prototype shall include reachable states for all four outcomes plus validation, loading, and unavailable-service states. Synthetic names and plan names may be displayed, but no data may represent or be derived from a real person.

## 9. Accessibility and Responsive Behavior

- Use semantic HTML landmarks, headings, form controls, buttons, and result/status regions.
- Every control shall have a programmatically associated visible label.
- The entire workflow shall be operable by keyboard with a logical focus order and visible focus indicator.
- Validation messages shall be associated with their fields; invalid fields shall expose their invalid state programmatically.
- New results and error states shall be announced to assistive technology through an appropriate live/status region without unexpectedly moving focus.
- Status shall be expressed by text and structure, not by color alone.
- Text and interactive controls shall meet WCAG 2.1 AA contrast: at least 4.5:1 for normal text and 3:1 for large text and non-text UI indicators.
- At desktop widths of 1024 CSS pixels and above, the form and result shall remain readable without horizontal scrolling.
- At narrower widths, form fields shall stack vertically and content shall reflow without clipping or horizontal page scrolling. Mobile-specific navigation or mobile-only features are not required.
- Touch/click targets shall be at least 44 by 44 CSS pixels where practical.
- Nonessential animation shall be absent; any loading motion shall honor `prefers-reduced-motion`.

## 10. Eligibility Business Rules

The decision uses one coverage segment and three date values: coverage effective date, optional coverage termination date, and **Check Coverage On** date.

Rules are evaluated in this order:

1. If no member exactly matches the submitted member ID, return `MEMBER_NOT_FOUND`.
2. If the check date is before the effective date, return `NOT_YET_ELIGIBLE`.
3. If a termination date exists and the check date is after that date, return `INELIGIBLE`.
4. Otherwise, return `ELIGIBLE`.

Boundary behavior is inclusive:

- A check on the effective date is `ELIGIBLE`.
- A check on the termination date is `ELIGIBLE`.
- A check one day after the termination date is `INELIGIBLE`.
- A `null` termination date means coverage remains active for all dates on or after the effective date.

The rules are deterministic and shall not use AI, probabilistic scoring, recommendations, benefits interpretation, or other healthcare data.

## 11. Technical Architecture

### 11.1 Frontend

- Next.js using the App Router, React, and TypeScript.
- One page containing the inquiry form and all result/error states.
- Client-side interaction; no Next.js server-side data fetching is required for eligibility.
- A typed API client shall call the API service URL configured for the environment.
- The browser calls FastAPI directly; the Next.js service is not a backend-for-frontend or API proxy.

### 11.2 Backend

- Python and FastAPI.
- One eligibility router/endpoint plus the existing health endpoint.
- Pydantic/FastAPI query validation.
- An isolated deterministic eligibility function separate from data access and HTTP concerns.
- SQLAlchemy for member, plan, and coverage data access.
- FastAPI-generated OpenAPI is the API contract of record; interactive `/docs` remains publicly reachable for the showcase.

### 11.3 API

- REST over HTTPS.
- Direct browser-to-API communication.
- CORS restricted to the deployed frontend origin; localhost may be allowed for local development.
- No API gateway, BFF, orchestration layer, or asynchronous messaging.

### 11.4 Data

- Seeded SQLite database bundled into the API container image.
- The SQLite database is immutable/read-only at runtime.
- The schema is created from SQLAlchemy models and seeded at build time.
- There is no runtime write path and no persistence requirement across deployments.
- PostgreSQL via Cloud SQL is only a future production evolution option; it is not required for MVP.
- Alembic or other database migration tooling is not required for MVP.

### 11.5 Logical request path

```text
Browser
  ├── HTTPS → Next.js web service (application assets)
  └── HTTPS REST + CORS → FastAPI API service
                               └── read-only SQLAlchemy query → bundled SQLite
```

## 12. Data Model

The MVP uses three relational entities and at most one coverage segment per member.

### Member

| Field | Type | Constraint |
|---|---|---|
| `member_id` | string | Primary key; synthetic identifier |
| `name` | string | Required; synthetic display name |

### Plan

| Field | Type | Constraint |
|---|---|---|
| `plan_id` | string | Primary key; synthetic identifier |
| `name` | string | Required; synthetic display name |

### Coverage

| Field | Type | Constraint |
|---|---|---|
| `member_id` | string | Primary key and foreign key to Member; enforces at most one coverage segment per member |
| `plan_id` | string | Required foreign key to Plan |
| `effective_date` | date | Required |
| `termination_date` | date or null | Optional; null means open-ended coverage |

Relationships:

- A member has zero or one coverage record in the schema.
- A plan may be associated with multiple coverage records.
- A coverage record belongs to exactly one member and one plan.

The MVP seed dataset shall include only synthetic members with the coverage needed to demonstrate the three date-based outcomes. The intentionally absent ID demonstrates `MEMBER_NOT_FOUND`.

## 13. API Contract

### 13.1 Endpoint

```http
GET /api/v1/eligibility?memberId={memberId}&checkDate={ISO-date}
```

| Query parameter | Type | Required | Validation |
|---|---|---:|---|
| `memberId` | string | Yes | Must be non-blank; matched exactly. |
| `checkDate` | ISO date | Yes | Must be a valid `YYYY-MM-DD` calendar date. |

### 13.2 HTTP 200 response

```json
{
  "memberId": "M-1001",
  "memberName": "Jordan Testcase",
  "planName": "Acme Health Plan",
  "coverageEffectiveDate": "2025-01-01",
  "coverageTerminationDate": null,
  "checkCoverageOnDate": "2026-08-22",
  "eligibilityStatus": "ELIGIBLE",
  "eligibilityReason": "Coverage is active on 2026-08-22."
}
```

Response model:

| Field | Type | Nullable | Notes |
|---|---|---:|---|
| `memberId` | string | No | Echoes the submitted ID for not-found results; otherwise the matched member ID. |
| `memberName` | string | Yes | `null` for `MEMBER_NOT_FOUND`. |
| `planName` | string | Yes | `null` for `MEMBER_NOT_FOUND`. |
| `coverageEffectiveDate` | ISO date | Yes | `null` for `MEMBER_NOT_FOUND`. |
| `coverageTerminationDate` | ISO date | Yes | `null` for not-found or open-ended coverage. |
| `checkCoverageOnDate` | ISO date | No | The date evaluated. |
| `eligibilityStatus` | enum | No | One of the four defined business outcomes. |
| `eligibilityReason` | string | No | Plain-language reason suitable for display. |

### 13.3 Status behavior

| Scenario | HTTP status | Contract behavior |
|---|---:|---|
| `ELIGIBLE` | `200` | Full result model. |
| `NOT_YET_ELIGIBLE` | `200` | Full result model. |
| `INELIGIBLE` | `200` | Full result model. |
| `MEMBER_NOT_FOUND` | `200` | Result model with nullable member/plan/coverage fields set to `null`. |
| Missing/blank member ID or missing/malformed date | `422` | FastAPI validation response; frontend maps it to friendly validation text. |
| Unexpected technical failure | `500` | Generic response without internal technical detail. |

An unexpected failure response may use the stable public shape:

```json
{
  "detail": "An unexpected error occurred. Please try again."
}
```

No endpoint beyond eligibility and operational health is required by this specification.

## 14. Security and Privacy

- No authentication or authorization is included for this public showcase.
- Both Cloud Run services are publicly invokable.
- All browser/service communication in the deployed environment uses HTTPS.
- API CORS is restricted to the deployed frontend origin; local development may explicitly allow the local frontend origin.
- All people, organizations, plans, and identifiers are fictional and synthetic.
- Real PHI, PII, customer data, credentials, or production extracts shall not be included in source control, the SQLite image, prototype fixtures, screenshots, logs, or demonstrations.
- The application is read-only and provides no mutation endpoint.
- Technical error responses shall not disclose internal implementation details.
- CI/CD authentication to Google Cloud uses GitHub Actions OIDC with Workload Identity Federation; no long-lived Google Cloud service-account key is stored in GitHub.

## 15. Error Handling and Reliability

| Condition | System behavior | User behavior |
|---|---|---|
| Blank/missing member ID or invalid date | Reject before business logic; API returns `422` if called. | Show a friendly validation message and preserve entered values. |
| Unknown member | API returns `200` and `MEMBER_NOT_FOUND`. | Show a completed not-found business result and allow another inquiry. |
| Unexpected backend/database failure | API returns `500` with a generic body. | Show the unavailable-service state and **Try Again**. |
| Network failure or unreachable API | Frontend catches the failed request. | Use the same unavailable-service state and preserve values for retry. |
| Repeated submit while pending | Frontend suppresses duplicate requests. | Keep one visible loading state. |

The backend health endpoint shall remain independent of database lookup so it can indicate that the process is running. The MVP does not require queues, retries inside the API, circuit breakers, multi-region failover, or a separate resilience platform.

## 16. Logging / Observability

- Use Google Cloud Run’s built-in request logging, application logging, metrics, and service health visibility.
- Backend unexpected failures shall be logged server-side with enough context for diagnosis while the public response remains generic.
- Logs used for the showcase shall contain synthetic data only and shall not include secrets or credentials.
- The `/health` endpoint provides a simple liveness signal.
- No external observability stack, custom analytics dashboard, distributed tracing platform, audit-reporting system, or product analytics is required for MVP.

## 17. Deployment Model

- Monorepo with separate `apps/web` and `apps/api` applications.
- One Docker image per service.
- Local development may use `docker-compose.yml`; Compose is not used in Cloud Run.
- GitHub Actions CI runs linting, type checking, automated tests, and both Docker builds on pull requests to `main`.
- After merge to `main`, GitHub Actions authenticates to Google Cloud using Workload Identity Federation, builds and tags both images, pushes them to Google Artifact Registry, and deploys them with `gcloud run deploy`.
- Deploy two public Google Cloud Run services: `member-eligibility-web` and `member-eligibility-api`.
- Both services are configured to scale to zero.
- The API service includes its seeded, read-only SQLite file and has no MVP external database dependency.
- No staging environment is required; local and live demo environments are sufficient for MVP.
- The Cloud Run region remains a deferred decision.

## 18. MVP Acceptance Criteria

Each criterion is independently testable and shall be recorded as PASS or FAIL.

| ID | Acceptance criterion |
|---|---|
| AC-01 | On initial page load, exactly one eligibility inquiry form is visible with labeled Member ID and Check Coverage On controls and a **Check Eligibility** action. |
| AC-02 | On initial page load, Check Coverage On contains the current calendar date and can be changed to another valid date. |
| AC-03 | Submitting a blank member ID is prevented or produces a friendly validation message; no business result is displayed. |
| AC-04 | Calling the API without `memberId`, with an empty `memberId`, without `checkDate`, or with a malformed `checkDate` returns HTTP `422`. |
| AC-05 | A valid inquiry causes the browser to call `GET /api/v1/eligibility` with `memberId` and ISO `checkDate` query parameters directly against the API service. |
| AC-06 | While a request is pending, a visible loading state is shown and a second submit does not create a duplicate in-flight request. |
| AC-07 | For a check date before the effective date, the API returns HTTP `200` with `eligibilityStatus: NOT_YET_ELIGIBLE`. |
| AC-08 | For a check date equal to the effective date, the API returns HTTP `200` with `eligibilityStatus: ELIGIBLE`. |
| AC-09 | For a check date between effective and termination dates, inclusive, the API returns HTTP `200` with `eligibilityStatus: ELIGIBLE`. |
| AC-10 | For a check date after the termination date, the API returns HTTP `200` with `eligibilityStatus: INELIGIBLE`. |
| AC-11 | For coverage with a null termination date, any check date on or after the effective date returns HTTP `200` with `eligibilityStatus: ELIGIBLE`. |
| AC-12 | Querying the intentionally absent `M-9999` returns HTTP `200` with `eligibilityStatus: MEMBER_NOT_FOUND`, the submitted member ID and check date, and null member/plan/coverage fields. |
| AC-13 | The seed/prototype data can demonstrate `ELIGIBLE`, `NOT_YET_ELIGIBLE`, `INELIGIBLE`, and `MEMBER_NOT_FOUND` without changing application code or using real data. |
| AC-14 | A found-member result displays status, reason, member ID, member name, plan name, effective date, termination state/date, and checked date. |
| AC-15 | The not-found UI displays a business result and reason, omits empty member/plan/coverage detail rows, and does not label the condition as a technical error. |
| AC-16 | Selecting **Start Another Inquiry** clears the displayed result and returns the page to a clean inquiry form with the current-date default. |
| AC-17 | An HTTP `500` or simulated network failure displays a generic unavailable-service message and **Try Again** while preserving the submitted values. |
| AC-18 | No `422` or `500` UI state displays raw JSON, stack traces, exception text, SQL, file paths, or infrastructure details. |
| AC-19 | The entire inquiry, result review, retry, and start-another flow can be completed with a keyboard, with visible focus on the active control. |
| AC-20 | Form labels are programmatically associated with controls, validation is programmatically associated with invalid fields, and new results/errors are announced by an accessible status/live region. |
| AC-21 | Normal text meets 4.5:1 contrast; large text and non-text UI indicators meet 3:1 contrast; every status remains understandable without color. |
| AC-22 | At 1024 CSS pixels and 1440 CSS pixels wide, the page has no horizontal scrolling and the form and result remain readable and usable. |
| AC-23 | At 375 CSS pixels wide, fields stack vertically and the page has no clipped controls or horizontal page scrolling. |
| AC-24 | The delivered UI uses Deep Navy `#0F172A`, Enterprise Blue `#2563EB`, Emerald `#10B981`, and white/light-neutral surfaces without gradients, glassmorphism, dashboards, sidebars, illustrations, or AI imagery. |
| AC-25 | FastAPI exposes the endpoint in its generated OpenAPI schema and serves the interactive contract at `/docs`. |
| AC-26 | The API reads member/plan/coverage data through SQLAlchemy from the seeded SQLite database and exposes no runtime data-mutation path. |
| AC-27 | The API container starts successfully with the SQLite database bundled in the image and can serve `/health` and a seeded eligibility inquiry without an external database. |
| AC-28 | In the deployed environment, a browser request from the configured frontend origin is allowed by CORS and a request from an unconfigured origin is denied by CORS. |
| AC-29 | CI passes only when frontend/backend linting, type checks, automated tests, and both Docker image builds succeed on a pull request. |
| AC-30 | After merge to `main`, both images are present in Google Artifact Registry and the two named Cloud Run services run the deployed revisions with scale-to-zero configured. |

## 19. Explicitly Out of Scope

The MVP shall not include:

- Authentication, authorization, enterprise SSO, or multiple user roles
- Salesforce or any other enterprise-system integration
- AI functionality inside the application
- Chatbots, RAG, recommendations, or agents inside the product
- Dashboards, analytics, audit reporting, notifications, or inquiry history
- Member search by name or attributes; only exact member-ID inquiry is supported
- Member, plan, or coverage updates
- Multiple coverage segments or coordination of benefits
- Enrollment, quoting, shopping, plan comparison, or eligibility enrollment changes
- Claims, benefits, accumulators, authorizations, billing, payments, or unrelated healthcare functionality
- Real PHI, PII, customer data, or production data
- API gateway or backend-for-frontend proxy
- Kubernetes or another container orchestrator beyond Cloud Run
- Queues, event streams, or asynchronous job processing
- Terraform or other infrastructure-as-code tooling for the MVP
- Unnecessary microservices beyond the separate web and API services
- Cloud SQL/PostgreSQL as an MVP dependency
- Database migration tooling for the seeded SQLite MVP
- Multiple hosted environments or a staging environment
- A separate observability platform beyond Cloud Run’s built-in capabilities

## 20. Future Evolution / Deferred Decisions

The following are intentionally deferred and shall not be treated as MVP requirements:

- **Cloud Run region:** select the single region closest to the primary demo audience.
- **PostgreSQL evolution:** consider PostgreSQL via Cloud SQL only if persistent transactional data, larger datasets, or multi-user write workloads are introduced. SQLAlchemy is retained to reduce coupling, but migration is not part of MVP.
- **Migration tooling:** consider Alembic or equivalent only with a future persistent database transition.
- **Synthetic dataset size:** decide whether additional fictional records improve the demonstration; the MVP only needs deterministic examples of the four outcomes.
- **Repository topology:** the current monorepo remains the MVP assumption; splitting web and API repositories is not required.
- **Member without coverage:** the product plan defines `MEMBER_NOT_FOUND` as no matching member, while the architecture schema permits a member with zero coverage records and defines no fifth outcome. The MVP seed data shall avoid this undefined state. A future product decision must define whether such a record is treated as not found, ineligible, or a separate outcome before supporting it.
- **Production identity and privacy controls:** authentication, authorization, audit controls, and real-data compliance would require a separate production scope and architecture review; they are not implied by this showcase.
- **Broader healthcare capabilities:** any coverage-history, enrollment, claims, benefits, billing, or integration capability requires a separate discovery and specification phase.

No deferred item authorizes implementation beyond the MVP defined in this document.
