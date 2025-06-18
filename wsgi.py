# wsgi.py
from app.web.routes import app

# Vercel’s Python builder will look for “app” or “application” in here
application = app
