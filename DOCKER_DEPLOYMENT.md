# 🐳 Docker Deployment Guide

Complete guide for deploying the Deadman Switch application using Docker and OrbStack.

## 🚀 Quick Start

### Prerequisites
- Docker installed (OrbStack recommended for Mac)
- Git for cloning the repository

### 1. Clone and Setup
```bash
git clone https://github.com/hyapadi/deadman-switch-app.git
cd deadman-switch-app
```

### 2. Development Deployment (SQLite)
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up

# Access the application
open http://localhost:8000
```

### 3. Production Deployment (PostgreSQL + Redis)
```bash
# Start production environment
docker-compose up

# Access the application
open http://localhost:8000
```

## 📋 Default Credentials
- **Username**: `admin`
- **Email**: `admin@deadmanswitch.com`
- **Password**: `admin123`

⚠️ **Important**: Change the admin password after first login!

## 🛠 Available Services

### Development Environment
- **Web App**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Database**: SQLite (local file)

### Production Environment
- **Web App**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Database**: PostgreSQL on port 5432
- **Cache**: Redis on port 6379

## 🔧 Configuration

### Environment Variables
Create a `.env` file for custom configuration:

```env
# Application
SECRET_KEY=your-super-secret-key-change-in-production
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database (Production)
DATABASE_URL=postgresql://deadman_switch_user:deadman_switch_password@postgres:5432/deadman_switch

# Redis (Production)
REDIS_URL=redis://redis:6379/0
```

### Custom Ports
To change the default port, modify the docker-compose files:

```yaml
services:
  app:
    ports:
      - "3000:8000"  # Change 3000 to your desired port
```

## 🐳 Docker Commands

### Build Image
```bash
docker build -t deadman-switch .
```

### Run Single Container
```bash
# Development (SQLite)
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./data/deadman_switch.db \
  -v $(pwd)/data:/app/data \
  deadman-switch

# Production (requires external database)
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e REDIS_URL=redis://host:6379/0 \
  deadman-switch
```

### View Logs
```bash
# Development
docker-compose -f docker-compose.dev.yml logs -f

# Production
docker-compose logs -f
```

### Stop Services
```bash
# Development
docker-compose -f docker-compose.dev.yml down

# Production
docker-compose down

# Remove volumes (⚠️ deletes data)
docker-compose down -v
```

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Database Access
```bash
# PostgreSQL (Production)
docker-compose exec postgres psql -U deadman_switch_user -d deadman_switch

# SQLite (Development)
docker-compose -f docker-compose.dev.yml exec app sqlite3 /app/data/deadman_switch.db
```

### Redis Access
```bash
# Redis CLI (Production)
docker-compose exec redis redis-cli
```

## 🔄 Updates and Maintenance

### Update Application
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Database Migrations
```bash
# Run migrations manually
docker-compose exec app uv run alembic upgrade head
```

### Backup Data
```bash
# PostgreSQL backup
docker-compose exec postgres pg_dump -U deadman_switch_user deadman_switch > backup.sql

# SQLite backup
docker-compose -f docker-compose.dev.yml exec app cp /app/data/deadman_switch.db /app/data/backup.db
```

## 🚀 Production Deployment Platforms

### Deploy to any Docker platform:
- **Railway**: Connect GitHub repo, auto-deploy
- **DigitalOcean App Platform**: Use docker-compose.yml
- **AWS ECS**: Use Dockerfile
- **Google Cloud Run**: Use Dockerfile
- **Heroku**: Use Dockerfile with heroku.yml

### Example heroku.yml:
```yaml
build:
  docker:
    web: Dockerfile
run:
  web: /app/start.sh
```

## 🛡 Security Notes

1. **Change default passwords** immediately
2. **Use strong SECRET_KEY** in production
3. **Enable HTTPS** with reverse proxy
4. **Restrict database access** to application only
5. **Regular backups** of data
6. **Monitor logs** for suspicious activity

## 🆘 Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find process using port 8000
lsof -i :8000
# Kill the process or use different port
```

**Permission denied:**
```bash
# Fix file permissions
chmod +x start.sh
```

**Database connection failed:**
```bash
# Check if PostgreSQL is running
docker-compose ps
# View database logs
docker-compose logs postgres
```

**Build fails:**
```bash
# Clean Docker cache
docker system prune -a
# Rebuild without cache
docker-compose build --no-cache
```

## 📞 Support

For issues and questions:
- Check the logs: `docker-compose logs`
- Review this guide
- Check GitHub issues
- Create new issue with logs and error details

---

🎉 **Your Deadman Switch application is now running in Docker!**
