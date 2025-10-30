#!/usr/bin/env python3
"""
Database Migration Management CLI
One command to initialize Alembic and create/apply migrations
"""
import sys
import argparse
from db import alembic_manager


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Database Migration Manager - Auto-initialize and migrate with Alembic"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Auto-migrate command (does everything)
    auto_parser = subparsers.add_parser(
        'auto',
        help='Auto-initialize Alembic (if needed) and create/apply migrations'
    )
    auto_parser.add_argument(
        '-m', '--message',
        default='auto migration',
        help='Migration message (default: "auto migration")'
    )
    
    # Initialize command
    subparsers.add_parser(
        'init',
        help='Initialize Alembic in the project'
    )
    
    # Create migration command
    create_parser = subparsers.add_parser(
        'create',
        help='Create a new migration'
    )
    create_parser.add_argument(
        '-m', '--message',
        required=True,
        help='Migration message'
    )
    
    # Upgrade command
    upgrade_parser = subparsers.add_parser(
        'upgrade',
        help='Apply migrations'
    )
    upgrade_parser.add_argument(
        'revision',
        nargs='?',
        default='head',
        help='Target revision (default: head)'
    )
    
    # Downgrade command
    downgrade_parser = subparsers.add_parser(
        'downgrade',
        help='Rollback migrations'
    )
    downgrade_parser.add_argument(
        'revision',
        nargs='?',
        default='-1',
        help='Target revision (default: -1)'
    )
    
    # Current command
    subparsers.add_parser(
        'current',
        help='Show current migration revision'
    )
    
    # History command
    subparsers.add_parser(
        'history',
        help='Show migration history'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Execute command
    print("🔧 Database Migration Manager")
    print("=" * 60)
    
    try:
        if args.command == 'auto':
            # One command to rule them all
            success = alembic_manager.auto_migrate(args.message)
            sys.exit(0 if success else 1)
        
        elif args.command == 'init':
            success = alembic_manager.initialize()
            sys.exit(0 if success else 1)
        
        elif args.command == 'create':
            success = alembic_manager.create_migration(args.message)
            sys.exit(0 if success else 1)
        
        elif args.command == 'upgrade':
            success = alembic_manager.upgrade(args.revision)
            sys.exit(0 if success else 1)
        
        elif args.command == 'downgrade':
            success = alembic_manager.downgrade(args.revision)
            sys.exit(0 if success else 1)
        
        elif args.command == 'current':
            alembic_manager.current()
            sys.exit(0)
        
        elif args.command == 'history':
            alembic_manager.history()
            sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
