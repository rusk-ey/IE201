from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'az1'  # Replace with a secure key
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database/app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    from .routes import main
    app.register_blueprint(main)

    from .models import db, initialize_database
    db.init_app(app)
    initialize_database(app)

    return app