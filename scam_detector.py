"""
Enhanced Scam Detection Module
Uses ML model + rule-based patterns + contextual analysis + sentiment detection
"""
import re
import os
import joblib
import pandas as pd
from typing import Tuple, List, Optional, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split

from config import (
    SCAM_CONFIDENCE_THRESHOLD,
    SCAM_TYPE_THRESHOLDS,
    SCORING_WEIGHTS,
    KEYWORD_WEIGHTS,
    MODEL_PATH,
    VECTORIZER_PATH,
    MODEL_PARAMS,
    SENTIMENT_PATTERNS,
    SCAM_PROGRESSION_PATTERNS,
)
from models import Message, ThreatLevel, ScamClassification
from exceptions import ModelNotTrainedError, ModelPredictionError
from logging_config import get_logger, log_with_context
import logging

logger = get_logger("honeypot.scam_detector")


class ScamDetector:
    """
    Enhanced hybrid scam detector using:
    1. ML model (TF-IDF + Gradient Boosting)
    2. Rule-based pattern matching for known scam indicators
    3. Contextual analysis of conversation history
    4. Sentiment analysis for urgency/fear tactics
    5. Multi-stage pattern detection
    6. Adaptive thresholds per scam type
    """
    
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.is_trained = False
        
        # Urgency keywords indicating scam intent
        self.urgency_keywords = [
            "urgent", "immediate", "immediately", "turant", "तुरंत", "तत्काल",
            "now", "today", "24 hours", "abhi", "अभी", "jaldi", "जल्दी",
            "last chance", "final notice", "warning", "alert", "asap",
            "expired", "expire", "block", "stop", "tonight"
        ]
        
        # Threat keywords
        self.threat_keywords = [
            "block", "suspend", "delete", "deactivate", "terminate",
            "blocked", "suspended", "compromised", "hacked", "infected",
            "ब्लॉक", "निलंबित", "हैक", "संक्रमित", "banned", "frozen",
            "arrest", "warrant", "court", "police", "jail", "cbi", "summons",
            "raid", "investigation", "crime", "illegal", "money laundering",
            "parcel", "drugs", "customs", "narcotics", "seized", "mumbai airport",
            "aadhaar linked", "fedex", "dhl", "digital arrest", "ncb", "officer sharma",
            "supreme court", "high court", "arrest warrant", "paisa laundering",
            "passport blocked", "skype call", "video verification", "officer", "disconnect",
            "single doctor", "widower", "profile on linkedin", "felt a connection"
        ]
        
        # Action request keywords
        self.action_keywords = [
            "verify", "click", "share", "send", "call", "whatsapp",
            "update", "confirm", "login", "download", "install",
            "सत्यापित", "क्लिक", "भेजें", "कॉल", "डाउनलोड"
        ]
        
        # Prize/reward scam keywords
        self.prize_keywords = [
            "won", "winner", "congratulations", "prize", "lottery", "gift",
            "reward", "claim", "selected", "lucky", "free", "badhai",
            "ambassador", "collab", "influencer", "watches",
            "जीत", "बधाई", "पुरस्कार", "मुफ्त", "इनाम"
        ]
        
        # Financial scam keywords
        self.financial_keywords = [
            "opportunity", "part time", "job", "HR", "hiring", "salary",
            "work from home", "daily income", "investment", "returns",
            "crypto", "bitcoin", "trading", "stock", "profit", "capital",
            "double", "multiply", "binance", "usd", "usdt", "growth potential",
            "joint venture", "business proposition", "partnership",
            "upi", "bank", "account", "payment", "loan", "interest",
            "emi", "credit", "debit", "aadhaar", "pan", "kyc",
            "crypto", "investment", "trading", "profit", "commission",
            "बैंक", "खाता", "भुगतान", "ऋण", "आधार", "otp", "cvv", "pin",
            "cryptocurrency", "broker", "lic", "policy", "insurance",
            "claim", "refund", "agent", "bonus", "premium", "maturity",
            "airtel", "jio", "bsnl", "vodafone", "sim card", "esim", "5g upgrade",
            "challan", "fine", "rto", "penalty", "payment gate"
        ]

        # Job/Task scam keywords
        self.job_keywords = [
            "part time", "job", "work from home", "earn money", "daily income",
            "salary", "bonus", "tasks", "review", "like youtube", "subscribe",
            "simple tasks", "side income", "telegram job"
        ]

        # Crypto keywords
        self.crypto_keywords = [
            "crypto", "bitcoin", "usdt", "binance", "trading", "expert",
            "signals", "investment", "profit", "double", "liquidity",
            "wallet", "private key", "seed phrase", "trust wallet"
        ]

        # Blackmail/Sextortion keywords
        self.blackmail_keywords = [
            "video", "recorded", "leaked", "scandal", "contacts", "friends",
            "social media", "ashamed", "police", "cyber cell", "delete",
            "payment", "money", "screenshot", "compromised"
        ]

        # Public Utility/Bill scam keywords
        self.utility_keywords = [
            "electricity", "disconnection", "unpaid bill", "sdo", "power cut",
            "electricity office", "update payment", "smart meter", "adani electricity",
            "bescom", "tneb", "mseb", "uppcl", "dhbvn", "supply", "consumer number", "bill"
        ]

        # V4.0: Pig Butchering / Long-Con Romance Scam
        self.pig_butchering_keywords = [
            "investment opportunity", "crypto platform", "trust me", "i love you",
            "trading signals", "withdraw profits", "guaranteed returns",
            "relationship", "overseas", "lonely", "widow", "widower",
            "long distance", "send me money", "my account is frozen",
            "mining pool", "liquidity pool", "eth", "btc", "usdt"
        ]

        # V4.0: Honey Trap / Video Call Sextortion
        self.honeytrap_keywords = [
            "video call", "whatsapp call", "nude", "intimate", "private video",
            "recorded you", "your contacts", "share with friends", "facebook leak",
            "morphed", "deepfake", "pay or else", "will viral", "your family will see"
        ]

        # V4.0: AI Voice Cloning / Deepfake Emergency
        self.voice_cloning_keywords = [
            "mom help", "dad i need money", "accident", "hospital urgent",
            "kidnapped", "held for ransom", "police custody", "bail money",
            "don't tell anyone", "this is your son", "i am in trouble",
            "send immediately", "my voice"
        ]

        # V4.0: CEO/Boss Fraud (BEC)
        self.ceo_fraud_keywords = [
            "this is your ceo", "urgent wire transfer", "confidential transaction",
            "do not discuss", "i am in a meeting", "handle this personally",
            "reply to my personal email", "vendor payment", "client payment"
        ]

        # V4.0: Viral Video Link Scam
        self.viral_link_keywords = [
            "7 minute viral video", "shocking video", "watch before deleted",
            "your video is trending", "click to see who viewed", "you are in this video"
        ]

        # V4.0: TRAI / DND Deactivation Scam
        self.trai_keywords = [
            "trai", "dnd", "sim deactivation", "your number will be disconnected",
            "press 1 to continue", "regulatory compliance", "telecom department"
        ]

        # V5.0: Stock Market / Trading Group / Fake IPO
        self.stock_trading_keywords = [
            "exclusive ipo", "premium trades", "guaranteed stock returns", 
            "adithya birla equity", "stock hub", "study circle", "sebi registered",
            "withdrawal tax", "processing fee for withdrawal", "500% returns",
            "trading platform", "insider tips", "whatsapp group", "citadel securities"
        ]

        # V5.0: Welfare / PM-Kisan / Ayushman Bharat
        self.welfare_scheme_keywords = [
            "pm kisan", "kisan samman nidhi", "ayushman mitra", "ayushman bharat", 
            "golden card", "govt subsidy", "registration fee for job", "₹2000 bonus",
            "eligibility check", "claim benefit"
        ]

        # V5.0: Rent / Security Deposit / OLX Property
        self.rent_scam_keywords = [
            "token amount", "block property", "security deposit before visit",
            "gate pass fee", "visiting charge", "property token", "olx rent",
            "magicbricks token", "rent deposit"
        ]

        # V5.0: Free Recharge / Data Lures
        self.recharge_scam_keywords = [
            "free recharge", "data balance", "3 months free", "jio free recharge", 
            "ram mandir free", "airtel free data", "recharge link"
        ]

        # V5.0: Election / Voter ID Fraud
        self.election_scam_keywords = [
            "voter id update", "election card", "voter list", "e-voter id", 
            "verify voter", "mandatory update", "govt portal kyc"
        ]

        # V5.1: Credit Card Reward Points
        self.credit_rewards_keywords = [
            "reward points", "expire today", "redeem points", "credit card limit",
            "redeem your cash", "points expiring", "bank reward", "hdfc points", "sbi points"
        ]

        # V5.1: FASTag KYC Update
        self.fastag_scam_keywords = [
            "fastag kyc", "fastag wallet", "fastag deactivated", "update kyc",
            "vehicle blocked", "call 1033", "uninterrupted service", "nhai"
        ]

        # V5.1: Income Tax Refund
        self.it_refund_keywords = [
            "income tax refund", "refund issued", "tax refund due", "refund pending",
            "verify bank account", "claim refund", "it department", "incometax.gov"
        ]
        
        # V5.1: Religious / Ram Mandir VIP
        self.religious_scam_keywords = [
            "ram mandir vip", "vip darshan", "prasad home delivery", "ayodhya entry",
            "donation drive", "temple trust", "vip pass"
        ]

        # V5.2: Hi Mom / Family Emergency WhatsApp
        self.hi_mom_keywords = [
            "hi mom", "hi mum", "hi dad", "new number", "lost my phone", "broken phone",
            "can't access bank", "urgent help", "need money now", "emergency transfer",
            "this is your son", "this is your daughter", "don't tell dad", "don't tell mom"
        ]

        # V5.2: Aadhaar / UIDAI Update
        self.aadhaar_scam_keywords = [
            "aadhaar update", "uidai update", "biometric update", "aadhaar expired",
            "aadhaar link", "aadhaar verification", "aeps", "aadhaar otp", "e-aadhaar"
        ]

        # V5.2: SBI YONO / Bank App Blocked
        self.yono_scam_keywords = [
            "yono blocked", "yono suspended", "sbi yono", "account blocked",
            "update pan", "pan aadhaar link", "download apk", "yono update",
            "account will be blocked", "netbanking suspended"
        ]

        # V5.2: EPF / PF Withdrawal
        self.epf_scam_keywords = [
            "pf withdrawal", "epf claim", "uan update", "epfo", "pf balance",
            "pf frozen", "pf transfer", "provident fund", "pf settlement"
        ]

        # V5.3: Education / Scholarship Scams (Targeting Parents)
        self.education_scam_keywords = [
            "scholarship approved", "pm scholarship", "cbse grant", "exam result fee",
            "school fee pending", "education loan approval", "child future fund", 
            "admission quota", "exam paper leaked"
        ]

        # V5.3: Malware Lures (WhatsApp Pink/Gold)
        self.malware_scam_keywords = [
            "whatsapp gold", "whatsapp pink", "update to premium", "exclusive features",
            "download apk", "install for 5g", "video call app", "screen share app"
        ]

        # V5.3: Telecom Mule / SMS Sender Apps
        self.telecom_mule_keywords = [
            "earn per sms", "rent your sim", "sms job", "background app",
            "sms forwarder", "earn passive income sms", "wingo app"
        ]
        
        # Suspicious link patterns
        self.suspicious_link_patterns = [
            r'http[s]?://[^\s]+(?:verify|secure|login|confirm|update|claim)',
            r'http[s]?://(?:bit\.ly|tinyurl|goo\.gl|t\.co|rb\.gy|is\.gd)\S+',
            r'http[s]?://[^\s]*(?:bank|upi|paytm|gpay|amazon|flipkart)[^\s]*\.(?:com|in|net)',
            r'www\.[^\s]+(?:verify|secure|confirm)',
            r'http[s]?://\d+\.\d+\.\d+\.\d+',  # IP-based URLs
        ]
        
        # Compile sentiment patterns
        self._compile_sentiment_patterns()
        
        # Load trained model if available
        self._load_model()
    
    def _compile_sentiment_patterns(self):
        """Pre-compile regex patterns for sentiment analysis"""
        self.compiled_sentiment = {}
        for category, patterns in SENTIMENT_PATTERNS.items():
            self.compiled_sentiment[category] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
    
    def _load_model(self):
        """Load pre-trained model if available"""
        try:
            if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
                self.model = joblib.load(MODEL_PATH)
                self.vectorizer = joblib.load(VECTORIZER_PATH)
                self.is_trained = True
                logger.info("Loaded pre-trained scam detection model")
        except Exception as e:
            logger.warning(f"Could not load model: {e}")
            self.is_trained = False
    
    def train_model(self, dataset_paths: List[str] = None):
        """Train the ML model on multiple scam datasets with enhanced processing"""
        try:
            if not dataset_paths:
                dataset_paths = [
                    "massive_20k_scam_dataset.csv",
                    "massive_5k_scam_dataset.csv"
                ]
            
            logger.info(f"Training scam detection model on {len(dataset_paths)} potential datasets...")
            
            dataframes = []
            
            # Common column names in various datasets
            text_cols = ['message_text', 'text', 'content']
            label_cols = ['label', 'is_scam', 'class']
            
            for path in dataset_paths:
                if not os.path.exists(path):
                    logger.warning(f"Dataset not found: {path}")
                    continue
                
                logger.info(f"Loading {path}...")
                try:
                    # Sniff headers
                    test_df = pd.read_csv(path, nrows=1)
                    has_headers = not str(test_df.iloc[0, 0]).isdigit() # Crude check for ID vs Name
                    
                    if not has_headers or "146" in str(test_df.columns[0]): # additional_data.csv style
                        # Matches: message_id,message_text,label,message_type,channel,language,locale,scam_keywords,confidence_score,scam_subtype,link_present,urgency_level
                        col_names = ['id', 'text', 'label', 'type', 'channel', 'lang', 'loc', 'keys', 'conf', 'sub', 'link', 'urgency']
                        curr_df = pd.read_csv(path, names=col_names, header=None)
                    else:
                        curr_df = pd.read_csv(path)
                    
                    # Unified columns
                    col_map = {}
                    for c in curr_df.columns:
                        if c.lower() in text_cols: col_map[c] = 'message_text'
                        if c.lower() in label_cols: col_map[c] = 'label'
                    
                    if 'message_text' not in col_map.values() or 'label' not in col_map.values():
                        # Fallback for datasets where we couldn't find named columns
                        if len(curr_df.columns) >= 3:
                            curr_df = curr_df.iloc[:, [1, 2]]
                            curr_df.columns = ['message_text', 'label']
                        else:
                            logger.warning(f"Could not parse columns for {path}")
                            continue
                    else:
                        curr_df.rename(columns=col_map, inplace=True)
                        curr_df = curr_df[['message_text', 'label']]
                    
                    dataframes.append(curr_df)
                    logger.info(f"Successfully loaded {len(curr_df)} samples from {path}")
                except Exception as e:
                    logger.error(f"Error loading {path}: {e}")
            
            if not dataframes:
                logger.error("No data loaded. Training aborted.")
                return None
            
            df = pd.concat(dataframes, ignore_index=True)
            df.drop_duplicates(inplace=True)
            logger.info(f"Total merged dataset size: {len(df)} samples")
            
            # Prepare data
            X = df['message_text'].astype(str).fillna('')
            y = (df['label'].astype(str).str.lower() == 'scam').astype(int)
            
            logger.info(f"Class distribution: {y.value_counts().to_dict()}")
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=MODEL_PARAMS["test_size"],
                random_state=MODEL_PARAMS["random_state"],
                stratify=y
            )
            
            # Vectorize text
            logger.info("Vectorizing features...")
            self.vectorizer = TfidfVectorizer(
                max_features=MODEL_PARAMS["max_features"],
                ngram_range=MODEL_PARAMS["ngram_range"],
                min_df=MODEL_PARAMS["min_df"],
                max_df=MODEL_PARAMS["max_df"]
            )
            X_train_vec = self.vectorizer.fit_transform(X_train)
            X_test_vec = self.vectorizer.transform(X_test)
            
            # Train model
            logger.info(f"Training GradientBoostingClassifier with {MODEL_PARAMS['n_estimators']} estimators...")
            self.model = GradientBoostingClassifier(
                n_estimators=MODEL_PARAMS["n_estimators"],
                max_depth=MODEL_PARAMS["max_depth"],
                learning_rate=MODEL_PARAMS["learning_rate"],
                random_state=MODEL_PARAMS["random_state"]
            )
            self.model.fit(X_train_vec, y_train)
            
            # Evaluate
            accuracy = self.model.score(X_test_vec, y_test)
            logger.info(f"Model trained with accuracy: {accuracy:.2%}")
            
            # Save model
            os.makedirs(os.path.dirname(MODEL_PATH) if os.path.dirname(MODEL_PATH) else "models", exist_ok=True)
            joblib.dump(self.model, MODEL_PATH)
            joblib.dump(self.vectorizer, VECTORIZER_PATH)
            logger.info(f"Model saved to {MODEL_PATH}")
            
            self.is_trained = True
            return accuracy
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return None
    
    def _rule_based_score(self, text: str) -> Tuple[float, List[str]]:
        """
        Calculate rule-based scam score based on keyword patterns
        Returns (score, detected_keywords)
        """
        text_lower = text.lower()
        score = 0.0
        detected_keywords = []
        
        # Check urgency keywords
        for keyword in self.urgency_keywords:
            if keyword.lower() in text_lower:
                score += KEYWORD_WEIGHTS["urgency"]
                detected_keywords.append(keyword)
        
        # Check threat keywords
        for keyword in self.threat_keywords:
            if keyword.lower() in text_lower:
                score += KEYWORD_WEIGHTS["threat"]
                detected_keywords.append(keyword)
        
        # Check action keywords
        for keyword in self.action_keywords:
            if keyword.lower() in text_lower:
                score += KEYWORD_WEIGHTS["action"]
                detected_keywords.append(keyword)
        
        # Check prize keywords
        for keyword in self.prize_keywords:
            if keyword.lower() in text_lower:
                score += KEYWORD_WEIGHTS["prize"]
                detected_keywords.append(keyword)
        
        # Check financial keywords
        for keyword in self.financial_keywords:
            if keyword.lower() in text_lower:
                score += KEYWORD_WEIGHTS["financial"]
                detected_keywords.append(keyword)
        
        # Check Job keywords
        for keyword in self.job_keywords:
            if keyword.lower() in text_lower:
                score += 0.15 # Default weight for job scam
                detected_keywords.append(keyword)

        # Check Crypto keywords
        for keyword in self.crypto_keywords:
            if keyword.lower() in text_lower:
                score += 0.2 # Default weight for crypto
                detected_keywords.append(keyword)

        # Check Blackmail keywords
        for keyword in self.blackmail_keywords:
            if keyword.lower() in text_lower:
                score += 0.2
                detected_keywords.append(keyword)

        # Check Utility/Bill keywords
        for keyword in self.utility_keywords:
            if keyword.lower() in text_lower:
                score += 0.25 # Higher weight for bill disconnection threats
                detected_keywords.append(keyword)

        # V4.0: Pig Butchering (Long-Con) - High risk
        for keyword in self.pig_butchering_keywords:
            if keyword.lower() in text_lower:
                score += 0.3
                detected_keywords.append(f"pigbutcher_{keyword}")

        # V4.0: Honey Trap / Video Call Sextortion
        for keyword in self.honeytrap_keywords:
            if keyword.lower() in text_lower:
                score += 0.35
                detected_keywords.append(f"honeytrap_{keyword}")

        # V4.0: AI Voice Cloning
        for keyword in self.voice_cloning_keywords:
            if keyword.lower() in text_lower:
                score += 0.35
                detected_keywords.append(f"voiceclone_{keyword}")

        # V4.0: CEO/Boss Fraud
        for keyword in self.ceo_fraud_keywords:
            if keyword.lower() in text_lower:
                score += 0.3
                detected_keywords.append(f"bec_{keyword}")

        # V4.0: Viral Video Link
        for keyword in self.viral_link_keywords:
            if keyword.lower() in text_lower:
                score += 0.3
                detected_keywords.append(f"virallink_{keyword}")

        # V5.1: Credit Card Rewards
        for keyword in self.credit_rewards_keywords:
            if keyword.lower() in text_lower:
                score += 0.25
                detected_keywords.append(f"credit_reward_{keyword}")

        # V5.1: FASTag KYC
        for keyword in self.fastag_scam_keywords:
            if keyword.lower() in text_lower:
                score += 0.25
                detected_keywords.append(f"fastag_{keyword}")
                
        # V5.1: Income Tax Refund
        for keyword in self.it_refund_keywords:
            if keyword.lower() in text_lower:
                score += 0.3
                detected_keywords.append(f"it_refund_{keyword}")

        # V5.1: Religious Scam
        for keyword in self.religious_scam_keywords:
            if keyword.lower() in text_lower:
                score += 0.25
                detected_keywords.append(f"religious_{keyword}")

        # V5.2: Hi Mom / Family Emergency
        for keyword in self.hi_mom_keywords:
            if keyword.lower() in text_lower:
                score += 0.35
                detected_keywords.append(f"hi_mom_{keyword}")

        # V5.2: Aadhaar / UIDAI Update
        for keyword in self.aadhaar_scam_keywords:
            if keyword.lower() in text_lower:
                score += 0.3
                detected_keywords.append(f"aadhaar_{keyword}")

        # V5.2: SBI YONO / Bank App Blocked
        for keyword in self.yono_scam_keywords:
            if keyword.lower() in text_lower:
                score += 0.3
                detected_keywords.append(f"yono_{keyword}")

        # V5.2: EPF / PF Withdrawal
        for keyword in self.epf_scam_keywords:
            if keyword.lower() in text_lower:
                score += 0.25
                detected_keywords.append(f"epf_{keyword}")

        # V4.0: TRAI/DND
        for keyword in self.trai_keywords:
            if keyword.lower() in text_lower:
                score += 0.25
                detected_keywords.append(f"trai_{keyword}")
        
        # Check for suspicious links
        for pattern in self.suspicious_link_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += KEYWORD_WEIGHTS["suspicious_link"]
                detected_keywords.append("suspicious_link")
        
        # Check for phone numbers
        phone_pattern = r'(?:\+91)?[\s-]?[6-9]\d{9}'
        if re.search(phone_pattern, text):
            score += KEYWORD_WEIGHTS["phone_number"]
            detected_keywords.append("phone_number")
        
        # Check for UPI ID pattern
        upi_pattern = r'[a-zA-Z0-9._-]+@[a-zA-Z]+'
        if re.search(upi_pattern, text):
            score += KEYWORD_WEIGHTS["upi_id"]
            detected_keywords.append("upi_id_request")
        
        # Cap at 1.0
        return min(score, 1.0), list(set(detected_keywords))
    
    def _analyze_sentiment(self, text: str) -> Tuple[float, List[str]]:
        """
        Analyze sentiment patterns for urgency, fear, and manipulation
        Returns (sentiment_score, detected_patterns)
        """
        score = 0.0
        patterns_found = []
        
        # Check urgency phrases
        for pattern in self.compiled_sentiment.get("urgency_phrases", []):
            if pattern.search(text):
                score += 0.15
                patterns_found.append("urgency_phrase")
        
        # Check fear phrases
        for pattern in self.compiled_sentiment.get("fear_phrases", []):
            if pattern.search(text):
                score += 0.20
                patterns_found.append("fear_tactic")
        
        # Check trust building (scammer trying to establish credibility)
        for pattern in self.compiled_sentiment.get("trust_building", []):
            if pattern.search(text):
                score += 0.10
                patterns_found.append("trust_building")

        # Check isolation phrases
        for pattern in self.compiled_sentiment.get("isolation_phrases", []):
            if pattern.search(text):
                score += 0.20
                patterns_found.append("isolation_attempt")

        # Check authority phrases
        for pattern in self.compiled_sentiment.get("authority_phrases", []):
            if pattern.search(text):
                score += 0.15
                patterns_found.append("authority_claim")

        # Check greed phrases
        for pattern in self.compiled_sentiment.get("greed_phrases", []):
            if pattern.search(text):
                score += 0.15
                patterns_found.append("greed_trap")
        
        return min(score, 0.6), list(set(patterns_found))
    
    def _analyze_context(self, current_message: str, context: List[str]) -> Tuple[float, List[str]]:
        """
        Analyze conversation context for multi-stage scam patterns
        Returns (context_score, detected_patterns)
        """
        if not context:
            return 0.0, []
        
        score = 0.0
        patterns_found = []
        
        # Combine all messages for full context analysis
        full_conversation = " ".join(context + [current_message]).lower()
        
        # Check for multi-stage scam progression
        for scam_type, stages in SCAM_PROGRESSION_PATTERNS.items():
            stages_matched = 0
            for stage_name, pattern in stages:
                if re.search(pattern, full_conversation, re.IGNORECASE):
                    stages_matched += 1
            
            # If multiple stages detected, it's likely a scam progression
            if stages_matched >= 3:
                progression_score = stages_matched / len(stages)
                score = max(score, progression_score * 0.3)
                patterns_found.append(f"multi_stage_{scam_type}")
        
        # Check if urgency is escalating
        urgency_scores = []
        for msg in context[-3:] + [current_message]:
            msg_urgency = sum(1 for kw in self.urgency_keywords if kw.lower() in msg.lower())
            urgency_scores.append(msg_urgency)
        
        if len(urgency_scores) >= 2:
            # Check if urgency is increasing
            if urgency_scores[-1] > urgency_scores[0]:
                score += 0.10
                patterns_found.append("escalating_urgency")
        
        # Check for Pivot Detection (Changing scam types in one session)
        potential_pivots = 0
        if any(k in full_conversation for k in ['parcel', 'fedex', 'dhl']) and \
           any(k in full_conversation for k in ['digital arrest', 'skype', 'police']):
            score += 0.2
            patterns_found.append("type_pivot_detected")

        # Check for isolation behavior
        if re.search(r"(?:don't|do\s+not)\s+(?:tell|inform|share|disconnect)", current_message.lower()):
            score += 0.15
            patterns_found.append("isolation_attempt")

        return min(score, 0.5), patterns_found
    
    def _determine_scam_type(self, text: str, keywords: List[str]) -> Tuple[str, Dict[str, float]]:
        """
        Determine the type of scam with confidence scores for alternatives
        Returns (primary_type, {alternative_type: confidence})
        """
        text_lower = text.lower()
        
        type_scores = {
            "UPI_Banking_Fraud": 0.0,
            "Prize_Lottery_Scam": 0.0,
            "Government_Phishing": 0.0,
            "Loan_Fraud": 0.0,
            "Phishing": 0.0,
            "Subscription_Fraud": 0.0,
            "Malware_Scam": 0.0,
            "Social_Media_Phishing": 0.0,
            "Link_Phishing": 0.0,
            "Digital_Arrest_Scam": 0.0,
            "Utility_Bill_Scam": 0.0,
            "General_Scam": 0.1,  # Base score
        }
        
        # Score each type based on keyword matches
        if any(k in text_lower for k in ['bank', 'upi', 'account block', 'खाता', 'neft', 'rtgs']):
            type_scores["UPI_Banking_Fraud"] += 0.8
        
        if any(k in text_lower for k in ['won', 'prize', 'lottery', 'gift', 'जीत', 'इनाम', 'lucky']):
            type_scores["Prize_Lottery_Scam"] += 0.8
        
        if any(k in text_lower for k in ['aadhaar', 'pan', 'kyc', 'आधार', 'income tax', 'refund']):
            type_scores["Government_Phishing"] += 0.8
        
        if any(k in text_lower for k in ['loan', 'interest', 'emi', 'ऋण', 'pre-approved', 'instant loan']):
            type_scores["Loan_Fraud"] += 0.8
        
        if any(k in text_lower for k in ['otp', 'password', 'verify', 'सत्यापित', 'login', 'credentials']):
            type_scores["Phishing"] += 0.6
        
        if any(k in text_lower for k in ['amazon', 'flipkart', 'subscription', 'prime', 'netflix']):
            type_scores["Subscription_Fraud"] += 0.8
        
        if any(k in text_lower for k in ['malware', 'virus', 'infected', 'download', 'trojan']):
            type_scores["Malware_Scam"] += 0.8
        
        if any(k in text_lower for k in ['instagram', 'facebook', 'whatsapp', 'telegram']):
            type_scores["Social_Media_Phishing"] += 0.7
        
        if any(k in text_lower for k in self.job_keywords):
            type_scores["Job_Task_Scam"] = 0.95
            
        if any(k in text_lower for k in self.crypto_keywords):
            type_scores["Crypto_Investment_Scam"] = 0.9
            
        if any(k in text_lower for k in ['leak', 'nude', 'shame', 'blackmail', 'compromised']) and \
           any(k in text_lower for k in ['video', 'recorded', 'recording']):
            type_scores["Sextortion_Blackmail"] = 0.98
            
        if any(k in text_lower for k in ['shaadi', 'matrimony', 'partner', 'marriage', 'gift stuck']):
            type_scores["Matrimonial_Fraud"] = 0.8

        if any(k in text_lower for k in ['digital arrest', 'ncb', 'cbi', 'arrest warrant', 'skype call']):
            type_scores["Digital_Arrest_Scam"] = 0.95
            
        if any(k in text_lower for k in self.utility_keywords):
            type_scores["Utility_Bill_Scam"] = 0.9

        if any(k in text_lower for k in ['olx', 'quikr', 'marketplace', 'carwale', 'bikewale', 'sofa set', 'iphone 99']):
            type_scores["Marketplace_Fraud"] = 0.8

        # V4.0: New Advanced Scam Categories
        if any(k in text_lower for k in self.pig_butchering_keywords):
            type_scores["Pig_Butchering_Scam"] = 0.9
        if any(k in text_lower for k in self.honeytrap_keywords):
            type_scores["Honeytrap_Video_Sextortion"] = 0.95
        if any(k in text_lower for k in self.voice_cloning_keywords):
            type_scores["Voice_Cloning_Deepfake"] = 0.95
        if any(k in text_lower for k in self.ceo_fraud_keywords):
            type_scores["CEO_BEC_Fraud"] = 0.9
        if any(k in text_lower for k in self.viral_link_keywords):
            type_scores["Viral_Link_Malware"] = 0.85
        if any(k in text_lower for k in self.trai_keywords):
            type_scores["TRAI_DND_Scam"] = 0.85
            
        # V5.0: Extended Indian Scam Categories
        if any(k in text_lower for k in self.stock_trading_keywords):
            type_scores["Stock_Market_Fraud"] = 0.95
        if any(k in text_lower for k in self.welfare_scheme_keywords):
            type_scores["Welfare_Scheme_Fraud"] = 0.9
        if any(k in text_lower for k in self.rent_scam_keywords):
            type_scores["Rent_Property_Fraud"] = 0.95
        if any(k in text_lower for k in self.recharge_scam_keywords):
            type_scores["Free_Recharge_Fraud"] = 0.85
        if any(k in text_lower for k in self.election_scam_keywords):
            type_scores["Election_Voter_Fraud"] = 0.85

        # V5.1: New Indian Scam Types
        if any(k in text_lower for k in self.credit_rewards_keywords):
            type_scores["Credit_Card_Rewards_Scam"] = 0.95
        if any(k in text_lower for k in self.fastag_scam_keywords):
            type_scores["FASTag_KYC_Fraud"] = 0.95
        if any(k in text_lower for k in self.it_refund_keywords):
            type_scores["Income_Tax_Refund_Scam"] = 0.98
        if any(k in text_lower for k in self.religious_scam_keywords):
            type_scores["Religious_Donation_Scam"] = 0.90

        if 'suspicious_link' in keywords:
            type_scores["Link_Phishing"] += 0.5
        
        # 🚨 PRIORITY OVERRIDE: If we hit a specific critical keyword, force that type
        if 'CRITICAL_DIGITAL_ARREST' in keywords: type_scores["Digital_Arrest_Scam"] = 1.0
        if 'CRITICAL_SEXTORTION_COMBO' in keywords: type_scores["Sextortion_Blackmail"] = 1.0
        if 'CRITICAL_EXTORTION_COMBO' in keywords: type_scores["Sextortion_Blackmail"] = 0.95
        if 'CRITICAL_COURIER_HANDOVER' in keywords: type_scores["Digital_Arrest_Scam"] = 0.95
        if 'CRITICAL_LIC_SCAM' in keywords: type_scores["Prize_Lottery_Scam"] = 0.95
        if 'CRITICAL_SCHEME_SCAM' in keywords: type_scores["Government_Phishing"] = 0.95
        if 'CRITICAL_TASK_JOB_SCAM' in keywords: type_scores["Job_Task_Scam"] = 0.95
        if 'CRITICAL_CHALLAN_SCAM' in keywords: type_scores["Utility_Bill_Scam"] = 0.95
        if 'CRITICAL_SIM_SWAP_SCAM' in keywords: type_scores["General_Scam"] = 0.95
        if 'CRITICAL_QR_SCAM' in keywords: type_scores["Marketplace_Fraud"] = 1.0
        if 'CRITICAL_LOAN_SCAM' in keywords: type_scores["Loan_Fraud"] = 0.95
        # V4.0 Priority Overrides
        if 'CRITICAL_PIG_BUTCHER' in keywords: type_scores["Pig_Butchering_Scam"] = 1.0
        if 'CRITICAL_HONEYTRAP' in keywords: type_scores["Honeytrap_Video_Sextortion"] = 1.0
        if 'CRITICAL_VOICE_CLONE' in keywords: type_scores["Voice_Cloning_Deepfake"] = 1.0
        if 'CRITICAL_CEO_FRAUD' in keywords: type_scores["CEO_BEC_Fraud"] = 1.0
        if 'CRITICAL_VIRAL_LINK' in keywords: type_scores["Viral_Link_Malware"] = 1.0
        if 'CRITICAL_TRAI_SCAM' in keywords: type_scores["TRAI_DND_Scam"] = 1.0
        
        # V5.0 Priority Overrides
        if 'CRITICAL_STOCK_TRADING' in keywords: type_scores["Stock_Market_Fraud"] = 1.0
        if 'CRITICAL_WELFARE_FRAUD' in keywords: type_scores["Welfare_Scheme_Fraud"] = 1.0
        if 'CRITICAL_RENT_SCAM' in keywords: type_scores["Rent_Property_Fraud"] = 1.0
        if 'CRITICAL_RECHARGE_SCAM' in keywords: type_scores["Free_Recharge_Fraud"] = 1.0
        if 'CRITICAL_ELECTION_SCAM' in keywords: type_scores["Election_Voter_Fraud"] = 1.0
        
        # V5.1 Priority Overrides
        if 'CRITICAL_CREDIT_REWARDS' in keywords: type_scores["Credit_Card_Rewards_Scam"] = 1.0
        if 'CRITICAL_FASTAG_SCAM' in keywords: type_scores["FASTag_KYC_Fraud"] = 1.0
        if 'CRITICAL_IT_REFUND' in keywords: type_scores["Income_Tax_Refund_Scam"] = 1.0
        if 'CRITICAL_RELIGIOUS_SCAM' in keywords: type_scores["Religious_Donation_Scam"] = 1.0

        # Get primary type and alternatives
        sorted_types = sorted(type_scores.items(), key=lambda x: x[1], reverse=True)
        primary_type = sorted_types[0][0]
        
        # Get alternatives with scores > 0.3
        alternatives = {k: v for k, v in sorted_types[1:4] if v > 0.3}
        
        return primary_type, alternatives
    
    def _assess_threat_level(
        self,
        confidence: float,
        keywords: List[str],
        sentiment_patterns: List[str],
        context_patterns: List[str]
    ) -> ThreatLevel:
        """Assess the sophistication/threat level of the scam"""
        
        sophistication_score = 0.0
        
        # Higher confidence suggests clearer scam signals
        if confidence > 0.8:
            sophistication_score += 0.2
        
        # Multi-stage patterns indicate sophisticated operation
        if any('multi_stage' in p for p in context_patterns):
            sophistication_score += 0.4
        
        # Fear tactics are more sophisticated than simple urgency
        if 'fear_tactic' in sentiment_patterns:
            sophistication_score += 0.2
        
        # Trust building attempts indicate social engineering
        if 'trust_building' in sentiment_patterns:
            sophistication_score += 0.3
        
        # Escalation patterns indicate adaptive scammer
        if 'escalating_urgency' in context_patterns:
            sophistication_score += 0.2
        
        # Multiple keyword categories suggest prepared script
        unique_categories = len(set(keywords))
        if unique_categories >= 5:
            sophistication_score += 0.2
        
        # Determine threat level
        if sophistication_score >= 0.6:
            return ThreatLevel.HIGH
        elif sophistication_score >= 0.3:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW
    
    def detect(
        self,
        text: str,
        context: Optional[List[str]] = None
    ) -> Tuple[bool, float, str, List[str], ScamClassification, ThreatLevel]:
        """
        Enhanced scam detection with contextual analysis
        
        Args:
            text: The message text to analyze
            context: Optional list of previous messages for context
            
        Returns:
            Tuple of (is_scam, confidence, scam_type, detected_keywords, classification, threat_level)
        """
        context = context or []
        
        # Get rule-based score
        rule_score, detected_keywords = self._rule_based_score(text)
        
        # Get sentiment analysis score
        sentiment_score, sentiment_patterns = self._analyze_sentiment(text)
        detected_keywords.extend(sentiment_patterns)
        
        # Get context analysis score
        context_score, context_patterns = self._analyze_context(text, context)
        detected_keywords.extend(context_patterns)
        
        # Get ML model score if available
        ml_score = 0.0
        if self.is_trained and self.model and self.vectorizer:
            try:
                # ✅ FIX: Concatenate last 2 messages from context for prediction
                # This makes the ML model context-aware
                full_context_text = text
                if context:
                    # Add last 2 messages to provide context to the model
                    recent_history = " ".join(context[-2:])
                    full_context_text = recent_history + " " + text
                
                text_vec = self.vectorizer.transform([full_context_text])
                ml_proba = self.model.predict_proba(text_vec)[0]
                ml_score = float(ml_proba[1]) if len(ml_proba) > 1 else float(ml_proba[0])
            except Exception as e:
                logger.warning(f"ML prediction error: {e}")
                ml_score = 0.0
        
        # 🚨 KILL SWITCH: Immediate Override for High-Risk Patterns
        # Don't rely on averages for guaranteed signs of fraud
        kill_switch_score = 0.0
        kill_switch_triggered = False
        
        # 1. Phishing Link + Any Urgency/Threat = 100% Scam
        if 'suspicious_link' in detected_keywords and (
            sentiment_score > 0.1 or 
            any(kw in detected_keywords for kw in ['urgency_phrase', 'fear_tactic'] + self.urgency_keywords)
        ):
            kill_switch_score = 1.0
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_PHISHING_COMBO")
            logger.info(f"Kill switch: Phishing link with urgency/threat detected")
        
        # 2. Digital Arrest Combo (Authority + Skype/Video + Crime) = 1.0 Scam
        if any(kw in text.lower() for kw in ['skype', 'video call', 'digital arrest']) and \
           any(kw in text.lower() for kw in ['cbi', 'police', 'customs', 'ncb', 'sharma']):
            kill_switch_score = 1.0
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_DIGITAL_ARREST")
            logger.info(f"Kill switch: Digital arrest pattern detected")

        # 3. Sextortion Combo (Video recorded + Social Media/Contacts + Threat) = 1.0 Scam
        # Note: Exclude if it looks like a Honeytrap (video CALL, whatsapp call, intimate) - that's a different, more specific category
        if any(kw in text.lower() for kw in ['recorded', 'video', 'recording']) and \
           any(kw in text.lower() for kw in ['contacts', 'friends', 'facebook', 'leaked']) and \
           any(kw in text.lower() for kw in ['pay', 'money', 'delete', 'rupees']) and \
           not any(kw in text.lower() for kw in ['video call', 'whatsapp call', 'intimate', 'nude']):
            kill_switch_score = 1.0
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_SEXTORTION_COMBO")
            logger.info(f"Kill switch: Sextortion pattern detected")

        # 4. Financial Request + Threat = 0.95 Scam (Extortion pattern)
        if (('upi_id_request' in detected_keywords or 
             any(kw in detected_keywords for kw in self.financial_keywords)) and \
            any(kw in detected_keywords for kw in self.threat_keywords)) and \
           not any(kw in text.lower() for kw in ['airtel', 'jio', 'vi', 'bsnl', 'challan', 'rto', 'customer care', 'agent id']):
            kill_switch_score = max(kill_switch_score, 0.95)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_EXTORTION_COMBO")
            logger.info(f"Kill switch: Financial request with threat detected")
        
        # 5. FedEx/Courier Illegal Item Handover = 0.95 Scam
        if any(kw in text.lower() for kw in ['fedex', 'dhl', 'parcel', 'courier']) and \
           any(kw in text.lower() for kw in ['drugs', 'illegal', 'contraband', 'passport']) and \
           any(kw in text.lower() for kw in ['cbi', 'customs', 'police']):
            kill_switch_score = max(kill_switch_score, 0.95)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_COURIER_HANDOVER")
            logger.info(f"Kill switch: Courier illegal item handover pattern detected")

        # 6. Known Multi-Stage Scam Pattern 
        if any('multi_stage' in p for p in detected_keywords):
            kill_switch_score = max(kill_switch_score, 0.85)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_MULTI_STAGE")
            logger.info(f"Kill switch: Multi-stage scam pattern detected")
        
        # 4. Suspicious link alone (even without urgency) is very high risk
        if 'suspicious_link' in detected_keywords and not kill_switch_triggered:
            kill_switch_score = max(kill_switch_score, 0.75)
            kill_switch_triggered = True
            logger.info(f"Kill switch: Suspicious link detected")
        
        # 7. LIC/Insurance Prize Scam (Congratulations + Policy/Bonus/LIC) = 0.95 Scam
        if any(kw in text.lower() for kw in ['congratulations', 'badhai', 'mubarak']) and \
           any(kw in text.lower() for kw in ['lic', 'policy', 'insurance', 'bonus', 'approve', 'maturity']):
            kill_switch_score = max(kill_switch_score, 0.95)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_LIC_SCAM")
            logger.info(f"Kill switch: LIC/Insurance prize scam detected")
        
        # 8. COVID/Scheme Urgency Scam (Scheme + Expire/Urgent) = 0.90 Scam
        if any(kw in text.lower() for kw in ['scheme', 'relief', 'subsidy', 'government']) and \
           any(kw in text.lower() for kw in ['expire', 'hours', 'today', 'immediate', 'last chance']):
            kill_switch_score = max(kill_switch_score, 0.90)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_SCHEME_SCAM")
            logger.info(f"Kill switch: Government scheme urgency scam detected")
        
        # 9. YouTube/Task Job Scam (Tasks/Reviews + Daily Income + WhatsApp/Telegram) = 0.95 Scam
        if any(kw in text.lower() for kw in ['like youtube', 'google maps review', 'task', 'subscribe']) and \
           any(kw in text.lower() for kw in ['daily income', 'earn', 'salary', 'bonus', 'rs', 'inr']):
            kill_switch_score = max(kill_switch_score, 0.95)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_TASK_JOB_SCAM")
            logger.info(f"Kill switch: YouTube/Task job scam detected")

        # 10. RTO/Challan/Traffic Fine Scam (Vehicle # + Fine + Disconnect/Block) = 0.95 Scam
        if any(kw in text.lower() for kw in ['challan', 'rto', 'traffic fine', 'vehicle number', 'dl block']) and \
           any(kw in text.lower() for kw in ['pending', 'unpaid', 'immediately', 'pay now']):
            kill_switch_score = max(kill_switch_score, 0.95)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_CHALLAN_SCAM")
            logger.info(f"Kill switch: RTO/Challan scam detected")

        # 11. SIM Swap / eSIM Upgrade Scam (Airtel/Jio + 5G Upgrade + OTP/QR) = 0.95 Scam
        if any(kw in text.lower() for kw in ['airtel', 'jio', 'vi', 'bsnl', 'voda', 'sim', 'esim', '5g']) and \
           any(kw in text.lower() for kw in ['blocked', 'verification', 'update', 'share', 'scan', 'deactivate', 'activate', 'upgrade']):
            kill_switch_score = max(kill_switch_score, 0.95)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_SIM_SWAP_SCAM")
            logger.info(f"Kill switch: SIM/eSIM upgrade scam detected")

        # 12. Marketplace/QR Code Scam (OLX + Scan to Receive + Amount) = 0.95 Scam
        if any(kw in text.lower() for kw in ['olx', 'quikr', 'marketplace', 'sofa', 'furnitur', 'interested']) and \
           any(kw in text.lower() for kw in ['qr', 'scan', 'receive', 'amount', 'barcode']):
            kill_switch_score = max(kill_switch_score, 0.98)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_QR_SCAM")
            logger.info(f"Kill switch: Marketplace QR code scam detected")

        # 13. Instant Loan / Harassment Scam (Instant Loan + No Docs + Gallery Access) = 0.90 Scam
        if any(kw in text.lower() for kw in ['instant loan', 'no documents', 'fast credit', 'loan approve']) and \
           any(kw in text.lower() for kw in ['emergency', 'pan card', 'aadhaar card', 'contacts access']):
            kill_switch_score = max(kill_switch_score, 0.90)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_LOAN_SCAM")
            logger.info(f"Kill switch: Predatory loan app scam detected")

        # --- V4.0: ADVANCED KILL SWITCHES (2024-2025 Research) ---

        # 14. Pig Butchering (Investment + Romance + Crypto) = 1.0 Scam
        if any(kw in text.lower() for kw in ['i love you', 'trust me', 'lonely', 'widower', 'overseas']) and \
           any(kw in text.lower() for kw in ['investment', 'crypto', 'trading', 'withdraw', 'platform', 'returns']):
            kill_switch_score = max(kill_switch_score, 1.0)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_PIG_BUTCHER")
            logger.info(f"Kill switch: Pig Butchering (romance + investment) scam detected")

        # 15. Honeytrap Video Call (Video Call + Recording Threat + Payment) = 1.0 Scam
        if any(kw in text.lower() for kw in ['video call', 'whatsapp call', 'nude', 'intimate', 'recorded you']) and \
           any(kw in text.lower() for kw in ['your contacts', 'will viral', 'pay or else', 'facebook leak', 'share with friends']):
            kill_switch_score = max(kill_switch_score, 1.0)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_HONEYTRAP")
            logger.info(f"Kill switch: Honeytrap video call sextortion detected")

        # 16. AI Voice Cloning / Deepfake Emergency (Family In Trouble + Money) = 1.0 Scam
        if any(kw in text.lower() for kw in ['mom help', 'dad i need', 'son in trouble', 'accident', 'hospital urgent', 'kidnapped', 'bail money']) and \
           any(kw in text.lower() for kw in ['send immediately', 'don\'t tell anyone', 'urgent transfer', 'police custody']):
            kill_switch_score = max(kill_switch_score, 1.0)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_VOICE_CLONE")
            logger.info(f"Kill switch: AI Voice Cloning / Deepfake emergency scam detected")

        # 17. CEO/Boss Fraud (Impersonation + Urgent Transfer) = 0.98 Scam
        if any(kw in text.lower() for kw in ['this is your ceo', 'boss here', 'i am in a meeting', 'confidential transaction']) and \
           any(kw in text.lower() for kw in ['urgent wire', 'vendor payment', 'do not discuss', 'handle personally', 'reply to personal email']):
            kill_switch_score = max(kill_switch_score, 0.98)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_CEO_FRAUD")
            logger.info(f"Kill switch: CEO/Business Email Compromise fraud detected")

        # 18. Viral Video Link Malware (Trending/Shocking + Link) = 0.9 Scam
        if any(kw in text.lower() for kw in ['7 minute viral', 'shocking video', 'your video is trending', 'you are in this video', 'click to see who']):
            kill_switch_score = max(kill_switch_score, 0.90)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_VIRAL_LINK")
            logger.info(f"Kill switch: Viral video link malware scam detected")

        # 19. TRAI/DND Deactivation (TRAI + Disconnect + Press 1) = 0.90 Scam
        if any(kw in text.lower() for kw in ['trai', 'telecom', 'dnd', 'regulatory compliance', 'telecom department']) and \
           any(kw in text.lower() for kw in ['disconnected', 'deactivated', 'press 1', 'press 2', 'within 24 hours']):
            kill_switch_score = max(kill_switch_score, 0.90)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_TRAI_SCAM")
            logger.info(f"Kill switch: TRAI/DND deactivation scam detected")

        # --- V5.0: EXTENDED INDIAN KILL SWITCHES ---

        # 20. Stock Market / Fake Trading Group (IPO + Expert + Withdrawal Fee) = 0.98 Scam
        if any(kw in text.lower() for kw in ['ipo', 'stock market', 'trading expert', 'trading signal', 'sebi', 'investment group']) and \
           any(kw in text.lower() for kw in ['guaranteed', 'withdrawal tax', 'processing fee', 'high profit', 'whatsapp group']):
            kill_switch_score = max(kill_switch_score, 0.98)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_STOCK_TRADING")
            logger.info(f"Kill switch: Fake stock market trading group detected")

        # 21. Welfare Scheme Fraud (PM-Kisan / Ayushman / Govt Subsidy) = 0.95 Scam
        if any(kw in text.lower() for kw in ['pm kisan', 'ayushman bharat', 'govt scheme', 'sarkari yojana', 'samman nidhi', 'subsidy']) and \
           any(kw in text.lower() for kw in ['kitsch', 'bonus', 'claim', 'registration fee', 'click to register']):
            kill_switch_score = max(kill_switch_score, 0.95)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_WELFARE_FRAUD")
            logger.info(f"Kill switch: Government welfare scheme fraud detected")

        # 22. Rent / Property Token Scam (Security Deposit Before Visit + OLX/MagicBricks) = 0.95 Scam
        if any(kw in text.lower() for kw in ['rent', 'property', 'flat', 'house', 'olx', 'magicbricks']) and \
           any(kw in text.lower() for kw in ['token amount', 'security deposit', 'gate pass', 'before visit', 'block property']):
            kill_switch_score = max(kill_switch_score, 0.95)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_RENT_SCAM")
            logger.info(f"Kill switch: Online rental property fraud detected")

        # 23. Free Recharge / Data Balance Scam (Free + Recharge + Brand) = 0.90 Scam
        if any(kw in text.lower() for kw in ['free recharge', 'free data', 'balance', 'recharge link']) and \
           any(kw in text.lower() for kw in ['jio', 'airtel', 'vi', 'offer', 'congratulations', 'won']):
            kill_switch_score = max(kill_switch_score, 0.90)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_RECHARGE_SCAM")
            logger.info(f"Kill switch: Free recharge/data баланс scam detected")

        # 24. Election / Voter ID Fraud (Voter ID + Update + Mandatory) = 0.85 Scam
        if any(kw in text.lower() for kw in ['voter id', 'election card', 'voter list']) and \
           any(kw in text.lower() for kw in ['update', 'mandatory', 'verify', 'click to update']):
            kill_switch_score = max(kill_switch_score, 0.85)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_ELECTION_SCAM")
            logger.info(f"Kill switch: Election/Voter ID fraud detected")

        # --- V5.1: NEW INDIAN SCAM CATEGORIES ---

        # 25. Credit Card Reward Points (Points + Expire/Redeem) = 0.95 Scam
        if any(kw in text.lower() for kw in ['reward points', 'credit card points', 'redeem points']) and \
           any(kw in text.lower() for kw in ['expire today', 'expiring', 'redeem now', 'cash value', 'click link']):
            kill_switch_score = max(kill_switch_score, 0.95)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_CREDIT_REWARDS")
            logger.info(f"Kill switch: Credit card reward points scam detected")

        # 26. FASTag KYC Update (FASTag + Deactivate/Update) = 0.95 Scam
        if any(kw in text.lower() for kw in ['fastag', 'toll tag', 'nhai', 'vehicle tag']) and \
           any(kw in text.lower() for kw in ['kyc pending', 'deactivated', 'blocked', 'update immediately', 'wallet expired']):
            kill_switch_score = max(kill_switch_score, 0.95)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_FASTAG_SCAM")
            logger.info(f"Kill switch: FASTag KYC update scam detected")

        # 27. Income Tax Refund (Refund + Approve/Verify) = 0.98 Scam
        if any(kw in text.lower() for kw in ['income tax', 'tax refund', 'it dept', 'refund issued', 'it department']) and \
           any(kw in text.lower() for kw in ['click to claim', 'verify account', 'refund pending', 'approved', 'update bank', 'claim', 'incorrect']):
            kill_switch_score = max(kill_switch_score, 0.98)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_IT_REFUND")
            logger.info(f"Kill switch: Income Tax refund phishing detected")

        # 28. Ram Mandir / Religious VIP Scam (Temple + VIP/Donation) = 0.90 Scam
        if any(kw in text.lower() for kw in ['ram mandir', 'ayodhya', 'temple trust', 'darshan', 'jai shri ram']) and \
           any(kw in text.lower() for kw in ['vip pass', 'vip entry', 'vip darshan', 'prasad', 'prasad delivery', 'donation qr', 'book now', 'skip the queue']):
            kill_switch_score = max(kill_switch_score, 0.90)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_RELIGIOUS_SCAM")
            logger.info(f"Kill switch: Religious/VIP Darshan scam detected")

        # --- V5.2: ADVANCED INDIAN IDENTITY SCAMS ---

        # 29. Hi Mom / Family Emergency WhatsApp (New Number + Urgent Money) = 0.98 Scam
        if any(kw in text.lower() for kw in ['hi mom', 'hi mum', 'hi dad', 'this is your son', 'this is your daughter', 'new number']) and \
           any(kw in text.lower() for kw in ['lost my phone', 'broken phone', 'can\'t access bank', 'urgent help', 'need money', 'emergency', 'don\'t tell']):
            kill_switch_score = max(kill_switch_score, 0.98)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_HI_MOM_SCAM")
            logger.info(f"Kill switch: Hi Mom/Family Emergency WhatsApp scam detected")

        # 30. Aadhaar / UIDAI Update Scam (Aadhaar + Update/Expired) = 0.95 Scam
        if any(kw in text.lower() for kw in ['aadhaar', 'uidai', 'biometric', 'aeps', 'e-aadhaar']) and \
           any(kw in text.lower() for kw in ['update', 'expired', 'verification', 'link expired', 'click to update', 'mandatory update']):
            kill_switch_score = max(kill_switch_score, 0.95)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_AADHAAR_SCAM")
            logger.info(f"Kill switch: Aadhaar/UIDAI update scam detected")

        # 31. SBI YONO / Bank App Blocked (YONO + Blocked/Suspended) = 0.95 Scam
        if any(kw in text.lower() for kw in ['yono', 'sbi yono', 'netbanking', 'mobile banking']) and \
           any(kw in text.lower() for kw in ['blocked', 'suspended', 'will be blocked', 'update pan', 'download apk', 'click to activate']):
            kill_switch_score = max(kill_switch_score, 0.95)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_YONO_SCAM")
            logger.info(f"Kill switch: SBI YONO/Bank App blocked scam detected")

        # 32. EPF / PF Withdrawal Scam (PF + Claim/Frozen) = 0.90 Scam
        if any(kw in text.lower() for kw in ['epf', 'pf withdrawal', 'provident fund', 'uan', 'epfo']) and \
           any(kw in text.lower() for kw in ['claim', 'frozen', 'settlement', 'processing fee', 'faster withdrawal', 'click to claim']):
            kill_switch_score = max(kill_switch_score, 0.90)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_EPF_SCAM")
            logger.info(f"Kill switch: EPF/PF withdrawal scam detected")
        
        # Apply Kill Switch or calculate weighted score
        if kill_switch_triggered and kill_switch_score > 0:
            combined_score = kill_switch_score
        else:
            # Fallback to weighted average
            if self.is_trained:
                combined_score = float(
                    (ml_score * SCORING_WEIGHTS["ml_model"]) +
                    (rule_score * SCORING_WEIGHTS["rule_based"]) +
                    (context_score * SCORING_WEIGHTS["context_bonus"]) +
                    (sentiment_score * SCORING_WEIGHTS["sentiment_weight"])
                )
            else:
                # Without ML model, rely more on rules and sentiment
                combined_score = float(
                    (rule_score * 0.6) +
                    (context_score * 0.25) +
                    (sentiment_score * 0.15)
                )
        
        # 🛡️ SAFETY CHECK: Reduce score for likely legitimate messages
        # This reduces false positives for common transactional messages
        legit_patterns = [
            r"otp is \d{4,6}",          # "OTP is 123456"
            r"code is \d{4,6}",          # "Code is 123456"
            r"sent you ₹\d+",            # "Sent you ₹500" (payment receipts)
            r"sent you rs\.?\s*\d+",     # "Sent you Rs 500"
            r"received ₹\d+",            # Transaction confirmations
            r"received rs\.?\s*\d+",
            r"credited to your",         # Bank credit messages
            r"debited from your",        # Bank debit messages
            r"your order #\w+",          # Order confirmations
            r"meeting.*rescheduled",     # Business meetings
            r"office.*meeting",          # Office context
            r"happy birthday",           # Greetings
            r"dinner",                   # Personal plans
            r"lunch",                    # Personal plans
            r"love you",                 # Personal affection
            r"miss you",                 # Personal affection
        ]
        
        is_likely_legit = any(re.search(p, text, re.IGNORECASE) for p in legit_patterns)
        
        # Only apply safety reduction if NOT a kill switch case and no suspicious link
        if is_likely_legit and 'suspicious_link' not in detected_keywords and not kill_switch_triggered:
            old_score = combined_score
            combined_score *= 0.5  # Halve the scam score for legitimate-looking patterns
            logger.debug(f"Safety check: Reduced score from {old_score:.2f} to {combined_score:.2f} for legit pattern")
        
        # Determine scam type and alternatives
        scam_type, alt_types = self._determine_scam_type(text, detected_keywords)
        
        # Get adaptive threshold for this scam type
        threshold = SCAM_TYPE_THRESHOLDS.get(scam_type, SCAM_CONFIDENCE_THRESHOLD)
        
        # Assess threat level (higher for kill switch cases)
        threat_level = self._assess_threat_level(
            combined_score, detected_keywords, sentiment_patterns, context_patterns
        )
        
        # Upgrade threat level for kill switch cases
        if kill_switch_triggered and threat_level != ThreatLevel.HIGH:
            if any("CRITICAL" in kw for kw in detected_keywords):
                threat_level = ThreatLevel.HIGH
        
        # Make decision with adaptive threshold
        is_scam = bool(combined_score >= threshold)
        
        # Create classification object
        classification = ScamClassification(
            scamType=scam_type,
            confidence=combined_score,
            alternativeTypes=[{k: v} for k, v in alt_types.items()],
            tacticsIdentified=list(set(sentiment_patterns + context_patterns))
        )
        
        log_with_context(
            logger, logging.DEBUG,
            "Scam detection complete",
            is_scam=is_scam,
            confidence=round(combined_score, 4),
            scam_type=scam_type,
            threat_level=threat_level.value,
            keywords_count=len(detected_keywords),
            kill_switch=kill_switch_triggered
        )
        
        return is_scam, combined_score, scam_type, list(set(detected_keywords)), classification, threat_level


# Global instance
detector = ScamDetector()
