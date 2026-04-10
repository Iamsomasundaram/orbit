# ORBIT Milestone 6

Milestone 6 adds bounded score recheck and committee re-synthesis on top of the persisted debate artifacts delivered in Milestone 5.

Delivered:

- synchronous API initiation for one re-synthesis session per persisted debate session
- deterministic score recheck logic that only activates when one or more conflict resolutions mark `score_change_required`
- durable storage for:
  - `resynthesis_sessions`
  - `resynthesized_scorecards`
  - `resynthesized_committee_reports`
- retrieval APIs that expose original committee artifacts alongside the active artifact set
- preservation of the original review-run scorecard and committee report even when re-synthesized artifacts are created

Boundaries kept intact:

- the approved Python thin-slice review path remains unchanged
- no committee re-synthesis runs unless persisted debate resolutions explicitly require it
- when no recheck is required, the original scorecard and report remain active and no replacement artifacts are materialized
- orchestration remains synchronous and bounded
- no provider-backed debate reasoning, async job systems, or advanced frontend history UX was introduced

Primary files:

- `apps/api/orbit_api/resyntheses.py`
- `apps/api/orbit_api/main.py`
- `apps/worker/orbit_worker/resynthesis.py`
- `apps/worker/orbit_worker/persistence.py`
- `apps/worker/tests/test_resynthesis_service.py`
- `apps/worker/tests/test_persistence_models.py`

Validation snapshot from April 10, 2026:

- worker pytest: `18 passed`
- frozen-baseline parity: `18 passed`
- live review run: `review-strong-ai-saas-001-20260410T063048874962Z`
- live debate session: `debate-review-strong-ai-saas-001-20260410T063048874962Z`
- live re-synthesis session: `resynthesis-debate-review-strong-ai-saas-001-20260410T063048874962Z`
- live no-change result: `completed_without_changes`
- active artifact source on live no-change result: `original`
- forced recheck path validated in worker tests produced a downgraded recommendation from `Proceed with Conditions` to `Pilot Only`

This milestone stops after bounded re-synthesis initiation, persistence, retrieval, and validation are complete.
