from flask import Blueprint

books_bp = Blueprint('books', __name__)

from app.books import routes
