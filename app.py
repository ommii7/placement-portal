from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Job, Application, Subscription, Document, Transaction, JobSource
from resume_parser import ResumeParser
from payment_handler import PaymentHandler
from email_service import EmailService
from admin_workflow import AdminWorkflow
from invoice_generator import InvoiceGenerator
from datetime import datetime, timedelta
import os
import json
import requests
from bs4 import BeautifulSoup
from werkzeug.utils import secure_filename
import requests
from flask import flash, redirect, url_for
from flask_login import login_required, current_user
from models import Job, db


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['DOCUMENT_FOLDER'] = 'static/documents'
app.config['INVOICE_FOLDER'] = 'static/invoices'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Services
resume_parser = ResumeParser()
payment_handler = PaymentHandler()
email_service = EmailService()
admin_workflow = AdminWorkflow()
invoice_generator = InvoiceGenerator()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------- Helper: Fetch external jobs (simulated) ----------
def fetch_external_jobs():
    """Simulate fetching jobs from Google, Indeed, LinkedIn."""
    # In real scenario, you'd use APIs or scraping. Here we create sample external jobs.
    external_jobs = [
        {
            'title': 'Software Engineer (Google)',
            'company': 'Google',
            'description': 'Build next-gen cloud solutions. Requires strong coding skills.',
            'requirements': 'BS in CS, 2+ years experience',
            'salary_min': 15,
            'salary_max': 30,
            'location': 'Bangalore',
            'job_type': 'Full-time',
            'application_link': 'https://careers.google.com',
            'source': 'google'
        },
        {
            'title': 'Data Scientist (Indeed)',
            'company': 'Indeed',
            'description': 'Work on massive job recommendation systems.',
            'requirements': 'Python, ML, SQL',
            'salary_min': 12,
            'salary_max': 25,
            'location': 'Remote',
            'job_type': 'Full-time',
            'application_link': 'https://indeed.com/careers',
            'source': 'indeed'
        },
        {
            'title': 'Frontend Developer (LinkedIn)',
            'company': 'LinkedIn',
            'description': 'Create responsive UI for millions of users.',
            'requirements': 'React, HTML/CSS, JavaScript',
            'salary_min': 10,
            'salary_max': 20,
            'location': 'Hyderabad',
            'job_type': 'Full-time',
            'application_link': 'https://linkedin.com/jobs',
            'source': 'linkedin'
        }
    ]
    for job_data in external_jobs:
        # Check if already exists
        existing = Job.query.filter_by(title=job_data['title'], company=job_data['company']).first()
        if not existing:
            job = Job(
                title=job_data.get('title', 'No Title'),
                company=job_data.get('companyName', 'Unknown'),
                description=job_data.get('excerpt', '')[:500],
                location=job_data.get('location', 'Remote'),
                salary_min=job_data.get('minSalary'),
                salary_max=job_data.get('maxSalary'),
                application_link=job_data.get('applicationLink'),
                source='himalayas',
                is_approved=False,          # <-- CRITICAL: requires admin approval
                is_premium=False
            )
            db.session.add(job)
    db.session.commit()

# ---------- Routes ----------
@app.route('/')
def index():
    recent_jobs = Job.query.filter_by(is_approved=True).order_by(Job.created_at.desc()).limit(6).all()
    return render_template('index.html', recent_jobs=recent_jobs)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if password != confirm:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))
        
        user = User(email=email, full_name=full_name, role=role, phone=request.form.get('phone'))
        user.set_password(password)
        
        if role == 'student':
            user.college = request.form.get('college')
            user.course = request.form.get('course')
            user.graduation_year = request.form.get('graduation_year', type=int)
            user.bio = request.form.get('bio')
            user.skills = request.form.get('skills')
            # Resume upload
            if 'resume' in request.files:
                file = request.files['resume']
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"resume_{email}_{file.filename}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    user.resume_path = filepath
                    # Parse resume
                    parsed = resume_parser.parse_resume(filepath)
                    user.resume_parsed_data = json.dumps(parsed)
                    if parsed.get('skills'):
                        user.skills = ', '.join(parsed['skills'])
        elif role == 'hr':
            user.company_name = request.form.get('company_name')
            user.company_website = request.form.get('company_website')
            user.company_description = request.form.get('company_description')
            user.industry = request.form.get('industry')
            user.designation = request.form.get('designation')
            if 'company_logo' in request.files:
                file = request.files['company_logo']
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"logo_{email}_{file.filename}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    user.company_logo = filepath
        
        db.session.add(user)
        db.session.commit()
        email_service.send_welcome_email(email, full_name, role)
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_revenue'))
            elif user.role == 'hr':
                return redirect(url_for('hr_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid email or password!', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# -------------------- Student --------------------
@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('index'))
    
    recommended_jobs = Job.query.filter_by(is_approved=True).order_by(Job.created_at.desc()).limit(6).all()
    applications = Application.query.filter_by(student_id=current_user.id).all()
    is_subscribed = current_user.is_subscription_active()  # This is the key variable
    
    return render_template('student_dashboard.html', 
                         recommended_jobs=recommended_jobs,
                         applications=applications,
                         is_subscribed=is_subscribed)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update text fields
        current_user.full_name = request.form.get('full_name')
        current_user.phone = request.form.get('phone')
        current_user.bio = request.form.get('bio')
        current_user.college = request.form.get('college')
        current_user.course = request.form.get('course')
        current_user.graduation_year = request.form.get('graduation_year', type=int)
        current_user.cgpa = request.form.get('cgpa', type=float)
        current_user.skills = request.form.get('skills')
        current_user.experience = request.form.get('experience')
        current_user.certifications = request.form.get('certifications')
        current_user.portfolio_url = request.form.get('portfolio_url')
        current_user.expected_salary = request.form.get('expected_salary', type=float)

        # Profile picture upload
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename and allowed_file(file.filename):
                # Create safe filename
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f"profile_{current_user.id}_{int(datetime.now().timestamp())}.{ext}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                # Store relative path
                current_user.profile_picture = f"uploads/{filename}"
                print(f"Profile picture saved: {current_user.profile_picture}")
                flash('Profile picture updated!', 'success')
            else:
                flash('Invalid file type for profile picture', 'danger')

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('student_profile.html')

@app.route('/upload-resume', methods=['GET', 'POST'])
@login_required
def upload_resume():
    if request.method == 'POST' and 'resume' in request.files:
        file = request.files['resume']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"resume_{current_user.id}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            current_user.resume_path = filepath
            parsed = resume_parser.parse_resume(filepath)
            current_user.resume_parsed_data = json.dumps(parsed)
            if parsed.get('skills'):
                current_user.skills = ', '.join(parsed['skills'])
            db.session.commit()
            flash('Resume uploaded and parsed!', 'success')
            return redirect(url_for('profile'))
    return render_template('resume_upload.html')

# -------------------- Document Locker --------------------
@app.route('/documents')
@login_required
def documents():
    docs = Document.query.filter_by(user_id=current_user.id).all()
    return render_template('documents.html', documents=docs)

@app.route('/upload-document', methods=['POST'])
@login_required
def upload_document():
    doc_type = request.form.get('document_type')
    if 'document' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('documents'))
    file = request.files['document']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('documents'))
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{current_user.id}_{doc_type}_{file.filename}")
        filepath = os.path.join(app.config['DOCUMENT_FOLDER'], filename)
        file.save(filepath)
        doc = Document(
            user_id=current_user.id,
            document_type=doc_type,
            file_name=file.filename,
            file_path=filepath,
            file_size=os.path.getsize(filepath)
        )
        db.session.add(doc)
        db.session.commit()
        flash('Document uploaded successfully!', 'success')
    else:
        flash('Invalid file type', 'danger')
    return redirect(url_for('documents'))

# -------------------- Jobs & Application --------------------
@app.route('/jobs')
def jobs():
    page = request.args.get('page', 1, type=int)
    jobs_list = Job.query.filter_by(is_approved=True).order_by(Job.created_at.desc()).paginate(page=page, per_page=12)
    return render_template('jobs.html', jobs=jobs_list)

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('job_detail.html', job=job)

@app.route('/apply/<int:job_id>', methods=['POST'])
@login_required
def apply_job(job_id):
    if current_user.role != 'student':
        flash('Only students can apply', 'danger')
        return redirect(url_for('job_detail', job_id=job_id))
    job = Job.query.get_or_404(job_id)
    # Check premium requirement
    if job.is_premium and not current_user.is_subscription_active():
        flash('This is a premium job (₹5+ LPA). Please subscribe to apply.', 'warning')
        return redirect(url_for('payment'))
    existing = Application.query.filter_by(student_id=current_user.id, job_id=job_id).first()
    if existing:
        flash('You have already applied for this job', 'info')
    else:
        app_obj = Application(student_id=current_user.id, job_id=job_id, status='pending')
        db.session.add(app_obj)
        db.session.commit()
        email_service.send_application_confirmation(current_user.email, job.title, job.company)
        flash('Application submitted!', 'success')
    return redirect(url_for('student_dashboard'))

# -------------------- HR Routes --------------------
@app.route('/hr/dashboard')
@login_required
def hr_dashboard():
    if current_user.role != 'hr':
        return redirect(url_for('index'))
    jobs = Job.query.filter_by(posted_by=current_user.id).all()
    return render_template('hr_dashboard.html', jobs=jobs)

@app.route('/hr/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    if current_user.role != 'hr':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        salary_min = request.form.get('salary_min', type=float)
        salary_max = request.form.get('salary_max', type=float)

        # Convert None to 0, and ensure they are numbers
        salary_min = salary_min if salary_min is not None else 0
        salary_max = salary_max if salary_max is not None else 0

        # Optional: round to 1 decimal
        salary_min = round(salary_min, 1)
        salary_max = round(salary_max, 1)
        salary_max: float | int = salary_max if salary_max is not None else 0

        job = Job(
            title=request.form.get('title'),
            company=current_user.company_name or request.form.get('company'),
            description=request.form.get('description'),
            requirements=request.form.get('requirements'),
            salary_min=salary_min,   # now a float
            salary_max=salary_max,
            location=request.form.get('location'),
            job_type=request.form.get('job_type'),
            skills_required=request.form.get('skills_required'),
            application_link=request.form.get('application_link'),
            posted_by=current_user.id,
            is_premium=(salary_max >= 5),   # premium if max >= 5 LPA
            is_approved=False               # wait for admin approval
        )
        
        db.session.add(job)
        db.session.commit()
        
        print(f"Job posted: {job.title}, Approved: {job.is_approved}")  # Debug
        
        flash('Job posted successfully and is now live!', 'success')
        return redirect(url_for('hr_dashboard'))
    
    return render_template('post_job.html')

@app.route('/hr/application/<int:app_id>/approve')
@login_required
def hr_approve_application(app_id):
    if current_user.role != 'hr':
        return redirect(url_for('index'))
    app = Application.query.get_or_404(app_id)
    job = Job.query.get(app.job_id)
    if job.posted_by != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('hr_dashboard'))
    app.status = 'shortlisted'
    db.session.commit()
    flash(f'Application from {app.student.full_name or app.student.email} has been approved (shortlisted).', 'success')
    return redirect(url_for('hr_job_applications', job_id=job.id))

@app.route('/hr/application/<int:app_id>/reject')
@login_required
def hr_reject_application(app_id):
    if current_user.role != 'hr':
        return redirect(url_for('index'))
    app = Application.query.get_or_404(app_id)
    job = Job.query.get(app.job_id)
    if job.posted_by != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('hr_dashboard'))
    app.status = 'rejected'
    db.session.commit()
    flash(f'Application from {app.student.full_name or app.student.email} has been rejected.', 'danger')
    return redirect(url_for('hr_job_applications', job_id=job.id))

@app.route('/job/<int:job_id>/hr-details')
@login_required
def job_hr_details(job_id):
    job = Job.query.get_or_404(job_id)
    
    # If job was posted by an HR user
    if job.posted_by:
        hr = User.query.get(job.posted_by)
        if hr and hr.role == 'hr':
            return jsonify({
                'company_name': hr.company_name,
                'company_website': hr.company_website,
                'hr_name': hr.full_name,
                'hr_email': hr.email,
                'hr_phone': hr.phone,
                'source': 'hr'
            })
    
    # For external jobs (no HR) – show job details and admin contact
    return jsonify({
        'company_name': job.company,
        'company_website': job.application_link or '#',
        'hr_name': 'Placement Portal Admin',
        'hr_email': 'admin@placementportal.com',
        'hr_phone': '+91-98765 43210',
        'source': 'external',
        'message': 'This is an external job listing. For any queries, please contact the admin or apply directly using the link below.'
    })


@app.route('/hr/application/<int:app_id>/status', methods=['POST'])
@login_required
def hr_update_application_status(app_id):
    if current_user.role != 'hr':
        return redirect(url_for('index'))
    app = Application.query.get_or_404(app_id)
    job = Job.query.get(app.job_id)
    if job.posted_by != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('hr_dashboard'))
    new_status = request.form.get('status')
    if new_status in ['pending', 'shortlisted', 'rejected', 'hired']:
        app.status = new_status
        db.session.commit()
        flash(f'Application status updated to {new_status}.', 'success')
    else:
        flash('Invalid status.', 'danger')
    return redirect(url_for('hr_job_applications', job_id=job.id))

@app.route('/hr/job/<int:job_id>/applications')
@login_required
def hr_job_applications(job_id):
    if current_user.role != 'hr':
        return redirect(url_for('index'))
    job = Job.query.get_or_404(job_id)
    if job.posted_by != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('hr_dashboard'))
    applications = Application.query.filter_by(job_id=job_id).all()
    return render_template('hr_applications.html', job=job, applications=applications)

@login_required
def hr_update_application_status(app_id):
    if current_user.role != 'hr':
        return redirect(url_for('index'))
    app = Application.query.get_or_404(app_id)
    job = Job.query.get(app.job_id)
    if job.posted_by != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('hr_dashboard'))
    new_status = request.form.get('status')
    if new_status in ['pending', 'shortlisted', 'rejected', 'hired']:
        app.status = new_status
        db.session.commit()
        flash(f'Application status updated to {new_status}.', 'success')
    else:
        flash('Invalid status.', 'danger')
    return redirect(url_for('hr_job_applications', job_id=job.id))

# -------------------- Admin Routes --------------------
@app.route('/admin/revenue')
@login_required
def admin_revenue():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    total_revenue = db.session.query(db.func.sum(Subscription.amount)).filter_by(payment_status='completed').scalar() or 0
    total_users = User.query.count()
    pending_jobs = Job.query.filter_by(is_approved=False).all()
    approved_jobs = Job.query.filter_by(is_approved=True).count()
    
    return render_template('admin_revenue.html',
                         total_revenue=total_revenue,
                         total_users=total_users,
                         pending_jobs=pending_jobs,
                         approved_jobs=approved_jobs)

# Admin approval
@app.route('/admin/approve-external/<int:job_id>')
@login_required
def approve_external_job(job_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    job = Job.query.get_or_404(job_id)
    job.is_approved = True
    db.session.commit()
    flash(f'External job "{job.title}" approved and published.', 'success')
    return redirect(url_for('admin_external_jobs'))

# Admin approve any job (HR or external)
@app.route('/admin/approve/<int:job_id>')
@login_required
def approve_job(job_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    job = Job.query.get_or_404(job_id)
    job.is_approved = True
    db.session.commit()
    flash(f'Job "{job.title}" has been approved and is now visible to students.', 'success')
    return redirect(url_for('admin_revenue'))

@app.route('/admin/external-jobs')
@login_required
def admin_external_jobs():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    external_sources = ['google', 'indeed', 'linkedin', 'himalayas', 'remotive', 
                        'stackoverflow', 'weworkremotely', 'jsearch', 'adzuna']
    external_pending = Job.query.filter(
        Job.source.in_(external_sources),
        Job.is_approved == False
    ).all()
    return render_template('admin_external_jobs.html', jobs=external_pending)
# Admin reject a job (delete it)
@app.route('/admin/reject/<int:job_id>')
@login_required
def admin_reject_job(job_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    job = Job.query.get_or_404(job_id)
    title = job.title
    db.session.delete(job)
    db.session.commit()
    flash(f'Job "{title}" has been rejected and deleted.', 'danger')
    return redirect(url_for('admin_revenue'))

@app.route('/admin/all-jobs')
@login_required
def admin_all_jobs():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    return render_template('admin_all_jobs.html', jobs=jobs)

@app.route('/admin/delete/<int:job_id>')
@login_required
def admin_delete_job(job_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    job = Job.query.get_or_404(job_id)
    title = job.title
    db.session.delete(job)
    db.session.commit()
    flash(f'Job "{title}" deleted.', 'success')
    return redirect(url_for('admin_all_jobs'))

@app.route('/admin/applications')
@login_required
def admin_applications():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    applications = Application.query.order_by(Application.applied_at.desc()).all()
    total = len(applications)
    pending = Application.query.filter_by(status='pending').count()
    shortlisted = Application.query.filter_by(status='shortlisted').count()
    rejected = Application.query.filter_by(status='rejected').count()
    hired = Application.query.filter_by(status='hired').count()
    return render_template('admin_applications.html',
                         applications=applications,
                         total=total,
                         pending=pending,
                         shortlisted=shortlisted,
                         rejected=rejected,
                         hired=hired)


@app.route('/admin/student/<int:user_id>')
@login_required
def admin_student_details(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    student = User.query.get_or_404(user_id)
    if student.role != 'student':
        flash('Not a student account.', 'danger')
        return redirect(url_for('admin_applications'))
    return render_template('admin_student_details.html', student=student)

@app.route('/admin/application/<int:app_id>/shortlist')
@login_required
def admin_shortlist_application(app_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    app = Application.query.get_or_404(app_id)
    app.status = 'shortlisted'
    db.session.commit()
    flash(f'Application from {app.student.full_name or app.student.email} shortlisted.', 'success')
    return redirect(url_for('admin_applications'))

@app.route('/admin/application/<int:app_id>/reject')
@login_required
def admin_reject_application(app_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    app = Application.query.get_or_404(app_id)
    app.status = 'rejected'
    db.session.commit()
    flash(f'Application from {app.student.full_name or app.student.email} rejected.', 'danger')
    return redirect(url_for('admin_applications'))

@app.route('/admin/application/<int:app_id>/hire')
@login_required
def admin_hire_application(app_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    app = Application.query.get_or_404(app_id)
    app.status = 'hired'
    db.session.commit()
    flash(f'Student {app.student.full_name or app.student.email} marked as hired!', 'success')
    return redirect(url_for('admin_applications'))
# Fetch external jobs (simulated)

@app.route('/admin/fetch-external-jobs')
@login_required
def fetch_external():
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    added_count = 0
    base_url = "https://himalayas.app/jobs/api"
    limit = 50               # Max jobs per request
    max_jobs_to_fetch = 100  # Total limit

    try:
        offset = 0
        while offset < max_jobs_to_fetch:
            params = {'limit': limit, 'offset': offset}
            resp = requests.get(base_url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            jobs = data.get('jobs', [])
            if not jobs:
                break

            for job_data in jobs:
                # Skip if job already exists (check by title and company)
                existing = Job.query.filter_by(
                    title=job_data.get('title'),
                    company=job_data.get('companyName')
                ).first()
                if existing:
                    continue

                # Create new job
                new_job = Job(
                    title=job_data.get('title', 'No Title'),
                    company=job_data.get('companyName', 'Unknown'),
                    description=job_data.get('excerpt', '')[:500],
                    location=job_data.get('location', 'Remote'),
                    salary_min=job_data.get('minSalary'),
                    salary_max=job_data.get('maxSalary'),
                    application_link=job_data.get('applicationLink'),
                    source='himalayas',
                    is_approved=True,
                    is_premium=False,
                    job_type=job_data.get('jobType', 'fulltime').capitalize()
                )
                db.session.add(new_job)
                added_count += 1

            offset += limit

        db.session.commit()
        flash(f'Successfully added {added_count} remote jobs from Himalayas!', 'success')

    except requests.exceptions.RequestException as e:
        flash(f'Error fetching jobs: {e}', 'danger')
        print(f"Himalayas API error: {e}")
    except Exception as e:
        db.session.rollback()
        flash(f'Unexpected error: {e}', 'danger')
        print(f"Unexpected error: {e}")

    return redirect(url_for('admin_revenue'))
# HR: Delete only their own jobs
@app.route('/hr/delete-job/<int:job_id>')
@login_required
def hr_delete_job(job_id):
    if current_user.role != 'hr':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    job = Job.query.get_or_404(job_id)
    if job.posted_by != current_user.id:
        flash('You can only delete your own jobs.', 'danger')
        return redirect(url_for('hr_dashboard'))
    
    title = job.title
    db.session.delete(job)
    db.session.commit()
    flash(f'Your job "{title}" has been deleted.', 'success')
    return redirect(url_for('hr_dashboard'))

# -------------------- Create DB & Admin --------------------
with app.app_context():
    db.create_all()
    if not User.query.filter_by(role='admin').first():
        admin = User(email='admin_placement@portal.com', full_name='Admin', role='admin', is_active=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin created: admin_placement@portal.com / admin123")
    # Add job sources if empty
    if JobSource.query.count() == 0:
        sources = [
            JobSource(name='Google Jobs', api_url='https://www.google.com/search?q=jobs', is_active=True),
            JobSource(name='Indeed', api_url='https://www.indeed.com', is_active=True),
            JobSource(name='LinkedIn', api_url='https://www.linkedin.com/jobs', is_active=True)
        ]
        db.session.add_all(sources)
        db.session.commit()
    # Fetch external jobs once on startup
    fetch_external_jobs()
@app.route('/admin/pending-jobs')
@login_required
def admin_pending_jobs():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    pending_jobs = Job.query.filter_by(is_approved=False).all()
    return render_template('admin_jobs_approval.html', jobs=pending_jobs)

@app.route('/debug-external-jobs')
@login_required
def debug_external_jobs():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    external_sources = ['google', 'indeed', 'linkedin', 'himalayas', 'remotive', 'stackoverflow', 'weworkremotely', 'jsearch', 'adzuna']
    external_jobs = Job.query.filter(Job.source.in_(external_sources), Job.is_approved == False).all()
    all_jobs = Job.query.all()
    return f"""
    External pending jobs: {len(external_jobs)}<br>
    All jobs: {len(all_jobs)}<br>
    Job sources: {[j.source for j in all_jobs]}<br>
    Pending job IDs: {[j.id for j in external_jobs]}
    """

@app.route('/debug-subscription')
@login_required
def debug_subscription():
    return f"""
    User: {current_user.email}<br>
    is_subscribed: {current_user.is_subscribed}<br>
    subscription_end_date: {current_user.subscription_end_date}<br>
    is_active: {current_user.is_subscription_active()}
    """
@app.route('/cancel-subscription')
@login_required
def cancel_subscription():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    if not current_user.is_subscribed:
        flash('You don\'t have an active subscription.', 'warning')
        return redirect(url_for('student_dashboard'))
    
    # Cancel subscription
    current_user.is_subscribed = False
    current_user.subscription_end_date = None
    
    # Mark the latest subscription record as cancelled (using id instead of created_at)
    latest_sub = Subscription.query.filter_by(
        user_id=current_user.id,
        payment_status='completed'
    ).order_by(Subscription.id.desc()).first()
    if latest_sub:
        latest_sub.payment_status = 'cancelled'
    
    db.session.commit()
    flash('Your subscription has been cancelled. No refund will be issued.', 'danger')
    return redirect(url_for('student_dashboard'))

@app.route('/upgrade-plan', methods=['GET', 'POST'])
@login_required
def upgrade_plan():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    if not current_user.is_subscribed:
        flash('You need an active subscription to upgrade.', 'warning')
        return redirect(url_for('payment'))
    
    # Get the user's current plan from their latest subscription
    latest_sub = Subscription.query.filter_by(
        user_id=current_user.id,
        payment_status='completed'
    ).order_by(Subscription.id.desc()).first()
    
    current_plan = latest_sub.plan if latest_sub else 'monthly'
    
    # Define upgrade options based on current plan
    upgrade_options = []
    if current_plan == 'monthly':
        upgrade_options = [
            {'name': 'Quarterly', 'price': 999, 'days': 90, 'savings': 198, 'badge': 'Save ₹198', 'color': 'success'},
            {'name': 'Yearly', 'price': 3499, 'days': 365, 'savings': 1289, 'badge': 'Best Value', 'color': 'info'}
        ]
    elif current_plan == 'quarterly':
        upgrade_options = [
            {'name': 'Yearly', 'price': 3499, 'days': 365, 'savings': 1298, 'badge': 'Save ₹1,298', 'color': 'info'}
        ]
    # else: yearly plan – no upgrades
    
    if request.method == 'POST':
        new_plan = request.form.get('plan')
        if new_plan not in [opt['name'].lower() for opt in upgrade_options]:
            flash('Invalid upgrade option.', 'danger')
            return redirect(url_for('upgrade_plan'))
        
        # Find selected plan details
        selected = next(opt for opt in upgrade_options if opt['name'].lower() == new_plan)
        amount = selected['price']
        days = selected['days']
        
        # Simulate payment
        result = payment_handler.process_payment(amount, current_user.email)
        if result.get('success'):
            # Extend subscription end date (no refund for remaining time)
            current_user.subscription_end_date = datetime.utcnow() + timedelta(days=days)
            
            # Create new subscription record
            sub = Subscription(
                user_id=current_user.id,
                plan=new_plan,
                amount=amount,
                payment_id=result.get('payment_id'),
                payment_status='completed',
                end_date=current_user.subscription_end_date
            )
            db.session.add(sub)
            db.session.commit()
            
            flash(f'Successfully upgraded to {selected["name"]} plan!', 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash('Payment failed. Please try again.', 'danger')
            return redirect(url_for('upgrade_plan'))
    
    return render_template('upgrade_plan.html', 
                         current_plan=current_plan,
                         upgrade_options=upgrade_options)

@app.route('/create-subscription', methods=['POST'])
@login_required
def create_subscription():
    plan = request.form.get('plan', 'monthly')
    plans = {
        'monthly': {'price': 399, 'days': 30, 'name': 'Monthly'},
        'quarterly': {'price': 999, 'days': 90, 'name': 'Quarterly'},
        'yearly': {'price': 3499, 'days': 365, 'name': 'Yearly'}
    }
    
    if plan not in plans:
        flash('Invalid plan selected.', 'danger')
        return redirect(url_for('payment'))
    
    plan_info = plans[plan]
    amount = plan_info['price']
    days = plan_info['days']
    
    # Simulate successful payment (for demo)
    # Ensure payment_handler.process_payment returns a dict with 'success' key
    try:
        result = payment_handler.process_payment(amount, current_user.email)
        payment_success = result.get('success', False)
        payment_id = result.get('payment_id', 'DEMO123')
    except Exception:
        # Fallback if payment_handler fails
        payment_success = True
        payment_id = 'DEMO123'
    
    if payment_success:
        end_date = datetime.utcnow() + timedelta(days=days)
        
        sub = Subscription(
            user_id=current_user.id,
            plan=plan,
            amount=amount,
            payment_id=payment_id,
            payment_status='completed',
            end_date=end_date
        )
        db.session.add(sub)
        
        current_user.is_subscribed = True
        current_user.subscription_end_date = end_date
        db.session.commit()
        
        flash(f'Successfully subscribed to {plan_info["name"]} plan!', 'success')
        return redirect(url_for('premium_jobs'))
    else:
        flash('Payment failed. Please try again.', 'danger')
        return redirect(url_for('payment'))
    
@app.route('/premium-jobs')
@login_required
def premium_jobs():
    if not current_user.is_subscription_active():
        flash('Please subscribe to access premium jobs.', 'warning')
        return redirect(url_for('payment'))
    page = request.args.get('page', 1, type=int)
    jobs = Job.query.filter_by(is_premium=True, is_approved=True).paginate(page=page, per_page=12)
    return render_template('premium_jobs.html', jobs=jobs)

from flask import send_file, abort
import os

@app.route('/document/view/<int:doc_id>')
@login_required
def view_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if doc.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    if not os.path.exists(doc.file_path):
        abort(404)
    return send_file(doc.file_path, as_attachment=False)

@app.route('/document/download/<int:doc_id>')
@login_required
def download_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if doc.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    if not os.path.exists(doc.file_path):
        abort(404)
    return send_file(doc.file_path, as_attachment=True, download_name=doc.file_name)

@app.route('/document/delete/<int:doc_id>')
@login_required
def delete_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if doc.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    # Delete the physical file
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.session.delete(doc)
    db.session.commit()
    flash('Document deleted successfully.', 'success')
    return redirect(url_for('documents'))

# ==================== ADMIN USER MANAGEMENT ====================

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    role_filter = request.args.get('role', 'all')
    if role_filter == 'student':
        users = User.query.filter_by(role='student').all()
    elif role_filter == 'hr':
        users = User.query.filter_by(role='hr').all()
    else:
        users = User.query.all()
    
    total_students = User.query.filter_by(role='student').count()
    total_hr = User.query.filter_by(role='hr').count()
    total_active = User.query.filter_by(is_active=True).count()
    total_blocked = User.query.filter_by(is_active=False).count()
    
    return render_template('admin_users.html',
                         users=users,
                         total_students=total_students,
                         total_hr=total_hr,
                         total_active=total_active,
                         total_blocked=total_blocked,
                         role_filter=role_filter)

@app.route('/admin/user/<int:user_id>')
@login_required
def admin_user_detail(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    user = User.query.get_or_404(user_id)
    return render_template('admin_user_detail.html', user=user)

@app.route('/admin/block-user/<int:user_id>')
@login_required
def admin_block_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Cannot block admin user', 'danger')
        return redirect(url_for('admin_users'))
    user.is_active = not user.is_active
    db.session.commit()
    status = 'blocked' if not user.is_active else 'unblocked'
    flash(f'User {user.email} has been {status}.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/delete-user/<int:user_id>')
@login_required
def admin_delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Cannot delete admin user', 'danger')
        return redirect(url_for('admin_users'))
    email = user.email
    # Delete related records
    if user.role == 'student':
        Application.query.filter_by(student_id=user.id).delete()
        Subscription.query.filter_by(user_id=user.id).delete()
        Document.query.filter_by(user_id=user.id).delete()
        Transaction.query.filter_by(user_id=user.id).delete()
    elif user.role == 'hr':
        Job.query.filter_by(posted_by=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash(f'User {email} has been permanently deleted.', 'danger')
    return redirect(url_for('admin_users'))

@app.route('/payment')
@login_required
def payment():
    return render_template('payment.html')

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DOCUMENT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['INVOICE_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)