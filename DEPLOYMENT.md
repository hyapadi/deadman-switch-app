# Deployment Guide

This guide covers deploying the Deadman Switch application to Render.com.

## Prerequisites

1. **GitHub Account**: Your code needs to be in a GitHub repository
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **Render CLI**: Already installed and configured

## Step 1: Push to GitHub

1. Create a new repository on GitHub
2. Add the remote and push your code:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy to Render

### Option A: Using Render Dashboard (Recommended)

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click "New +" and select "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file
5. Review the configuration and click "Apply"

### Option B: Using Render CLI

```bash
# From your project directory
render blueprint launch
```

## Step 3: Configure Environment Variables

The following environment variables will be automatically set by Render:

- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Auto-generated secure key
- `ENVIRONMENT` - Set to "production"
- `PORT` - Set by Render
- `HOST` - Set to "0.0.0.0"

## Step 4: Access Your Application

1. Once deployed, Render will provide you with a URL like: `https://deadman-switch-xyz.onrender.com`
2. Visit the URL to access your application
3. Login with the default admin credentials:
   - Username: `admin`
   - Password: `admin123`

**Important**: Change the admin password immediately after first login!

## Step 5: Post-Deployment Setup

1. **Change Admin Password**: Login and update the default password
2. **Configure Email**: Set up SMTP settings for notifications (if needed)
3. **Create Users**: Add client users through the admin interface
4. **Test Functionality**: Create a test deadman switch and verify it works

## Services Created

The deployment will create:

1. **Web Service**: The main FastAPI application
2. **PostgreSQL Database**: For data storage
3. **Redis Instance**: For background tasks and caching

## Monitoring

- **Logs**: View logs in the Render dashboard
- **Metrics**: Monitor performance and uptime
- **Health Check**: Available at `/health` endpoint

## Troubleshooting

### Common Issues

1. **Build Fails**: Check the build logs in Render dashboard
2. **Database Connection**: Ensure DATABASE_URL is properly set
3. **Static Files**: Make sure templates and static directories exist

### Useful Commands

```bash
# View logs
render logs --service deadman-switch

# Restart service
render restart --service deadman-switch

# Check service status
render services list
```

## Custom Domain (Optional)

1. In Render dashboard, go to your service settings
2. Add your custom domain
3. Configure DNS records as instructed by Render

## Scaling

- **Horizontal Scaling**: Increase the number of instances in Render dashboard
- **Vertical Scaling**: Upgrade to a higher tier plan for more resources

## Security Considerations

1. **Environment Variables**: Never commit sensitive data to Git
2. **HTTPS**: Render provides SSL certificates automatically
3. **Database**: PostgreSQL instance is private by default
4. **Admin Access**: Change default credentials immediately

## Backup

- **Database**: Render provides automated backups for PostgreSQL
- **Code**: Your Git repository serves as code backup
- **Configuration**: The `render.yaml` file contains your infrastructure as code

## Updates

To deploy updates:

1. Push changes to your GitHub repository
2. Render will automatically trigger a new deployment
3. Monitor the deployment in the Render dashboard

## Support

- **Render Documentation**: [render.com/docs](https://render.com/docs)
- **Application Logs**: Available in Render dashboard
- **Health Check**: Monitor at `/health` endpoint
