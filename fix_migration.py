#!/usr/bin/env python3
"""
Fix migration state - check database and potentially stamp migrations
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text, inspect
from config import settings

def check_database_state():
    """Check what's already in the database"""
    engine = create_engine(settings.DATABASE_URL)
    
    print("🔍 Checking database state...")
    print("=" * 60)
    
    with engine.connect() as conn:
        # Check if form_reviewed table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'form_reviewed'
            )
        """))
        form_reviewed_exists = result.scalar()
        print(f"✓ form_reviewed table: {'EXISTS' if form_reviewed_exists else 'MISSING'}")
        
        # Check if meet_scheduler table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'meet_scheduler'
            )
        """))
        meet_scheduler_exists = result.scalar()
        print(f"✓ meet_scheduler table: {'EXISTS' if meet_scheduler_exists else 'MISSING'}")
        
        # Check if CIM_TRAINING enum exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'CIM_TRAINING' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname IN ('formtype', 'form_type'))
            )
        """))
        cim_training_enum = result.scalar()
        print(f"✓ CIM_TRAINING enum: {'EXISTS' if cim_training_enum else 'MISSING'}")
        
        # Check if meetingtype enum exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_type 
                WHERE typname = 'meetingtype'
            )
        """))
        meetingtype_enum = result.scalar()
        print(f"✓ meetingtype enum: {'EXISTS' if meetingtype_enum else 'MISSING'}")
        
        # Check forms table columns
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'forms' 
            AND table_schema = 'public'
            AND column_name IN ('scheduled_at', 'time', 'meeting_host', 'scheduled_count')
        """))
        form_columns = [row[0] for row in result]
        print(f"✓ Forms table columns: {form_columns}")
        
        # Check alembic version table
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'alembic_version'
            )
        """))
        alembic_version_exists = result.scalar()
        
        if alembic_version_exists:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current_version = result.scalar()
            print(f"✓ Current Alembic version: {current_version}")
        else:
            print("✓ Alembic version table: MISSING")
    
    print("=" * 60)
    return {
        'form_reviewed': form_reviewed_exists,
        'meet_scheduler': meet_scheduler_exists,
        'cim_training_enum': cim_training_enum,
        'meetingtype_enum': meetingtype_enum,
        'form_columns': form_columns,
        'current_version': current_version if alembic_version_exists else None
    }

if __name__ == "__main__":
    state = check_database_state()

