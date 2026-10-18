import os
import logging
from app import create_app

logger = logging.getLogger(__name__)

# Vercel Serverless Function entry point
app = create_app(os.environ.get('FLASK_ENV', 'production'))

# Automatically initialize tables and seed demonstration data if needed
with app.app_context():
    try:
        from app.seed_util import seed_database
        seed_database()
        logger.info("Vercel database initialization and seed check completed.")
    except Exception as e:
        logger.warning(f"Vercel auto-init skipped or encountered: {e}")
