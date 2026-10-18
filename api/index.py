import os
from app import create_app

# Vercel Serverless Function entry point
app = create_app(os.environ.get('FLASK_ENV', 'production'))
