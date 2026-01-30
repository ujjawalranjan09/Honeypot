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
            "expired", "expire", "block", "stop"
        ]
        
        # Threat keywords
        self.threat_keywords = [
            "block", "suspend", "delete", "deactivate", "terminate",
            "blocked", "suspended", "compromised", "hacked", "infected",
            "ब्लॉक", "निलंबित", "हैक", "संक्रमित", "banned", "frozen",
            "arrest", "warrant", "court", "police", "jail", "cbi", "summons",
            "raid", "investigation", "crime", "illegal", "money laundering",
            "parcel", "drugs", "customs", "narcotics", "seized", "mumbai airport",
            "aadhaar linked", "fedex", "dhl"
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
            "upi", "bank", "account", "payment", "loan", "interest",
            "emi", "credit", "debit", "aadhaar", "pan", "kyc",
            "crypto", "investment", "trading", "profit", "commission",
            "बैंक", "खाता", "भुगतान", "ऋण", "आधार", "otp", "cvv", "pin"
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
    
    def train_model(self, dataset_path: str = "massive_5k_scam_dataset.csv"):
        """Train the ML model on the scam dataset (supports CSV or JSON)"""
        try:
            logger.info("Training scam detection model...")
            
            # Load dataset (support JSON extended dataset)
            df = None
            if os.path.exists("extended_scam_dataset.json"):
                logger.info("Loading extended JSON dataset...")
                import json
                with open("extended_scam_dataset.json", 'r') as f:
                    data = json.load(f)
                df = pd.DataFrame(data)
                # Rename columns if needed to match expected format
                if 'text' in df.columns and 'message_text' not in df.columns:
                    df.rename(columns={'text': 'message_text'}, inplace=True)
            
            elif os.path.exists(dataset_path):
                df = pd.read_csv(dataset_path)
            
            if df is None:
                logger.error("No dataset found for training.")
                return None
                
            logger.info(f"Loaded {len(df)} samples")
            
            # Prepare data
            X = df['message_text'].fillna('')
            y = (df['label'] == 'scam').astype(int)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=MODEL_PARAMS["test_size"],
                random_state=MODEL_PARAMS["random_state"],
                stratify=y
            )
            
            # Vectorize text
            self.vectorizer = TfidfVectorizer(
                max_features=MODEL_PARAMS["max_features"],
                ngram_range=MODEL_PARAMS["ngram_range"],
                min_df=MODEL_PARAMS["min_df"],
                max_df=MODEL_PARAMS["max_df"]
            )
            X_train_vec = self.vectorizer.fit_transform(X_train)
            X_test_vec = self.vectorizer.transform(X_test)
            
            # Train model
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
        
        return min(score, 0.5), list(set(patterns_found))
    
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
        
        # Check for information request escalation
        info_patterns = [r'otp', r'password', r'pin', r'cvv', r'account\s*(?:number|no)?']
        info_requests = 0
        for msg in context + [current_message]:
            for pattern in info_patterns:
                if re.search(pattern, msg, re.IGNORECASE):
                    info_requests += 1
        
        if info_requests >= 2:
            score += 0.15
            patterns_found.append("repeated_info_requests")
        
        return min(score, 0.4), patterns_found
    
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
        
        if 'suspicious_link' in keywords:
            type_scores["Link_Phishing"] += 0.5
        
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
        
        # 2. Financial Request + Threat = 100% Scam (Extortion pattern)
        if ('upi_id_request' in detected_keywords or 
            any(kw in detected_keywords for kw in self.financial_keywords)) and \
           any(kw in detected_keywords for kw in self.threat_keywords):
            kill_switch_score = max(kill_switch_score, 0.95)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_EXTORTION_COMBO")
            logger.info(f"Kill switch: Financial request with threat detected")
        
        # 3. Known Multi-Stage Scam Pattern 
        if any('multi_stage' in p for p in context_patterns):
            kill_switch_score = max(kill_switch_score, 0.85)
            kill_switch_triggered = True
            detected_keywords.append("CRITICAL_MULTI_STAGE")
            logger.info(f"Kill switch: Multi-stage scam pattern detected")
        
        # 4. Suspicious link alone (even without urgency) is very high risk
        if 'suspicious_link' in detected_keywords and not kill_switch_triggered:
            kill_switch_score = max(kill_switch_score, 0.75)
            kill_switch_triggered = True
            logger.info(f"Kill switch: Suspicious link detected")
        
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
