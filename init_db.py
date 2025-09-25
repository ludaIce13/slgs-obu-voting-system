#!/usr/bin/env python3
"""
Database initialization script for production deployment
"""

import os
import sys

def init_database():
    """Initialize database and populate sample data"""
    try:
        print("Initializing database...")

        # Import after potential path setup
        from app import create_app, db
        from app.models import Voter, Position, Candidate, Vote

        app = create_app()

        with app.app_context():
            # Create all tables
            db.create_all()
            print("Database tables created successfully")

            # Check if we need to populate sample data
            position_count = Position.query.count()
            if position_count == 0:
                print("Populating sample data...")
                try:
                    # Import and run setup script
                    import setup_sample_data
                    print("Sample data populated successfully")
                except Exception as e:
                    print(f"Warning: Could not populate sample data: {e}")
            else:
                print(f"Database already has {position_count} positions")

            print("Database initialization completed successfully")
            return True

    except Exception as e:
        print(f"Database initialization failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)