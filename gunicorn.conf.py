import os

# Gunicorn Configuration for Render Free Tier
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
# 1 worker is sufficient for free tier to save memory
workers = 1

# Timeouts - increased for evaluation harness burst traffic
# Render free tier can be slow to process concurrent requests
timeout = 180           # Worker silent timeout (was 120)
graceful_timeout = 30   # Time to finish in-flight requests on shutdown
keepalive = 5           # Keep connections alive for 5s (helps evaluator bursts)

# Limit concurrent connections to prevent free-tier OOM crashes
worker_connections = 100

# Logging
loglevel = "info"
accesslog = "-"  # Stdout
errorlog = "-"   # Stderr
