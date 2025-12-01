"""Add google_event_id to meet_scheduler

Revision ID: 004_add_google_event_id
Revises: add_meeting_instances
Create Date: 2025-12-01 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_google_event_id'
down_revision = 'add_meeting_instances'
branch_labels = None
depends_on = None


def upgrade():
    # Add google_event_id column to meet_scheduler
    try:
        op.add_column('meet_scheduler', 
            sa.Column('google_event_id', sa.String(200), nullable=True, unique=True)
        )
        op.create_index('ix_meet_scheduler_google_event_id', 'meet_scheduler', ['google_event_id'])
    except Exception as e:
        print(f"Note: google_event_id column may already exist: {e}")
    
    # Make existing fields nullable (since we'll fetch from Google Calendar)
    try:
        op.alter_column('meet_scheduler', 'title', nullable=True)
        op.alter_column('meet_scheduler', 'meeting_time', nullable=True)
        op.alter_column('meet_scheduler', 'meeting_link', nullable=True)
    except Exception as e:
        print(f"Note: Columns may already be nullable: {e}")
    
    # Add google_event_id column to meeting_instance
    try:
        op.add_column('meeting_instance', 
            sa.Column('google_event_id', sa.String(200), nullable=True)
        )
        op.create_index('ix_meeting_instance_google_event_id', 'meeting_instance', ['google_event_id'])
    except Exception as e:
        print(f"Note: google_event_id column may already exist in meeting_instance: {e}")
    
    # Make scheduler_id nullable in meeting_instance (for backward compatibility)
    try:
        op.alter_column('meeting_instance', 'scheduler_id', nullable=True)
    except Exception as e:
        print(f"Note: scheduler_id may already be nullable: {e}")


def downgrade():
    # Remove google_event_id column from meeting_instance
    try:
        op.drop_index('ix_meeting_instance_google_event_id', table_name='meeting_instance')
        op.drop_column('meeting_instance', 'google_event_id')
    except Exception as e:
        print(f"Note: google_event_id column may not exist in meeting_instance: {e}")
    
    # Remove google_event_id column from meet_scheduler
    try:
        op.drop_index('ix_meet_scheduler_google_event_id', table_name='meet_scheduler')
        op.drop_column('meet_scheduler', 'google_event_id')
    except Exception as e:
        print(f"Note: google_event_id column may not exist: {e}")
    
    # Revert nullable changes (optional - may cause issues if data exists)
    # op.alter_column('meet_scheduler', 'title', nullable=False)
    # op.alter_column('meet_scheduler', 'meeting_time', nullable=False)
    # op.alter_column('meet_scheduler', 'meeting_link', nullable=False)
    # op.alter_column('meeting_instance', 'scheduler_id', nullable=False)

