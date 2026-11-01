# 11 — Change Log and Scope Evolution

UniNest's requirements may evolve during development. Use this log to record meaningful changes.

## Completed MVP milestones — 2026-10-16

- Confirmed the first MVP scope and selected the existing MongoDB + Beanie implementation as the project database baseline.
- Completed backend authentication, owner listing management, admin verification/rejection, and student booking request workflows, with API integration coverage.
- Replaced the Vite starter screen with public search/details, student, owner, and admin pages connected to the API.
- Added disposable per-test MongoDB databases, a local interactive admin provisioning command, and the [MVP test and demo runbook](./12-test-and-demo.md).
- Fixed the admin review blank-page issue by aligning the pending-listings API response with the fields rendered by the admin dashboard.
- Validation: backend integration tests, frontend production build, and frontend lint pass. Payment processing and reservation conflict prevention remain out of scope.

## Change entry template
- Change ID:
- Date:
- Requested change:
- Reason / user problem:
- Type: new feature / changed requirement / bug fix / deferred feature
- Priority: P0 / P1 / P2 / future
- Impacted user roles:
- Impacted requirements and user stories:
- UI impact:
- API impact:
- Database/migration impact:
- Security/privacy impact:
- Testing required:
- Estimate / risk:
- Decision: accept / defer / reject
- Decision rationale:
- Status:

## Change rules
1. Keep the original presentation as the initial business concept, not a frozen feature list.
2. Record new ideas in the backlog before implementing them.
3. Review how a change affects frontend, backend, database, permissions, tests, and deployment.
4. If a database schema changes, create and test a migration.
5. Update requirements and acceptance criteria when behavior changes.
6. Do not silently change commission, payment, verification, or cancellation rules.
7. Keep completed work and decisions traceable; mark superseded decisions rather than deleting their history.
