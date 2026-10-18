import os
from app import create_app

# WSGI application callable for production servers (Gunicorn, uWSGI, Vercel)
app = create_app(os.environ.get('FLASK_ENV', 'production'))

if __name__ == "__main__":
    app.run()
