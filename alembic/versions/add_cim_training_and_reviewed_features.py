"""add cim training and reviewed features

Revision ID: add_cim_training_reviewed
Revises: cb04253dfea9
Create Date: 2025-01-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_cim_training_reviewed'
down_revision: Union[str, None] = 'cb04253dfea9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Alter the form_type enum to add CIM_TRAINING
    # For PostgreSQL, find the enum type and add the value
    connection = op.get_bind()
    
    # Find the enum type name
    enum_result = connection.execute(sa.text("""
        SELECT typname FROM pg_type 
        WHERE typtype = 'e' 
        AND (typname = 'formtype' OR typname = 'form_type')
        LIMIT 1
    """))
    enum_row = enum_result.fetchone()
    
    if enum_row:
        enum_type_name = enum_row[0]
        # Check if CIM_TRAINING already exists
        check_result = connection.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'CIM_TRAINING' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = '{enum_type_name}')
            )
        """))
        if not check_result.scalar():
            op.execute(f"ALTER TYPE {enum_type_name} ADD VALUE 'CIM_TRAINING'")
    
    # Step 2: Add new columns to forms table
    # Use IF NOT EXISTS pattern for safety
    try:
        op.add_column('forms', sa.Column('scheduled_at', sa.String(length=100), nullable=True))
    except Exception:
        pass  # Column might already exist
    
    try:
        op.add_column('forms', sa.Column('time', sa.String(length=50), nullable=True))
    except Exception:
        pass
    
    try:
        op.add_column('forms', sa.Column('meeting_host', sa.String(length=100), nullable=True))
    except Exception:
        pass
    
    try:
        op.add_column('forms', sa.Column('scheduled_count', sa.Integer(), nullable=True, server_default='0'))
    except Exception:
        pass
    
    # Step 3: Create form_reviewed table
    # Check if table exists first
    table_check = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'form_reviewed'
        )
    """))
    
    if not table_check.scalar():
        op.create_table(
            'form_reviewed',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('form_id', sa.Integer(), nullable=False),
            sa.Column('reviewed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('reviewed_by', sa.String(length=100), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('form_id'),
            sa.ForeignKeyConstraint(['form_id'], ['forms.id'], ),
        )
        op.create_index('ix_form_reviewed_form_id', 'form_reviewed', ['form_id'], unique=False)


def downgrade() -> None:
    # Step 1: Drop form_reviewed table
    op.drop_index('ix_form_reviewed_form_id', table_name='form_reviewed')
    op.drop_table('form_reviewed')
    
    # Step 2: Remove columns from forms table
    op.drop_column('forms', 'scheduled_count')
    op.drop_column('forms', 'meeting_host')
    op.drop_column('forms', 'time')
    op.drop_column('forms', 'scheduled_at')
    
    # Note: PostgreSQL doesn't support removing enum values easily
    # The enum value CIM_TRAINING will remain but won't be used
    # To fully remove it, you would need to recreate the enum type
