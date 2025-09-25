from app import create_app, db
from app.models import Voter, Candidate, Vote, Position
from app.routes import main, admin

app = create_app()

# Register blueprints
app.register_blueprint(main)
app.register_blueprint(admin)

@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print("Database initialized successfully!")

@app.cli.command()
def create_admin():
    """Create initial admin user (for development only)."""
    from werkzeug.security import generate_password_hash

    # This is a placeholder - in production, use proper admin authentication
    print("Admin token:", app.config['SECRET_KEY'][:32])
    print("Use this token in Authorization header: Bearer " + app.config['SECRET_KEY'][:32])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)

# Export app for Gunicorn/WGSI servers
app = app