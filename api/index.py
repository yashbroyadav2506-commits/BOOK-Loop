import os
from app import create_app

# Vercel Python Serverless entry point
app = create_app(os.environ.get('FLASK_ENV', 'production'))

# Expose app for WSGI handler
