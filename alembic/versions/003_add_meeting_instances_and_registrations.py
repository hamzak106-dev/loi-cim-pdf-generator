"""add meeting instances and registrations

Revision ID: add_meeting_instances
Revises: add_meet_scheduler
Create Date: 2025-11-28 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_meeting_instances'
down_revision: Union[str, None] = 'add_meet_scheduler'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    
    # Step 1: Create meeting_instance table
    table_check = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'meeting_instance'
        )
    """))
    
    if not table_check.scalar():
        op.create_table(
            'meeting_instance',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('scheduler_id', sa.Integer(), nullable=False),
            sa.Column('instance_time', sa.DateTime(timezone=True), nullable=False),
            sa.Column('guest_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('max_guests', sa.Integer(), nullable=False, server_default='10'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['scheduler_id'], ['meet_scheduler.id'], ),
        )
        
        # Create indexes
        op.create_index('idx_meeting_instance_scheduler_id', 'meeting_instance', ['scheduler_id'], unique=False)
        op.create_index('idx_meeting_instance_instance_time', 'meeting_instance', ['instance_time'], unique=False)
    
    # Step 2: Create meeting_registration table
    table_check2 = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'meeting_registration'
        )
    """))
    
    if not table_check2.scalar():
        op.create_table(
            'meeting_registration',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('instance_id', sa.Integer(), nullable=False),
            sa.Column('full_name', sa.String(length=100), nullable=False),
            sa.Column('email', sa.String(length=120), nullable=False),
            sa.Column('registered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['instance_id'], ['meeting_instance.id'], ),
        )
        
        # Create indexes
        op.create_index('idx_meeting_registration_instance_id', 'meeting_registration', ['instance_id'], unique=False)
        op.create_index('idx_meeting_registration_email', 'meeting_registration', ['email'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_meeting_registration_email', table_name='meeting_registration')
    op.drop_index('idx_meeting_registration_instance_id', table_name='meeting_registration')
    op.drop_index('idx_meeting_instance_instance_time', table_name='meeting_instance')
    op.drop_index('idx_meeting_instance_scheduler_id', table_name='meeting_instance')
    
    # Drop tables
    op.drop_table('meeting_registration')
    op.drop_table('meeting_instance')

