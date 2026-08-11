import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

import app.models  # noqa: F401
from app.core.database import NovelBase

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = NovelBase.metadata


def run_migrations_offline() -> None:
    url = os.environ["NOVEL_DB_URL"]
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = os.environ["NOVEL_DB_URL"]
    engine = create_engine(url, connect_args={"check_same_thread": False})
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
