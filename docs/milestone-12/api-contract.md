# ORBIT Milestone 12 API Contract

Milestone 12 does not add new reasoning APIs. Committee Mode is a UI consumer of the existing persisted deliberation endpoints introduced in Milestone 11.

## Existing API surface used by Committee Mode

### `GET /api/v1/review-runs/{run_id}/deliberation`

Committee Mode fetches the full ordered deliberation timeline once, then drives playback locally in the browser.

Usage in Milestone 12:

- preserves persisted `sequence_number` order
- provides the statement stream used for staged reveal
- provides `conflict_reference` values used by the conflict spotlight
- preserves lineage and active artifact-selection state

### `GET /api/v1/review-runs/{run_id}/deliberation/summary`

Committee Mode fetches the summary view once and uses it to render the phase rail and final verdict metadata.

Usage in Milestone 12:

- phase labels and counts
- representative phase summaries
- final recommendation
- weighted composite score
- active artifact source

## New UI route

Milestone 12 adds one web route:

- `/review-runs/{run_id}/committee`

Behavior:

- fetches the two existing deliberation endpoints server-side
- passes the persisted data into a client-side playback controller
- performs no new server-side reasoning
- performs no new llm calls

## Playback behavior

Committee Mode playback is derived only from the stored deliberation records:

- reveals entries in persisted order
- supports pause / resume without refetching
- supports skipping to the next phase
- supports jumping to the final verdict
- highlights conflicts using persisted conflict references

## Persistence impact

Milestone 12 does not change the persistence schema.

No new tables:

- no new review tables
- no new debate tables
- no new deliberation tables
- no new migration revision

The persisted deliberation records remain the authoritative source for both:

- static timeline inspection
- Committee Mode boardroom playback
