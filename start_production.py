#!/usr/bin/env python3
"""
SLGS OBU Voting System - Production Startup Script
"""

import os
from app import create_app, db

def start_production():
    """Start the application in production mode"""
    print("🚀 Starting SLGS OBU Voting System in Production Mode")
    print("=" * 60)

    app = create_app()

    # Verify database connection
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database connection verified")

            # Show system status
            from app.models import Voter, Position, Candidate
            voters = Voter.query.count()
            positions = Position.query.count()
            candidates = Candidate.query.count()

            print(f"📊 System Status: {voters} voters, {positions} positions, {candidates} candidates")

        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return

    # Start the server
    print("🌐 Starting Gunicorn server...")
    print("📝 Admin Token:", os.environ.get('ADMIN_TOKEN', 'admin-token'))
    print("🔗 Access URLs will be provided by your hosting platform")

    # Use Gunicorn for production
    os.system("gunicorn run:app --bind 0.0.0.0:$PORT")

if __name__ == '__main__':
    start_production()