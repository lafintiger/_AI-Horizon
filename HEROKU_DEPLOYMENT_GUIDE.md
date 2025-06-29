# AI-Horizon Heroku Deployment Guide

This guide walks you through deploying the AI-Horizon project to Heroku with a custom subdomain (`portal.theaihorizon.org`).

## 📋 Prerequisites

- **Heroku Account**: [Sign up here](https://signup.heroku.com/)
- **Heroku CLI**: [Download and install](https://devcenter.heroku.com/articles/heroku-cli)
- **Git Repository**: Your AI-Horizon project on GitHub
- **Domain Access**: Ability to modify DNS settings for `theaihorizon.org`

## 🚀 Phase 1: Heroku App Setup

### 1. Login to Heroku
```bash
heroku login
```

### 2. Create Heroku App
```bash
# Create app (choose a unique name)
heroku create ai-horizon-portal

# Or let Heroku choose a name
heroku create
```

### 3. Add Required Buildpacks
```bash
heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-apt
heroku buildpacks:add --index 2 heroku/python
```

### 4. Add PostgreSQL Database
```bash
# Add Heroku Postgres (free tier)
heroku addons:create heroku-postgresql:mini

# Get database URL (note this for later)
heroku config:get DATABASE_URL
```

## 🔧 Phase 2: Environment Configuration

### 1. Set Environment Variables
```bash
# Application settings
heroku config:set FLASK_ENV=production
heroku config:set FLASK_DEBUG=False
heroku config:set SECRET_KEY="your-super-secret-key-here-change-this"

# API Keys (replace with your actual keys)
heroku config:set ANTHROPIC_API_KEY="your-anthropic-api-key"
heroku config:set OPENAI_API_KEY="your-openai-api-key" 
heroku config:set PERPLEXITY_API_KEY="your-perplexity-api-key"

# Application configuration
heroku config:set MAX_CONTENT_LENGTH=16777216
heroku config:set UPLOAD_FOLDER=uploads
heroku config:set SESSION_TIMEOUT_HOURS=8
```

### 2. View All Config Vars
```bash
heroku config
```

## 🔄 Phase 3: GitHub Integration

### 1. Connect to GitHub (via Heroku Dashboard)
1. Go to [Heroku Dashboard](https://dashboard.heroku.com/)
2. Select your app
3. Go to **Deploy** tab
4. Connect to GitHub and select your repository
5. Enable **Automatic deploys** from your main branch

### 2. Manual Deploy (Alternative)
```bash
# Add Heroku remote
heroku git:remote -a your-app-name

# Deploy manually
git push heroku main
```

## 🏗️ Phase 4: Database Migration

Since Heroku uses PostgreSQL instead of SQLite, you'll need to migrate your data:

### 1. Install Migration Tool (Local)
```bash
pip install sqlite3-to-postgres
```

### 2. Export SQLite Data
```bash
# Export your local SQLite database
sqlite3 data/aih_database.db .dump > database_dump.sql
```

### 3. Import to Heroku Postgres
```bash
# Get Heroku database credentials
heroku pg:credentials:url DATABASE_URL

# Import data (you may need to clean up the SQL file first)
heroku pg:psql DATABASE_URL < database_dump.sql
```

## 🌐 Phase 5: Domain & Subdomain Setup

### 1. Add Custom Domain to Heroku
```bash
# Add your subdomain to Heroku
heroku domains:add portal.theaihorizon.org

# Get the DNS target (note this)
heroku domains
```

### 2. Configure DNS Settings

You'll need to set up DNS for your subdomain. Since your main domain (`theaihorizon.org`) is hosted by Wix, you have two options:

#### Option A: Use Wix DNS Management
1. Log into your Wix account
2. Go to Domain settings
3. Add a CNAME record:
   - **Name**: `portal`
   - **Value**: `your-app-name.herokuapp.com` (or the DNS target from Heroku)

#### Option B: Use External DNS (Recommended)
1. Change nameservers to Cloudflare/Route53/etc.
2. Add CNAME record pointing `portal.theaihorizon.org` to your Heroku app

### 3. SSL Certificate (Automatic)
Heroku automatically provides SSL certificates for custom domains on paid dynos.

```bash
# Upgrade to hobby dyno for SSL (optional but recommended)
heroku ps:scale web=1:hobby
```

## 🔍 Phase 6: Testing & Monitoring

### 1. Test Deployment
```bash
# Open your app
heroku open

# Check logs
heroku logs --tail

# Check app status
heroku ps
```

### 2. Test Subdomain
- Visit `https://portal.theaihorizon.org`
- Test all major features:
  - Login system
  - Manual entry
  - Analysis functions
  - PDF exports
  - Chat system

## 📊 Phase 7: Production Optimization

### 1. Scale Application
```bash
# Scale to multiple workers if needed
heroku ps:scale web=2

# Check dyno usage
heroku ps
```

### 2. Monitor Performance
```bash
# Add New Relic monitoring (optional)
heroku addons:create newrelic:wayne

# View metrics
heroku addons:open newrelic
```

### 3. Set up Backups
```bash
# Enable automatic backups
heroku pg:backups:schedule DATABASE_URL --at '04:00 America/New_York'

# Create manual backup
heroku pg:backups:capture
```

## 🔄 Phase 8: Continuous Deployment

Your GitHub integration is now set up for automatic deployment:

1. **Push to GitHub** → Heroku automatically deploys
2. **View deployment logs** in Heroku Dashboard
3. **Rollback if needed**: `heroku releases:rollback`

## 🛠️ Troubleshooting

### Common Issues:

#### 1. Build Failures
```bash
# Check build logs
heroku logs --tail --dyno=web

# Restart dynos
heroku restart
```

#### 2. Database Connection Issues
```bash
# Check database status
heroku pg:info

# Reset database if needed
heroku pg:reset DATABASE_URL
```

#### 3. PDF Export Issues
```bash
# Check if system dependencies installed
heroku run bash
# Then: apt list --installed | grep cairo
```

#### 4. Memory Issues
```bash
# Upgrade dyno type
heroku ps:scale web=1:standard-1x
```

### Useful Commands:

```bash
# SSH into app
heroku run bash

# Run database migrations
heroku run python -c "from aih.utils.database import DatabaseManager; DatabaseManager()"

# View environment variables
heroku config

# View recent logs
heroku logs --tail --num=100
```

## 💡 Best Practices

1. **Environment Variables**: Store all secrets in Heroku Config Vars
2. **Database Backups**: Schedule regular backups
3. **Monitoring**: Set up alerts for errors/downtime
4. **Scaling**: Start with 1 dyno, scale as needed
5. **Logging**: Use structured logging for better debugging
6. **SSL**: Always use HTTPS in production

## 🎯 Expected Results

After successful deployment:

- ✅ **Main Site**: `theaihorizon.org` (unchanged, still on Wix)
- ✅ **Portal**: `portal.theaihorizon.org` (AI-Horizon application)
- ✅ **Auto-deploy**: Push to GitHub → Automatic Heroku deployment
- ✅ **Full functionality**: All AI-Horizon features working in production
- ✅ **SSL security**: HTTPS enabled automatically
- ✅ **Scalability**: Ready to handle production traffic

## 📞 Support

If you encounter issues:

1. Check Heroku logs: `heroku logs --tail`
2. Review the troubleshooting section above
3. Check [Heroku documentation](https://devcenter.heroku.com/)
4. Contact the development team

---

**Next Steps**: Once deployed, you can access your full AI-Horizon platform at `https://portal.theaihorizon.org` while keeping your main marketing site on Wix! 