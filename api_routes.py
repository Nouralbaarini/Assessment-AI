"""
API routes for the application.
"""

from flask import request, jsonify
from src.models.models import (
    AssessmentBrief, Rubric, StudentWork, Mark, CriteriaMark, 
    Feedback, AnalyticsData, Recommendation, WebsiteSection, 
    PageLayout, db
)
from src.models.ai_marking import AssessmentAI
import os
import json
import datetime

# Initialize AI marking engine
ai_engine = AssessmentAI()

def mark_work():
    """API endpoint to mark student work."""
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    data = request.get_json()
    work_id = data.get('work_id')
    
    if not work_id:
        return jsonify({'error': 'Student work ID is required'}), 400
    
    # Get student work
    student_work = StudentWork.query.get(work_id)
    if not student_work:
        return jsonify({'error': 'Student work not found'}), 404
    
    # Get assessment brief and rubric
    assessment = AssessmentBrief.query.get(student_work.assessment_id)
    if not assessment:
        return jsonify({'error': 'Assessment brief not found'}), 404
    
    rubric = Rubric.query.filter_by(assessment_id=assessment.id).first()
    if not rubric:
        return jsonify({'error': 'Rubric not found for this assessment'}), 404
    
    try:
        # Update student work status
        student_work.status = 'marking'
        db.session.commit()
        
        # Read files
        brief_path = os.path.join('src', assessment.file_path.lstrip('/'))
        rubric_path = os.path.join('src', rubric.file_path.lstrip('/'))
        work_path = os.path.join('src', student_work.file_path.lstrip('/'))
        
        with open(brief_path, 'r') as f:
            brief_text = f.read()
        
        with open(rubric_path, 'r') as f:
            rubric_text = f.read()
        
        with open(work_path, 'r') as f:
            work_text = f.read()
        
        # Process with AI
        brief_analysis = ai_engine.process_assessment_brief(brief_text)
        rubric_analysis = ai_engine.process_rubric(rubric_text)
        
        # Extract URLs from student work
        urls = ai_engine.extract_urls(work_text)
        student_work.urls = urls
        db.session.commit()
        
        # Mark student work
        marking_result = ai_engine.mark_student_work(work_text, brief_analysis, rubric_analysis)
        
        # Create mark record
        mark = Mark(
            student_work_id=student_work.id,
            total_score=marking_result['total_score'],
            percentage=marking_result['percentage'],
            marked_by_ai=True,
            verified_by_teacher=False
        )
        db.session.add(mark)
        db.session.commit()
        
        # Create criteria marks
        for criterion_mark in marking_result['criteria_marks']:
            criteria = rubric.criteria.filter_by(name=criterion_mark['name']).first()
            
            if criteria:
                new_criteria_mark = CriteriaMark(
                    mark_id=mark.id,
                    criteria_id=criteria.id,
                    score=criterion_mark['score'],
                    comments=json.dumps(criterion_mark['feedback'])
                )
                db.session.add(new_criteria_mark)
        
        # Create feedback
        feedback = Feedback(
            mark_id=mark.id,
            general_comments=marking_result['feedback']['general_comments'],
            strengths='\n\n'.join(marking_result['feedback']['strengths']),
            areas_for_improvement='\n\n'.join(marking_result['feedback']['areas_for_improvement']),
            recommendations='\n\n'.join(marking_result['feedback']['recommendations'])
        )
        db.session.add(feedback)
        
        # Update student work status
        student_work.status = 'marked'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mark_id': mark.id,
            'percentage': marking_result['percentage'],
            'grade': marking_result['grade']
        })
    
    except Exception as e:
        # Rollback in case of error
        db.session.rollback()
        
        # Update student work status back to submitted
        student_work.status = 'submitted'
        db.session.commit()
        
        return jsonify({'error': str(e)}), 500

def process_brief():
    """API endpoint to process assessment brief."""
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    data = request.get_json()
    brief_id = data.get('brief_id')
    
    if not brief_id:
        return jsonify({'error': 'Assessment brief ID is required'}), 400
    
    # Get assessment brief
    assessment = AssessmentBrief.query.get(brief_id)
    if not assessment:
        return jsonify({'error': 'Assessment brief not found'}), 404
    
    try:
        # Read brief file
        brief_path = os.path.join('src', assessment.file_path.lstrip('/'))
        
        with open(brief_path, 'r') as f:
            brief_text = f.read()
        
        # Process with AI
        brief_analysis = ai_engine.process_assessment_brief(brief_text)
        
        return jsonify({
            'success': True,
            'analysis': brief_analysis
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def process_rubric():
    """API endpoint to process rubric."""
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    data = request.get_json()
    rubric_id = data.get('rubric_id')
    
    if not rubric_id:
        return jsonify({'error': 'Rubric ID is required'}), 400
    
    # Get rubric
    rubric = Rubric.query.get(rubric_id)
    if not rubric:
        return jsonify({'error': 'Rubric not found'}), 404
    
    try:
        # Read rubric file
        rubric_path = os.path.join('src', rubric.file_path.lstrip('/'))
        
        with open(rubric_path, 'r') as f:
            rubric_text = f.read()
        
        # Process with AI
        rubric_analysis = ai_engine.process_rubric(rubric_text)
        
        return jsonify({
            'success': True,
            'analysis': rubric_analysis
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_analytics():
    """API endpoint to generate analytics for an assessment."""
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    data = request.get_json()
    assessment_id = data.get('assessment_id')
    
    if not assessment_id:
        return jsonify({'error': 'Assessment ID is required'}), 400
    
    # Get assessment
    assessment = AssessmentBrief.query.get(assessment_id)
    if not assessment:
        return jsonify({'error': 'Assessment not found'}), 404
    
    try:
        # Get all marked student work for this assessment
        student_works = StudentWork.query.filter_by(
            assessment_id=assessment_id,
            status='marked'
        ).all()
        
        if not student_works:
            return jsonify({'error': 'No marked student work found for this assessment'}), 404
        
        # Collect marking results
        marking_results = []
        for work in student_works:
            if work.mark:
                # Get criteria marks
                criteria_marks = []
                for cm in work.mark.criteria_marks:
                    criteria_marks.append({
                        'name': cm.criteria.name,
                        'score': cm.score,
                        'max_score': cm.criteria.max_score,
                        'feedback': json.loads(cm.comments) if cm.comments else {}
                    })
                
                # Get feedback
                feedback = {}
                if work.mark.feedback:
                    feedback = {
                        'general_comments': work.mark.feedback.general_comments,
                        'strengths': work.mark.feedback.strengths.split('\n\n'),
                        'areas_for_improvement': work.mark.feedback.areas_for_improvement.split('\n\n'),
                        'recommendations': work.mark.feedback.recommendations.split('\n\n')
                    }
                
                # Add to results
                marking_results.append({
                    'total_score': work.mark.total_score,
                    'percentage': work.mark.percentage,
                    'grade': 'A' if work.mark.percentage >= 70 else 'B' if work.mark.percentage >= 60 else 'C' if work.mark.percentage >= 50 else 'D' if work.mark.percentage >= 40 else 'F',
                    'criteria_marks': criteria_marks,
                    'feedback': feedback,
                    'statistics': {
                        'word_count': 0,  # Placeholder
                        'sentence_count': 0,  # Placeholder
                        'avg_sentence_length': 0,  # Placeholder
                        'url_count': len(work.urls) if work.urls else 0,
                        'topic_coverage': 0.7  # Placeholder
                    },
                    'url_analyses': []  # Placeholder
                })
        
        # Generate analytics
        analytics = ai_engine.generate_analytics(marking_results)
        
        # Save analytics to database
        analytics_data = AnalyticsData(
            assessment_id=assessment_id,
            data_type='marking_analytics',
            data=analytics
        )
        db.session.add(analytics_data)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'analytics': analytics,
            'analytics_id': analytics_data.id
        })
    
    except Exception as e:
        # Rollback in case of error
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def generate_recommendations():
    """API endpoint to generate recommendations based on analytics."""
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    data = request.get_json()
    analytics_id = data.get('analytics_id')
    
    if not analytics_id:
        return jsonify({'error': 'Analytics ID is required'}), 400
    
    # Get analytics data
    analytics_data = AnalyticsData.query.get(analytics_id)
    if not analytics_data:
        return jsonify({'error': 'Analytics data not found'}), 404
    
    try:
        # Generate recommendations
        recommendations = ai_engine.generate_recommendations(analytics_data.data)
        
        # Save recommendations to database
        assessment_id = analytics_data.assessment_id
        assessment = AssessmentBrief.query.get(assessment_id)
        
        for rec in recommendations:
            new_recommendation = Recommendation(
                assessment_id=assessment_id,
                module_id=assessment.module_id,
                recommendation_text=rec['text'],
                recommendation_type=rec['type'],
                priority=rec['priority']
            )
            db.session.add(new_recommendation)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'count': len(recommendations)
        })
    
    except Exception as e:
        # Rollback in case of error
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def extract_urls():
    """API endpoint to extract URLs from text."""
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    data = request.get_json()
    text = data.get('text')
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    try:
        # Extract URLs
        urls = ai_engine.extract_urls(text)
        
        return jsonify({
            'success': True,
            'urls': urls,
            'count': len(urls)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def analyze_url():
    """API endpoint to analyze URL content."""
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    try:
        # Analyze URL
        analysis = ai_engine.analyze_url_content(url)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def save_section():
    """API endpoint to save website section via AJAX."""
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    data = request.get_json()
    section_id = data.get('section_id')
    content = data.get('content')
    
    if not section_id or not content:
        return jsonify({'error': 'Section ID and content are required'}), 400
    
    try:
        # Get section
        section = WebsiteSection.query.get(section_id)
        if not section:
            return jsonify({'error': 'Section not found'}), 404
        
        # Update section content
        section.content = content
        section.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'section_id': section_id
        })
    
    except Exception as e:
        # Rollback in case of error
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def save_layout():
    """API endpoint to save page layout via AJAX."""
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    data = request.get_json()
    layout_id = data.get('layout_id')
    sections = data.get('sections')
    
    if not layout_id or not sections:
        return jsonify({'error': 'Layout ID and sections are required'}), 400
    
    try:
        # Get layout
        layout = PageLayout.query.get(layout_id)
        if not layout:
            return jsonify({'error': 'Layout not found'}), 404
        
        # Update layout sections
        layout.sections = sections
        layout.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'layout_id': layout_id
        })
    
    except Exception as e:
        # Rollback in case of error
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def mark_work_route(work_id):
    """Route to mark student work and redirect."""
    # This is a wrapper for the API endpoint that can be called from routes
    try:
        # Call the API endpoint
        result = mark_work(work_id)
        
        # Redirect to view student work
        student_work = StudentWork.query.get(work_id)
        return redirect(url_for(
            'teacher.view_student_work',
            assessment_id=student_work.assessment_id,
            work_id=work_id
        ))
    
    except Exception as e:
        flash(f'Error marking student work: {str(e)}', 'danger')
        
        # Redirect to view assessment
        student_work = StudentWork.query.get(work_id)
        return redirect(url_for(
            'teacher.view_assessment',
            assessment_id=student_work.assessment_id
        ))
