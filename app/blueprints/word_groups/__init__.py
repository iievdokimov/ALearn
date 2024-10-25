from flask import Blueprint

word_groups_bp = Blueprint('word_groups', __name__, template_folder='templates')

from . import routes
