# ☁️ Deployment Guide

## 🚀 Quick Deploy (Railway/Render)

### Railway (5 minutes)

```bash
railway login
railway new
railway up

Render.com

1. New Web Service → GitHub Repo
2. Build: pip install -r requirements.txt
3. Start: python main.py

🔄 Environment Variables

| Variable     | Development                 | Production            |
| ------------ | --------------------------- | --------------------- |
| DATABASE_URL | duckdb:///data/device_fp.db | postgresql://...      |
| FLASK_ENV    | development                 | production            |
| SECRET_KEY   | dev-secret-key              | production-secret-key |
| DEBUG        | True                        | False                 |

🐍 Production venv Setup

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
gunicorn main:app --workers 4 --bind 0.0.0.0:5000

🧪 Health Check

GET /health → {"status": "healthy", "database": "connected"}

🔄 Database Migration (Dev → Prod)

# Generate schema
python src/generate_schema.py > schema.sql

# PostgreSQL
psql -U user -d device_fp_db -f schema.sql

Production Checklist: [ ] DB Migration [ ] SSL [ ] Monitoring [ ] venv

```
