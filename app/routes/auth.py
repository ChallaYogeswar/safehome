from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, SecurityLog
from app.services.auth_service import AuthService
from app.utils.validators import validate_email, validate_password
from datetime import datetime, timedelta, timezone
import pyotp
import qrcode
import io
import base64

bp = Blueprint('auth', __name__, url_prefix='/auth')
auth_service = AuthService()

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('auth/register.html')
        
        if not validate_email(email):
            flash('Invalid email address', 'error')
            return render_template('auth/register.html')
        
        if not validate_password(password):
            flash('Password must be at least 8 characters with uppercase, lowercase, number and special character', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        user.is_verified = True
        
        db.session.add(user)
        db.session.commit()
        
        auth_service.log_event(user.id, 'user_registered', 'User registered successfully', request)
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        mfa_token = request.form.get('mfa_token', '').strip()
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            auth_service.log_event(None, 'login_failed', f'Login attempt with non-existent email: {email}', request)
            flash('Invalid email or password', 'error')
            return render_template('auth/login.html')
        
        if user.locked_until:
            current_time = datetime.now(timezone.utc)
            lock_time = user.locked_until
            # Make lock_time timezone-aware if it isn't already
            if lock_time.tzinfo is None:
                lock_time = lock_time.replace(tzinfo=timezone.utc)
            if lock_time > current_time:
                auth_service.log_event(user.id, 'login_blocked', 'Login attempt on locked account', request)
                flash('Account is locked. Please try again later.', 'error')
                return render_template('auth/login.html')
        
        if not user.check_password(password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
                auth_service.log_event(user.id, 'account_locked', 'Account locked due to multiple failed attempts', request)
            db.session.commit()
            
            auth_service.log_event(user.id, 'login_failed', 'Invalid password', request)
            flash('Invalid email or password', 'error')
            return render_template('auth/login.html')
        
        if user.mfa_enabled:
            if not mfa_token:
                return render_template('auth/login.html', require_mfa=True, email=email)
            
            if not user.verify_mfa_token(mfa_token):
                auth_service.log_event(user.id, 'mfa_failed', 'Invalid MFA token', request)
                flash('Invalid MFA token', 'error')
                return render_template('auth/login.html', require_mfa=True, email=email)
        
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        
        login_user(user, remember=remember)
        auth_service.log_event(user.id, 'login_success', 'User logged in successfully', request)
        
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('dashboard.index')
        
        return redirect(next_page)
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    auth_service.log_event(current_user.id, 'logout', 'User logged out', request)
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/setup-mfa', methods=['GET', 'POST'])
@login_required
def setup_mfa():
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        
        if current_user.verify_mfa_token(token):
            current_user.mfa_enabled = True
            db.session.commit()
            
            auth_service.log_event(current_user.id, 'mfa_enabled', 'MFA enabled for account', request)
            flash('Two-factor authentication enabled successfully', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid token. Please try again.', 'error')
    
    if not current_user.mfa_secret:
        current_user.generate_mfa_secret()
        db.session.commit()
    
    uri = pyotp.totp.TOTP(current_user.mfa_secret).provisioning_uri(
        name=current_user.email,
        issuer_name='SafeHome'
    )
    
    img = qrcode.make(uri)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_code = base64.b64encode(buffered.getvalue()).decode()
    
    return render_template('auth/setup_mfa.html', qr_code=qr_code, secret=current_user.mfa_secret)

@bp.route('/disable-mfa', methods=['POST'])
@login_required
def disable_mfa():
    password = request.form.get('password', '')
    
    if not current_user.check_password(password):
        flash('Invalid password', 'error')
        return redirect(url_for('dashboard.index'))
    
    current_user.mfa_enabled = False
    db.session.commit()
    
    auth_service.log_event(current_user.id, 'mfa_disabled', 'MFA disabled for account', request)
    flash('Two-factor authentication disabled', 'info')
    return redirect(url_for('dashboard.index'))

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            username = request.form.get('username', '').strip()
            
            if username and username != current_user.username:
                if User.query.filter_by(username=username).first():
                    flash('Username already taken', 'error')
                else:
                    current_user.username = username
                    db.session.commit()
                    flash('Profile updated successfully', 'success')
        
        elif action == 'change_password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if not current_user.check_password(current_password):
                flash('Current password is incorrect', 'error')
            elif not validate_password(new_password):
                flash('New password does not meet requirements', 'error')
            elif new_password != confirm_password:
                flash('Passwords do not match', 'error')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                auth_service.log_event(current_user.id, 'password_changed', 'Password changed successfully', request)
                flash('Password changed successfully', 'success')
    
    return render_template('auth/profile.html')
