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

## Troubleshooting
- **Build Failed**: Check the logs. If `gunicorn` not found, ensure `requirements.txt` is updated.
- **Application Error**: Check the "Logs" tab in Render for Python errors.
- **Frontend not loading**: Ensure `frontend/` folder is in the root of the repo.
