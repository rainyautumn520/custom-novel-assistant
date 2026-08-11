from logging.config import fileConfig
from pathlib import Path

from alembic import context

import app.models  # noqa: F401
from app.core.database import AppBase, app_engine, settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = AppBase.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    with app_engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
