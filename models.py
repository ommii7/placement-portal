from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15))
    role = db.Column(db.String(20), default='student')  # student, hr, admin
    is_active = db.Column(db.Boolean, default=True)
    is_subscribed = db.Column(db.Boolean, default=False)
    subscription_end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile_picture = db.Column(db.String(200))
    
    # Student specific
    college = db.Column(db.String(200))
    course = db.Column(db.String(100))
    graduation_year = db.Column(db.Integer)
    bio = db.Column(db.Text)
    resume_path = db.Column(db.String(200))
    resume_parsed_data = db.Column(db.Text)  # JSON
    skills = db.Column(db.Text)
    experience = db.Column(db.Text)
    
    # HR specific
    company_name = db.Column(db.String(200))
    company_website = db.Column(db.String(500))
    company_description = db.Column(db.Text)
    industry = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    company_logo = db.Column(db.String(200))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_subscription_active(self):
        if not self.is_subscribed:
            return False
        if self.subscription_end_date and self.subscription_end_date < datetime.utcnow():
            return False
        return True

class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    salary_min = db.Column(db.Integer)   # in LPA
    salary_max = db.Column(db.Integer)
    location = db.Column(db.String(200))
    job_type = db.Column(db.String(50))
    experience_required = db.Column(db.String(50))
    skills_required = db.Column(db.Text)
    application_link = db.Column(db.String(500))
    source = db.Column(db.String(50), default='manual')
    posted_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_approved = db.Column(db.Boolean, default=False)
    is_premium = db.Column(db.Boolean, default=False)  # True if salary_max >= 5
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime)
    
    applications = db.relationship('Application', backref='job', lazy=True)

class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'))
    status = db.Column(db.String(20), default='pending')
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    cover_letter = db.Column(db.Text)
    
    student = db.relationship('User', foreign_keys=[student_id])

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    plan = db.Column(db.String(50))
    amount = db.Column(db.Integer)
    payment_id = db.Column(db.String(100))
    payment_status = db.Column(db.String(20), default='pending')
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    document_type = db.Column(db.String(50))
    file_name = db.Column(db.String(200))
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    amount = db.Column(db.Integer)
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    invoice_path = db.Column(db.String(200))

class JobSource(db.Model):
    __tablename__ = 'job_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    api_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    last_fetched = db.Column(db.DateTime)