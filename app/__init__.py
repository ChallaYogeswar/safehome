from flask import Flask, send_from_directory, redirect, url_for
from flask_socketio import SocketIO
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_cors import CORS
from config import config
from app.models import db, User
from app.services.scheduler import scheduler
from app.services.metrics import metrics_endpoint
import logging
from logging.handlers import RotatingFileHandler
import os

socketio = SocketIO()
login_manager = LoginManager()
migrate = Migrate()
jwt = JWTManager()
mail = Mail()

def init_firebase(app):
    """Initialize Firebase Admin SDK (graceful fallback if not configured)"""
    try:
        import firebase_admin
        from firebase_admin import credentials
        
        cred_path = app.config.get('FIREBASE_CREDENTIALS_PATH')
        db_url = app.config.get('FIREBASE_DATABASE_URL')
        storage_bucket = app.config.get('FIREBASE_STORAGE_BUCKET')
        
        if not cred_path or not os.path.exists(cred_path):
            app.logger.warning("⚠️ Firebase credentials not found — Firebase features disabled")
            app.config['FIREBASE_ENABLED'] = False
            return
        
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': db_url,
                'storageBucket': storage_bucket
            })
            app.logger.info("✅ Firebase initialized successfully")
        
        app.config['FIREBASE_ENABLED'] = True
        
    except Exception as e:
        app.logger.error(f"❌ Firebase initialization failed: {e}")
        app.config['FIREBASE_ENABLED'] = False

def create_app(config_name='default'):
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    # Force threading async mode to avoid eventlet SSL compatibility issues on some Windows/Python builds
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
    login_manager.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app)
    
    # Initialize Firebase
    init_firebase(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    from app.routes import auth, dashboard, camera, alerts, automation, analytics, api_docs, face
    from app.routes import entries, notifications
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(camera.bp)
    app.register_blueprint(alerts.bp)
    app.register_blueprint(automation.bp)
    app.register_blueprint(analytics.bp)
    app.register_blueprint(face.bp)
    app.register_blueprint(entries.bp)
    app.register_blueprint(notifications.bp)
    app.register_blueprint(api_docs.api_docs_bp)
    app.register_blueprint(api_docs.swaggerui_blueprint, url_prefix=api_docs.SWAGGER_URL)
    
    @app.route('/')
    def root():
        """Root route - redirect to dashboard if logged in, else to login"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))
    
    @app.route('/metrics')
    def metrics():
        return metrics_endpoint()
    
    # Security Headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=*, payment=()'
        if app.config.get('SESSION_COOKIE_SECURE'):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    # Serve static files explicitly
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory(app.static_folder, filename)
    
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/safehome.log', maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('SafeHome startup')
    
    with app.app_context():
        db.create_all()
        if not app.config.get('TESTING', False):
            scheduler.init_app(app)
    
    return app

