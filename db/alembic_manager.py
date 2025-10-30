"""
Alembic Migration Manager
Auto-initializes Alembic and creates migrations with a single command
"""
import os
import subprocess
from pathlib import Path
from alembic.config import Config
from alembic import command
from config import settings


class AlembicManager:
    """Manages Alembic migrations automatically"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.alembic_dir = self.project_root / "alembic"
        self.alembic_ini = self.project_root / "alembic.ini"
    
    def is_initialized(self) -> bool:
        """Check if Alembic is already initialized"""
        return self.alembic_dir.exists() and self.alembic_ini.exists()
    
    def initialize(self):
        """Initialize Alembic in the project"""
        if self.is_initialized():
            print("✅ Alembic already initialized")
            return True
        
        print("🔧 Initializing Alembic...")
        try:
            # Run alembic init command
            subprocess.run(
                ["alembic", "init", "alembic"],
                cwd=str(self.project_root),
                check=True,
                capture_output=True
            )
            
            # Update alembic.ini with database URL
            self._update_alembic_ini()
            
            # Update env.py to use our models
            self._update_env_py()
            
            print("✅ Alembic initialized successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to initialize Alembic: {e}")
            return False
    
    def _update_alembic_ini(self):
        """Update alembic.ini with database URL from settings"""
        if not self.alembic_ini.exists():
            return
        
        with open(self.alembic_ini, 'r') as f:
            content = f.read()
        
        # Replace sqlalchemy.url with our DATABASE_URL
        content = content.replace(
            'sqlalchemy.url = driver://user:pass@localhost/dbname',
            f'sqlalchemy.url = {settings.DATABASE_URL}'
        )
        
        with open(self.alembic_ini, 'w') as f:
            f.write(content)
        
        print("✅ Updated alembic.ini with database URL")
    
    def _update_env_py(self):
        """Update env.py to import our models"""
        env_py = self.alembic_dir / "env.py"
        if not env_py.exists():
            return
        
        with open(env_py, 'r') as f:
            content = f.read()
        
        # Add imports for our models
        import_block = """
# Import your models here for autogenerate support
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import Base
from db.models import Form, FormType, LOIQuestion, CIMQuestion, User
"""
        
        # Insert after the config import
        if "from db.database import Base" not in content:
            content = content.replace(
                "# add your model's MetaData object here",
                f"{import_block}\n# add your model's MetaData object here"
            )
            
            # Update target_metadata
            content = content.replace(
                "target_metadata = None",
                "target_metadata = Base.metadata"
            )
        
        with open(env_py, 'w') as f:
            f.write(content)
        
        print("✅ Updated env.py with model imports")
    
    def create_migration(self, message: str = "auto migration"):
        """Create a new migration"""
        if not self.is_initialized():
            print("⚠️  Alembic not initialized, initializing now...")
            if not self.initialize():
                return False
        
        print(f"📝 Creating migration: {message}")
        try:
            alembic_cfg = Config(str(self.alembic_ini))
            command.revision(
                alembic_cfg,
                autogenerate=True,
                message=message
            )
            print("✅ Migration created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create migration: {e}")
            return False
    
    def upgrade(self, revision: str = "head"):
        """Apply migrations"""
        if not self.is_initialized():
            print("❌ Alembic not initialized. Run initialize first.")
            return False
        
        print(f"⬆️  Upgrading database to: {revision}")
        try:
            alembic_cfg = Config(str(self.alembic_ini))
            command.upgrade(alembic_cfg, revision)
            print("✅ Database upgraded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to upgrade database: {e}")
            return False
    
    def downgrade(self, revision: str = "-1"):
        """Rollback migrations"""
        if not self.is_initialized():
            print("❌ Alembic not initialized")
            return False
        
        print(f"⬇️  Downgrading database to: {revision}")
        try:
            alembic_cfg = Config(str(self.alembic_ini))
            command.downgrade(alembic_cfg, revision)
            print("✅ Database downgraded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to downgrade database: {e}")
            return False
    
    def current(self):
        """Show current migration revision"""
        if not self.is_initialized():
            print("❌ Alembic not initialized")
            return
        
        try:
            alembic_cfg = Config(str(self.alembic_ini))
            command.current(alembic_cfg)
        except Exception as e:
            print(f"❌ Failed to get current revision: {e}")
    
    def history(self):
        """Show migration history"""
        if not self.is_initialized():
            print("❌ Alembic not initialized")
            return
        
        try:
            alembic_cfg = Config(str(self.alembic_ini))
            command.history(alembic_cfg)
        except Exception as e:
            print(f"❌ Failed to get history: {e}")
    
    def auto_migrate(self, message: str = "auto migration"):
        """
        One command to rule them all:
        - Initialize Alembic if not initialized
        - Create migration if schema changed
        - Apply migration automatically
        """
        print("🚀 Starting auto-migration...")
        print("=" * 60)
        
        # Step 1: Initialize if needed
        if not self.is_initialized():
            if not self.initialize():
                return False
        
        # Step 2: Create migration
        if not self.create_migration(message):
            return False
        
        # Step 3: Apply migration
        if not self.upgrade():
            return False
        
        print("=" * 60)
        print("🎉 Auto-migration completed successfully!")
        return True


# Singleton instance
alembic_manager = AlembicManager()
