#!/usr/bin/env python3
"""
Run Alembic migration for MeetScheduler
This script runs the Alembic upgrade command programmatically
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from alembic.config import Config
from alembic import command
from config import settings

def main():
    """Run Alembic migration"""
    print("🚀 Running Alembic migration for MeetScheduler...")
    print("=" * 60)
    
    # Get the alembic.ini path
    alembic_ini = Path(__file__).parent / "alembic.ini"
    
    if not alembic_ini.exists():
        print(f"❌ alembic.ini not found at: {alembic_ini}")
        return False
    
    # Create Alembic config
    alembic_cfg = Config(str(alembic_ini))
    
    # Override database URL
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    
    print(f"📍 Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
    print(f"📁 Migration directory: {Path(__file__).parent / 'alembic'}")
    print("-" * 60)
    
    try:
        # Show current revision
        print("📊 Current revision:")
        command.current(alembic_cfg, verbose=True)
        print()
        
        # Run upgrade
        print("⬆️  Upgrading to head...")
        command.upgrade(alembic_cfg, "head")
        
        print()
        print("✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

