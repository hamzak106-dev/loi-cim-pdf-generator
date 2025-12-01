#!/usr/bin/env python3
"""
Add CIM_TRAINING to formtype enum in PostgreSQL
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from config import settings

def add_cim_training_enum():
    """Add CIM_TRAINING value to formtype enum"""
    
    # Fix postgres:// to postgresql://
    db_url = settings.DATABASE_URL
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    print("🔧 Adding CIM_TRAINING to formtype enum")
    print("=" * 60)
    print(f"📊 Database: {db_url.split('@')[1] if '@' in db_url else db_url}")
    print()
    
    engine = create_engine(db_url)
    
    with engine.connect() as connection:
        trans = connection.begin()
        try:
            # Check current enum values
            result = connection.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'formtype')
                ORDER BY enumlabel
            """))
            current_values = [row[0] for row in result]
            print(f"📋 Current enum values: {', '.join(current_values)}")
            print()
            
            if 'CIM_TRAINING' in current_values:
                print("✅ CIM_TRAINING already exists in enum")
                trans.commit()
                return True
            
            # Add CIM_TRAINING to enum
            print("➕ Adding CIM_TRAINING to formtype enum...")
            connection.execute(text("ALTER TYPE formtype ADD VALUE IF NOT EXISTS 'CIM_TRAINING'"))
            
            trans.commit()
            
            # Verify it was added
            result = connection.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'formtype')
                ORDER BY enumlabel
            """))
            new_values = [row[0] for row in result]
            
            print()
            print("=" * 60)
            print(f"✅ Successfully added CIM_TRAINING to enum")
            print(f"📋 Updated enum values: {', '.join(new_values)}")
            print()
            return True
            
        except Exception as e:
            trans.rollback()
            error_msg = str(e)
            
            # Check if it's already added (some PostgreSQL versions)
            if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                print("ℹ️  CIM_TRAINING already exists in enum (this is OK)")
                return True
            
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = add_cim_training_enum()
    sys.exit(0 if success else 1)


