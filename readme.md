# Task Manager

A robust task management system built with Django, featuring Pomodoro timing, Google authentication, and real-time notifications.

## 🚀 Features

- User authentication via email and Google OAuth2
- Task management with customizable categories
- Pomodoro timer integration for productivity
- Real-time notification system
- Multi-language support (Spanish localization included)
- Secure session management
- Mobile-responsive design

## 🛠 Tech Stack

- **Framework:** Django 5.1.2
- **Authentication:** django-allauth
- **Database:** SQLite3 (easily configurable for other backends)
- **Frontend:** Static files with CSS and JavaScript
- **Email:** SMTP integration (Gmail)
- **Development Tools:** python-dotenv for environment management

## 📋 Prerequisites

- Python 3.x
- pip (Python package manager)
- Virtual environment (recommended)

## 🔧 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/task-manager.git
cd task-manager
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file in the root directory:
```env
SECRET_KEY=your_secret_key_here
EMAIL_HOST_USER=your_gmail_address
EMAIL_HOST_PASSWORD=your_app_specific_password
```

5. Apply migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

## 🏗 Project Structure

```
task_manager/
├── apps/
│   ├── core/           # Core functionality
│   ├── security/       # Authentication and authorization
│   ├── tasks/          # Task management
│   ├── notifications/  # User notifications
│   └── pomodoro/       # Pomodoro timer feature
├── static/             # Static files (CSS, JS, images)
├── templates/          # HTML templates
├── media/             # User-uploaded content
└── task_manager/      # Project configuration
```

## ⚙️ Configuration

### Google OAuth2 Setup

1. Create a project in Google Cloud Console
2. Enable Google+ API
3. Configure OAuth2 credentials
4. Add authorized redirect URIs:
   - `http://localhost:8000/accounts/google/login/callback/`
   - Your production domain when deployed

### Email Configuration

The project uses Gmail SMTP for email communications. Configure your Gmail account to:
- Enable 2-factor authentication
- Generate an app-specific password
- Update `.env` with your credentials

## 🔐 Security Features

- CSRF protection enabled
- Secure session configuration
- Password validation rules
- Email verification
- HTTPOnly cookies
- XFrame options configured

## 🌐 Production Deployment Notes

Before deploying to production:

1. Set `DEBUG = False`
2. Configure `ALLOWED_HOSTS`
3. Enable `SESSION_COOKIE_SECURE`
4. Update `DATABASES` configuration
5. Configure proper static files serving
6. Set up proper email backend
7. Review and update security settings

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For support, email jpincaym7@unemi.edu.ec or open an issue in the repository.