from . import db
from datetime import datetime
import secrets
import string

class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    graduation_year = db.Column(db.Integer, nullable=False)
    voter_id = db.Column(db.String(8), unique=True, nullable=False)
    has_voted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def generate_voter_id(self):
        """Generate a unique 8-digit numeric voter ID"""
        while True:
            # Generate 8-digit numeric ID
            voter_id = ''.join(secrets.choice(string.digits) for _ in range(8))
            # Check if it already exists
            if not Voter.query.filter_by(voter_id=voter_id).first():
                self.voter_id = voter_id
                break
        return self.voter_id

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