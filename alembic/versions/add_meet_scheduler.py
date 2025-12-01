"""add meet scheduler

Revision ID: add_meet_scheduler
Revises: add_cim_training_reviewed
Create Date: 2025-11-28 19:08:18.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_meet_scheduler'
down_revision: Union[str, None] = 'add_cim_training_reviewed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    
    # Step 1: Create meetingtype enum if it doesn't exist
    enum_check = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_type 
            WHERE typname = 'meetingtype'
        )
    """))
    
    if not enum_check.scalar():
        op.execute("CREATE TYPE meetingtype AS ENUM ('LOI Call', 'CIM Call')")
    
    # Step 2: Create meet_scheduler table if it doesn't exist
    table_check = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'meet_scheduler'
        )
    """))
    
    if not table_check.scalar():
        op.create_table(
            'meet_scheduler',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('meeting_time', sa.DateTime(timezone=True), nullable=False),
            sa.Column('meeting_link', sa.String(length=500), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('host', sa.String(length=100), nullable=False),
            sa.Column('guest_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('form_type', postgresql.ENUM('LOI Call', 'CIM Call', name='meetingtype', create_type=False), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('recurring_day', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes
        op.create_index('idx_meet_scheduler_meeting_time', 'meet_scheduler', ['meeting_time'], unique=False)
        op.create_index('idx_meet_scheduler_form_type', 'meet_scheduler', ['form_type'], unique=False)
        op.create_index('idx_meet_scheduler_is_active', 'meet_scheduler', ['is_active'], unique=False)


def downgrade() -> None:
    # Step 1: Drop indexes
    op.drop_index('idx_meet_scheduler_is_active', table_name='meet_scheduler')
    op.drop_index('idx_meet_scheduler_form_type', table_name='meet_scheduler')
    op.drop_index('idx_meet_scheduler_meeting_time', table_name='meet_scheduler')
    
    # Step 2: Drop table
    op.drop_table('meet_scheduler')
    
    # Step 3: Drop enum (optional - might be used elsewhere)
    # Note: PostgreSQL doesn't support dropping enum types if they're used
    # Uncomment if you want to drop the enum type
    # op.execute("DROP TYPE IF EXISTS meetingtype")

