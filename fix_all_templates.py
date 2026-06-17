import os

# Ensure templates folder exists
os.makedirs('templates', exist_ok=True)

# Content for job_detail.html
content = """{% extends "base.html" %}

{% block title %}{{ job.title }} at {{ job.company }}{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-8">
        <div class="card shadow-sm">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <h2>{{ job.title }}</h2>
                    {% if job.is_premium %}
                        <span class="premium-badge fs-6"><i class="fas fa-crown"></i> Premium (5+ LPA)</span>
                    {% endif %}
                </div>
                <h5 class="text-muted">{{ job.company }}</h5>
                <hr>
                <p><i class="fas fa-map-marker-alt"></i> {{ job.location }} &nbsp;|&nbsp; 
                   <i class="fas fa-briefcase"></i> {{ job.job_type }}</p>
                <p><strong>Salary:</strong> ₹{{ job.salary_min }} – ₹{{ job.salary_max }} LPA</p>
                <hr>
                <h5>Description</h5>
                <p>{{ job.description }}</p>
                <h5>Requirements</h5>
                <p>{{ job.requirements or 'Not specified' }}</p>
                <h5>Skills Required</h5>
                <p>{{ job.skills_required or 'Any' }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card shadow-sm">
            <div class="card-body text-center">
                <h5>How to Apply</h5>
                {% if current_user.is_authenticated and current_user.role == 'student' %}
                    {% if job.is_premium and not current_user.is_subscription_active() %}
                        <div class="alert alert-warning">
                            <i class="fas fa-lock"></i> Premium job requires subscription.<br>
                            <a href="{{ url_for('payment') }}" class="btn btn-warning btn-sm mt-2">Subscribe ₹399</a>
                        </div>
                    {% else %}
                        <form method="POST" action="{{ url_for('apply_job', job_id=job.id) }}">
                            <button type="submit" class="btn btn-success btn-lg w-100">Apply Now</button>
                        </form>
                    {% endif %}
                {% elif not current_user.is_authenticated %}
                    <a href="{{ url_for('login') }}" class="btn btn-primary w-100">Login to Apply</a>
                {% else %}
                    <div class="alert alert-info">Only students can apply.</div>
                {% endif %}
                {% if job.application_link %}
                    <hr>
                    <a href="{{ job.application_link }}" target="_blank" class="btn btn-outline-secondary w-100 mt-2">
                        <i class="fas fa-external-link-alt"></i> Apply on Company Site
                    </a>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

file_path = os.path.join('templates', 'job_detail.html')
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ File created: {os.path.abspath(file_path)}")
print("Now restart your Flask app: python app.py")