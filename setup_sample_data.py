#!/usr/bin/env python3
"""
Setup script to create sample positions and candidates for testing
"""

from app import create_app, db
from app.models import Position, Candidate

def setup_sample_data():
    app = create_app()

    with app.app_context():
        # Create database tables
        db.create_all()

        # Create positions
        positions_data = [
            {
                'name': 'President',
                'description': 'President of SLGS Old Boys Union'
            },
            {
                'name': 'Vice President',
                'description': 'Vice President of SLGS Old Boys Union'
            },
            {
                'name': 'Secretary',
                'description': 'Secretary of SLGS Old Boys Union'
            },
            {
                'name': 'Assistant Secretary',
                'description': 'Assistant Secretary of SLGS Old Boys Union'
            },
            {
                'name': 'Treasurer',
                'description': 'Treasurer of SLGS Old Boys Union'
            },
            {
                'name': 'Assistant Treasurer',
                'description': 'Assistant Treasurer of SLGS Old Boys Union'
            },
            {
                'name': 'Social & Organizing Secretary',
                'description': 'Social & Organizing Secretary of SLGS Old Boys Union'
            },
            {
                'name': 'Assistant Social Secretary & Organizing Secretary',
                'description': 'Assistant Social Secretary & Organizing Secretary of SLGS Old Boys Union'
            },
            {
                'name': 'Publicity Secretary',
                'description': 'Publicity Secretary of SLGS Old Boys Union'
            },
            {
                'name': 'Chairman Improvement Committee',
                'description': 'Chairman of the Improvement Committee'
            },
            {
                'name': 'Diaspora Coordinator',
                'description': 'Diaspora Coordinator of SLGS Old Boys Union'
            },
            {
                'name': 'Chief Whip',
                'description': 'Chief Whip of SLGS Old Boys Union'
            }
        ]

        # Create sample candidates for each position
        candidates_data = [
            # President candidates
            {'name': 'John Smith', 'bio': 'Experienced leader with 15 years in management', 'position_name': 'President'},
            {'name': 'Mary Johnson', 'bio': 'Community organizer and education advocate', 'position_name': 'President'},
            {'name': 'David Williams', 'bio': 'Former school administrator with strong organizational skills', 'position_name': 'President'},

            # Vice President candidates
            {'name': 'Sarah Brown', 'bio': 'Technology expert and project manager', 'position_name': 'Vice President'},
            {'name': 'Michael Davis', 'bio': 'Financial advisor with extensive experience', 'position_name': 'Vice President'},

            # Secretary candidates
            {'name': 'Emily Wilson', 'bio': 'Communications specialist and event coordinator', 'position_name': 'Secretary'},
            {'name': 'Robert Taylor', 'bio': 'Administrative professional with attention to detail', 'position_name': 'Secretary'},

            # Assistant Secretary candidates
            {'name': 'Lisa Garcia', 'bio': 'Executive assistant with strong organizational skills', 'position_name': 'Assistant Secretary'},
            {'name': 'Kevin Rodriguez', 'bio': 'Administrative coordinator with attention to detail', 'position_name': 'Assistant Secretary'},

            # Treasurer candidates
            {'name': 'Jennifer Anderson', 'bio': 'Certified accountant with financial expertise', 'position_name': 'Treasurer'},
            {'name': 'James Martinez', 'bio': 'Business analyst and financial planner', 'position_name': 'Treasurer'},

            # Assistant Treasurer candidates
            {'name': 'Michelle Lee', 'bio': 'Financial analyst with accounting background', 'position_name': 'Assistant Treasurer'},
            {'name': 'Thomas Walker', 'bio': 'Budget coordinator with financial management experience', 'position_name': 'Assistant Treasurer'},

            # Social & Organizing Secretary candidates
            {'name': 'Amanda Hall', 'bio': 'Event planner with community organizing experience', 'position_name': 'Social & Organizing Secretary'},
            {'name': 'Christopher Allen', 'bio': 'Social coordinator with networking expertise', 'position_name': 'Social & Organizing Secretary'},

            # Assistant Social Secretary & Organizing Secretary candidates
            {'name': 'Ashley Young', 'bio': 'Community outreach specialist with event coordination skills', 'position_name': 'Assistant Social Secretary & Organizing Secretary'},
            {'name': 'Matthew King', 'bio': 'Assistant event coordinator with social media experience', 'position_name': 'Assistant Social Secretary & Organizing Secretary'},

            # Publicity Secretary candidates
            {'name': 'Jessica Wright', 'bio': 'Marketing specialist with public relations expertise', 'position_name': 'Publicity Secretary'},
            {'name': 'Andrew Lopez', 'bio': 'Communications coordinator with media relations background', 'position_name': 'Publicity Secretary'},

            # Chairman Improvement Committee candidates
            {'name': 'Stephanie Hill', 'bio': 'Project manager with improvement initiative experience', 'position_name': 'Chairman Improvement Committee'},
            {'name': 'Daniel Green', 'bio': 'Committee leader with strategic planning skills', 'position_name': 'Chairman Improvement Committee'},

            # Diaspora Coordinator candidates
            {'name': 'Rachel Adams', 'bio': 'International relations specialist with diaspora experience', 'position_name': 'Diaspora Coordinator'},
            {'name': 'Brian Nelson', 'bio': 'Global coordinator with international networking skills', 'position_name': 'Diaspora Coordinator'},

            # Chief Whip candidates
            {'name': 'Nicole Baker', 'bio': 'Organizational strategist with leadership experience', 'position_name': 'Chief Whip'},
            {'name': 'Mark Carter', 'bio': 'Policy coordinator with strategic planning background', 'position_name': 'Chief Whip'}
        ]

        # Create positions
        for pos_data in positions_data:
            position = Position.query.filter_by(name=pos_data['name']).first()
            if not position:
                position = Position(**pos_data)
                db.session.add(position)

        db.session.commit()

        # Create candidates
        for cand_data in candidates_data:
            position = Position.query.filter_by(name=cand_data['position_name']).first()
            if position:
                candidate = Candidate.query.filter_by(name=cand_data['name']).first()
                if not candidate:
                    candidate = Candidate(
                        name=cand_data['name'],
                        bio=cand_data['bio'],
                        position_id=position.id
                    )
                    db.session.add(candidate)

        db.session.commit()

        print("Sample data created successfully!")
        print(f"Created {len(positions_data)} positions and {len(candidates_data)} candidates")

        # Display created positions
        positions = Position.query.all()
        print("\nPositions created:")
        for position in positions:
            print(f"  - {position.name}: {len(position.candidates)} candidates")

if __name__ == '__main__':
    setup_sample_data()