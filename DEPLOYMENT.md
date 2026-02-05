# 🚀 Deployment Guide for Agentic Honey-Pot

This project is configured for easy deployment on **Render.com**. Follow these steps to get your honeypot live.

## 1. Prerequisites
- A GitHub account.
- A Render.com account.
- API Keys:
  - `HONEYPOT_API_KEY`: Create a strong secret string.
  - `GEMINI_API_KEY`: Your Google Gemini API key.

## 2. Prepare Repository
1. Ensure all changes are committed and pushed to your GitHub repository.
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

## 3. Deploy to Render (The Easy Way)
We use a `render.yaml` Blueprint which automates the configuration.

1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** and select **Blueprint**.
3. Connect your GitHub repository.
4. Render will detect the `render.yaml` file.
5. You will be prompted to enter the **Environment Variables**:
   - `HONEYPOT_API_KEY`: Enter your chosen secret key.
   - `GEMINI_API_KEY`: Enter your Gemini API Key.
   - `LOG_LEVEL`: `INFO` (Default)
   - `LOG_FORMAT`: `json` (Default)
   - `RATE_LIMIT_ENABLED`: `true` (Default)
6. Click **Apply**.

Render will now:
- Build the environment (install Python dependencies).
- Start the server using Gunicorn.
- Serve your API and the Dashboard Frontend users at the root URL.

## 4. Verify Deployment
Once deployed, Render will provide a URL (e.g., `https://honey-pot-agent.onrender.com`).

1. **Dashboard**: Visit the URL to see the live Visual Dashboard.
2. **API**: The API endpoints are available at `/api/...`.
3. **Docs**: Visit `/docs` for the interactive API documentation.

## Vercel (Serverless) — Quick notes
This project is Vercel-ready and has a small model bundle (models ≈ 0.33 MB). To deploy on Vercel:

1. Import the repository in Vercel and set these environment variables:
   - `HONEYPOT_API_KEY`
   - `OPENROUTER_API_KEY` (or keys for rotation)
   - `OPENROUTER_MODEL` (optional)
2. Ensure `vercel.json` and `.vercelignore` are present (they are configured to include `models/**` and exclude large datasets and `venv/`).
3. If you hit the 250 MB limit, enable builder debug in Vercel (temporary):

```bash
# In Vercel dashboard (Environment Variables) or in CLI
VERCEL_BUILDER_DEBUG=1
```

Check the build log for `uncompressedLayerBytes` to see which function exceeded the limit.

### Quick fixes for the 250 MB error
- Exclude unnecessary files with `.vercelignore` and `vercel.json` `excludeFiles`/`includeFiles`.
- Remove heavy dev deps from `requirements.txt` (e.g., `pytest`, `pandas` if only used for training).
- Offload heavy work (training, analytics) to an external service or CI — only store the serialized `joblib` model in `models/`.
- Consider bundling/stripping optional compiled libs (use manylinux wheels) or move them to an external API.

### Recommended CI check (example)
Add this to CI to fail early if function size is near the limit:

```yaml
# .github/workflows/ci.yml snippet
- name: Build and measure function size (Linux runner)
  run: |
    pip install -r requirements.txt --no-build-isolation --no-deps
    vercel build --confirm || true
    # parse builder debug output or check .vercel/output/functions size
    du -sh .vercel/output/functions || true
```

## Troubleshooting
- **Build Failed**: Check Vercel build logs; enable `VERCEL_BUILDER_DEBUG=1` to see function sizes.
- **Missing dependencies at runtime**: Avoid importing heavy libraries at module import time—import them lazily inside the handler used for training only.
- **Model not loading in production**: Ensure `models/*.joblib` exist and are included via `includeFiles` in `vercel.json`.
- **Frontend not loading**: Ensure `frontend/` artifacts are present and `vercel.json` routing is correct.

If Vercel is unsuitable for extremely heavy server-side workloads, follow the Render instructions above (or use a small VM/container on any cloud provider).
