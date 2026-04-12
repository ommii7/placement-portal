class EmailService:
    def send_welcome_email(self, email, name, role):
        print(f"WELCOME EMAIL to {email}: Hello {name}, welcome as {role}!")
    def send_application_confirmation(self, email, job_title, company):
        print(f"APPLICATION CONFIRMATION to {email}: Applied for {job_title} at {company}")
    def send_job_approval_notification(self, email, job_title):
        print(f"JOB APPROVED email to {email}: {job_title} approved")