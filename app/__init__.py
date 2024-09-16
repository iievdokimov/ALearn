from flask import Flask
from config import Config
from app.extensions import db, login_manager
from flask_migrate import Migrate
import logging
from logging.handlers import SMTPHandler

from app.blueprints.main import main_bp
from app.blueprints.word_groups import word_groups_bp
from app.blueprints.tasks import tasks_bp
from app.blueprints.errors import errors_bp


# app = Flask(__name__) #, template_folder='../templates')
# app.config.from_object(Config)
# db = SQLAlchemy(app)
# migrate = Migrate(app, db)
# login = LoginManager(app)
# login.login_view = 'login'



# def create_app():
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'main.login'
migrate = Migrate(app, db)


# register Blueprints
app.register_blueprint(main_bp)
app.register_blueprint(word_groups_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(errors_bp)

# return app
from app.models import User, Word, WordGroup, sa, so

@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'User': User, 'Word': Word, 'WordGroup': WordGroup}
