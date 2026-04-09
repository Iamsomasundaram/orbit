from __future__ import annotations

from orbit_worker.persistence import PERSISTENCE_SCHEMA_VERSION, PersistenceSchemaCatalog, get_persistence_schema_catalog, render_postgres_ddl
from orbit_worker.schemas import OrbitModel


class PersistenceDdlResponse(OrbitModel):
    schema_version: str
    dialect: str
    table_count: int
    ddl: str


def persistence_schema_catalog() -> PersistenceSchemaCatalog:
    return get_persistence_schema_catalog()


def persistence_ddl_response() -> PersistenceDdlResponse:
    catalog = get_persistence_schema_catalog()
    return PersistenceDdlResponse(
        schema_version=PERSISTENCE_SCHEMA_VERSION,
        dialect="postgresql",
        table_count=len(catalog.tables),
        ddl=render_postgres_ddl(),
    )
