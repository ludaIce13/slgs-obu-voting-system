# 🚀 SLGS OBU Voting System - Deployment Guide

This guide provides comprehensive instructions for deploying the SLGS OBU Voting System to various hosting platforms.

## 📋 Prerequisites

- Python 3.8+
- Git
- PostgreSQL database (recommended for production)

## 🗂️ Project Structure

```
slgs-voting-system/
├── app/                    # Flask application
├── templates/             # HTML templates
├── static/               # CSS/JS files
├── instance/             # SQLite database (dev)
├── requirements.txt      # Python dependencies
├── run.py               # Development server
├── Procfile            # Production server config
├── .env               # Environment variables
└── deploy.py          # Deployment utilities
```

## 🛠️ Deployment Options

### Option 1: Railway (Recommended - Free & Easy)

Railway provides free PostgreSQL databases and easy deployment.

#### Step 1: Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub/GitLab
3. Create a new project

#### Step 2: Deploy to Railway
1. **Connect Repository**
   ```bash
   # Fork this repository to your GitHub
   git clone https://github.com/your-username/slgs-voting-system.git
   cd slgs-voting-system
   ```

2. **Deploy on Railway**
   - Click "Deploy from GitHub"
   - Connect your repository
   - Railway will auto-detect Flask app

3. **Configure Environment Variables**
   - Go to your Railway project settings
   - Add environment variables:
     ```
     ADMIN_TOKEN=your-secure-admin-token-123456789
     SECRET_KEY=your-super-secret-key-change-this-987654321
     ```

4. **Railway will automatically:**
   - Install Python dependencies
   - Create PostgreSQL database
   - Run migrations
   - Start the application

#### Step 3: Access Your App
- Railway provides a public URL: `https://your-app-name.railway.app`
- Admin Dashboard: `https://your-app-name.railway.app/admin`
- Voting Page: `https://your-app-name.railway.app/vote`

### Option 2: Render (Free PostgreSQL)

#### Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up and create a new service

#### Step 2: Deploy to Render
1. **Connect Repository**
   - Choose "Web Service"
   - Connect your GitHub repository
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `gunicorn run:app`

2. **Environment Variables**
   ```
   ADMIN_TOKEN=your-secure-admin-token-123456789
   SECRET_KEY=your-super-secret-key-change-this-987654321
   DATABASE_URL=postgresql://... (auto-provided by Render)
   ```

3. **Render will automatically:**
   - Create PostgreSQL database
   - Build and deploy your app
   - Provide SSL certificate

### Option 3: Heroku (Classic Option)

#### Step 1: Install Heroku CLI
```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh
```

#### Step 2: Deploy to Heroku
```bash
# Login to Heroku
heroku login

# Create Heroku app
heroku create slgs-obu-voting

# Add PostgreSQL database
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set ADMIN_TOKEN=your-secure-admin-token-123456789
heroku config:set SECRET_KEY=your-super-secret-key-change-this-987654321

# Deploy
git push heroku main
```

### Option 4: Manual VPS Deployment

#### Step 1: Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and PostgreSQL
sudo apt install python3 python3-pip postgresql postgresql-contrib nginx -y

# Install Python dependencies
pip3 install -r requirements.txt
```

#### Step 2: Database Setup
```bash
# Create database user and database
sudo -u postgres psql
CREATE USER voting_user WITH PASSWORD 'secure_password';
CREATE DATABASE voting_db OWNER voting_user;
GRANT ALL PRIVILEGES ON DATABASE voting_db TO voting_user;
\q
```

#### Step 3: Configure Environment
```bash
# Set environment variables
export DATABASE_URL="postgresql://voting_user:secure_password@localhost:5432/voting_db"
export ADMIN_TOKEN="your-secure-admin-token-123456789"
export SECRET_KEY="your-super-secret-key-change-this-987654321"
```

#### Step 4: Run Application
```bash
# Start with Gunicorn
gunicorn run:app --bind 0.0.0.0:5000 --workers 4
```

## 🔧 Post-Deployment Setup

### Step 1: Initialize Database
```bash
# Run database initialization
python deploy.py
```

### Step 2: Create Admin User
```bash
# Set admin token
export ADMIN_TOKEN="your-secure-admin-token-123456789"
```

### Step 3: Upload Voter Data
1. Go to your admin dashboard: `https://your-domain.com/admin`
2. Upload your voter CSV file
3. Generate Voter IDs

## 🔐 Security Configuration

### Change Default Tokens
```bash
# Generate secure random tokens
python -c "import secrets; print('Admin Token:', secrets.token_hex(32))"
python -c "import secrets; print('Secret Key:', secrets.token_hex(32))"
```

### Environment Variables
```bash
# Production .env file
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this-987654321
DATABASE_URL=postgresql://username:password@host:port/database
ADMIN_TOKEN=your-secure-admin-token-123456789
ELECTION_NAME=SLGS OBU Presidential Election 2024
```

## 📊 Monitoring & Maintenance

### Check Application Logs
```bash
# Railway
railway logs

# Heroku
heroku logs --tail

# Render
# Check dashboard logs
```

### Database Backup
```bash
# PostgreSQL backup
pg_dump voting_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Update Voter Data
1. Go to Admin Dashboard
2. Use "Clear All Voters" if needed
3. Upload new CSV file
4. Generate new Voter IDs

## 🚨 Troubleshooting

### Common Issues

**1. Database Connection Error**
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test database connection
python -c "from app import create_app, db; app = create_app(); print('DB Connected:', db.engine.connect())"
```

**2. Admin Access Issues**
- Ensure `ADMIN_TOKEN` is set correctly
- Check browser console for errors
- Try debug mode: `/admin?debug=true`

**3. Voter Upload Fails**
- Verify CSV format: `MemberID,FullName,GraduationYear`
- Check file encoding (UTF-8)
- Ensure MemberID is unique

**4. Voting Page Not Working**
- Check if Voter IDs are generated
- Verify database has voter records
- Check browser console for JavaScript errors

### Debug Mode
```bash
# Enable debug logging
export FLASK_ENV=development
```

## 📞 Support

For deployment issues:
1. Check application logs
2. Verify environment variables
3. Test database connectivity
4. Review security settings

## 🎯 Production Checklist

- [ ] Database is PostgreSQL (not SQLite)
- [ ] Environment variables are set
- [ ] Admin token is changed from default
- [ ] SSL certificate is active
- [ ] Voter data is uploaded
- [ ] Voter IDs are generated
- [ ] Security settings reviewed
- [ ] Backup procedures established

---

**🎉 Congratulations! Your SLGS OBU Voting System is now deployed and ready for secure, anonymous voting!**

**Admin Dashboard**: `https://your-domain.com/admin`
**Voting Page**: `https://your-domain.com/vote`
**Default Admin Token**: `admin-token` (change this immediately!)