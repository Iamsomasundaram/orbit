# ORBIT Milestone 5

Milestone 5 adds bounded conflict resolution and debate handling on top of the persisted review-run artifacts delivered in Milestone 4.

Delivered:

- synchronous API initiation for one debate session per persisted review run
- deterministic moderator-controlled debate built from persisted structured conflicts and agent reviews only
- durable storage for `debate_sessions` and `conflict_resolutions`
- debate-scoped audit events persisted alongside the existing review audit trail
- debate detail retrieval that links back to the original review run, conflicts, scorecard, and committee report

Boundaries kept intact:

- the approved Python thin-slice review behavior is unchanged
- committee scorecard and report generation remain unchanged
- score changes are not applied automatically by debate; the moderator can only mark `score_change_required`
- orchestration remains bounded and synchronous
- no async job system, frontend history workflow, or provider-backed LLM execution was introduced

Primary files:

- `apps/api/orbit_api/debates.py`
- `apps/api/orbit_api/main.py`
- `apps/worker/orbit_worker/debate.py`
- `apps/worker/orbit_worker/persistence.py`
- `apps/worker/tests/test_debate_service.py`
- `apps/worker/tests/test_persistence_models.py`

Validation snapshot from April 10, 2026:

- worker pytest: `14 passed`
- frozen-baseline parity: `14 passed`
- live review run: `review-strong-ai-saas-001-20260410T055330553109Z`
- live debate session: `debate-review-strong-ai-saas-001-20260410T055330553109Z`
- persisted conflicts considered: `5`
- persisted conflict resolutions: `5`
- score-change-required count: `0`
- final recommendation remained `Proceed with Conditions`
- weighted composite remained `3.61`

This milestone stops after bounded debate initiation, persistence, and retrieval are validated.
