"""
Authentication Service
Handles user authentication and session management
"""
from werkzeug.security import check_password_hash, generate_password_hash
from db import User, SessionLocal, AppSetting
from typing import Optional, Tuple


class AuthService:
    """Handle authentication operations"""
    
    @staticmethod
    def authenticate_user(email: str, password: str) -> Tuple[bool, Optional[User], str]:
        """
        Authenticate a user with email and password
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            Tuple of (success: bool, user: User or None, message: str)
        """
        db = SessionLocal()
        try:
            # Find user by email
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                return False, None, "Invalid email or password"
            
            # Check if account is active
            if not user.is_active:
                return False, None, "Account is inactive"
            
            # Verify password
            if not check_password_hash(user.password, password):
                return False, None, "Invalid email or password"
            
            return True, user, "Login successful"
            
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False, None, "Authentication failed"
        finally:
            db.close()

    # ===== Super Password Management =====
    # Store super password as plaintext (admin-only visibility). Hash is no longer used.
    SUPER_PASSWORD_KEY = 'super_password_plain'

    @staticmethod
    def set_super_password(new_password: str) -> Tuple[bool, str]:
        """Store the super password as plaintext in AppSetting."""
        db = SessionLocal()
        try:
            record = db.query(AppSetting).filter(AppSetting.key == AuthService.SUPER_PASSWORD_KEY).first()
            if record:
                record.value = new_password
            else:
                record = AppSetting(key=AuthService.SUPER_PASSWORD_KEY, value=new_password)
                db.add(record)
            db.commit()
            return True, 'Super password updated'
        except Exception as e:
            db.rollback()
            print(f"❌ Error setting super password: {e}")
            return False, f"Failed to set super password: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def verify_super_password(password: str) -> bool:
        """Verify the super password. Prefer plaintext; fallback to legacy hash and migrate on success."""
        if not password:
            return False
        db = SessionLocal()
        try:
            # 1) Prefer plaintext key
            plain = db.query(AppSetting).filter(AppSetting.key == AuthService.SUPER_PASSWORD_KEY).first()
            if plain and plain.value:
                return plain.value == password

            # 2) Fallback: legacy hashed key
            legacy = db.query(AppSetting).filter(AppSetting.key == 'super_password_hash').first()
            if legacy and legacy.value and check_password_hash(legacy.value, password):
                # Migrate: store plaintext for future checks
                existing_plain = db.query(AppSetting).filter(AppSetting.key == AuthService.SUPER_PASSWORD_KEY).first()
                if existing_plain:
                    existing_plain.value = password
                else:
                    db.add(AppSetting(key=AuthService.SUPER_PASSWORD_KEY, value=password))
                db.commit()
                return True

            return False
        except Exception as e:
            print(f"❌ Error verifying super password: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    @staticmethod
    def has_super_password() -> bool:
        db = SessionLocal()
        try:
            # Consider either plaintext or legacy hashed key present
            has_plain = db.query(AppSetting).filter(AppSetting.key == AuthService.SUPER_PASSWORD_KEY).first() is not None
            if has_plain:
                return True
            has_legacy = db.query(AppSetting).filter(AppSetting.key == 'super_password_hash').first() is not None
            return has_legacy
        finally:
            db.close()

    @staticmethod
    def get_super_password_hash() -> Optional[str]:
        """Compatibility getter: returns the stored super password (plaintext)."""
        db = SessionLocal()
        try:
            record = db.query(AppSetting).filter(AppSetting.key == AuthService.SUPER_PASSWORD_KEY).first()
            return record.value if record else None
        except Exception as e:
            print(f"❌ Error fetching super password: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    def get_super_password_plain() -> Optional[str]:
        """Fetch the stored super password plaintext from AppSetting, or None if not set."""
        db = SessionLocal()
        try:
            record = db.query(AppSetting).filter(AppSetting.key == AuthService.SUPER_PASSWORD_KEY).first()
            return record.value if record else None
        except Exception as e:
            print(f"❌ Error fetching super password plaintext: {e}")
            return None
        finally:
            db.close()

    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID"""
        db = SessionLocal()
        try:
            return db.query(User).filter(User.id == user_id).first()
        finally:
            db.close()
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email"""
        db = SessionLocal()
        try:
            return db.query(User).filter(User.email == email).first()
        finally:
            db.close()
    
    @staticmethod
    def create_user(name: str, email: str, password: str, user_type: str = 'user') -> Tuple[bool, Optional[User], str]:
        """
        Create a new user
        
        Args:
            name: User's full name
            email: User's email address
            password: Plain text password (will be hashed)
            user_type: 'user' or 'admin'
            
        Returns:
            Tuple of (success: bool, user: User or None, message: str)
        """
        db = SessionLocal()
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                return False, None, "User with this email already exists"
            
            # Hash password
            hashed_password = generate_password_hash(password)
            
            # Create user
            user = User(
                name=name,
                email=email,
                password=hashed_password,
                user_type=user_type,
                is_active=True
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return True, user, "User created successfully"
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error creating user: {e}")
            return False, None, f"Failed to create user: {str(e)}"
        finally:
            db.close()
    
    @staticmethod
    def reset_user_password(user_id: int, new_password: str = None) -> Tuple[bool, Optional[str], str]:
        """
        Reset a user's password
        
        Args:
            user_id: User ID
            new_password: New password (if None, generates a secure password)
            
        Returns:
            Tuple of (success: bool, password: str or None, message: str)
        """
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, None, "User not found"
            
            # Generate password if not provided
            if not new_password:
                import secrets
                import string
                alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
                new_password = ''.join(secrets.choice(alphabet) for i in range(12))
            
            # Hash and update password
            hashed_password = generate_password_hash(new_password)
            user.password = hashed_password
            db.commit()
            
            return True, new_password, "Password reset successfully"
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error resetting password: {e}")
            return False, None, f"Failed to reset password: {str(e)}"
        finally:
            db.close()


# Singleton instance
auth_service = AuthService()
