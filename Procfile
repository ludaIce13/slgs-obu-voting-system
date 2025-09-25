web: gunicorn wsgi:app --bind 0.0.0.0:$PORT
release: python -c "from app import create_app, db; app = create_app(); db.create_all(); print('Database initialized')"