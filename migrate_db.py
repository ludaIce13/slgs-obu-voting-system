#!/usr/bin/env python3
"""
Database migration script to add missing voting_token column to Voter table
Run this script to update the production database schema
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Voter
from sqlalchemy import text

def migrate_database():
    """Add missing voting_token column to Voter table"""
    app = create_app()

    with app.app_context():
        print("Starting database migration...")

        try:
            # Check if voting_token column exists
            try:
                # Try to access the voting_token column
                test_voter = Voter.query.first()
                if test_voter:
                    # Try to access the voting_token attribute
                    _ = test_voter.voting_token
                    print("✅ voting_token column already exists")
                    return True
            except AttributeError:
                pass
                # Column doesn't exist, need to add it
                print("❌ voting_token column missing, adding it...")

                # Use raw SQL to add the column
                if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql'):
                    # PostgreSQL migration
                    with db.engine.connect() as conn:
                        # Add voting_token column
                        conn.execute(text("ALTER TABLE voter ADD COLUMN voting_token VARCHAR(16) UNIQUE"))
                        conn.commit()
                        print("✅ Added voting_token column to PostgreSQL database")
                elif app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
                    # SQLite migration (recreate table)
                    print("⚠️ SQLite detected - this should not happen in production")
                    print("For SQLite, please delete the database file and restart the application")
                else:
                    print("❌ Unsupported database type")
                    return False

                # Verify the column was added
                try:
                    test_voter = Voter.query.first()
                    if test_voter:
                        _ = test_voter.voting_token
                        print("✅ Migration successful - voting_token column is now available")
                        return True
                except AttributeError:
                    print("❌ Migration failed - voting_token column still not accessible")
                    return False
            except Exception as e:
                print(f"❌ Error checking existing column: {e}")
                return False

        except Exception as e:
            print(f"❌ Migration error: {e}")
            import traceback
            traceback.print_exc()
            return False

def check_database_schema():
    """Check current database schema"""
    app = create_app()

    with app.app_context():
        print("\nChecking database schema...")

        try:
            # Check database type
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            if db_uri.startswith('postgresql'):
                print(f"📊 Database type: PostgreSQL")
            elif db_uri.startswith('sqlite'):
                print(f"📊 Database type: SQLite")
            else:
                print(f"📊 Database type: Unknown")

            # Check voter table columns
            print("\n🔍 Checking voter table structure...")
            with db.engine.connect() as conn:
                if db_uri.startswith('postgresql'):
                    # PostgreSQL schema query
                    result = conn.execute(text("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_name = 'voter'
                        ORDER BY ordinal_position
                    """))
                    columns = result.fetchall()
                    print("Columns in voter table:")
                    for col in columns:
                        print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
                else:
                    print("Schema check not implemented for this database type")

            # Check if voting_token column exists by trying to query it
            try:
                result = db.session.execute(text("SELECT voting_token FROM voter LIMIT 1"))
                print("✅ voting_token column exists and is accessible")
            except Exception as e:
                print(f"❌ voting_token column issue: {e}")

        except Exception as e:
            print(f"❌ Schema check error: {e}")

if __name__ == "__main__":
    print("SLGS OBU Voting System - Database Migration Tool")
    print("=" * 50)

    # First check the current schema
    check_database_schema()

    print("\n" + "=" * 50)

    # Then run the migration
    success = migrate_database()

    if success:
        print("\n🎉 Migration completed successfully!")
        print("The voting system should now work properly.")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above and fix manually.")