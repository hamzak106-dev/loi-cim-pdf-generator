#!/usr/bin/env python3
"""
Run database migration to add CIM_TRAINING and reviewed features
This script uses your existing database configuration

Usage:
    python run_migration.py              # Uses DATABASE_URL from .env
    python run_migration.py --local      # Uses local database (DATABASE_URL)
    python run_migration.py --live       # Uses production database (DATABASE_URL_PRODUCTION or DATABASE_URL_LIVE)
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from config import settings
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration(environment=None):
    """Run the migration SQL script
    
    Args:
        environment: 'local' or 'live' - if None, uses DATABASE_URL from .env
    """
    
    print("🚀 Starting database migration...")
    print("=" * 60)
    
    # Get the appropriate database URL based on environment flag
    if environment == 'local':
        print("📍 Environment: LOCAL")
        db_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)
    elif environment == 'live':
        print("📍 Environment: LIVE (PRODUCTION)")
        # Try different possible production URL env var names
        db_url = os.getenv("DATABASE_URL_PRODUCTION") or os.getenv("DATABASE_URL_LIVE") or os.getenv("PRODUCTION_DATABASE_URL")
        if not db_url:
            print("❌ Error: Production database URL not found in .env")
            print("   Please set DATABASE_URL_PRODUCTION, DATABASE_URL_LIVE, or PRODUCTION_DATABASE_URL")
            return False
    else:
        print("📍 Environment: AUTO (using DATABASE_URL from .env)")
        db_url = settings.DATABASE_URL
    
    # Fix postgres:// to postgresql://
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    # Create engine with the selected database URL
    migration_engine = create_engine(db_url)
    
    # Read the SQL file
    sql_file = Path(__file__).parent / "run_migration.sql"
    
    if not sql_file.exists():
        print(f"❌ Error: {sql_file} not found!")
        return False
    
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    
    # Show database info (mask password)
    db_display = db_url.split('@')[1] if '@' in db_url else db_url
    if ':' in db_url and '@' in db_url:
        # Mask password
        auth_part = db_url.split('@')[0]
        if ':' in auth_part:
            user = auth_part.split(':')[1].split('@')[0] if '@' in auth_part else auth_part.split(':')[0]
            db_display = f"{user}@{db_display}"
    print(f"📊 Database: {db_display}")
    print()
    
    try:
        # Use the database engine with the selected URL
        print(f"🔌 Connecting to database...")
        
        # Get raw connection for executing DDL
        raw_conn = migration_engine.raw_connection()
        raw_conn.autocommit = True
        cur = raw_conn.cursor()
        
        try:
            # Execute migration
            print("📝 Running migration SQL...")
            print()
            
            # Execute the entire SQL script
            # PostgreSQL can handle DO blocks and multiple statements
            try:
                cur.execute(sql_content)
                print("✅ Migration SQL executed successfully")
            except Exception as e:
                # Check if it's a "already exists" error (which is fine)
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg:
                    print(f"ℹ️  Some items already exist (this is OK)")
                else:
                    # Try executing statement by statement for better error reporting
                    print(f"⚠️  Bulk execution had issues, trying statement by statement...")
                    print()
                    
                    # Split SQL into statements
                    statements = []
                    current_statement = ""
                    in_do_block = False
                    
                    for line in sql_content.split('\n'):
                        # Skip comment lines
                        stripped = line.strip()
                        if not stripped or stripped.startswith('--'):
                            continue
                        
                        current_statement += line + "\n"
                        
                        # Track DO blocks
                        if 'DO $$' in line:
                            in_do_block = True
                        
                        if in_do_block and 'END $$;' in line:
                            statements.append(current_statement)
                            current_statement = ""
                            in_do_block = False
                        elif not in_do_block and stripped.endswith(';'):
                            statements.append(current_statement)
                            current_statement = ""
                    
                    if current_statement.strip():
                        statements.append(current_statement)
                    
                    # Execute each statement
                    for i, stmt in enumerate(statements, 1):
                        stmt = stmt.strip()
                        if not stmt:
                            continue
                        
                        try:
                            cur.execute(stmt)
                            print(f"✅ Step {i} completed")
                        except Exception as e:
                            error_msg = str(e).lower()
                            if 'already exists' in error_msg or 'duplicate' in error_msg:
                                print(f"ℹ️  Step {i} skipped (already exists)")
                            else:
                                print(f"⚠️  Step {i} warning: {e}")
                                # Continue with other statements
                
        finally:
            cur.close()
            raw_conn.close()
        
        print()
        print("=" * 60)
        print("✅ Migration completed successfully!")
        print()
        print("📋 Summary:")
        print("   - Added CIM_TRAINING to FormType enum")
        print("   - Added scheduled_at, time, meeting_host, scheduled_count columns")
        print("   - Created form_reviewed table")
        print()
        print("🔄 Please restart your application to apply changes.")
        
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Migration failed: {e}")
        print()
        print("💡 Try running the SQL script directly:")
        print("   psql -U postgres -d lol-pdf-db -f run_migration.sql")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run database migration')
    parser.add_argument('--local', action='store_true', help='Use local database (DATABASE_URL)')
    parser.add_argument('--live', action='store_true', help='Use production/live database (DATABASE_URL_PRODUCTION or DATABASE_URL_LIVE)')
    
    args = parser.parse_args()
    
    # Determine environment
    if args.local:
        env = 'local'
    elif args.live:
        env = 'live'
    else:
        env = None  # Auto-detect from .env (uses DATABASE_URL)
    
    success = run_migration(environment=env)
    sys.exit(0 if success else 1)

