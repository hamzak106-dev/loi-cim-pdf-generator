#!/usr/bin/env python3
"""
Seed file to create demo admin users
Run this file to populate the database with initial admin accounts
"""
from db import SessionLocal, User
from werkzeug.security import generate_password_hash

def seed_admin_users():
    """Create demo admin users"""
    db = SessionLocal()
    
    try:
        # Check if admin users already exist
        existing_admins = db.query(User).filter(User.user_type == 'admin').count()
        
        if existing_admins > 0:
            print(f"ℹ️  {existing_admins} admin user(s) already exist. Skipping seed.")
            return
        
        # Demo admin users
        admin_users = [
            {
                'name': 'Admin User',
                'email': 'admin@example.com',
                'password': 'admin123',  # Change this in production!
                'user_type': 'admin'
            },
            {
                'name': 'John Admin',
                'email': 'john.admin@example.com',
                'password': 'admin123',  # Change this in production!
                'user_type': 'admin'
            },
            {
                'name': 'Sarah Manager',
                'email': 'sarah.manager@example.com',
                'password': 'admin123',  # Change this in production!
                'user_type': 'admin'
            }
        ]
        
        print("🌱 Seeding admin users...")
        
        for user_data in admin_users:
            # Hash the password
            hashed_password = generate_password_hash(user_data['password'])
            
            # Create user
            user = User(
                name=user_data['name'],
                email=user_data['email'],
                password=hashed_password,
                user_type=user_data['user_type'],
                is_active=True
            )
            
            db.add(user)
            print(f"  ✅ Created admin: {user_data['name']} ({user_data['email']})")
        
        db.commit()
        print("\n🎉 Admin users seeded successfully!")
        print("\n📋 Login Credentials:")
        print("=" * 50)
        for user_data in admin_users:
            print(f"Email: {user_data['email']}")
            print(f"Password: {user_data['password']}")
            print("-" * 50)
        print("\n⚠️  IMPORTANT: Change these passwords in production!")
        
    except Exception as e:
        print(f"❌ Error seeding admin users: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting admin user seed...")
    seed_admin_users()
