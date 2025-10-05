#!/usr/bin/env python3
"""
Database fix script for SLGS OBU Voting System
This script will reset and recreate the database with the correct schema
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_database():
    """Reset and recreate database with correct schema"""
    print("🔧 SLGS OBU Voting System - Database Fix Tool")
    print("=" * 55)

    # Check if we're dealing with PostgreSQL or SQLite
    database_url = os.environ.get('DATABASE_URL')

    if database_url and 'postgresql' in database_url:
        print("📊 Detected PostgreSQL database")
        print("❌ Cannot automatically reset PostgreSQL database for safety reasons")
        print("\n💡 SOLUTION: Please run this SQL command in your PostgreSQL database:")
        print("   ALTER TABLE voter ADD COLUMN voting_token VARCHAR(16) UNIQUE;")
        print("\n   Or recreate the voter table with the updated schema.")
        return False
    else:
        print("📊 Using SQLite database (local development)")
        print("🔄 Resetting SQLite database...")

        # For SQLite, we can safely reset the database
        from app import create_app, db

        app = create_app()

        with app.app_context():
            try:
                # Drop all tables
                print("🗑️ Dropping existing tables...")
                db.drop_all()

                # Recreate all tables with correct schema
                print("🏗️ Creating tables with updated schema...")
                db.create_all()

                # Create positions
                print("📋 Creating SLGS OBU positions...")
                from app.models import Position

                positions_data = [
                    'President', 'Vice President', 'Secretary', 'Assistant Secretary',
                    'Treasurer', 'Assistant Treasurer', 'Social & Organizing Secretary',
                    'Assistant Social Secretary & Organizing Secretary', 'Publicity Secretary',
                    'Chairman Improvement Committee', 'Diaspora Coordinator', 'Chief Whip'
                ]

                for name in positions_data:
                    pos = Position(name=name, description=f'{name} of SLGS Old Boys Union')
                    db.session.add(pos)

                db.session.commit()

                print("✅ Database reset successful!")
                print(f"✅ Created {len(positions_data)} positions")

                # Verify the schema
                print("\n🔍 Verifying database schema...")
                try:
                    from app.models import Voter
                    test_voter = Voter.query.first()
                    if test_voter:
                        # Test if voting_token column exists
                        _ = test_voter.voting_token
                        print("✅ voting_token column is available")
                    else:
                        print("ℹ️ No voters found (this is normal for new database)")
                except AttributeError as e:
                    print(f"❌ Schema issue: {e}")
                    return False

                return True

            except Exception as e:
                print(f"❌ Database reset failed: {e}")
                import traceback
                traceback.print_exc()
                return False

if __name__ == "__main__":
    success = fix_database()

    if success:
        print("\n🎉 Database fix completed successfully!")
        print("🚀 You can now restart your application and it should work properly.")
    else:
        print("\n❌ Database fix failed!")
        print("Please check the error messages above.")