# Finacle - Financial Management Application

A modern, scalable financial management application built with Django REST Framework and React Native.

## 🚀 Features

- **Modern Architecture**: Django REST Framework backend with React Native mobile app
- **Scalable**: Docker containerization with production-ready configuration
- **Secure**: Built-in security features, environment-based configuration
- **Observable**: Structured logging, health checks, and error tracking with Sentry
- **Tested**: Comprehensive test suite with CI/CD pipeline

## 📋 Prerequisites

- Python 3.12+
- Docker and Docker Compose
- PostgreSQL (for production)
- Redis (for caching)

## 🛠️ Quick Start

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd finacle-app
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv finacle_env
   source finacle_env/bin/activate  # On Windows: finacle_env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   make install-dev
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Run setup**
   ```bash
   make setup
   ```

6. **Start development server**
   ```bash
   make runserver
   ```

The application will be available at `http://localhost:8000`

### Docker Development

1. **Start with Docker Compose**
   ```bash
   make docker-up
   ```

2. **View logs**
   ```bash
   make docker-logs
   ```

3. **Stop services**
   ```bash
   make docker-down
   ```

## 🏗️ Architecture

### Backend Structure
```
finacle_app/
├── finacle_app/          # Django project settings
├── core/                 # Core app (health checks, utilities)
├── tests/               # Test suite
├── requirements.txt     # Production dependencies
├── requirements-dev.txt # Development dependencies
├── Dockerfile          # Multi-stage Docker build
├── docker-compose.yml  # Development environment
└── docker-compose.prod.yml # Production environment
```

### Key Components

- **Health Endpoints**: `/api/v1/health/`, `/api/v1/ready/`, `/api/v1/alive/`
- **Admin Interface**: `/admin/` (superuser: admin/admin in dev)
- **API Documentation**: Available via Django REST Framework browsable API

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run linting
make lint

# Format code
make format

# Run all CI checks locally
make ci
```

## 🔧 Configuration

### Environment Variables

Key environment variables (see `env.example` for full list):

- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode (True/False)
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection string
- `SENTRY_DSN`: Sentry error tracking DSN
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

### Database Configuration

**Development**: SQLite (default)
```
DATABASE_URL=sqlite:///db.sqlite3
```

**Production**: PostgreSQL
```
DATABASE_URL=postgresql://user:password@localhost:5432/finacle_db
```

## 🚀 Deployment

### Production with Docker

1. **Set up environment**
   ```bash
   cp env.example .env.prod
   # Configure production values in .env.prod
   ```

2. **Deploy**
   ```bash
   make docker-prod-up
   ```

### Manual Deployment

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   export DEBUG=False
   export SECRET_KEY=your-secret-key
   export DATABASE_URL=postgresql://...
   ```

3. **Run migrations and collect static files**
   ```bash
   python manage.py migrate
   python manage.py collectstatic
   ```

4. **Start with Gunicorn**
   ```bash
   gunicorn finacle_app.wsgi:application
   ```

## 📊 Monitoring & Observability

### Health Checks

- **Health**: `GET /api/v1/health/` - Basic service health
- **Readiness**: `GET /api/v1/ready/` - Service dependencies check
- **Liveness**: `GET /api/v1/alive/` - Service liveness probe

### Logging

Structured JSON logging configured with multiple levels:
- Console output (development)
- File logging (`logs/django.log`)
- Sentry integration for error tracking

### Error Tracking

Configure Sentry for production error tracking:
```bash
export SENTRY_DSN=https://your-sentry-dsn
```

## 🔄 CI/CD Pipeline

GitHub Actions workflow includes:

- **Code Quality**: Black, isort, flake8, mypy
- **Testing**: pytest with coverage reporting
- **Security**: safety, bandit scans
- **Build**: Docker image build and test
- **Performance**: Basic load testing with Locust

## 🤝 Development Workflow

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make changes and test**
   ```bash
   make ci  # Run all checks locally
   ```

3. **Commit and push**
   ```bash
   git commit -m "Add your feature"
   git push origin feature/your-feature
   ```

4. **Create Pull Request**
   - CI pipeline will run automatically
   - All checks must pass before merge

## 📚 API Documentation

- **Browsable API**: Available at `/api/v1/` when `DEBUG=True`
- **Admin Interface**: Available at `/admin/`

## 🛡️ Security

- Environment-based configuration
- CORS protection
- CSRF protection
- SQL injection protection (Django ORM)
- XSS protection
- Secure headers in production
- Dependency vulnerability scanning

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Create GitHub issues for bugs and feature requests
- **Health Checks**: Monitor `/api/v1/health/` endpoint for service status

## 🗺️ Roadmap

### Phase 1: Foundations (Current)
- ✅ Django + DRF setup
- ✅ Docker containerization
- ✅ CI/CD pipeline
- ✅ Health checks and monitoring
- ✅ Basic testing infrastructure

### Phase 2: Core Features (Next)
- User authentication and authorization
- Financial data models
- API endpoints for financial operations
- React Native mobile app setup

### Phase 3: Advanced Features
- Real-time notifications
- Advanced analytics
- Third-party integrations
- Performance optimization



