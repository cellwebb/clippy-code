# Flask Web Application Example

## 🎯 Scenario

Create a complete Flask web application with:
- User authentication system
- Database models (SQLite)
- HTML templates with Bootstrap
- RESTful API endpoints
- Configuration management
- Error handling
- Testing setup

## 🚀 Quick Start

```bash
# Navigate to this directory
cd examples/web_development/flask_app

# Create the complete Flask app
clippy "Create a complete Flask web application with user authentication, SQLite database, Bootstrap templates, and REST API endpoints. Include proper configuration, error handling, and testing setup."
```

## 📁 Expected Project Structure

```
flask_app/
├── app/
│   ├── __init__.py
│   ├── models.py          # Database models
│   ├── routes.py          # Flask routes
│   ├── auth.py            # Authentication routes
│   ├── api.py             # REST API endpoints
│   ├── templates/         # HTML templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   └── dashboard.html
│   └── static/            # CSS, JS, images
│       ├── css/
│       ├── js/
│       └── img/
├── config.py              # Flask configuration
├── requirements.txt       # Python dependencies
├── run.py                 # Application runner
├── tests/                 # Test files
├── .env.example           # Environment variables template
└── README.md              # Project documentation
```

## 🛠️ Step-by-Step Commands

### 1. Create Basic Flask Structure
```bash
clippy "Create a basic Flask application structure with app/__init__.py, config.py, and run.py"
```

### 2. Add Database Models
```bash
clippy "Add SQLAlchemy models for User with id, username, email, password_hash, and created_at fields. Include database initialization."
```

### 3. Implement Authentication
```bash
clippy "Create Flask routes for user registration, login, logout with password hashing using werkzeug"
```

### 4. Create HTML Templates
```bash
clippy "Create Bootstrap 5 templates for login, register, dashboard, and base template with navigation"
```

### 5. Add REST API
```bash
clippy "Create RESTful API endpoints for user management with JSON responses and error handling"
```

### 6. Add Configuration
```bash
clippy "Create Flask configuration with development, testing, and production environments using environment variables"
```

### 7. Setup Testing
```bash
clippy "Create pytest tests for the Flask application with fixtures for testing database operations"
```

## 💡 Advanced Features

### Add API Authentication
```bash
clippy "Add JWT token authentication for the REST API endpoints with login and refresh tokens"
```

### Add File Upload
```bash
clippy "Add file upload functionality for user profile pictures with secure file handling"
```

### Add Email Support
```bash
clippy "Add email verification for user registration using Flask-Mail"
```

## 🔍 Validation Examples

clippy-code will automatically validate the syntax of all files:

```bash
# ✅ Python files validated for syntax errors
clippy "Create routes.py with Flask blueprints"

# ✅ JSON config files validated for structure
clippy "Create package.json with development dependencies"

# ✅ HTML templates validated for proper tags
clippy "Create responsive Bootstrap templates"

# ❌ Binary files detected and rejected with guidance
# clippy "Create a logo file" 
# → "Binary file .png detected - use skip_validation=True"
```

## 📝 Example Session

```
$ clippy
> Create a Flask app with user authentication

🤖 I'll create a complete Flask application with user authentication.

📋 Plan:
1. Create project structure
2. Setup Flask configuration
3. Create User model with SQLAlchemy
4. Implement authentication routes
5. Create HTML templates
6. Add REST API endpoints

🎯 Starting with project structure...

✅ Successfully wrote to app/__init__.py
✅ Successfully wrote to config.py
✅ Successfully wrote to run.py

🤖 Now creating the User model...

✅ Successfully wrote to app/models.py (SQLAlchemy User model created)

🤖 Implementing authentication routes...

✅ Successfully wrote to app/auth.py
✅ Successfully wrote to app/routes.py

🤖 Creating HTML templates...

✅ Successfully wrote to app/templates/base.html
✅ Successfully wrote to app/templates/login.html
✅ Successfully wrote to app/templates/register.html

🤖 Adding REST API...

✅ Successfully wrote to app/api.py
✅ Successfully wrote to requirements.txt

🎉 Flask application created successfully!
Run: `python run.py` to start the development server
```

## 🧪 Testing the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Run the app
python run.py

# Run tests
pytest tests/
```

## 🎯 Customization Ideas

- Add different user roles (admin, user, moderator)
- Implement OAuth integration (Google, GitHub)
- Add caching with Redis
- Add database migrations with Alembic
- Add API rate limiting
- Add CORS support for frontend integration

## 🔧 Troubleshooting

### Common Issues:
```bash
# Database errors
clippy "Fix SQLAlchemy connection issues in Flask config"

# Template not found
clippy "Fix Flask template path configuration"

# Import errors
clippy "Fix circular import issues in Flask application structure"
```