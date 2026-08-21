# WorkflowFox Showcase 3 — Cloud-Native Member Eligibility

**Document:** Product Plan  
**Version:** 0.1  
**Status:** Draft for approval

## 1. Purpose

Build a small enterprise application that helps a service representative determine whether a member has active coverage on a selected date.

The showcase will demonstrate a complete product journey while keeping the business capability intentionally narrow and easy to understand.

## 2. Business Problem

Member eligibility information is often distributed across systems or checked through manual steps. A representative may take too long to answer a simple coverage question, and inconsistent interpretation of coverage dates can produce errors.

## 3. Primary User

**Service Representative**

The representative receives an eligibility inquiry from a member or provider and needs a fast, consistent answer.

## 4. Desired Outcome

The representative can enter a member ID, select **Check Coverage On**, and receive a clear eligibility decision with the supporting coverage details and reason.

## 5. MVP User Journey

1. The representative opens the eligibility application.
2. The representative enters a member ID.
3. The **Check Coverage On** field defaults to today but can be changed.
4. The representative submits the inquiry.
5. The application validates the input and finds the member's coverage.
6. The application returns the eligibility status, coverage details, and a plain-language reason.
7. The representative communicates the result to the member or provider.

## 6. Information Displayed

- Member ID
- Member name
- Plan name
- Coverage effective date
- Coverage termination date, when applicable
- Check Coverage On date
- Eligibility status
- Eligibility reason

## 7. Eligibility Decisions

The MVP supports four outcomes:

| Outcome | Rule |
|---|---|
| `ELIGIBLE` | The Check Coverage On date falls within the active coverage period. |
| `NOT_YET_ELIGIBLE` | The Check Coverage On date is before the coverage effective date. |
| `INELIGIBLE` | The Check Coverage On date is after the coverage termination date. |
| `MEMBER_NOT_FOUND` | No member matches the submitted member ID. |

## 8. Functional Requirements

- Accept a member ID and Check Coverage On date.
- Require a non-empty member ID and a valid date.
- Retrieve a matching synthetic member and coverage record.
- Apply the defined eligibility rules consistently.
- Display a clear result without exposing internal system details.
- Provide a friendly message for invalid input, missing members, and unavailable service.
- Allow the representative to start another inquiry.

## 9. MVP Scope

### In Scope

- One eligibility inquiry workflow
- One primary user role
- Synthetic member, plan, and coverage data
- Current and historical coverage-date checks
- Clear success, ineligible, not-yet-eligible, not-found, and error states
- Basic accessibility and responsive use on common desktop screens

### Out of Scope

- Salesforce integration
- Member or coverage updates
- Claims, benefits, accumulators, authorizations, or payments
- Quoting, shopping, enrollment, or plan comparison
- Multiple coverage segments or coordination of benefits
- Real customer data or protected health information
- Generative AI, chat, recommendations, or automated decisions beyond the stated rules
- Production identity management, enterprise SSO, or multiple user roles
- Analytics, dashboards, notifications, or audit reporting

## 10. Assumptions and Constraints

- All people, organizations, plans, and identifiers are fictional.
- Eligibility is determined only from the effective date, termination date, and Check Coverage On date.
- An absent termination date means coverage remains active after the effective date.
- The showcase is read-only.
- Simplicity, fast completion, low operating cost, and clear demonstration value take priority over feature breadth.

## 11. Success Criteria

The MVP is successful when:

- A representative can complete an inquiry without training.
- Each defined eligibility outcome can be demonstrated with synthetic data.
- Invalid and unavailable scenarios produce clear, non-technical messages.
- The same input always produces the same decision.
- No real personal or health information is used.
- The application is suitable for a short public demonstration.

## 12. Acceptance Scenarios

1. A Check Coverage On date within coverage returns `ELIGIBLE`.
2. A Check Coverage On date before coverage begins returns `NOT_YET_ELIGIBLE`.
3. A Check Coverage On date after coverage ends returns `INELIGIBLE`.
4. An unknown member ID returns `MEMBER_NOT_FOUND`.
5. A blank member ID or invalid date is rejected with a helpful message.
6. A temporary service failure does not expose technical details and allows retry.

## 13. Deferred Decisions

Technology stack, solution architecture, data storage, hosting, deployment, observability, security implementation, and delivery tooling will be evaluated only after this product plan is reviewed and approved.
