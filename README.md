# Agentic Honey-Pot API for Scam Detection & Intelligence Extraction

**Version 5.2 "Bharat Shield Ultimate"** - An AI-powered honeypot system that detects scam intent using **32 specialized Kill Switches** and autonomously engages scammers to extract useful intelligence without revealing detection.

## 🚀 Features

- **Hybrid Scam Detection**: ML + Rule-based + 32 Kill Switches for English, Hindi, and Hinglish
- **Indian Environment Hardening**: Hi Mom, Aadhaar, SBI YONO, EPF, FASTag, and 27 more scam types
- **32 Scam Categories**: Comprehensive coverage of the Indian cybercrime landscape
- **Universal Semantic Filter**: LLM intent analysis handles novel "grooming" scams missed by keyword filters
- **Global Scammer Profiling**: Persistent cross-session tracking of repeat offenders (UPI, Phone, Crypto)
- **Enhanced Intelligence Extraction**: Vehicle Numbers, Employee IDs, Bank Details, and Crypto Wallets
- **Multi-Model Fallback**: Ultra-robust queue using 30+ Free-tier models and 10+ rotating API keys
- **116+ Contextual Fallbacks**: Specialized Hinglish responses for each scam category
- **Visual Intelligence Reports**: Premium cyberpunk-themed HTML dashboard
- **2024-2025 Threat Intelligence**: Updated with latest Indian cybercrime research and web-crawled trends

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

## 🧪 Testing

```bash
# Run the end-to-end validation test
python final_validation_test.py
```

## 🏗️ Project Structure

```
honeypot-project/
├── main.py                 # FastAPI application
├── config.py               # Configuration settings
├── models.py               # Pydantic models
├── scam_detector.py        # ML + rule-based detection
├── intelligence_extractor.py  # Extract scam intel
├── ai_agent.py             # AI persona engine
├── session_manager.py      # Session lifecycle
├── test_api.py             # Test script
├── requirements.txt        # Dependencies
├── .env.example            # Environment template
├── massive_5k_scam_dataset.csv  # Training data
└── models/                 # Trained ML models
    ├── scam_detector.joblib
    └── tfidf_vectorizer.joblib
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
