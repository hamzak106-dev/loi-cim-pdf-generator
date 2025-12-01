#!/usr/bin/env python3
"""
Stamp Alembic version table to mark migrations as applied
Since the database already has all the tables, we'll stamp it to the latest revision
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from alembic.config import Config
from alembic import command
from config import settings

def main():
    """Stamp the database to the latest revision"""
    print("🏷️  Stamping Alembic version...")
    print("=" * 60)
    
    alembic_ini = Path(__file__).parent / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    
    print(f"📍 Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
    print("-" * 60)
    
    try:
        # Stamp to the latest revision (add_meet_scheduler)
        print("🏷️  Stamping to: add_meet_scheduler")
        command.stamp(alembic_cfg, "add_meet_scheduler")
        
        print()
        print("✅ Database stamped successfully!")
        print("   All migrations are now marked as applied.")
        
        # Show current version
        print()
        print("📊 Current version:")
        command.current(alembic_cfg, verbose=True)
        
        return True
        
    except Exception as e:
        print(f"❌ Stamping failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

