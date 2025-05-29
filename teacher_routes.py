"""
Teacher dashboard routes for the application.
"""

from flask import render_template, redirect, url_for, flash, request, session, jsonify
from src.routes.auth_routes import login_required
from src.models.models import (
    User, Category, Module, AssessmentBrief, Rubric, RubricCriteria,
    StudentWork, Mark, Feedback, AnalyticsData, Recommendation, db
)
from src.models.ai_marking import AssessmentAI
from werkzeug.utils import secure_filename
import os
import datetime
import json

# Initialize AI marking engine
ai_engine = AssessmentAI()

def dashboard():
    """Teacher dashboard home page."""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    # Get recent assessments
    recent_assessments = AssessmentBrief.query.filter_by(
        created_by=user_id
    ).order_by(AssessmentBrief.created_at.desc()).limit(5).all()
    
    # Get recent student work submissions
    recent_submissions = StudentWork.query.join(
        AssessmentBrief
    ).filter(
        AssessmentBrief.created_by == user_id
    ).order_by(StudentWork.submission_date.desc()).limit(10).all()
    
    # Get categories and modules count
    categories_count = Category.query.filter_by(created_by=user_id).count()
    modules_count = Module.query.filter_by(created_by=user_id).count()
    assessments_count = AssessmentBrief.query.filter_by(created_by=user_id).count()
    
    # Get marking statistics
    marked_count = StudentWork.query.join(
        AssessmentBrief
    ).filter(
        AssessmentBrief.created_by == user_id,
        StudentWork.status == 'marked'
    ).count()
    
    pending_count = StudentWork.query.join(
        AssessmentBrief
    ).filter(
        AssessmentBrief.created_by == user_id,
        StudentWork.status == 'submitted'
    ).count()
    
    # Get recent recommendations
    recent_recommendations = Recommendation.query.join(
        AssessmentBrief
    ).filter(
        AssessmentBrief.created_by == user_id
    ).order_by(Recommendation.created_at.desc()).limit(5).all()
    
    return render_template(
        'teacher/dashboard.html',
        user=user,
        recent_assessments=recent_assessments,
        recent_submissions=recent_submissions,
        categories_count=categories_count,
        modules_count=modules_count,
        assessments_count=assessments_count,
        marked_count=marked_count,
        pending_count=pending_count,
        recent_recommendations=recent_recommendations
    )

def categories():
    """Manage categories."""
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Category name is required.', 'danger')
            return redirect(url_for('teacher.categories'))
        
        new_category = Category(
            name=name,
            description=description,
            created_by=user_id
        )
        
        db.session.add(new_category)
        db.session.commit()
        
        flash('Category created successfully!', 'success')
        return redirect(url_for('teacher.categories'))
    
    # Get all categories for this user
    categories = Category.query.filter_by(created_by=user_id).order_by(Category.name).all()
    
    return render_template('teacher/categories.html', categories=categories)

def view_category(category_id):
    """View a specific category and its modules."""
    user_id = session.get('user_id')
    category = Category.query.get_or_404(category_id)
    
    # Ensure user owns this category
    if category.created_by != user_id:
        flash('You do not have permission to view this category.', 'danger')
        return redirect(url_for('teacher.categories'))
    
    # Get modules in this category
    modules = Module.query.filter_by(category_id=category_id).order_by(Module.name).all()
    
    return render_template('teacher/view_category.html', category=category, modules=modules)

def modules():
    """Manage modules."""
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        description = request.form.get('description')
        category_id = request.form.get('category_id')
        
        if not all([name, code, category_id]):
            flash('Module name, code, and category are required.', 'danger')
            return redirect(url_for('teacher.modules'))
        
        # Verify category belongs to user
        category = Category.query.get(category_id)
        if not category or category.created_by != user_id:
            flash('Invalid category selected.', 'danger')
            return redirect(url_for('teacher.modules'))
        
        new_module = Module(
            name=name,
            code=code,
            description=description,
            category_id=category_id,
            created_by=user_id
        )
        
        db.session.add(new_module)
        db.session.commit()
        
        flash('Module created successfully!', 'success')
        return redirect(url_for('teacher.modules'))
    
    # Get all modules for this user
    modules = Module.query.filter_by(created_by=user_id).order_by(Module.name).all()
    
    # Get categories for dropdown
    categories = Category.query.filter_by(created_by=user_id).order_by(Category.name).all()
    
    return render_template('teacher/modules.html', modules=modules, categories=categories)

def view_module(module_id):
    """View a specific module and its assessments."""
    user_id = session.get('user_id')
    module = Module.query.get_or_404(module_id)
    
    # Ensure user owns this module
    if module.created_by != user_id:
        flash('You do not have permission to view this module.', 'danger')
        return redirect(url_for('teacher.modules'))
    
    # Get assessments in this module
    assessments = AssessmentBrief.query.filter_by(module_id=module_id).order_by(AssessmentBrief.title).all()
    
    return render_template('teacher/view_module.html', module=module, assessments=assessments)

def assessments():
    """Manage assessment briefs."""
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        module_id = request.form.get('module_id')
        
        if not all([title, module_id]):
            flash('Assessment title and module are required.', 'danger')
            return redirect(url_for('teacher.assessments'))
        
        # Verify module belongs to user
        module = Module.query.get(module_id)
        if not module or module.created_by != user_id:
            flash('Invalid module selected.', 'danger')
            return redirect(url_for('teacher.assessments'))
        
        # Handle file upload
        if 'brief_file' not in request.files:
            flash('Assessment brief file is required.', 'danger')
            return redirect(url_for('teacher.assessments'))
        
        file = request.files['brief_file']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(url_for('teacher.assessments'))
        
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join('src/static/uploads/briefs', filename)
            file.save(file_path)
            
            new_assessment = AssessmentBrief(
                title=title,
                description=description,
                module_id=module_id,
                file_path=f'/static/uploads/briefs/{filename}',
                created_by=user_id
            )
            
            db.session.add(new_assessment)
            db.session.commit()
            
            flash('Assessment brief created successfully!', 'success')
            return redirect(url_for('teacher.assessments'))
    
    # Get all assessments for this user
    assessments = AssessmentBrief.query.join(
        Module
    ).filter(
        Module.created_by == user_id
    ).order_by(AssessmentBrief.title).all()
    
    # Get modules for dropdown
    modules = Module.query.filter_by(created_by=user_id).order_by(Module.name).all()
    
    return render_template('teacher/assessments.html', assessments=assessments, modules=modules)

def view_assessment(assessment_id):
    """View a specific assessment brief."""
    user_id = session.get('user_id')
    assessment = AssessmentBrief.query.get_or_404(assessment_id)
    
    # Ensure user owns this assessment
    if assessment.created_by != user_id:
        flash('You do not have permission to view this assessment.', 'danger')
        return redirect(url_for('teacher.assessments'))
    
    # Check if rubric exists
    has_rubric = assessment.rubric is not None
    
    # Get student work submissions
    student_works = StudentWork.query.filter_by(assessment_id=assessment_id).order_by(StudentWork.submission_date.desc()).all()
    
    # Count submissions by status
    submitted_count = sum(1 for work in student_works if work.status == 'submitted')
    marking_count = sum(1 for work in student_works if work.status == 'marking')
    marked_count = sum(1 for work in student_works if work.status == 'marked')
    
    return render_template(
        'teacher/view_assessment.html',
        assessment=assessment,
        has_rubric=has_rubric,
        student_works=student_works,
        submitted_count=submitted_count,
        marking_count=marking_count,
        marked_count=marked_count
    )

def manage_rubric(assessment_id):
    """Manage rubric for an assessment."""
    user_id = session.get('user_id')
    assessment = AssessmentBrief.query.get_or_404(assessment_id)
    
    # Ensure user owns this assessment
    if assessment.created_by != user_id:
        flash('You do not have permission to manage this rubric.', 'danger')
        return redirect(url_for('teacher.assessments'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        if not title:
            flash('Rubric title is required.', 'danger')
            return redirect(url_for('teacher.manage_rubric', assessment_id=assessment_id))
        
        # Handle file upload
        if 'rubric_file' not in request.files:
            flash('Rubric file is required.', 'danger')
            return redirect(url_for('teacher.manage_rubric', assessment_id=assessment_id))
        
        file = request.files['rubric_file']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(url_for('teacher.manage_rubric', assessment_id=assessment_id))
        
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join('src/static/uploads/rubrics', filename)
            file.save(file_path)
            
            # Check if rubric already exists
            rubric = assessment.rubric
            if rubric:
                # Update existing rubric
                rubric.title = title
                rubric.description = description
                rubric.file_path = f'/static/uploads/rubrics/{filename}'
                rubric.updated_at = datetime.datetime.utcnow()
            else:
                # Create new rubric
                rubric = Rubric(
                    assessment_id=assessment_id,
                    title=title,
                    description=description,
                    file_path=f'/static/uploads/rubrics/{filename}'
                )
                db.session.add(rubric)
            
            db.session.commit()
            
            # Process rubric with AI
            try:
                with open(file_path, 'r') as f:
                    rubric_text = f.read()
                
                rubric_analysis = ai_engine.process_rubric(rubric_text)
                
                # Create criteria based on AI analysis
                if rubric_analysis and 'criteria' in rubric_analysis:
                    # Clear existing criteria
                    RubricCriteria.query.filter_by(rubric_id=rubric.id).delete()
                    
                    # Add new criteria
                    for i, criterion in enumerate(rubric_analysis['criteria']):
                        new_criterion = RubricCriteria(
                            rubric_id=rubric.id,
                            name=criterion['name'],
                            description=criterion['description'],
                            weight=1.0,  # Default weight
                            max_score=10.0  # Default max score
                        )
                        db.session.add(new_criterion)
                    
                    db.session.commit()
            except Exception as e:
                flash(f'Rubric saved, but AI processing failed: {str(e)}', 'warning')
            
            flash('Rubric saved successfully!', 'success')
            return redirect(url_for('teacher.view_assessment', assessment_id=assessment_id))
    
    # Check if rubric exists
    rubric = assessment.rubric
    criteria = []
    
    if rubric:
        criteria = RubricCriteria.query.filter_by(rubric_id=rubric.id).all()
    
    return render_template(
        'teacher/manage_rubric.html',
        assessment=assessment,
        rubric=rubric,
        criteria=criteria
    )

def student_work(assessment_id):
    """Manage student work submissions for an assessment."""
    user_id = session.get('user_id')
    assessment = AssessmentBrief.query.get_or_404(assessment_id)
    
    # Ensure user owns this assessment
    if assessment.created_by != user_id:
        flash('You do not have permission to manage student work for this assessment.', 'danger')
        return redirect(url_for('teacher.assessments'))
    
    if request.method == 'POST':
        student_name = request.form.get('student_name')
        student_id = request.form.get('student_id')
        
        if not all([student_name, student_id]):
            flash('Student name and ID are required.', 'danger')
            return redirect(url_for('teacher.student_work', assessment_id=assessment_id))
        
        # Handle file upload
        if 'work_file' not in request.files:
            flash('Student work file is required.', 'danger')
            return redirect(url_for('teacher.student_work', assessment_id=assessment_id))
        
        file = request.files['work_file']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(url_for('teacher.student_work', assessment_id=assessment_id))
        
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join('src/static/uploads/student_work', filename)
            file.save(file_path)
            
            new_work = StudentWork(
                assessment_id=assessment_id,
                student_name=student_name,
                student_id=student_id,
                file_path=f'/static/uploads/student_work/{filename}',
                status='submitted',
                uploaded_by=user_id
            )
            
            db.session.add(new_work)
            db.session.commit()
            
            flash('Student work uploaded successfully!', 'success')
            
            # Check if auto-marking is requested
            if request.form.get('auto_mark') == 'yes':
                # Redirect to API endpoint for marking
                return redirect(url_for('api.mark_work_route', work_id=new_work.id))
            
            return redirect(url_for('teacher.view_assessment', assessment_id=assessment_id))
    
    # Get all student work for this assessment
    student_works = StudentWork.query.filter_by(assessment_id=assessment_id).order_by(StudentWork.submission_date.desc()).all()
    
    return render_template(
        'teacher/student_work.html',
        assessment=assessment,
        student_works=student_works
    )

def view_student_work(assessment_id, work_id):
    """View a specific student work submission and its marking."""
    user_id = session.get('user_id')
    assessment = AssessmentBrief.query.get_or_404(assessment_id)
    
    # Ensure user owns this assessment
    if assessment.created_by != user_id:
        flash('You do not have permission to view this student work.', 'danger')
        return redirect(url_for('teacher.assessments'))
    
    student_work = StudentWork.query.get_or_404(work_id)
    
    # Ensure student work belongs to this assessment
    if student_work.assessment_id != assessment_id:
        flash('Invalid student work for this assessment.', 'danger')
        return redirect(url_for('teacher.view_assessment', assessment_id=assessment_id))
    
    # Get mark and feedback if available
    mark = student_work.mark
    feedback = mark.feedback if mark else None
    
    # Get criteria marks if available
    criteria_marks = []
    if mark:
        criteria_marks = mark.criteria_marks.all()
    
    return render_template(
        'teacher/view_student_work.html',
        assessment=assessment,
        student_work=student_work,
        mark=mark,
        feedback=feedback,
        criteria_marks=criteria_marks
    )

def assessment_analytics(assessment_id):
    """View analytics for an assessment."""
    user_id = session.get('user_id')
    assessment = AssessmentBrief.query.get_or_404(assessment_id)
    
    # Ensure user owns this assessment
    if assessment.created_by != user_id:
        flash('You do not have permission to view analytics for this assessment.', 'danger')
        return redirect(url_for('teacher.assessments'))
    
    # Get analytics data
    analytics_data = AnalyticsData.query.filter_by(
        assessment_id=assessment_id
    ).order_by(AnalyticsData.created_at.desc()).first()
    
    if not analytics_data:
        flash('No analytics data available for this assessment.', 'info')
        return redirect(url_for('teacher.view_assessment', assessment_id=assessment_id))
    
    # Parse analytics data
    analytics = analytics_data.data
    
    return render_template(
        'teacher/assessment_analytics.html',
        assessment=assessment,
        analytics=analytics
    )

def assessment_recommendations(assessment_id):
    """View recommendations for an assessment."""
    user_id = session.get('user_id')
    assessment = AssessmentBrief.query.get_or_404(assessment_id)
    
    # Ensure user owns this assessment
    if assessment.created_by != user_id:
        flash('You do not have permission to view recommendations for this assessment.', 'danger')
        return redirect(url_for('teacher.assessments'))
    
    # Get recommendations
    recommendations = Recommendation.query.filter_by(
        assessment_id=assessment_id
    ).order_by(Recommendation.priority).all()
    
    if not recommendations:
        flash('No recommendations available for this assessment.', 'info')
        return redirect(url_for('teacher.view_assessment', assessment_id=assessment_id))
    
    return render_template(
        'teacher/assessment_recommendations.html',
        assessment=assessment,
        recommendations=recommendations
    )
