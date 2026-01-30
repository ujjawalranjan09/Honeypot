# Agentic Honey-Pot API for Scam Detection & Intelligence Extraction

An AI-powered honeypot system that detects scam intent and autonomously engages scammers to extract useful intelligence without revealing detection.

## 🚀 Features

- **Scam Detection**: Hybrid ML + rule-based detection for English, Hindi, and Hinglish
- **Multi-turn Conversations**: Maintains context across conversation sessions
- **AI Agent Personas**: 6 distinct personas with Hinglish/localized support
- **Intelligence Extraction**: Extracts phone numbers, UPI IDs, bank accounts, phishing links
- **Multi-Model Fallback**: Robust queue-based system using 15+ models (Llama 3.3, Gemini, Qwen, etc.)
- **GUVI Callback**: Automatically reports results to GUVI evaluation endpoint
- **REST API**: Production-ready FastAPI with authentication

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

## 🔧 Architecture

1. **Scam Detector**: Hybrid approach using:
   - TF-IDF + Gradient Boosting ML model
   - Rule-based pattern matching for urgency, threats, financial keywords

2. **AI Agent**: Uses Google Gemini with fallback templates
   - Three personas for different scam scenarios
   - Context-aware response generation

3. **Intelligence Extractor**: Regex-based extraction for:
   - Phone numbers (Indian format)
   - UPI IDs (all banks)
   - Bank account numbers
   - Phishing links
   - Suspicious keywords

4. **Session Manager**: Tracks conversation state and triggers GUVI callback

## 📄 License

MIT License
