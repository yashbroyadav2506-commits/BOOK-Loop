from flask import Blueprint

exchanges_bp = Blueprint('exchanges', __name__, url_prefix='/exchanges')

from app.exchanges import routes
