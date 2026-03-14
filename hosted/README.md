# Talent-Augmenting Layer -- Hosted Web App

A FastAPI application providing LLM-powered conversational assessment, persistent
user profiles with Google OAuth, 2-week email reminders for profile check-ins, and
profile export for any LLM platform.

## Quick Start

### 1. Install dependencies

```bash
pip install -r hosted/requirements.txt
```

### 2. Set environment variables

Create a `.env` file or export these variables:

```bash
# Required for LLM-powered assessment
ANTHROPIC_API_KEY=sk-ant-...           # or use OpenAI or Gemini
# LLM_PROVIDER=openai                  # uncomment to use OpenAI
# LLM_PROVIDER=gemini                  # uncomment to use Gemini
# OPENAI_API_KEY=sk-...                # required if using OpenAI
# GOOGLE_API_KEY=...                   # required if using Gemini
# LLM_MODEL=gemini-2.5-flash-lite      # or gemini-1.5-pro, gemini-1.5-flash, etc.

# Required for Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Security
SECRET_KEY=generate-a-strong-random-string

# Optional: email reminders
SENDGRID_API_KEY=SG.xxx               # omit to log emails instead of sending
FROM_EMAIL=noreply@yourdomain.com

# Optional: app URL (for OAuth callback and email links)
APP_URL=http://localhost:8000          # change in production
```

### 3. Run locally

From the **project root**:

```bash
uvicorn hosted.app:app --reload
```

Open http://localhost:8000 in your browser.

> **Note**: Make sure to update the Google OAuth redirect URI to include `http://localhost:8000/auth/callback` for local development.

### 4. Run with Docker

From the project root:

```bash
docker build -f hosted/Dockerfile -t talent-augmenting-layer-hosted .
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e GOOGLE_CLIENT_ID=... \
  -e GOOGLE_CLIENT_SECRET=... \
  -e SECRET_KEY=... \
  talent-augmenting-layer-hosted
```

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Navigate to **APIs & Services > Credentials**
4. Click **Create Credentials > OAuth 2.0 Client ID**
5. Set application type to **Web application**
6. Add authorized redirect URI: `http://localhost:8000/auth/callback`
   (update for production)
7. Copy the Client ID and Client Secret into your environment variables

## Deployment to Render

### Option 1: One-Click Deploy (Recommended)

1. **Fork this repository** to your GitHub account

2. **Click this button** (or follow manual steps below):
   - Go to [Render.com](https://render.com) and sign up/login
   - Click **New +** → **Blueprint**
   - Connect your GitHub repository
   - Render will detect `render.yaml` automatically

3. **Set required secrets** in the Render dashboard:
   ```
   LLM_PROVIDER=gemini
   GOOGLE_API_KEY=your-google-api-key
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

4. **Update Google OAuth redirect URL**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to your OAuth credentials
   - Add authorized redirect URI: `https://YOUR-APP-NAME.onrender.com/auth/callback`
   - Replace `YOUR-APP-NAME` with your actual Render service name

5. **Update APP_URL** environment variable in Render to match your deployed URL

6. Deploy! Render will build and deploy your app automatically.

### Option 2: Manual Render Deploy

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New +** → **Web Service**
3. Connect your repository
4. Configure:
   - **Name**: `talent-augmenting-layer-hosted`
   - **Runtime**: Docker
   - **Dockerfile Path**: `./hosted/Dockerfile`
   - **Plan**: Free (or Starter for production)
5. Add environment variables (see step 3 above)
6. Create a PostgreSQL database:
   - Click **New +** → **PostgreSQL**
   - **Name**: `talent-augmenting-layer-db`
   - **Plan**: Free (90-day trial) or Starter ($7/mo)
   - Copy the **Internal Database URL**
   - Add to web service as `DATABASE_URL` environment variable
7. Deploy!

### Cost Estimate (Render)
- **Free tier**: Web service (750 hrs/mo) + PostgreSQL (90 days free)
- **Production**: Starter web ($7/mo) + PostgreSQL ($7/mo) = **$14/mo**

### Local Testing Before Deploy

```bash
# Test with production-like settings
export APP_URL=http://localhost:8000
export LLM_PROVIDER=gemini
export GOOGLE_API_KEY=your-key
uvicorn hosted.app:app --reload
```

---

## Architecture

```
hosted/
  app.py              Main FastAPI application with all routes
  config.py           Environment-based configuration
  database.py         SQLAlchemy 2.0 async models (User, Profile, Session, Reminder)
  auth.py             Google OAuth + JWT session management
  llm_client.py       Anthropic / OpenAI API wrapper
  scoring.py          Thin import layer over mcp-server/src/assessment.py
  email_service.py    SendGrid email + check-in question generation
  scheduler.py        APScheduler for daily reminder checks
  templates/          Jinja2 HTML templates
  static/             CSS and JavaScript
```

## Core Flows

1. **Login**: Google OAuth -> JWT cookie -> session
2. **Assessment**: Chat UI -> LLM conversation -> extract structured data -> compute scores -> save profile
3. **Dashboard**: View scores, expertise map, export profile
4. **Export**: Download profile as Markdown, JSON, or platform-specific format (ChatGPT, Claude, Gemini)
5. **Check-in**: Every 2 weeks, receive an email with targeted reflection questions

## Email Configuration

Email reminders are sent every 2 weeks to users whose profiles are overdue for a check-in.
Set `SENDGRID_API_KEY` to enable actual email delivery. Without it, emails are logged to
stdout (useful for development).

The check-in interval can be configured with `CHECKIN_INTERVAL_DAYS` (default: 14).
