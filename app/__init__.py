import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Get the absolute path to the database file
    base_dir = os.path.abspath(os.path.dirname(__file__))  # Gets the absolute path to the folder 'app/'
    db_path = os.path.join(base_dir, "database", "app.db")
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    # Disable SQLAlchemy track modifications (it's deprecated)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Example: Import models
    from app.models import StudentProgress

    # Example: import routes and register blueprints
    from app.routes import main
    app.register_blueprint(main)

    return app