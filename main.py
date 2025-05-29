"""
Main entry point for the Flask application.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # DON'T CHANGE THIS !!!

from flask import Flask, render_template, redirect, url_for, session, request, flash
from flask_wtf.csrf import CSRFProtect
from src.models.models import db
from src.routes import auth_bp, teacher_bp, admin_bp, api_bp
import os

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure the app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_development_only')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'mydb')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    csrf = CSRFProtect(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    
    # Create upload directories if they don't exist
    os.makedirs('src/static/uploads/briefs', exist_ok=True)
    os.makedirs('src/static/uploads/rubrics', exist_ok=True)
    os.makedirs('src/static/uploads/student_work', exist_ok=True)
    os.makedirs('src/static/uploads/profile_pictures', exist_ok=True)
    
    # Root route
    @app.route('/')
    def index():
        if 'user_id' in session:
            if session.get('role') == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('teacher.dashboard'))
        return redirect(url_for('auth.login'))
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
