# Deadman Switch Application

A comprehensive deadman switch application with web-based admin and client interfaces, built with Python and FastAPI.

## Features

- **User Management**: Admin and client user roles
- **Deadman Switches**: Create and manage multiple switches with customizable check-in intervals
- **Emergency Contacts**: Configure contacts to be notified when switches are triggered
- **Mobile-Friendly**: Responsive web interface optimized for mobile devices
- **API Ready**: RESTful API endpoints for future React Native mobile apps
- **Real-time Monitoring**: Track check-ins and switch statuses
- **Secure Authentication**: JWT-based authentication with password hashing

## Technology Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, Alembic
- **Database**: SQLite (development), PostgreSQL (production)
- **Frontend**: Jinja2 templates, Bootstrap 5, HTMX
- **Authentication**: JWT tokens, bcrypt password hashing
- **Deployment**: Render.com ready with Docker support

## Quick Start

### Prerequisites

- Python 3.10+
- uv (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd panggil-python-web
```

2. Install dependencies:
```bash
uv sync
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run database migrations:
```bash
uv run alembic upgrade head
```

5. Create an admin user:
```bash
uv run python create_admin.py
```

6. Start the development server:
```bash
uv run python -m deadman_switch.main
```

The application will be available at `http://localhost:8000`

### Default Admin Credentials

- Username: `admin`
- Password: `admin123`

**Important**: Change the default password after first login.

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Deployment

### Render.com

This application is configured for easy deployment on Render.com:

1. Connect your GitHub repository to Render
2. The `render.yaml` file contains all necessary configuration
3. Environment variables will be automatically set

### Manual Deployment

For other platforms:

1. Set environment variables (see `.env.example`)
2. Run migrations: `uv run alembic upgrade head`
3. Start with: `uv run gunicorn deadman_switch.main:app -w 4 -k uvicorn.workers.UvicornWorker`

## Development

### Project Structure

```
src/deadman_switch/
├── main.py          # FastAPI application entry point
├── models.py        # Database models
├── database.py      # Database configuration
├── auth.py          # Authentication logic
├── admin.py         # Admin interface routes
├── client.py        # Client interface routes
├── api.py           # API routes for mobile
└── ...

templates/           # Jinja2 templates
├── base.html
├── auth/
├── admin/
└── client/

static/              # Static files (CSS, JS, images)
alembic/             # Database migrations
```

### Running Tests

```bash
uv run pytest
```

### Database Migrations

Create a new migration:
```bash
uv run alembic revision --autogenerate -m "Description"
```

Apply migrations:
```bash
uv run alembic upgrade head
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.