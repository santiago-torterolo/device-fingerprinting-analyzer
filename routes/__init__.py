"""
Routes package initialization.
Blueprint registration for views and API endpoints.
"""

from flask import Blueprint

views_bp = Blueprint('views', __name__)
api_bp = Blueprint('api', __name__)
