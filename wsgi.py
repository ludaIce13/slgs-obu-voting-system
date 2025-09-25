"""
WSGI entry point for production deployment
This file is used by Gunicorn and other WSGI servers
"""

from run import app

if __name__ == '__main__':
    app.run()