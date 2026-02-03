---
description: How to run and use the Interactive Honeypot Dashboard
---

# Interactive Honeypot Dashboard

This workflow explains how to launch and use the new interactive frontend to track your AI Honeypot's backend status, model queue, and active sessions.

## 1. Start the Backend API
Make sure your FastAPI server is running.
```powershell
# In terminal 1
cd e:\Python\honeypot-project
.\venv\Scripts\python.exe main.py
```

## 2. Launch the Dashboard
Since the dashboard is a static HTML/JS file, you can simply open it in your browser.
```powershell
# Open via command line
start frontend/index.html
```
*Alternatively, double-click `frontend/index.html` in File Explorer.*

## 3. Dashboard Features

### 📊 Real-Time Monitoring
- **Live Sessions**: Shows the count of active scammer interactions.
- **Threat Counter**: Tracks total detected scam attempts.
- **Intelligence Vault**: Displays captured UPI IDs, Bank Accounts, and Phone Numbers in real-time.

### 🧠 Neural Core Status (New!)
- **Key Pool**: Shows how many API keys are active in your rotation pool (e.g., "5 Active Keys").
- **Current Model**: Displays which AI model is currently serving requests (e.g., `llama-3.3-70b`).
- **Fallback Queue**: Shows the number of backup models ready to take over if the primary fails.

### 🧪 Scammer Sandbox
1. Click the **"Sandbox Mode"** button.
2. The UI switches to a simulated environment.
3. Type a message as a "Scammer" (e.g., "Madam, your parcel is blocked").
4. Watch the AI Agent reply using its current Persona and Stalling Logic.
5. Verify that it extracts info or stalls correctly.

## 4. Troubleshooting
- If "System Degraded" or "disconnected" appears:
  - Check if `main.py` is running.
  - Open console (F12) to see connection errors.
  - Ensure `http://127.0.0.1:8000` is accessible.
