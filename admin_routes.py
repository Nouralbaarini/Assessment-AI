"""
Admin dashboard routes for the application.
"""

from flask import render_template, redirect, url_for, flash, request, session, jsonify
from src.routes.auth_routes import admin_required
from src.models.models import (
    User, UserProfile, Category, Module, AssessmentBrief, 
    WebsiteSection, Template, PageLayout, db
)
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import os
import datetime
import json

def dashboard():
    """Admin dashboard home page."""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    # Get system statistics
    user_count = User.query.count()
    teacher_count = User.query.filter_by(role='teacher').count()
    admin_count = User.query.filter_by(role='admin').count()
    
    assessment_count = AssessmentBrief.query.count()
    category_count = Category.query.count()
    module_count = Module.query.count()
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Get website customization stats
    section_count = WebsiteSection.query.count()
    template_count = Template.query.count()
    layout_count = PageLayout.query.count()
    
    return render_template(
        'admin/dashboard.html',
        user=user,
        user_count=user_count,
        teacher_count=teacher_count,
        admin_count=admin_count,
        assessment_count=assessment_count,
        category_count=category_count,
        module_count=module_count,
        recent_users=recent_users,
        section_count=section_count,
        template_count=template_count,
        layout_count=layout_count
    )

def manage_users():
    """Manage users in the system."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role')
        
        if not all([username, email, password, first_name, last_name, role]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin.manage_users'))
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin.manage_users'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('admin.manage_users'))
        
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
        
        flash('User created successfully!', 'success')
        return redirect(url_for('admin.manage_users'))
    
    # Get all users
    users = User.query.order_by(User.username).all()
    
    return render_template('admin/manage_users.html', users=users)

def edit_user(user_id):
    """Edit a specific user."""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role')
        is_active = request.form.get('is_active') == 'on'
        
        if not all([username, email, first_name, last_name, role]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        # Check if username or email already exists (excluding this user)
        username_exists = User.query.filter(
            User.username == username,
            User.id != user_id
        ).first()
        
        if username_exists:
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        email_exists = User.query.filter(
            User.email == email,
            User.id != user_id
        ).first()
        
        if email_exists:
            flash('Email already exists.', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        # Update user
        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.role = role
        user.is_active = is_active
        
        # Update password if provided
        new_password = request.form.get('new_password')
        if new_password:
            user.password_hash = generate_password_hash(new_password)
        
        db.session.commit()
        
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.manage_users'))
    
    return render_template('admin/edit_user.html', user=user)

def website_customization():
    """Website customization dashboard."""
    # Get templates
    templates = Template.query.filter_by(is_active=True).all()
    
    # Get sections
    sections = WebsiteSection.query.filter_by(is_active=True).order_by(WebsiteSection.position).all()
    
    # Get layouts
    layouts = PageLayout.query.filter_by(is_active=True).all()
    
    return render_template(
        'admin/website_customization.html',
        templates=templates,
        sections=sections,
        layouts=layouts
    )

def manage_templates():
    """Manage website templates."""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        template_data = request.form.get('template_data')
        
        if not all([name, template_data]):
            flash('Template name and data are required.', 'danger')
            return redirect(url_for('admin.manage_templates'))
        
        try:
            # Validate JSON data
            template_json = json.loads(template_data)
            
            new_template = Template(
                name=name,
                description=description,
                template_data=template_json,
                is_active=True
            )
            
            db.session.add(new_template)
            db.session.commit()
            
            flash('Template created successfully!', 'success')
            return redirect(url_for('admin.manage_templates'))
        except json.JSONDecodeError:
            flash('Invalid JSON data for template.', 'danger')
            return redirect(url_for('admin.manage_templates'))
    
    # Get all templates
    templates = Template.query.order_by(Template.name).all()
    
    return render_template('admin/manage_templates.html', templates=templates)

def edit_template(template_id):
    """Edit a specific template."""
    template = Template.query.get_or_404(template_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        template_data = request.form.get('template_data')
        is_active = request.form.get('is_active') == 'on'
        
        if not all([name, template_data]):
            flash('Template name and data are required.', 'danger')
            return redirect(url_for('admin.edit_template', template_id=template_id))
        
        try:
            # Validate JSON data
            template_json = json.loads(template_data)
            
            # Update template
            template.name = name
            template.description = description
            template.template_data = template_json
            template.is_active = is_active
            template.updated_at = datetime.datetime.utcnow()
            
            db.session.commit()
            
            flash('Template updated successfully!', 'success')
            return redirect(url_for('admin.manage_templates'))
        except json.JSONDecodeError:
            flash('Invalid JSON data for template.', 'danger')
            return redirect(url_for('admin.edit_template', template_id=template_id))
    
    # Convert template data to JSON string for editing
    template_data_json = json.dumps(template.template_data, indent=2)
    
    return render_template(
        'admin/edit_template.html',
        template=template,
        template_data_json=template_data_json
    )

def manage_sections():
    """Manage website sections."""
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        content = request.form.get('content')
        position = request.form.get('position', 0)
        
        if not all([name, content]):
            flash('Section name and content are required.', 'danger')
            return redirect(url_for('admin.manage_sections'))
        
        try:
            # Validate JSON data
            content_json = json.loads(content)
            
            new_section = WebsiteSection(
                name=name,
                description=description,
                content=content_json,
                position=position,
                is_active=True,
                created_by=user_id
            )
            
            db.session.add(new_section)
            db.session.commit()
            
            flash('Section created successfully!', 'success')
            return redirect(url_for('admin.manage_sections'))
        except json.JSONDecodeError:
            flash('Invalid JSON data for section content.', 'danger')
            return redirect(url_for('admin.manage_sections'))
    
    # Get all sections
    sections = WebsiteSection.query.order_by(WebsiteSection.position).all()
    
    return render_template('admin/manage_sections.html', sections=sections)

def edit_section(section_id):
    """Edit a specific website section."""
    section = WebsiteSection.query.get_or_404(section_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        content = request.form.get('content')
        position = request.form.get('position', 0)
        is_active = request.form.get('is_active') == 'on'
        
        if not all([name, content]):
            flash('Section name and content are required.', 'danger')
            return redirect(url_for('admin.edit_section', section_id=section_id))
        
        try:
            # Validate JSON data
            content_json = json.loads(content)
            
            # Update section
            section.name = name
            section.description = description
            section.content = content_json
            section.position = position
            section.is_active = is_active
            section.updated_at = datetime.datetime.utcnow()
            
            db.session.commit()
            
            flash('Section updated successfully!', 'success')
            return redirect(url_for('admin.manage_sections'))
        except json.JSONDecodeError:
            flash('Invalid JSON data for section content.', 'danger')
            return redirect(url_for('admin.edit_section', section_id=section_id))
    
    # Convert section content to JSON string for editing
    content_json = json.dumps(section.content, indent=2)
    
    return render_template(
        'admin/edit_section.html',
        section=section,
        content_json=content_json
    )

def manage_layouts():
    """Manage page layouts."""
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        sections = request.form.get('sections')
        
        if not all([name, sections]):
            flash('Layout name and sections are required.', 'danger')
            return redirect(url_for('admin.manage_layouts'))
        
        try:
            # Validate JSON data
            sections_json = json.loads(sections)
            
            new_layout = PageLayout(
                name=name,
                description=description,
                sections=sections_json,
                is_active=True,
                created_by=user_id
            )
            
            db.session.add(new_layout)
            db.session.commit()
            
            flash('Layout created successfully!', 'success')
            return redirect(url_for('admin.manage_layouts'))
        except json.JSONDecodeError:
            flash('Invalid JSON data for layout sections.', 'danger')
            return redirect(url_for('admin.manage_layouts'))
    
    # Get all layouts
    layouts = PageLayout.query.all()
    
    # Get all sections for dropdown
    sections = WebsiteSection.query.filter_by(is_active=True).order_by(WebsiteSection.name).all()
    
    return render_template('admin/manage_layouts.html', layouts=layouts, sections=sections)

def edit_layout(layout_id):
    """Edit a specific page layout."""
    layout = PageLayout.query.get_or_404(layout_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        sections = request.form.get('sections')
        is_active = request.form.get('is_active') == 'on'
        
        if not all([name, sections]):
            flash('Layout name and sections are required.', 'danger')
            return redirect(url_for('admin.edit_layout', layout_id=layout_id))
        
        try:
            # Validate JSON data
            sections_json = json.loads(sections)
            
            # Update layout
            layout.name = name
            layout.description = description
            layout.sections = sections_json
            layout.is_active = is_active
            layout.updated_at = datetime.datetime.utcnow()
            
            db.session.commit()
            
            flash('Layout updated successfully!', 'success')
            return redirect(url_for('admin.manage_layouts'))
        except json.JSONDecodeError:
            flash('Invalid JSON data for layout sections.', 'danger')
            return redirect(url_for('admin.edit_layout', layout_id=layout_id))
    
    # Convert layout sections to JSON string for editing
    sections_json = json.dumps(layout.sections, indent=2)
    
    # Get all sections for dropdown
    sections = WebsiteSection.query.filter_by(is_active=True).order_by(WebsiteSection.name).all()
    
    return render_template(
        'admin/edit_layout.html',
        layout=layout,
        sections_json=sections_json,
        available_sections=sections
    )

def system_settings():
    """Manage system settings."""
    if request.method == 'POST':
        # Process system settings update
        # This would typically involve updating configuration values in the database
        
        flash('System settings updated successfully!', 'success')
        return redirect(url_for('admin.system_settings'))
    
    # Here you would load current system settings from database or config
    settings = {
        'site_name': 'Assessment AI System',
        'allow_registration': True,
        'enable_ai_marking': True,
        'max_file_size_mb': 10,
        'allowed_file_types': '.pdf,.doc,.docx,.txt',
        'analytics_retention_days': 90
    }
    
    return render_template('admin/system_settings.html', settings=settings)
