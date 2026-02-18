# Deploying Baisoft Backend to Render.com

This guide walks you through deploying the Django backend to Render.com.

## Prerequisites

- A Render.com account (free or paid)
- Your GitHub repository pushed with all changes
- Environment variables ready to configure

## Deployment Steps

### 1. Connect Your Repository to Render

1. Go to [render.com](https://render.com) and sign in
2. Click **"New +"** and select **"Web Service"**
3. Connect your GitHub account and select the `WinfredWinfred/Baisoft` repository
4. Authorize Render to access your repository

### 2. Configure the Web Service

**Basic Settings:**
- **Name**: `baisoft-backend` (or your preferred name)
- **Region**: Choose closest to your users (e.g., Oregon, Virginia)
- **Branch**: `main`
- **Runtime**: `Python`
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn backend.wsgi:application`

**Instance Type:**
- Select **Free** or **Starter** tier initially (you can upgrade later)

### 3. Set Environment Variables

Click on **"Environment"** and add these variables:

```
DEBUG = false
DJANGO_SECRET_KEY = <generate a strong secret key>
ALLOWED_HOSTS = .onrender.com
CORS_ALLOWED_ORIGINS = https://your-frontend-domain.onrender.com,http://localhost:3000
CORS_ALLOW_ALL_ORIGINS = false
FRONTEND_URL = https://your-frontend-domain.onrender.com
```

**Important:** Replace `your-frontend-domain.onrender.com` with your actual frontend URL.

### 4. Deploy

Click **"Create Web Service"** and Render will:
1. Pull your code
2. Run `build.sh` (installs dependencies, runs migrations, collects static files)
3. Start the gunicorn server

### 5. Verify Deployment

Once the deployment is complete:
- Your API will be available at: `https://baisoft-backend.onrender.com`
- Check logs in the Render dashboard for any issues
- Test endpoints with a tool like Postman or curl

## Troubleshooting

### Static Files Not Loading
- Run in Render dashboard terminal: `python manage.py collectstatic --noinput`
- Ensure `STATIC_ROOT` is set correctly in `settings.py`

### Database Issues
- Current setup uses SQLite (fine for development)
- For production, upgrade to PostgreSQL:
  1. Create a PostgreSQL instance on Render
  2. Add `DATABASE_URL` environment variable
  3. Update `settings.py` to use dj-database-url

### CORS Errors
- Update `CORS_ALLOWED_ORIGINS` with your frontend URL
- Ensure frontend makes requests to `https://baisoft-backend.onrender.com`

### Build Failures
- Check logs in Render dashboard
- Ensure all dependencies in `requirements.txt` are correct
- Verify `build.sh` has proper permissions

## Updating Your Deployment

After making changes:
1. Push to GitHub: `git push`
2. Render automatically redeploys on push to main branch
3. Monitor deployment in Render dashboard

## Next Steps

1. **Configure Frontend**: Deploy frontend to Render (see frontend README)
2. **Setup Database**: Consider PostgreSQL for production with persistent data
3. **Enable HTTPS**: Render provides free SSL certificates automatically
4. **Monitor**: Use Render's built-in monitoring for errors and performance

## Production Checklist

- [ ] Change `DEBUG` to `false` in environment variables
- [ ] Set a strong `DJANGO_SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Update `CORS_ALLOWED_ORIGINS` with production frontend URL
- [ ] Test all API endpoints
- [ ] Check static files are loading
- [ ] Review security settings in browser dev tools
- [ ] Enable auto-deploy on branch push
- [ ] Set up error notifications

## Support

For issues with Render deployment, check:
- [Render Django Documentation](https://render.com/docs/deploy-django)
- [Render Dashboard Logs](https://dashboard.render.com/)
- Project documentation in `API_DOCUMENTATION.md`
