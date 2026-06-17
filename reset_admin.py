from app import app, db, User

with app.app_context():
    admin = User.query.filter_by(email='admin_placement@portal.com').first()
    if admin:
        print(f"Found admin: {admin.email}")
        admin.set_password('admin123')
        db.session.commit()
        print("Password reset to: admin123")
        # Verify
        if admin.check_password('admin123'):
            print("✅ Verification successful!")
        else:
            print("❌ Verification failed")
    else:
        print("Admin not found. Creating new one...")
        admin = User(email='admin_placement@portal.com', full_name='Admin', role='admin', is_active=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin created with admin123")