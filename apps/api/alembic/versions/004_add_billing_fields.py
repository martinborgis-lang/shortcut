"""Add billing and subscription fields to User model

Revision ID: 004_add_billing_fields
Revises: 003_video_pipeline_models
Create Date: 2024-12-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '004_add_billing_fields'
down_revision = '003_video_pipeline_models'
branch_labels = None
depends_on = None


def upgrade():
    """Add billing and subscription fields to users table"""

    # Add new billing-related fields
    op.add_column('users', sa.Column('monthly_clips_generated', sa.Integer, nullable=False, default=0))
    op.add_column('users', sa.Column('grace_period_end', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('last_monthly_reset', sa.DateTime(timezone=True), nullable=True))

    # Set default values for existing users
    op.execute("""
        UPDATE users
        SET monthly_clips_generated = 0
        WHERE monthly_clips_generated IS NULL
    """)


def downgrade():
    """Remove billing and subscription fields from users table"""

    # Remove the new columns
    op.drop_column('users', 'last_monthly_reset')
    op.drop_column('users', 'grace_period_end')
    op.drop_column('users', 'monthly_clips_generated')