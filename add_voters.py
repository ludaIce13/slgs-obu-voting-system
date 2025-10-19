#!/usr/bin/env python3
"""
Emergency Voter Addition Script for SLGS OBU Voting System
Run this script to add voters directly to the database for presentation
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Voter

def add_emergency_voters():
    """Add voters directly to database for presentation"""

    app = create_app()
    with app.app_context():
        try:
            print("EMERGENCY: Adding voters for presentation...")

            # Clear existing voters to start fresh
            existing_count = Voter.query.count()
            if existing_count > 0:
                Voter.query.delete()
                print(f"Cleared {existing_count} existing voters")

            # Add presentation voters (without phone_number for compatibility)
            presentation_voters = [
                ('OBUSLG001', 'John Smith'),
                ('OBUSLG002', 'Mary Johnson'),
                ('OBUSLG003', 'David Williams'),
                ('OBUSLG004', 'Sarah Brown'),
                ('OBUSLG005', 'Michael Davis'),
                ('OBUSLG006', 'Emily Wilson'),
                ('OBUSLG007', 'Robert Taylor'),
                ('OBUSLG008', 'Jennifer Anderson'),
            ]

            added_count = 0
            for member_id, full_name in presentation_voters:
                voter = Voter(
                    member_id=member_id,
                    full_name=full_name,
                    voter_id=member_id,  # Use MemberID as VoterID
                    voting_token='12345678'  # Simple token for presentation
                )

                # Generate credentials
                voter.generate_voter_id()
                voter.generate_voting_token()

                db.session.add(voter)
                added_count += 1
                print(f"Added: {member_id} - {full_name}")

            db.session.commit()
            print(f"\nSuccessfully added {added_count} voters to database!")

            # Show voters for presentation
            print("\nVoters for your presentation:")
            voters = Voter.query.all()
            for voter in voters:
                print(f"  Member ID: {voter.member_id}")
                print(f"  Name: {voter.full_name}")
                print(f"  Voter ID: {voter.voter_id}")
                print(f"  Voting Token: {voter.voting_token}")
                print("  ---")

            return True

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = add_emergency_voters()

    if success:
        print("\nSUCCESS! Voters added successfully!")
        print("Restart your Render app to see the voters.")
        print("Go to: https://slgs-obu-voting-system.onrender.com/admin")
    else:
        print("\nFAILED! Please check the error messages above.")