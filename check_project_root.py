from app import app, db, Job

with app.app_context():
    jobs = Job.query.all()
    print(f"Total jobs in DB: {len(jobs)}")
    for job in jobs:
        print(f"ID: {job.id} | Title: {job.title} | Approved: {job.is_approved} | Posted by: {job.posted_by}")