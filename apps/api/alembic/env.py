from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = WORKSPACE_ROOT / "apps" / "api"
WORKER_ROOT = WORKSPACE_ROOT / "apps" / "worker"

for candidate in (str(API_ROOT), str(WORKER_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from orbit_worker.persistence import persistence_metadata  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

database_url = config.get_main_option("sqlalchemy.url") or os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL must be set for Alembic migrations.")
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

target_metadata = persistence_metadata


def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
