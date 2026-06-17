import os

# Ensure templates folder exists
os.makedirs('templates', exist_ok=True)

# Content for admin_users.html
content = '''{% extends "base.html" %}

{% block title %}User Management - Admin{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <h2><i class="fas fa-users me-2"></i>User Management</h2>
    <p class="text-muted">View, block/unblock, or delete users</p>

    <!-- Stats Cards -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="card bg-primary text-white shadow">
                <div class="card-body">
                    <h5>Total Students</h5>
                    <h2>{{ total_students }}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card bg-success text-white shadow">
                <div class="card-body">
                    <h5>Total HR</h5>
                    <h2>{{ total_hr }}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card bg-info text-white shadow">
                <div class="card-body">
                    <h5>Active Users</h5>
                    <h2>{{ total_active }}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card bg-warning text-dark shadow">
                <div class="card-body">
                    <h5>Blocked Users</h5>
                    <h2>{{ total_blocked }}</h2>
                </div>
            </div>
        </div>
    </div>

    <!-- Filter Buttons -->
    <div class="mb-3">
        <a href="{{ url_for('admin_users', role='all') }}" class="btn btn-secondary {% if role_filter == 'all' %}active{% endif %}">All</a>
        <a href="{{ url_for('admin_users', role='student') }}" class="btn btn-secondary {% if role_filter == 'student' %}active{% endif %}">Students</a>
        <a href="{{ url_for('admin_users', role='hr') }}" class="btn btn-secondary {% if role_filter == 'hr' %}active{% endif %}">HR</a>
    </div>

    <!-- Users Table -->
    <div class="card shadow">
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Role</th>
                            <th>Phone</th>
                            <th>College/Company</th>
                            <th>Registered</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for user in users %}
                        <tr>
                            <td>{{ user.id }}</td>
                            <td>{{ user.full_name or 'N/A' }}</td>
                            <td>{{ user.email }}</td>
                            <td>
                                {% if user.role == 'student' %}
                                    <span class="badge bg-primary">Student</span>
                                {% elif user.role == 'hr' %}
                                    <span class="badge bg-success">HR</span>
                                {% else %}
                                    <span class="badge bg-danger">Admin</span>
                                {% endif %}
                            </td>
                            <td>{{ user.phone or 'N/A' }}</td>
                            <td>
                                {% if user.role == 'student' %}
                                    {{ user.college or 'N/A' }}
                                {% else %}
                                    {{ user.company_name or 'N/A' }}
                                {% endif %}
                            </td>
                            <td>{{ user.created_at.strftime('%Y-%m-%d') if user.created_at else 'N/A' }}</td>
                            <td>
                                {% if user.is_active %}
                                    <span class="badge bg-success">Active</span>
                                {% else %}
                                    <span class="badge bg-danger">Blocked</span>
                                {% endif %}
                            </td>
                            <td>
                                <div class="btn-group btn-group-sm">
                                    {% if user.role != 'admin' %}
                                        <a href="{{ url_for('admin_block_user', user_id=user.id) }}" class="btn btn-warning" onclick="return confirm('Toggle block/unblock this user?')">
                                            {% if user.is_active %}
                                                <i class="fas fa-ban"></i> Block
                                            {% else %}
                                                <i class="fas fa-check-circle"></i> Unblock
                                            {% endif %}
                                        </a>
                                        <a href="{{ url_for('admin_delete_user', user_id=user.id) }}" class="btn btn-danger" onclick="return confirm('Delete this user permanently? All their data will be removed.')">
                                            <i class="fas fa-trash"></i> Delete
                                        </a>
                                    {% else %}
                                        <span class="text-muted">Protected</span>
                                    {% endif %}
                                </div>
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="9" class="text-center">No users found.</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

file_path = os.path.join('templates', 'admin_users.html')
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Template created at: {os.path.abspath(file_path)}")