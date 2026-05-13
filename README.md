<div align="center">

# 🛡️ Honeypot — AI-Powered Scam Detection System

**Version 5.3 "Neural Sentinel"**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![ML](https://img.shields.io/badge/ML-scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Vercel](https://img.shields.io/badge/Deployed-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

*An intelligent honeypot API that autonomously engages scammers, extracts threat intelligence, and protects users — built specifically for the Indian cybercrime landscape.*

</div>

---

## 🎯 What This Project Does

Honeypot is a **production-deployed FastAPI backend** that acts as a decoy to trap, analyze, and extract intelligence from cyber scammers. When a scammer sends a message, the system:

1. **Detects scam intent** using a hybrid ML + rule-based engine (97.8% accuracy on 158,740 samples)
2. **Responds like a victim** using AI personas to keep the scammer engaged
3. **Extracts criminal intelligence** — UPI IDs, phone numbers, phishing links, bank accounts
4. **Profiles repeat offenders** across sessions for persistent tracking
5. **Generates visual threat reports** via a cyberpunk-themed HTML dashboard

> 🏆 Built for the **Indian cybercrime landscape** — covers 33 scam categories including SBI YONO, Aadhaar, EPF, FASTag, UPI fraud, and more.

---

## ✨ Key Features

- **32 Kill Switches** — specialized detection rules for English, Hindi, and Hinglish scams
- **Hybrid Detection** — TF-IDF + Gradient Boosting ML + rule-based engine
- **Multi-Model AI Agent** — 12 personas, 68+ fallback responses, rotating API keys
- **Intelligence Extraction** — captures UPI IDs, phone numbers, phishing URLs, crypto wallets
- **Strategy Pivot Detection** — identifies mid-session tactic changes by scammers
- **Global Scammer Profiling** — cross-session tracking of repeat offenders
- **Production Ready** — deployed to Vercel serverless (<250 MB)
- **Novel Scam Synergies** — detects Authority Trap, Double Bait, Isolation Pressure tactics

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| API Framework | FastAPI + Uvicorn |
| ML Engine | scikit-learn (TF-IDF + Gradient Boosting) |
| LLM Integration | OpenRouter API (Llama 3.3 70B) |
| Deployment | Vercel Serverless / Render.com |
| Frontend Dashboard | Vanilla HTML/JS (cyberpunk theme) |
| Testing | pytest |

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/ujjawalranjan09/Honeypot.git
cd Honeypot

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys
```

## ⚙️ Configuration

Edit `.env` with your keys:
```env
HONEYPOT_API_KEY=your-secret-api-key-here
OPENROUTER_API_KEY=your-openrouter-api-key-here
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free
```

## 🏃 Running the API

```bash
# Start the server
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

---

## 📡 API Endpoints

### Health Check
```http
GET /api/health
```

### Process Message (Main Endpoint)
```http
POST /api/message
X-API-Key: YOUR_SECRET_API_KEY
Content-Type: application/json

{
  "sessionId": "unique-session-id",
  "message": {
    "sender": "scammer",
    "text": "Your bank account will be blocked. Verify immediately.",
    "timestamp": "2026-01-29T10:15:30Z"
  },
  "conversationHistory": [],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

### Get Session Status
```http
GET /api/session/{session_id}
X-API-Key: YOUR_SECRET_API_KEY
```

### Get Statistics
```http
GET /api/stats
X-API-Key: YOUR_SECRET_API_KEY
```

---

## 📊 Sample Response

```json
{
  "status": "success",
  "scamDetected": true,
  "reply": "Oh dear, what happened to my account? Please help me.",
  "engagementMetrics": {
    "engagementDurationSeconds": 120,
    "totalMessagesExchanged": 4,
    "currentPhase": "compliance"
  },
  "extractedIntelligence": {
    "upiIds": [],
    "phishingLinks": ["http://bank-secure.com"],
    "phoneNumbers": ["+919876543210"],
    "suspiciousKeywords": ["urgent", "verify", "blocked"]
  },
  "agentNotes": "Scammer using urgency tactics",
  "engagementComplete": false
}
```

---

## 📈 Performance Metrics

- **Model Accuracy**: 97.8% on training set (158,740 samples)
- **Test Coverage**: 71.4% on diverse real-world test cases
- **Model Size**: 0.33 MB (well under Vercel 250 MB limit)
- **Scam Categories**: 33 categories covering Indian cybercrime landscape
- **Kill Switches**: 32 specialized high-confidence detection rules

---

## 🏗️ Project Structure

```
honeypot/
├── main.py                    # FastAPI application entry point
├── config.py                  # Configuration & detection thresholds
├── models.py                  # Pydantic data models
├── scam_detector.py           # ML + rule-based detection engine
├── intelligence_extractor.py  # Extract UPI IDs, phishing links, etc.
├── ai_agent.py                # AI persona engine with multi-model fallback
├── session_manager.py         # Session lifecycle & state management
├── api/index.py               # Vercel serverless handler
├── frontend/                  # Visual dashboard (HTML/JS)
├── tests/                     # pytest test suite
├── requirements.txt
├── vercel.json
└── .env.example
```

---

## 🚀 Deployment

### Vercel (Recommended)
1. Push to GitHub
2. Import repo in Vercel dashboard
3. Set environment variables (`HONEYPOT_API_KEY`, `OPENROUTER_API_KEY`)
4. Deploy

### Render.com
See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions.

---

## 🧪 Testing

```bash
python final_validation_test.py   # End-to-end validation
python quick_test.py              # Quick smoke test
pytest tests/                     # Full test suite
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ by [Ujjawal Ranjan](https://github.com/ujjawalranjan09) | RTU, Jaipur**

*Fighting cybercrime, one scammer at a time.*

</div>
