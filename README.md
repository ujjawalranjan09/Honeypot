# Agentic Honey-Pot API for Scam Detection & Intelligence Extraction

**Version 5.3 "Neural Sentinel"** - An AI-powered honeypot system that detects scam intent using **32 specialized Kill Switches** and **Tactical Diversity Tracking** to autonomously engage scammers and extract useful intelligence.

## 🚀 Features

- **Hybrid Scam Detection**: ML + Rule-based + 32 Kill Switches for English, Hindi, and Hinglish
- **Novel Scam Synergies**: Detects complex manipulation tactics (Authority Trap, Double Bait, Isolation Pressure)
- **Strategy Pivot Detection**: Automatically identifies when a scammer shifts tactics or narrative mid-session
- **Tactical Diversity Tracking**: Monitors unique social engineering markers to assess scammer sophistication
- **Indian Environment Hardening**: Hi Mom, Aadhaar, SBI YONO, EPF, FASTag, and 28 more scam types
- **33 Scam Categories**: Comprehensive coverage of the Indian cybercrime landscape including Novel Scams
- **Universal Semantic Filter**: LLM intent analysis handles novel "grooming" scams missed by keyword filters
- **Global Scammer Profiling**: Persistent cross-session tracking of repeat offenders (UPI, Phone, Crypto)
- **"Fail-Fast" Multi-Model Fallback**: Ultra-robust queue with rotating API keys and fast fallback to 30+ contextual responses
- **Intelligent Plateau Completion**: Automatically disengages when learning value peaks or scammer disengages
- **Visual Intelligence Reports**: Premium cyberpunk-themed HTML dashboard
- **2024-2025 Threat Intelligence**: Updated with the latest Indian cybercrime research and web-crawled trends
- **Production Ready**: Deploys to Vercel serverless (<250 MB) with optimized dependencies

## 📦 Installation

```bash
# Clone or navigate to project
cd honeypot-project

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## ⚙️ Configuration

1. Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```

2. Update `.env` with your keys:
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

### Complete Engagement (Trigger Callback)
```http
POST /api/complete/{session_id}
X-API-Key: YOUR_SECRET_API_KEY
```

### Train Model
```http
POST /api/train
X-API-Key: YOUR_SECRET_API_KEY
```

### Get Statistics
```http
GET /api/stats
X-API-Key: YOUR_SECRET_API_KEY
```

## 📊 Response Format (GUVI Compliant)

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
    "bankAccounts": [],
    "upiIds": [],
    "phishingLinks": ["http://bank-secure.com"],
    "phoneNumbers": ["+919876543210"],
    "suspiciousKeywords": ["urgent", "verify", "blocked"]
  },
  "agentNotes": "Scammer using urgency tactics",
  "engagementComplete": false
}
```

## 🚀 Deployment

### Vercel (Serverless)
The project is optimized for Vercel serverless functions (<250 MB).

1. Push to GitHub (main branch)
2. Import repository in Vercel
3. Set environment variables:
   - `HONEYPOT_API_KEY`
   - `OPENROUTER_API_KEY`
   - `OPENROUTER_MODEL` (optional)
4. Deploy

**Note**: The `vercel.json` configuration handles serverless routing. Model files are auto-included.

### Render.com (Alternative)
See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed Render deployment instructions.

## 🧪 Testing

```bash
# Run model prediction test
python test_model.py

# Run detector integration test
python test_detector.py

# Run end-to-end validation
python final_validation_test.py
```

**Test Results** (as of Feb 2026):
- Model accuracy: 97.8% on training set (158,740 samples)
- Prediction tests: 71.4% on diverse test cases
- Model size: 0.33 MB (well under Vercel 250 MB limit)

## 🏗️ Project Structure

```
honeypot-project/
├── main.py                 # FastAPI application (entry point)
├── config.py               # Configuration settings & thresholds
├── models.py               # Pydantic data models
├── scam_detector.py        # ML + rule-based detection engine
├── intelligence_extractor.py  # Extract scam intel (UPI, links, phones)
├── ai_agent.py             # AI persona engine with multi-model fallback
├── session_manager.py      # Session lifecycle & state management
├── logging_config.py       # Structured logging setup
├── exceptions.py           # Custom exception classes
├── requirements.txt        # Python dependencies (production)
├── .env.example            # Environment variables template
├── vercel.json             # Vercel serverless configuration
├── .vercelignore           # Files to exclude from deployment
├── api/
│   └── index.py            # Vercel function handler
├── models/                 # Trained ML artifacts (git-ignored locally, tracked in repo)
│   ├── scam_detector.joblib
│   └── tfidf_vectorizer.joblib
├── frontend/               # Visual dashboard (HTML/JS)
│   ├── index.html
│   └── app.js
├── tests/                  # Unit tests
│   ├── test_api.py
│   ├── test_detector.py
│   └── test_extractor.py
└── docs/                   # Documentation (optional)
    ├── ARCHITECTURE.md
    ├── DEPLOYMENT.md
    └── MODULE_DOCUMENTATION.md
```

## 🔧 Architecture (V4.0)

1. **Scam Detector** (19 Kill Switches):
   - TF-IDF + Gradient Boosting ML model
   - 19 specialized Kill Switches for high-confidence detection
   - Categories: Pig Butchering, Honeytrap, Voice Cloning, CEO Fraud, etc.

2. **AI Agent** (68+ Fallback Responses):
   - 12 specialized personas for different scam scenarios
   - Hinglish psychological counter-interrogation tactics
   - Multi-model fallback with 30+ free-tier models

3. **Intelligence Extractor** (Enhanced):
   - Phone numbers (Indian format)
   - UPI IDs (all banks)
   - Bank account numbers
   - Vehicle Numbers (Indian plates)
   - Employee/Agent IDs
   - Crypto Wallets
   - Phishing links

4. **Session Manager**: Tracks conversation state and triggers GUVI callback

## 📄 License

MIT License
