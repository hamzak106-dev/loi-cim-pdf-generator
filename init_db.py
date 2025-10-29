#!/usr/bin/env python3
"""
Database initialization script for Business Acquisition PDF Generator
Run this script to create the database tables.
"""

from db.database import DatabaseManager, get_db_info
from config import settings

def init_database():
    """Initialize the database with all tables"""
    try:
        # Check database connection first
        is_connected, message = DatabaseManager.check_connection()
        if not is_connected:
            print(f"❌ {message}")
            return False
        
        # Create all tables
        DatabaseManager.init_db()
        print("📊 Tables created:")
        print("   - business_acquisitions")
        
        # Show database info
        db_info = get_db_info()
        print(f"\n📍 Database URL: {db_info['database_url']}")
        
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Initializing Business Acquisition PDF Generator Database...")
    print("=" * 60)
    
    if init_database():
        print("\n✨ Database initialization completed!")
        print("You can now run the application with:")
        print("   python app.py")
        print("   or")
        print("   python run.py")
    else:
        print("\n💥 Database initialization failed!")
        print("Please check your PostgreSQL connection and try again.")
