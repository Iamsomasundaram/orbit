# API App

Milestone 1 establishes the FastAPI platform foundation for ORBIT.

Current capability:

- process-level service metadata endpoint
- liveness and readiness health endpoints
- typed environment settings for local Compose execution
- readiness checks for postgres and redis

Entry points:

- `apps/api/orbit_api/main.py`
- `apps/api/Dockerfile`
