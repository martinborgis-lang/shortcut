"""Add user plan and monthly minutes fields

Revision ID: 002_add_user_plan_fields
Revises:
Create Date: 2026-02-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = '002_add_user_plan_fields'
down_revision: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    # Create enum type for plan
    plan_enum = postgresql.ENUM('free', 'starter', 'pro', 'enterprise', name='plantype')
    plan_enum.create(op.get_bind())

    # Add new columns
    op.add_column('users', sa.Column('plan', plan_enum, nullable=False, server_default='free'))
    op.add_column('users', sa.Column('monthly_minutes_used', sa.Integer(), nullable=False, server_default='0'))

    # Remove server defaults after adding
    op.alter_column('users', 'plan', server_default=None)
    op.alter_column('users', 'monthly_minutes_used', server_default=None)


def downgrade() -> None:
    # Remove columns
    op.drop_column('users', 'monthly_minutes_used')
    op.drop_column('users', 'plan')

    # Drop enum type
    plan_enum = postgresql.ENUM('free', 'starter', 'pro', 'enterprise', name='plantype')
    plan_enum.drop(op.get_bind())