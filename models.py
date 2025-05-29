from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    """User model for both teachers and administrators."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'teacher'
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='creator', lazy='dynamic')
    modules = db.relationship('Module', backref='creator', lazy='dynamic')
    assessments = db.relationship('AssessmentBrief', backref='creator', lazy='dynamic')
    website_sections = db.relationship('WebsiteSection', backref='creator', lazy='dynamic')
    page_layouts = db.relationship('PageLayout', backref='creator', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'


class UserProfile(db.Model):
    """Extended profile information for users."""
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    department = db.Column(db.String(128), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    _preferences = db.Column(db.Text, nullable=True)  # JSON stored as text
    
    @property
    def preferences(self):
        if self._preferences:
            return json.loads(self._preferences)
        return {}
    
    @preferences.setter
    def preferences(self, value):
        self._preferences = json.dumps(value)
    
    def __repr__(self):
        return f'<UserProfile for User {self.user_id}>'


class Category(db.Model):
    """Categories for organizing modules."""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    modules = db.relationship('Module', backref='category', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Category {self.name}>'


class Module(db.Model):
    """Teaching modules within categories."""
    __tablename__ = 'modules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    code = db.Column(db.String(32), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assessments = db.relationship('AssessmentBrief', backref='module', lazy='dynamic', cascade='all, delete-orphan')
    recommendations = db.relationship('Recommendation', backref='module', lazy='dynamic')
    
    def __repr__(self):
        return f'<Module {self.code}: {self.name}>'


class AssessmentBrief(db.Model):
    """Assessment briefs created by teachers."""
    __tablename__ = 'assessment_briefs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    rubric = db.relationship('Rubric', backref='assessment', uselist=False, cascade='all, delete-orphan')
    student_works = db.relationship('StudentWork', backref='assessment', lazy='dynamic', cascade='all, delete-orphan')
    analytics_data = db.relationship('AnalyticsData', backref='assessment', lazy='dynamic', cascade='all, delete-orphan')
    recommendations = db.relationship('Recommendation', backref='assessment', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<AssessmentBrief {self.title}>'


class Rubric(db.Model):
    """Marking rubrics associated with assessment briefs."""
    __tablename__ = 'rubrics'
    
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment_briefs.id'), nullable=False, unique=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    criteria = db.relationship('RubricCriteria', backref='rubric', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Rubric {self.title}>'


class RubricCriteria(db.Model):
    """Individual criteria within a rubric."""
    __tablename__ = 'rubric_criteria'
    
    id = db.Column(db.Integer, primary_key=True)
    rubric_id = db.Column(db.Integer, db.ForeignKey('rubrics.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    weight = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, nullable=False)
    
    # Relationships
    criteria_marks = db.relationship('CriteriaMark', backref='criteria', lazy='dynamic')
    
    def __repr__(self):
        return f'<RubricCriteria {self.name}>'


class StudentWork(db.Model):
    """Student work submissions for assessment."""
    __tablename__ = 'student_works'
    
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment_briefs.id'), nullable=False)
    student_name = db.Column(db.String(128), nullable=False)
    student_id = db.Column(db.String(32), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    _urls = db.Column(db.Text, nullable=True)  # JSON stored as text
    status = db.Column(db.String(20), nullable=False, default='submitted')  # 'submitted', 'marking', 'marked'
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    mark = db.relationship('Mark', backref='student_work', uselist=False, cascade='all, delete-orphan')
    
    @property
    def urls(self):
        if self._urls:
            return json.loads(self._urls)
        return []
    
    @urls.setter
    def urls(self, value):
        self._urls = json.dumps(value)
    
    def __repr__(self):
        return f'<StudentWork {self.student_id}: {self.student_name}>'


class Mark(db.Model):
    """Marks awarded to student work."""
    __tablename__ = 'marks'
    
    id = db.Column(db.Integer, primary_key=True)
    student_work_id = db.Column(db.Integer, db.ForeignKey('student_works.id'), nullable=False, unique=True)
    total_score = db.Column(db.Float, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    marked_by_ai = db.Column(db.Boolean, default=True)
    verified_by_teacher = db.Column(db.Boolean, default=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    criteria_marks = db.relationship('CriteriaMark', backref='mark', lazy='dynamic', cascade='all, delete-orphan')
    feedback = db.relationship('Feedback', backref='mark', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Mark {self.total_score} ({self.percentage}%)>'


class CriteriaMark(db.Model):
    """Individual criteria marks within an overall mark."""
    __tablename__ = 'criteria_marks'
    
    id = db.Column(db.Integer, primary_key=True)
    mark_id = db.Column(db.Integer, db.ForeignKey('marks.id'), nullable=False)
    criteria_id = db.Column(db.Integer, db.ForeignKey('rubric_criteria.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    comments = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<CriteriaMark {self.score}>'


class Feedback(db.Model):
    """Detailed feedback for student work."""
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    mark_id = db.Column(db.Integer, db.ForeignKey('marks.id'), nullable=False, unique=True)
    general_comments = db.Column(db.Text, nullable=True)
    strengths = db.Column(db.Text, nullable=True)
    areas_for_improvement = db.Column(db.Text, nullable=True)
    recommendations = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Feedback for Mark {self.mark_id}>'


class AnalyticsData(db.Model):
    """Analytics data for assessments."""
    __tablename__ = 'analytics_data'
    
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment_briefs.id'), nullable=False)
    data_type = db.Column(db.String(64), nullable=False)
    _data = db.Column(db.Text, nullable=False)  # JSON stored as text
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def data(self):
        return json.loads(self._data)
    
    @data.setter
    def data(self, value):
        self._data = json.dumps(value)
    
    def __repr__(self):
        return f'<AnalyticsData {self.data_type} for Assessment {self.assessment_id}>'


class Recommendation(db.Model):
    """Recommendations for improving teaching materials."""
    __tablename__ = 'recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment_briefs.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    recommendation_text = db.Column(db.Text, nullable=False)
    recommendation_type = db.Column(db.String(64), nullable=False)
    priority = db.Column(db.Integer, nullable=False, default=3)  # 1 (highest) to 5 (lowest)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Recommendation for Assessment {self.assessment_id}>'


class WebsiteSection(db.Model):
    """Customizable website sections."""
    __tablename__ = 'website_sections'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    _content = db.Column(db.Text, nullable=False)  # JSON stored as text
    display_order = db.Column(db.Integer, nullable=False)  # Renamed from position to avoid SQL reserved word
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def content(self):
        return json.loads(self._content)
    
    @content.setter
    def content(self, value):
        self._content = json.dumps(value)
    
    def __repr__(self):
        return f'<WebsiteSection {self.name}>'


class Template(db.Model):
    """Website templates for customization."""
    __tablename__ = 'templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    _template_data = db.Column(db.Text, nullable=False)  # JSON stored as text
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def template_data(self):
        return json.loads(self._template_data)
    
    @template_data.setter
    def template_data(self, value):
        self._template_data = json.dumps(value)
    
    def __repr__(self):
        return f'<Template {self.name}>'


class PageLayout(db.Model):
    """Page layouts for website customization."""
    __tablename__ = 'page_layouts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    _sections = db.Column(db.Text, nullable=False)  # JSON stored as text
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def sections(self):
        return json.loads(self._sections)
    
    @sections.setter
    def sections(self, value):
        self._sections = json.dumps(value)
    
    def __repr__(self):
        return f'<PageLayout {self.name}>'
