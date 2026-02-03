import os

# Gunicorn Configuration Strategey
# This file is automatically loaded by Gunicorn and enforces the correct settings
# regardless of the command line arguments used by Render.

# Worker Class - CRITICAL for FastAPI
# Using 'sync' (default) causes the "missing 'send'" error. 
# We must enforce UvicornWorker.
worker_class = "uvicorn.workers.UvicornWorker"

# Binding
# Bind to 0.0.0.0 to expose externally, use PORT env var (default 10000 on Render)
port = os.getenv("PORT", "10000")
bind = f"0.0.0.0:{port}"

# Worker Processes
# 1 worker is usually sufficient for free tier to save memory
workers = 1

# Timeout
# Increase timeout to handle ML model loading/training on startup
timeout = 120

# Logging
loglevel = "info"
accesslog = "-"  # Stdout
errorlog = "-"   # Stderr
