"""
Authentication routes for the application.
"""

from flask import render_template, redirect, url_for, flash, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.models import User, UserProfile, db
from functools import wraps
import datetime

def login_required(f):
    """Decorator to ensure user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to ensure user is an admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('teacher.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def login():
    """Handle user login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            # Update last login time
            user.last_login = datetime.datetime.utcnow()
            db.session.commit()
            
            flash(f'Welcome back, {user.first_name}!', 'success')
            
            # Redirect based on role
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('teacher.dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
    
    return render_template('auth/login.html')

def logout():
    """Handle user logout."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

def register():
    """Handle user registration."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role', 'teacher')  # Default to teacher
        
        # Validate input
        if not all([username, email, password, confirm_password, first_name, last_name]):
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return render_template('auth/register.html')
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            role=role
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Create user profile
        new_profile = UserProfile(user_id=new_user.id)
        db.session.add(new_profile)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@login_required
def profile():
    """Handle user profile management."""
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        # Update profile information
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.email = request.form.get('email')
        
        # Update profile details
        profile = user.profile
        profile.department = request.form.get('department')
        profile.bio = request.form.get('bio')
        
        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file.filename:
                # Save file and update profile picture path
                filename = secure_filename(file.filename)
                file_path = os.path.join('src/static/uploads/profile_pictures', filename)
                file.save(file_path)
                profile.profile_picture = f'/static/uploads/profile_pictures/{filename}'
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html', user=user)

@login_required
def change_password():
    """Handle password change."""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        user = User.query.get(session['user_id'])
        
        # Validate input
        if not check_password_hash(user.password_hash, current_password):
            flash('Current password is incorrect.', 'danger')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return render_template('auth/change_password.html')
        
        # Update password
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html')
