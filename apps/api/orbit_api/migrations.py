from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from orbit_worker.persistence import persistence_metadata

MigrationAction = Literal["upgrade", "stamp_then_upgrade"]


def expected_table_names() -> set[str]:
    return {table.name for table in persistence_metadata.sorted_tables}


def determine_migration_action(table_names: set[str]) -> MigrationAction:
    expected = expected_table_names()
    has_version_table = "alembic_version" in table_names
    has_expected_tables = expected.issubset(table_names)
    has_any_expected_tables = bool(table_names & expected)

    if has_version_table:
        return "upgrade"
    if not has_any_expected_tables:
        return "upgrade"
    if has_expected_tables:
        return "stamp_then_upgrade"
    missing_tables = ", ".join(sorted(expected - table_names))
    raise RuntimeError(
        "Database is in a partial pre-Alembic ORBIT state. "
        f"Missing expected tables: {missing_tables}. "
        "Reset the local database or complete the schema before stamping."
    )


def alembic_config() -> Config:
    workspace_root = Path(__file__).resolve().parents[3]
    config = Config(str(workspace_root / "apps" / "api" / "alembic.ini"))
    config.set_main_option("script_location", str(workspace_root / "apps" / "api" / "alembic"))
    config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
    return config


def run_migrations() -> MigrationAction:
    database_url = os.environ["DATABASE_URL"]
    engine = create_engine(database_url, future=True, pool_pre_ping=True)
    try:
        action = determine_migration_action(set(inspect(engine).get_table_names()))
    finally:
        engine.dispose()

    config = alembic_config()
    if action == "stamp_then_upgrade":
        command.stamp(config, "head")
    command.upgrade(config, "head")
    return action


def main() -> None:
    action = run_migrations()
    print(f"Applied migration action: {action}")


if __name__ == "__main__":
    main()
