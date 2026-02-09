"""Video pipeline model updates for F4

Revision ID: 003
Revises: 002
Create Date: 2024-02-06 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update projects table for video pipeline
    # Add new columns
    op.add_column('projects', sa.Column('source_url', sa.Text(), nullable=False, server_default=''))
    op.add_column('projects', sa.Column('source_s3_key', sa.Text(), nullable=True))
    op.add_column('projects', sa.Column('source_filename', sa.String(length=255), nullable=True))
    op.add_column('projects', sa.Column('source_size', sa.Integer(), nullable=True))
    op.add_column('projects', sa.Column('source_duration', sa.Float(), nullable=True))
    op.add_column('projects', sa.Column('current_step', sa.String(length=50), nullable=True))
    op.add_column('projects', sa.Column('transcript_json', JSON(), nullable=True))
    op.add_column('projects', sa.Column('viral_segments', JSON(), nullable=True))
    op.add_column('projects', sa.Column('max_clips_requested', sa.Integer(), nullable=False, server_default='5'))

    # Remove old columns (rename first for data migration)
    op.alter_column('projects', 'original_video_url', new_column_name='old_original_video_url')
    op.alter_column('projects', 'original_video_filename', new_column_name='old_original_video_filename')
    op.alter_column('projects', 'original_video_size', new_column_name='old_original_video_size')
    op.alter_column('projects', 'original_video_duration', new_column_name='old_original_video_duration')
    op.alter_column('projects', 'transcription', new_column_name='old_transcription')
    op.alter_column('projects', 'viral_moments', new_column_name='old_viral_moments')

    # Remove unused columns
    op.drop_column('projects', 'topics')
    op.drop_column('projects', 'sentiment_analysis')

    # Update clips table for video pipeline
    # Add new columns
    op.add_column('clips', sa.Column('s3_key', sa.Text(), nullable=True))
    op.add_column('clips', sa.Column('reason', sa.Text(), nullable=True))
    op.add_column('clips', sa.Column('hook', sa.Text(), nullable=True))
    op.add_column('clips', sa.Column('subtitle_config', JSON(), nullable=True))
    op.add_column('clips', sa.Column('crop_settings', JSON(), nullable=True))

    # Modify existing columns
    op.alter_column('clips', 'subtitle_style',
                   type_=sa.String(length=50),
                   server_default='hormozi',
                   nullable=False)

    # Remove unused columns
    op.drop_column('clips', 'engagement_prediction')
    op.drop_column('clips', 'hook_strength')
    op.drop_column('clips', 'content_quality')
    op.drop_column('clips', 'background_music')
    op.drop_column('clips', 'visual_effects')
    op.drop_column('clips', 'branding')
    op.drop_column('clips', 'is_favorite')
    op.drop_column('clips', 'user_rating')
    op.drop_column('clips', 'user_notes')

    # Make name column nullable in projects
    op.alter_column('projects', 'name', nullable=True)


def downgrade() -> None:
    # Restore projects table
    op.alter_column('projects', 'name', nullable=False)

    # Add back removed columns with default values
    op.add_column('projects', sa.Column('topics', JSON(), nullable=True))
    op.add_column('projects', sa.Column('sentiment_analysis', JSON(), nullable=True))

    # Restore old column names
    op.alter_column('projects', 'old_original_video_url', new_column_name='original_video_url')
    op.alter_column('projects', 'old_original_video_filename', new_column_name='original_video_filename')
    op.alter_column('projects', 'old_original_video_size', new_column_name='original_video_size')
    op.alter_column('projects', 'old_original_video_duration', new_column_name='original_video_duration')
    op.alter_column('projects', 'old_transcription', new_column_name='transcription')
    op.alter_column('projects', 'old_viral_moments', new_column_name='viral_moments')

    # Remove new columns
    op.drop_column('projects', 'max_clips_requested')
    op.drop_column('projects', 'viral_segments')
    op.drop_column('projects', 'transcript_json')
    op.drop_column('projects', 'current_step')
    op.drop_column('projects', 'source_duration')
    op.drop_column('projects', 'source_size')
    op.drop_column('projects', 'source_filename')
    op.drop_column('projects', 'source_s3_key')
    op.drop_column('projects', 'source_url')

    # Restore clips table
    # Add back removed columns
    op.add_column('clips', sa.Column('user_notes', sa.Text(), nullable=True))
    op.add_column('clips', sa.Column('user_rating', sa.Integer(), nullable=True))
    op.add_column('clips', sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('clips', sa.Column('branding', JSON(), nullable=True))
    op.add_column('clips', sa.Column('visual_effects', JSON(), nullable=True))
    op.add_column('clips', sa.Column('background_music', sa.String(length=255), nullable=True))
    op.add_column('clips', sa.Column('content_quality', sa.Float(), nullable=True))
    op.add_column('clips', sa.Column('hook_strength', sa.Float(), nullable=True))
    op.add_column('clips', sa.Column('engagement_prediction', JSON(), nullable=True))

    # Restore subtitle_style as JSON
    op.alter_column('clips', 'subtitle_style',
                   type_=JSON(),
                   server_default=None,
                   nullable=True)

    # Remove new columns
    op.drop_column('clips', 'crop_settings')
    op.drop_column('clips', 'subtitle_config')
    op.drop_column('clips', 'hook')
    op.drop_column('clips', 'reason')
    op.drop_column('clips', 's3_key')