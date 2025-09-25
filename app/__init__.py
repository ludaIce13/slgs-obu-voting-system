from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database configuration - prioritize PostgreSQL for production
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Render provides PostgreSQL via DATABASE_URL
        # Convert postgres:// to postgresql+psycopg:// for SQLAlchemy with psycopg3
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
        elif database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        print(f"Using PostgreSQL database: {database_url[:50]}...")
    else:
        # Check if we're in production environment
        is_production = os.environ.get('RENDER') or os.environ.get('PRODUCTION')
        if is_production:
            # In production without DATABASE_URL, connecting to localhost Postgres
            # will fail on Render (no local Postgres). Fall back to SQLite so the
            # site can still run, but instruct the admin to provision a proper
            # managed Postgres database and set DATABASE_URL in the service env.
            print("WARNING: Production environment detected but no DATABASE_URL found.")
            print("Falling back to SQLite (instance/voting.db). This is not suitable for a multi-instance production setup.")
            print("Please provision a managed PostgreSQL database on Render and add the DATABASE_URL environment variable to your service.")
            # Fallback to SQLite (allows the app to run but not recommended for production)
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/voting.db'
        else:
            # Fallback to SQLite for local development
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/voting.db'
            print("Using SQLite database (development mode)")

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,  # Verify connections before use
        'pool_recycle': 300,    # Recycle connections every 5 minutes
    }

    # Initialize extensions
    db.init_app(app)

    # If using SQLite fallback, ensure the instance folder exists and
    # create the database tables so the app doesn't error on first request.
    try:
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:'):
            # Ensure instance folder exists
            try:
                os.makedirs(app.instance_path, exist_ok=True)
            except Exception:
                # instance_path may already exist or permissions may vary
                pass

            # Create tables if they don't exist
            with app.app_context():
                db.create_all()
                print('SQLite database initialized (instance folder and tables created).')
    except Exception as e:
        # Print but don't crash the app; the health endpoint will surface DB errors
        print(f'Warning: failed to initialize SQLite DB automatically: {e}')

    return app