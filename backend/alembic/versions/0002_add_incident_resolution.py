"""Add incident resolution field.

Revision ID: 0002_add_incident_resolution
Revises: 0001_initial_schema
Create Date: 2026-07-09
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_add_incident_resolution"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("incidents", sa.Column("resolution", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("incidents", "resolution")
