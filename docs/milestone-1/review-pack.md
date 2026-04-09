# ORBIT Milestone 1 Review Pack

## Scope Delivered

Completed in this milestone:

- Docker Compose platform foundation for `web`, `api`, `worker`, `postgres`, and `redis`
- FastAPI API scaffold with typed settings, liveness, readiness, and system info endpoints
- Python worker service scaffold with typed settings and health endpoints while preserving the approved thin-slice runtime modules
- Next.js web scaffold with platform landing page plus liveness and readiness endpoints
- host port allocation aligned to the approved development ports
- optional `baseline` Compose profile retaining the JS reference runner and Python parity test path
- committed dependency lockfiles for the pnpm workspace and the Python api and worker services
- local setup documentation and carry-forward planning for parity expansion, JS archival, and CI regression strategy

## Architecture Decisions

- the Python worker runtime remains the source of truth for active backend execution
- the JS thin-slice path remains reference-only and is isolated to the `baseline` Compose profile
- Milestone 1 adds service wrappers and health surfaces without changing the approved Milestone 0.5 or 0.5a review behavior
- API and worker readiness checks use dependency-level postgres and redis connectivity rather than placeholder success responses
- web, api, and worker run as local development services under Docker Compose; postgres and redis persist through named volumes
- typed runtime settings are enforced in Python through Pydantic settings models and in the web app through typed config helpers
- reproducibility is anchored on committed `pnpm-lock.yaml`, `apps/api/poetry.lock`, and `apps/worker/poetry.lock`, generated from inside the validated containers

## Quality Status

Validation executed successfully:

- `docker compose build api worker web` -> pass
- `docker compose up -d postgres redis api worker web` -> pass
- `docker compose ps` -> all five services healthy
- `http://localhost:5001/health/ready` -> pass
- `http://localhost:5000/api/health/ready` -> pass
- internal worker `http://127.0.0.1:8002/health/ready` via container exec -> pass
- `docker compose --profile baseline run --rm worker-js-baseline` -> pass
- `docker compose --profile baseline run --rm worker-parity` -> pass
- lockfiles generated and persisted in the repo from the running containers -> pass

Observed platform results:

- api ready status: `ok`
- worker ready status: `ok`
- web ready status: `ok`
- postgres: healthy
- redis: healthy
- reference thin slice still returns `Proceed with Conditions` and weighted composite `3.61`

Known issues:

- host `corepack` still fails signature verification on this machine, so direct host `pnpm install` remains unreliable even though the committed lockfile has been generated through the containerized path
- API and worker service wrappers expose platform health and metadata only; review submission and persistence APIs remain out of scope until Milestone 2+
- the baseline parity suite still covers only the strong portfolio, with expansion planned for the other two starter fixtures

## Risks

Technical risk:

- the web service currently runs the Next.js development server inside Compose, which is acceptable for local foundation work but not the final production posture
- parity coverage remains narrow until the other two starter portfolios are added to the executable baseline suite
- host package-manager trust issues could still confuse local onboarding if Docker-first setup is not followed

Product risk:

- Milestone 1 proves the platform shell, not end-user review workflows beyond the already approved thin-slice path
- the web app is intentionally a platform landing shell, not the Milestone 7 report experience

Delivery risk:

- if the JS baseline stays active too long without archival discipline, teams may accidentally treat it as a second backend direction
- Docker-first development works now, but future CI and onboarding docs must keep the container path primary to avoid host drift

## Validation

How to validate locally:

1. Review `.env.example` and optionally create `.env`.
2. Run `docker compose build api worker web`.
3. Run `docker compose up -d postgres redis api worker web`.
4. Run `docker compose ps`.
5. Check `http://localhost:5001/health/ready`.
6. Check `http://localhost:5000/api/health/ready`.
7. Open `http://localhost:5000`.
8. Run `docker compose --profile baseline run --rm worker-js-baseline`.
9. Run `docker compose --profile baseline run --rm worker-parity`.
10. Run `docker compose down --remove-orphans` when finished.

## Review Checklist

- Does the Compose foundation now bring up `web`, `api`, `worker`, `postgres`, and `redis` locally?
- Is the Python worker clearly the active backend direction, with JS kept reference-only?
- Do health endpoints provide meaningful readiness checks for the platform services?
- Did Milestone 1 avoid broadening into Milestone 2 schema, persistence, or workflow implementation scope?
- Are the carry-forward plans for parity expansion, JS archival, and CI regression explicitly captured?

## Recommendation

Proceed with fixes.

Fixes to carry into the next approved planning gate, not Milestone 1 expansion:

- resolve the host `corepack` signature issue so host-side pnpm usage matches the validated container path
- extend the parity suite to the promising and weak starter portfolios
- formalize the CI pipeline for Compose health checks and parity regression before broader backend feature work
- define the exact milestone when the JS baseline moves from active reference to documented archive

Milestone 1 is complete and should stop here pending review.
