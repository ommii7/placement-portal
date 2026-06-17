import os

def check_templates():
    templates_dir = 'templates'
    required_templates = [
        'base.html',
        'index.html',
        'register.html',
        'login.html',
        'student_dashboard.html',
        'student_profile.html',
        'hr_dashboard.html',
        'admin_dashboard.html',
        'admin_jobs_approval.html',
        'admin_revenue.html',
        'post_job.html',
        'payment.html',
        'resume_upload.html',
        'invoice.html',
        'browse_jobs.html',
        'job_detail.html'
    ]
    
    print("Checking template files...")
    print("-" * 50)
    
    missing_files = []
    existing_files = []
    
    for template in required_templates:
        file_path = os.path.join(templates_dir, template)
        if os.path.exists(file_path):
            existing_files.append(template)
            print(f"✓ {template} - FOUND")
        else:
            missing_files.append(template)
            print(f"✗ {template} - MISSING")
    
    print("-" * 50)
    print(f"\nSummary:")
    print(f"Found: {len(existing_files)}/{len(required_templates)} files")
    
    if missing_files:
        print(f"\nMissing {len(missing_files)} file(s):")
        for file in missing_files:
            print(f"  - {file}")
        return False
    else:
        print("\nAll template files are present!")
        return True

if __name__ == '__main__':
    check_templates()