"""
Configuration Settings for Honey-Pot API
Enhanced with adaptive thresholds, engagement phases, and production settings
"""
import os
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

# ============== API Configuration ==============
API_KEY = os.getenv("HONEYPOT_API_KEY", "your-secret-api-key-here")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
GEMINI_API_KEY = "" # Deprecated


# GUVI Callback Endpoint
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# ============== Scam Detection Thresholds ==============
# Base threshold - lowered from 0.60 to catch subtle scams earlier
SCAM_CONFIDENCE_THRESHOLD = 0.48

# Adaptive thresholds per scam type (some require higher confidence)
SCAM_TYPE_THRESHOLDS: Dict[str, float] = {
    "UPI_Banking_Fraud": 0.40,      # Catch banking fraud early
    "Government_Phishing": 0.42,    # Government scams are serious
    "Phishing": 0.45,               # General phishing
    "Loan_Fraud": 0.45,             # Loan scams often target desperate
    "Prize_Lottery_Scam": 0.55,     # Need higher confidence (false positives common)
    "Subscription_Fraud": 0.50,     # Moderate confidence
    "Malware_Scam": 0.45,           # Security threats
    "Social_Media_Phishing": 0.48,  # Social engineering
    "Link_Phishing": 0.45,          # Suspicious links
    "General_Scam": 0.48,           # Default threshold
}

# ============== Scoring Weights ==============
SCORING_WEIGHTS = {
    "ml_model": 0.60,               # Weight for ML model prediction
    "rule_based": 0.40,             # Weight for rule-based detection
    "context_bonus": 0.15,          # Bonus for contextual patterns
    "sentiment_weight": 0.10,       # Weight for sentiment analysis
}

# Keyword category weights for rule-based scoring
# These are aggressive - suspicious links alone should almost trigger detection
KEYWORD_WEIGHTS = {
    "urgency": 0.25,            # Was 0.15 - increased for urgency detection
    "threat": 0.30,             # Was 0.15 - threats are rare in normal chats
    "action": 0.15,             # Was 0.10 - action requests are suspicious
    "prize": 0.40,              # Was 0.15 - lotteries are almost always scams
    "financial": 0.20,          # Was 0.10 - financial keywords are significant
    "suspicious_link": 0.60,    # Was 0.25 - links are huge scam signals
    "phone_number": 0.20,       # Was 0.10 - phone in unsolicited msg is suspicious
    "upi_id": 0.30,             # Was 0.10 - UPI ID requests are high risk
}

# ============== Engagement Configuration ==============
MIN_ENGAGEMENT_MESSAGES = 5         # Minimum messages before extracting final intelligence
MAX_ENGAGEMENT_MESSAGES = 100       # Increased for 40+ turn ultra-marathons

# Engagement phases with message ranges and goals
ENGAGEMENT_PHASES = {
    "confusion": {
        "range": (1, 3),
        "goals": ["Express confusion", "Ask clarifying questions", "Establish persona"],
        "tactics": ["delayed_understanding", "repeat_questions", "seek_help"]
    },
    "compliance": {
        "range": (4, 8),
        "goals": ["Show willingness", "Extract contact info", "Build trust"],
        "tactics": ["cooperative", "ask_verification", "share_hesitation"]
    },
    "fake_info": {
        "range": (9, 15),
        "goals": ["Provide fake information", "Keep engaged", "Extract more details"],
        "tactics": ["incomplete_info", "wrong_format", "ask_for_help"]
    },
    "stalling": {
        "range": (16, 100),
        "goals": ["Stall for time", "Final extraction", "Document evidence"],
        "tactics": ["interruptions", "technical_issues", "family_consultation"]
    }
}

# ============== Response Configuration ==============
RESPONSE_LIMITS = {
    "max_length": 150,              # Shorter for realism (SMS/chat style)
    "min_length": 15,               # Can be very short
    "max_sentences": 2,             # Max 2 sentences for natural chat
    "typo_probability": 0.20,       # Increased typo rate for realism
    "delay_simulation_ms": (1000, 3000),    # 1-3 seconds for faster testing (was 30-60s)
}

# ============== Model Configuration ==============
MODEL_PATH = "models/scam_detector.joblib"
VECTORIZER_PATH = "models/tfidf_vectorizer.joblib"

# Model training parameters
MODEL_PARAMS = {
    "n_estimators": 200,
    "max_depth": 7,
    "learning_rate": 0.1,
    "max_features": 5000,
    "ngram_range": (1, 3),
    "min_df": 2,
    "max_df": 0.95,
    "test_size": 0.2,
    "random_state": 42,
}

# ============== Session Configuration ==============
SESSION_TIMEOUT_MINUTES = 30
SESSION_CLEANUP_INTERVAL_SECONDS = 300

# Intelligence quality thresholds for smart completion
INTELLIGENCE_QUALITY_THRESHOLDS = {
    "min_phone_numbers": 1,
    "min_evidence_pieces": 2,
    "min_confidence": 0.6,
}

# ============== Callback Configuration ==============
CALLBACK_CONFIG = {
    "timeout_seconds": 10,
    "max_retries": 3,
    "retry_backoff_base": 2,        # Exponential backoff base (2^attempt seconds)
    "retry_backoff_max": 30,        # Maximum backoff delay
}

# ============== Logging Configuration ==============
LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "json",               # 'json' or 'text'
    "include_request_body": True,
    "include_response_body": True,
    "max_body_length": 1000,        # Truncate long bodies
}

# ============== Rate Limiting ==============
RATE_LIMIT_CONFIG = {
    "enabled": True,
    "requests_per_session_per_minute": 30,
    "requests_per_ip_per_minute": 100,
}

# ============== Sentiment Analysis Patterns ==============
SENTIMENT_PATTERNS = {
    "urgency_phrases": [
        r"(?:do|act)\s+(?:now|immediately|fast|quickly)",
        r"(?:only|just)\s+\d+\s+(?:minutes?|hours?|days?)\s+(?:left|remaining)",
        r"(?:last|final)\s+(?:chance|warning|notice)",
        r"(?:time\s+is\s+running\s+out|don't\s+delay|hurry\s+up)",
        r"(?:before\s+it's\s+too\s+late|urgent\s+action)",
    ],
    "fear_phrases": [
        r"(?:account|card)\s+(?:will\s+be|has\s+been)\s+(?:blocked|suspended|frozen)",
        r"(?:unauthorized|suspicious)\s+(?:activity|transaction|access)",
        r"(?:legal\s+action|police|court|arrest)",
        r"(?:your\s+money\s+is|funds\s+are)\s+(?:at\s+risk|not\s+safe)",
        r"(?:security\s+(?:breach|alert|threat))",
    ],
    "trust_building": [
        r"(?:i\s+am|this\s+is)\s+(?:from|calling\s+from)\s+(?:\w+\s+)?(?:bank|support|service)",
        r"(?:official|verified|authorized)\s+(?:representative|agent|officer)",
        r"(?:for\s+your\s+(?:safety|security|protection))",
        r"(?:government|rbi|sebi)\s+(?:approved|authorized|mandated)",
    ],
}

# ============== Multi-Stage Pattern Detection ==============
SCAM_PROGRESSION_PATTERNS = {
    "classic_banking": [
        ("greeting", r"(?:hello|hi|dear\s+(?:sir|madam|customer))"),
        ("identity_claim", r"(?:from\s+(?:\w+\s+)?bank|customer\s+(?:care|service))"),
        ("problem_statement", r"(?:account|card|kyc)\s+(?:blocked|suspended|expired|issue)"),
        ("urgency", r"(?:within\s+\d+\s+hours?|immediately|today)"),
        ("action_request", r"(?:share|send|provide|verify)\s+(?:otp|details|number)"),
    ],
    "prize_scam": [
        ("congratulations", r"(?:congratulations|congrats|you\s+(?:have\s+)?won)"),
        ("prize_claim", r"(?:prize|reward|lottery|gift|lucky\s+winner)"),
        ("urgency", r"(?:claim\s+(?:now|within)|limited\s+time|expires?)"),
        ("fee_request", r"(?:processing\s+fee|tax|charges|pay\s+(?:small\s+)?amount)"),
    ],
    "loan_scam": [
        ("offer", r"(?:loan\s+(?:approved|offer|available)|pre-?approved)"),
        ("attractive_terms", r"(?:low\s+interest|no\s+documents?|instant|easy)"),
        ("urgency", r"(?:limited\s+(?:time\s+)?offer|today\s+only|expires?)"),
        ("fee_request", r"(?:processing\s+fee|advance|deposit|charges)"),
    ],
}

# ============== Geographic Indicators ==============
INDIAN_CITY_CODES = {
    "011": "Delhi",
    "022": "Mumbai",
    "033": "Kolkata",
    "044": "Chennai",
    "080": "Bangalore",
    "040": "Hyderabad",
    "079": "Ahmedabad",
    "020": "Pune",
    "0124": "Gurgaon",
    "0120": "Noida",
}

INDIAN_CITIES = [
    "delhi", "mumbai", "bangalore", "bengaluru", "chennai", "kolkata",
    "hyderabad", "pune", "ahmedabad", "jaipur", "lucknow", "kanpur",
    "nagpur", "indore", "thane", "bhopal", "visakhapatnam", "patna",
    "vadodara", "ghaziabad", "ludhiana", "agra", "nashik", "faridabad",
    "meerut", "rajkot", "varanasi", "srinagar", "aurangabad", "dhanbad",
    "amritsar", "allahabad", "ranchi", "howrah", "coimbatore", "jabalpur",
    "gwalior", "vijayawada", "jodhpur", "madurai", "raipur", "kota",
    "gurgaon", "noida", "chandigarh",
]

# ============== Payment Platforms ==============
PAYMENT_PLATFORMS = [
    "paytm", "phonepe", "googlepay", "gpay", "bhim", "amazonpay",
    "mobikwik", "freecharge", "airtel money", "jio money",
    "phonepay", "google pay", "amazon pay", "bhim upi",
]
