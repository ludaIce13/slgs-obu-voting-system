#!/usr/bin/env python3
"""
Test script to verify positions are created in the database
Run this script to check and create positions if needed
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Position

def test_positions():
    """Test and create positions if needed"""
    app = create_app()

    with app.app_context():
        print("Checking database for positions...")

        # Check current positions
        positions = Position.query.all()
        print(f"Found {len(positions)} positions in database")

        if positions:
            print("Current positions:")
            for pos in positions:
                print(f"  - {pos.name} (ID: {pos.id})")
        else:
            print("No positions found. Creating SLGS OBU positions...")

            # Create all 12 positions
            positions_data = [
                'President', 'Vice President', 'Secretary', 'Assistant Secretary',
                'Treasurer', 'Assistant Treasurer', 'Social & Organizing Secretary',
                'Assistant Social Secretary & Organizing Secretary', 'Publicity Secretary',
                'Chairman Improvement Committee', 'Diaspora Coordinator', 'Chief Whip'
            ]

            created_count = 0
            for name in positions_data:
                existing = Position.query.filter_by(name=name).first()
                if not existing:
                    pos = Position(name=name, description=f'{name} of SLGS Old Boys Union')
                    db.session.add(pos)
                    created_count += 1
                    print(f'Created position: {name}')
                else:
                    print(f'Position already exists: {name}')

            if created_count > 0:
                db.session.commit()
                print(f"\n✅ Successfully created {created_count} positions")

            # Verify positions were created
            positions = Position.query.all()
            print(f"\n✅ Total positions now: {len(positions)}")
            for pos in positions:
                print(f"  - {pos.name} (ID: {pos.id})")

if __name__ == "__main__":
    test_positions()