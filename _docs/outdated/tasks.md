# WorkflowFox Showcase 3 — Implementation Backlog

**Document:** Task Backlog
**Version:** 0.2
**Status:** Approved
**Derived from:** [plan.md](./plan.md) v0.1, [architecture.md](./architecture.md) v0.2

Each task below is scoped to be completable in one session and self-contained — it names the relevant stack, file locations, and source document section so it can be picked up without reading the other tasks.

## 1. Project scaffolding with a passing test
Goal: Stand up the monorepo skeleton so CI has something to run before any feature work begins.
Description: Create the `apps/web` and `apps/api` directories per the layout in `_docs/architecture.md` §12, each with a minimal dependency manifest (`package.json`, `pyproject.toml`/`requirements.txt`) and the minimal placeholder toolchain setup needed to run one trivial passing test in each — a Vitest/Jest test in `apps/web` and a pytest test in `apps/api`. This task establishes directory structure and tooling only, not application code; the real Next.js App Router application shell is built in task 9.

## 2. Backend: FastAPI app skeleton with a health check
Goal: Provide a running FastAPI application with a health endpoint before any business logic exists.
Description: In `apps/api`, create the FastAPI app instance and a `GET /health` endpoint returning a simple 200 status, runnable locally via `uvicorn`. Add a test asserting the endpoint returns 200 — this is the foundation the eligibility endpoint will be added to later.

## 3. Backend: data model and synthetic seed dataset
Goal: Define the Member/Plan/Coverage schema and seed it with synthetic data that can demonstrate every eligibility outcome.
Description: Using SQLAlchemy (per `_docs/architecture.md` §4.3), define Member, Plan, and Coverage tables/models matching the ER diagram there, and write a seed script that builds a SQLite database populated with synthetic records covering `ELIGIBLE`, `NOT_YET_ELIGIBLE`, and `INELIGIBLE` per `_docs/plan.md` §7. `MEMBER_NOT_FOUND` requires no database record; instead, document a specific member ID that is intentionally absent from the seed data so it can be used to demonstrate that outcome during demos.

## 4. Backend: eligibility decision logic
Goal: Implement the eligibility rule as an isolated, testable function.
Description: Write a pure function that takes a coverage effective date, an optional termination date, and a "Check Coverage On" date, and returns `ELIGIBLE`, `NOT_YET_ELIGIBLE`, or `INELIGIBLE` per the rules in `_docs/plan.md` §7. (`MEMBER_NOT_FOUND` is handled separately, at the lookup layer.) Cover boundary cases — on the effective date, on the termination date, and no termination date — with unit tests.

## 5. Backend: member and coverage lookup
Goal: Retrieve a member's coverage record from the database, or signal that none exists.
Description: Add a data-access function in `apps/api` that queries the SQLite database (via the models from task 3) for a member by ID and returns their coverage details, or a clear "not found" result if no match exists. Include tests for both the found and not-found cases.

## 6. Backend: eligibility REST endpoint
Goal: Expose the eligibility check as a REST endpoint per the agreed API contract.
Description: Add `GET /api/v1/eligibility` (query params `memberId`, `checkDate`) to the FastAPI app, wiring together the lookup (task 5) and decision logic (task 4), and shaping the response per `_docs/architecture.md` §5 — including returning `MEMBER_NOT_FOUND` as a `200` business outcome rather than a `404`.

## 7. Backend: input validation and error responses
Goal: Make invalid input and unexpected failures return the friendly, non-technical responses plan.md requires.
Description: Add Pydantic-based validation to the eligibility endpoint so a blank member ID or malformed date returns a `422` with a clear message, and add a generic exception handler so unexpected backend failures return a `500` with no internal details exposed, per `_docs/architecture.md` §10.

## 8. Backend: Dockerfile for the api service
Goal: Package the FastAPI service, including the seeded SQLite file, into a container image.
Description: Write `apps/api/Dockerfile` from a slim Python base image, installing dependencies, copying the app code and the seeded SQLite database (from task 3) into the image, and running the app via `uvicorn`. Verify the built image serves `/health` when run locally.

## 9. Frontend: Next.js app skeleton
Goal: Stand up the real Next.js App Router application shell to build the UI on.
Description: In `apps/web` (created in task 1), build the actual Next.js (App Router) + TypeScript application structure — a single page route and a basic layout, no business logic yet. Confirm it builds and runs locally with `next dev` and continues to pass the placeholder test from task 1.

## 10. Frontend: eligibility inquiry form
Goal: Let a user enter a member ID and a Check Coverage On date and submit an inquiry.
Description: Build the input form described in `_docs/plan.md` §5 — a member ID text field and a date field defaulted to today — with client-side state and a submit handler. The submit handler can stub out the actual API call for now; that is a separate task.

## 11. Frontend: API client for the eligibility endpoint
Goal: Connect the form to the live backend eligibility endpoint.
Description: Add a typed fetch wrapper in `apps/web` that calls `GET /api/v1/eligibility` (per `_docs/architecture.md` §5) with the member ID and check date, and wire it into the form's submit handler from task 10, replacing the stub. Distinguish the `200`/`422`/`500` response shapes so later tasks can render each one.

## 12. Frontend: result display
Goal: Show the eligibility outcome and supporting details to the user.
Description: Build a result panel that renders every field listed in `_docs/plan.md` §6 (member name, plan name, coverage dates, check date, status, reason) for a successful (`200`) response, plus a "start another inquiry" action that resets the form, per `_docs/plan.md` §8.

## 13. Frontend: error and not-found states
Goal: Give the user a clear, friendly message for every non-success outcome.
Description: Add UI states for the `MEMBER_NOT_FOUND` business outcome, for `422` validation errors (invalid member ID or date), and for `500`/network failures (a generic "temporarily unavailable" message with a retry option), per `_docs/plan.md` §12 acceptance scenarios 4–6 and `_docs/architecture.md` §10.

## 14. Frontend: Dockerfile for the web service
Goal: Package the Next.js app into a production container image.
Description: Write `apps/web/Dockerfile` using a multi-stage Node build (build the Next.js app, then run it from a slim production image), configured to call the api service's URL via an environment variable. Verify the built container serves the app locally.

## 15. Local dev: docker-compose for both services
Goal: Let a developer run the full app locally with one command.
Description: Add a `docker-compose.yml` at the repo root that builds and runs both the web and api containers (from tasks 8 and 14) on a shared network, with the frontend configured to call the backend's local URL, per `_docs/architecture.md` §6.

## 16. CI workflow: lint, test, and build on every PR
Goal: Catch failures automatically before merge.
Description: Add `.github/workflows/ci.yml` that, on every pull request, lints and runs the test suites for both `apps/web` and `apps/api`, and builds both Docker images to confirm they build cleanly, per `_docs/architecture.md` §7.

## 17. Cloud infrastructure: provision the two Cloud Run services
Goal: Create the destination the CD pipeline will deploy into.
Description: In Google Cloud, create the Artifact Registry repository and the two Cloud Run services (`member-eligibility-web`, `member-eligibility-api`) referenced in `_docs/architecture.md` §8, configured as public (no auth) and scale-to-zero, with the api service's CORS restricted to the web service's origin. This is a manual/console or CLI provisioning task, not a code change, and must exist before the CD workflow can deploy into it.

## 18. CD workflow: deploy to Cloud Run on merge to main
Goal: Automatically ship every merge to the live demo.
Description: Add `.github/workflows/cd.yml` that, on merge to `main`, builds and tags both images and pushes them to the Artifact Registry repository provisioned in task 17, then deploys both to the Cloud Run services provisioned in that same task via `gcloud run deploy`, authenticating through Workload Identity Federation rather than a stored service-account key, per `_docs/architecture.md` §7.

## 19. Accessibility and responsive layout pass
Goal: Meet plan.md's requirement for basic accessibility and desktop responsiveness.
Description: Review the form and result UI (tasks 10–13) for keyboard navigation and label/input associations, and check layout on common desktop screen widths, per `_docs/plan.md` §9 ("Basic accessibility and responsive use on common desktop screens"). Detailed acceptance criteria are deferred to task grooming.
