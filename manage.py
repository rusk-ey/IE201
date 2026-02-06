from flask.cli import FlaskGroup
from flask_migrate import Migrate
from app import create_app, db  # Import app and SQLAlchemy instance

# Create the Flask application instance
app = create_app()

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Create a CLI group to include the migrate commands
cli = FlaskGroup(create_app=lambda: app)  # Pass the app factory

if __name__ == "__main__":
    # Call Flask CLI commands
    cli()