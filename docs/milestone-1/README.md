# ORBIT Milestone 1

Milestone 1 establishes the local platform foundation around the approved Python backend direction without changing the Milestone 0.5 or 0.5a committee behavior.

Included in this milestone:

- Docker Compose foundation for `web`, `api`, `worker`, `postgres`, and `redis`
- FastAPI control-plane scaffold with health endpoints
- Python worker service wrapper around the approved runtime path
- Next.js platform shell with web health endpoints and runtime-facing landing page
- typed environment and settings strategy for Python and web services
- carry-forward planning for parity expansion, JS archival, and CI regression checks

Primary runtime entry points:

- `apps/api/orbit_api/main.py`
- `apps/worker/orbit_worker/service.py`
- `apps/web/app/page.tsx`
- `docker-compose.yml`

Reference-only services retained under the `baseline` Compose profile:

- `worker-js-baseline`
- `worker-parity`

Validation commands:

- `docker compose build api worker web`
- `docker compose up -d postgres redis api worker web`
- `docker compose ps`
- `docker compose --profile baseline run --rm worker-js-baseline`
- `docker compose --profile baseline run --rm worker-parity`

Stop rule:

- Milestone 2 work must not start until the Milestone 1 review pack is accepted.
