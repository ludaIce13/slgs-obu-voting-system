from . import db
from datetime import datetime
import secrets
import string

class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    voter_id = db.Column(db.String(20), unique=True, nullable=False)  # Increased from 8 to 20 to accommodate longer MemberIDs
    voting_token = db.Column(db.String(8), unique=True, nullable=False)
    has_voted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def generate_voter_id(self):
        """Generate a unique voter ID with OBUSLG prefix (same as MemberID if not already taken)"""
        # First try to use MemberID as VoterID if it's not already taken
        if hasattr(self, 'member_id') and self.member_id:
            if not Voter.query.filter_by(voter_id=self.member_id).first():
                self.voter_id = self.member_id
                return

        # Fallback to OBUSLG prefix with sequential number if MemberID is already used or not available
        while True:
            # Find the highest existing OBUSLG number to continue sequentially
            existing_obuslg = Voter.query.filter(Voter.voter_id.like('OBUSLG%')).all()
            if existing_obuslg:
                # Extract numbers from existing OBUSLG IDs and find the highest
                max_number = 0
                for voter in existing_obuslg:
                    try:
                        number = int(voter.voter_id[6:])  # Extract number after 'OBUSLG'
                        max_number = max(max_number, number)
                    except (ValueError, IndexError):
                        continue
                next_number = max_number + 1
            else:
                next_number = 1

            # Generate OBUSLG ID with 3-digit padding
            voter_id = f'OBUSLG{next_number:03d}'

            # Check if it already exists
            if not Voter.query.filter_by(voter_id=voter_id).first():
                self.voter_id = voter_id
                break
        return self.voter_id

    def generate_voting_token(self):
        """Generate a unique 8-digit numeric voting token"""
        while True:
            # Generate 8-digit numeric token
            voting_token = ''.join(secrets.choice(string.digits) for _ in range(8))
            # Check if it already exists
            if not Voter.query.filter_by(voting_token=voting_token).first():
                self.voting_token = voting_token
                break
        return self.voting_token

class Position(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # President, Vice President, Secretary, Treasurer
    description = db.Column(db.String(255))
    max_votes = db.Column(db.Integer, default=1)  # Usually 1 for each position
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to candidates
    candidates = db.relationship('Candidate', backref='position', lazy=True)

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    photo_url = db.Column(db.String(255))
    position_id = db.Column(db.Integer, db.ForeignKey('position.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to votes
    votes = db.relationship('Vote', backref='candidate', lazy=True)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.Integer, db.ForeignKey('voter.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    position_id = db.Column(db.Integer, db.ForeignKey('position.id'), nullable=False)
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Setting(db.Model):
    """Simple key/value store for runtime settings like voting state."""
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.String(255))

    def __repr__(self):
        return f"<Setting {self.key}={self.value}>"