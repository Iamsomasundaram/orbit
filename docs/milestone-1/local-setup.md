# ORBIT Milestone 1 Local Setup

## Environment

1. Copy `.env.example` to `.env` if you want to override defaults.
2. Set `OPENAI_API_KEY` in `.env` when you are ready to test provider-backed integrations in later milestones.
3. Leave `LLM_PROVIDER=openai` unless you are intentionally testing a placeholder provider path.

## Default Ports

- web: `5000`
- api: `5001`
- postgres: `5002`
- redis: `5003`

## Bring Up The Platform

1. Run `docker compose build api worker web`.
2. Run `docker compose up -d postgres redis api worker web`.
3. Run `docker compose ps`.

## Smoke Checks

- API live: `http://localhost:5001/health/live`
- API ready: `http://localhost:5001/health/ready`
- Web live: `http://localhost:5000/api/health/live`
- Web ready: `http://localhost:5000/api/health/ready`
- Web shell: `http://localhost:5000`

The worker is intentionally internal-only. Its health surface is available inside the container network at `http://worker:8002/health/live` and `http://worker:8002/health/ready`.

## Reference Baseline Profile

These commands remain available for regression checks but are not the active backend direction:

- `docker compose --profile baseline run --rm worker-js-baseline`
- `docker compose --profile baseline run --rm worker-parity`

## Tear Down

- `docker compose down --remove-orphans`
