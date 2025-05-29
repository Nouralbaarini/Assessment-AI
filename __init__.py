"""
Routes package initialization.
"""

from flask import Blueprint

# Create blueprints for different sections of the application
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import routes to register them with blueprints
from src.routes import auth_routes, teacher_routes, admin_routes, api_routes

# Register routes with blueprints
# Auth routes
auth_bp.add_url_rule('/login', view_func=auth_routes.login, methods=['GET', 'POST'])
auth_bp.add_url_rule('/logout', view_func=auth_routes.logout)
auth_bp.add_url_rule('/register', view_func=auth_routes.register, methods=['GET', 'POST'])
auth_bp.add_url_rule('/profile', view_func=auth_routes.profile, methods=['GET', 'POST'])
auth_bp.add_url_rule('/change-password', view_func=auth_routes.change_password, methods=['GET', 'POST'])

# Teacher routes
teacher_bp.add_url_rule('/', view_func=teacher_routes.dashboard)
teacher_bp.add_url_rule('/categories', view_func=teacher_routes.categories, methods=['GET', 'POST'])
teacher_bp.add_url_rule('/categories/<int:category_id>', view_func=teacher_routes.view_category)
teacher_bp.add_url_rule('/modules', view_func=teacher_routes.modules, methods=['GET', 'POST'])
teacher_bp.add_url_rule('/modules/<int:module_id>', view_func=teacher_routes.view_module)
teacher_bp.add_url_rule('/assessments', view_func=teacher_routes.assessments, methods=['GET', 'POST'])
teacher_bp.add_url_rule('/assessments/<int:assessment_id>', view_func=teacher_routes.view_assessment)
teacher_bp.add_url_rule('/assessments/<int:assessment_id>/rubric', view_func=teacher_routes.manage_rubric, methods=['GET', 'POST'])
teacher_bp.add_url_rule('/assessments/<int:assessment_id>/student-work', view_func=teacher_routes.student_work, methods=['GET', 'POST'])
teacher_bp.add_url_rule('/assessments/<int:assessment_id>/student-work/<int:work_id>', view_func=teacher_routes.view_student_work)
teacher_bp.add_url_rule('/assessments/<int:assessment_id>/analytics', view_func=teacher_routes.assessment_analytics)
teacher_bp.add_url_rule('/assessments/<int:assessment_id>/recommendations', view_func=teacher_routes.assessment_recommendations)

# Admin routes
admin_bp.add_url_rule('/', view_func=admin_routes.dashboard)
admin_bp.add_url_rule('/users', view_func=admin_routes.manage_users, methods=['GET', 'POST'])
admin_bp.add_url_rule('/users/<int:user_id>', view_func=admin_routes.edit_user, methods=['GET', 'POST'])
admin_bp.add_url_rule('/website', view_func=admin_routes.website_customization)
admin_bp.add_url_rule('/templates', view_func=admin_routes.manage_templates, methods=['GET', 'POST'])
admin_bp.add_url_rule('/templates/<int:template_id>', view_func=admin_routes.edit_template, methods=['GET', 'POST'])
admin_bp.add_url_rule('/sections', view_func=admin_routes.manage_sections, methods=['GET', 'POST'])
admin_bp.add_url_rule('/sections/<int:section_id>', view_func=admin_routes.edit_section, methods=['GET', 'POST'])
admin_bp.add_url_rule('/layouts', view_func=admin_routes.manage_layouts, methods=['GET', 'POST'])
admin_bp.add_url_rule('/layouts/<int:layout_id>', view_func=admin_routes.edit_layout, methods=['GET', 'POST'])
admin_bp.add_url_rule('/system-settings', view_func=admin_routes.system_settings, methods=['GET', 'POST'])

# API routes
api_bp.add_url_rule('/mark-work', view_func=api_routes.mark_work, methods=['POST'])
api_bp.add_url_rule('/process-brief', view_func=api_routes.process_brief, methods=['POST'])
api_bp.add_url_rule('/process-rubric', view_func=api_routes.process_rubric, methods=['POST'])
api_bp.add_url_rule('/generate-analytics', view_func=api_routes.generate_analytics, methods=['POST'])
api_bp.add_url_rule('/generate-recommendations', view_func=api_routes.generate_recommendations, methods=['POST'])
api_bp.add_url_rule('/extract-urls', view_func=api_routes.extract_urls, methods=['POST'])
api_bp.add_url_rule('/analyze-url', view_func=api_routes.analyze_url, methods=['POST'])
api_bp.add_url_rule('/save-section', view_func=api_routes.save_section, methods=['POST'])
api_bp.add_url_rule('/save-layout', view_func=api_routes.save_layout, methods=['POST'])
