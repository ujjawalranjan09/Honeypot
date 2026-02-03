"""
Enhanced Session Manager Module
Handles conversation session state with intelligent completion and robust callbacks
"""
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, Optional, List

from config import (
    GUVI_CALLBACK_URL,
    MIN_ENGAGEMENT_MESSAGES,
    MAX_ENGAGEMENT_MESSAGES,
    SESSION_TIMEOUT_MINUTES,
    CALLBACK_CONFIG,
    INTELLIGENCE_QUALITY_THRESHOLDS,
)
from models import (
    SessionState,
    Message,
    ExtractedIntelligence,
    GUVICallbackPayload,
    EngagementPhase,
    ThreatLevel,
    ConversationAnalytics,
    ResponseQuality,
)
from intelligence_extractor import extractor
from ai_agent import reasoning_agent as agent
from exceptions import (
    SessionNotFoundError,
    SessionExpiredError,
    CallbackTimeoutError,
    CallbackRetryExhaustedError,
)
from logging_config import get_logger, log_with_context, api_logger
import logging

logger = get_logger("honeypot.session_manager")


class SessionManager:
    """
    Enhanced session management with:
    - Intelligent completion based on quality metrics
    - Conversation analytics tracking
    - Detection risk monitoring
    - Graceful exit strategies
    - Retry logic for callbacks with exponential backoff
    - Cross-session pattern learning
    """
    
    def __init__(self):
        self.sessions: Dict[str, SessionState] = {}
        self._lock = asyncio.Lock()
        
        # Cross-session analytics
        self.scammer_profiles: Dict[str, dict] = {}  # identifier -> profile
        self.completed_sessions: List[dict] = []  # Analytics from completed sessions
    
    async def get_or_create_session(
        self,
        session_id: str,
        scam_type: Optional[str] = None,
        forced_persona: Optional[str] = None,
        first_message: Optional[str] = None
    ) -> SessionState:
        """Get existing session or create new one"""
        async with self._lock:
            if session_id not in self.sessions:
                persona = forced_persona or agent.select_persona(scam_type or "General_Scam", first_message=first_message)
                self.sessions[session_id] = SessionState(
                    session_id=session_id,
                    scam_type=scam_type,
                    persona=persona
                )
                log_with_context(
                    logger, logging.INFO,
                    "New session created",
                    session_id=session_id,
                    persona=persona,
                    scam_type=scam_type
                )
            return self.sessions[session_id]
    
    def _update_analytics(
        self,
        session: SessionState,
        message: Message
    ) -> None:
        """Update conversation analytics"""
        analytics = session.analytics
        
        # Track message timing
        if session.conversation_history:
            last_msg = session.conversation_history[-1]
            try:
                # Robust timestamp parsing (Handles ISO string or Epoch int/float)
                def parse_ts(ts):
                    if isinstance(ts, (int, float)):
                        return datetime.fromtimestamp(ts)
                    return datetime.fromisoformat(str(ts).replace('Z', '+00:00'))

                last_time = parse_ts(last_msg.timestamp)
                current_time = parse_ts(message.timestamp)
                
                time_diff = (current_time - last_time).total_seconds()
                analytics.messageTimings.append(time_diff)
            except Exception as e:
                # Log the specific error to help debugging
                logger.error(f"Timestamp parsing error: {e}. Last: {last_msg.timestamp}, Curr: {message.timestamp}")
                pass
        
        # Track message length
        analytics.messageLengths.append(len(message.text))
        
        # Track urgency progression
        urgency_keywords = ['urgent', 'immediate', 'now', 'hurry', 'fast', 'quick']
        urgency_score = sum(1 for kw in urgency_keywords if kw in message.text.lower()) / len(urgency_keywords)
        analytics.urgencyProgression.append(urgency_score)
        
        # Check if new info is still emerging
        if len(analytics.messageLengths) > 5:
            recent_lengths = analytics.messageLengths[-5:]
            if all(l < 30 for l in recent_lengths):
                analytics.newInfoEmergence = False
        
        # --- Scammer Sentiment Analysis (V34) ---
        msg_text = message.text.lower()
        frustration_keywords = ["hurry", "last chance", "hello?", "are you there", "waiting", "fast", "immediately"]
        threat_keywords = ["arrest", "seize", "police", "legal action", "jail", "court", "warrant"]
        
        if any(kw in msg_text for kw in threat_keywords):
            analytics.scammer_sentiment = "threatening"
        elif any(kw in msg_text for kw in frustration_keywords):
            analytics.scammer_sentiment = "frustrated"
        else:
            analytics.scammer_sentiment = "neutral"
        
        # Update scammer engagement level based on response patterns
        if len(analytics.messageTimings) >= 3:
            recent_timings = analytics.messageTimings[-3:]
            avg_timing = sum(recent_timings) / len(recent_timings)
            # Quick responses = high engagement
            if avg_timing < 30:
                analytics.scammerEngagementLevel = min(1.0, analytics.scammerEngagementLevel + 0.1)
            elif avg_timing > 120:
                analytics.scammerEngagementLevel = max(0.0, analytics.scammerEngagementLevel - 0.2)
    
    def _assess_detection_risk(self, session: SessionState) -> float:
        """Assess risk of being detected as a bot"""
        risk = 0.0
        
        # Long conversations increase risk
        if session.messages_exchanged > 15:
            risk += 0.15
        if session.messages_exchanged > 25:
            risk += 0.25
        
        # Repetitive responses increase risk (check persona state)
        if len(session.persona_state.previousStatements) >= 3:
            statements = session.persona_state.previousStatements
            # Check for similarity (basic check)
            for i, stmt in enumerate(statements[:-1]):
                for j, other in enumerate(statements[i+1:], i+1):
                    if stmt[:20] == other[:20]:
                        risk += 0.1
        
        # Too many questions about scammer details might raise suspicion
        intel = session.extracted_intelligence
        if len(intel.personNames) > 2 and len(intel.phoneNumbers) > 2:
            risk += 0.1

        # Scammer frustration increases risk
        if session.analytics.scammer_sentiment == "frustrated":
            risk += 0.2
        
        session.analytics.detectionRisk = min(risk, 1.0)
        return session.analytics.detectionRisk
    
    def _should_complete_intelligently(self, session: SessionState) -> tuple[bool, str]:
        """
        Determine if session should complete based on quality metrics
        Returns (should_complete, reason)
        """
        # Always complete at max messages
        if session.messages_exchanged >= MAX_ENGAGEMENT_MESSAGES:
            return True, "max_messages_reached"
        
        # Check intelligence quality
        intel = session.extracted_intelligence
        quality_score = extractor.calculate_quality_score(intel)
        session.intelligence_quality_score = quality_score
        
        # High quality + sufficient messages = can complete
        if quality_score >= 0.7 and session.messages_exchanged >= MIN_ENGAGEMENT_MESSAGES:
            return True, "high_quality_intel"
        
        # Very high quality (rare) - complete early
        if quality_score >= 0.85 and session.messages_exchanged >= 8:
            return True, "excellent_quality_intel"
        
        # Check if scammer is disengaging
        if session.analytics.scammerEngagementLevel < 0.3:
            if session.messages_exchanged >= MIN_ENGAGEMENT_MESSAGES:
                return True, "scammer_disengaging"
        
        # No new info emerging
        if not session.analytics.newInfoEmergence and session.messages_exchanged >= 10:
            return True, "no_new_info"
        
        # High detection risk
        if self._assess_detection_risk(session) > 0.6:
            return True, "detection_risk_high"
        
        return False, ""
    
    async def update_session(
        self,
        session_id: str,
        message: Message,
        is_scam: bool,
        confidence: float,
        scam_type: str,
        keywords: list,
        threat_level: ThreatLevel = ThreatLevel.MEDIUM,
        forced_persona: Optional[str] = None
    ) -> SessionState:
        """Update session with new message and detection results"""
        session = await self.get_or_create_session(
            session_id, 
            scam_type, 
            forced_persona=forced_persona,
            first_message=message.text
        )
        
        async with self._lock:
            # Update basic info
            session.scam_detected = session.scam_detected or is_scam
            session.scam_confidence = max(session.scam_confidence, confidence)
            session.cumulative_scam_confidence.append(confidence)
            session.messages_exchanged += 1
            session.last_activity = datetime.now()
            session.conversation_history.append(message)
            session.threat_level = threat_level
            
            # Update scam type if not set
            if not session.scam_type and scam_type:
                session.scam_type = scam_type
                # Potentially re-evaluate persona if it was 'General_Scam' but we now know the type
                if session.persona == "naive_victim" and session.messages_exchanged <= 1:
                    session.persona = agent.select_persona(scam_type, first_message=message.text)
            
            # Update analytics
            self._update_analytics(session, message)
            
            # Update persona emotional state
            agent.update_persona_emotion(session, message.text)
            
            # Extract and accumulate intelligence
            new_intel = extractor.extract_from_text(message.text)
            
            # --- 🛡️ REFINEMENT: Update Global Scammer Profiler ---
            try:
                from scammer_profiler import profiler
                for upi in new_intel.get('upi_ids', []):
                    profiler.update_profile("upi", str(upi), session_id, session.scam_type or "Unknown")
                for phone in new_intel.get('phone_numbers', []):
                    profiler.update_profile("phone", str(phone), session_id, session.scam_type or "Unknown")
                for wallet in new_intel.get('crypto_wallets', []):
                    profiler.update_profile("wallet", str(wallet), session_id, session.scam_type or "Unknown")
            except Exception as e:
                logger.error(f"Global profiler update failed: {e}")

            session.extracted_intelligence = extractor.merge_intelligence(
                session.extracted_intelligence,
                ExtractedIntelligence(
                    bankAccounts=list(new_intel.get('bank_accounts', set())),
                    upiIds=list(new_intel.get('upi_ids', set())),
                    phishingLinks=list(new_intel.get('phishing_links', set())),
                    phoneNumbers=list(new_intel.get('phone_numbers', set())),
                    cryptoWallets=list(new_intel.get('crypto_wallets', set())),
                    suspiciousKeywords=list(new_intel.get('suspicious_keywords', set())),
                    emailAddresses=list(new_intel.get('email_addresses', set())),
                    personNames=list(new_intel.get('person_names', set())),
                    organizationNames=list(new_intel.get('organization_names', set())),
                    paymentPlatforms=list(new_intel.get('payment_platforms', set())),
                    socialMediaHandles=list(new_intel.get('social_handles', set())),
                    geographicIndicators=list(new_intel.get('geographic_indicators', set())),
                    referenceNumbers=list(new_intel.get('reference_numbers', set())),
                    vehicleNumbers=list(new_intel.get('vehicle_numbers', set())),
                    employeeIds=list(new_intel.get('employee_ids', set())),
                )
            )
            
            # Update scammer profile
            self._update_scammer_profile(session, new_intel)
            
            # Check if engagement should complete (intelligent completion)
            should_complete, reason = self._should_complete_intelligently(session)
            if should_complete and not session.engagement_complete:
                session.engagement_complete = True
                log_with_context(
                    logger, logging.INFO,
                    "Intelligent completion triggered",
                    session_id=session_id,
                    reason=reason,
                    messages=session.messages_exchanged,
                    quality_score=session.intelligence_quality_score
                )
                await self._trigger_callback_with_retry(session)
        
        return session
    
    def _update_scammer_profile(self, session: SessionState, new_intel: dict) -> None:
        """Update cross-session scammer profile with behavioral patterns"""
        identifiers = (
            list(new_intel.get('phone_numbers', [])) +
            list(new_intel.get('upi_ids', []))
        )
        
        # Also check existing intel for identifiers if not in new_intel
        if not identifiers:
            identifiers = (
                session.extracted_intelligence.phoneNumbers +
                session.extracted_intelligence.upiIds
            )

        for identifier in identifiers:
            if identifier not in self.scammer_profiles:
                from models import ScammerProfile
                self.scammer_profiles[identifier] = ScammerProfile(
                    firstSeen=datetime.now(),
                    identifiers=[identifier]
                )
            
            profile = self.scammer_profiles[identifier]
            profile.lastSeen = datetime.now()
            if session.session_id not in [s for s in profile.scamTypesUsed]: # Using this as a proxy for session list check for now
                profile.totalSessions += 1
            
            if session.scam_type and session.scam_type not in profile.scamTypesUsed:
                profile.scamTypesUsed.append(session.scam_type)

            # --- Behavioral Profiling ---
            
            # 1. Authority Claim
            authority_keywords = {
                "CBI Officer": ["cbi", "inspector", "police", "officer sharma", "investigation"],
                "Bank Manager": ["bank manager", "sbi", "hdfc", "cyber cell", "manager singh"],
                "Customer Care": ["customer care", "support", "amazon", "fedex", "kbc"]
            }
            last_msg = session.conversation_history[-1].text.lower() if session.conversation_history else ""
            for claim, kws in authority_keywords.items():
                if any(kw in last_msg for kw in kws):
                    profile.authority_claim = claim
                    break

            # 2. Payment Method
            if new_intel.get('upi_ids'):
                profile.payment_method = f"UPI: {', '.join(new_intel['upi_ids'])}"
            elif new_intel.get('bank_accounts'):
                profile.payment_method = f"Bank: {', '.join(new_intel['bank_accounts'])}"

            # 3. Threat Escalation
            threat_indicators = ["block", "arrest", "jail", "court", "disconnect", "penalty"]
            for indicator in threat_indicators:
                if indicator in last_msg and indicator not in profile.threat_escalation:
                    profile.threat_escalation.append(indicator)

            # 4. Patience Level
            if session.messages_exchanged > 20:
                profile.patience_level = "high"
            elif session.messages_exchanged > 10:
                profile.patience_level = "medium"
            else:
                profile.patience_level = "low"

            # 5. Script Flexibility
            # If scammer continues after a language pivot or derailment
            if session.messages_exchanged > 15:
                # Basic check: if they are still engaged after many turns, they have some flexibility
                profile.script_flexibility = "high"
            
            # Sync session's profile view
            session.scammer_profile = profile
    
    async def add_agent_response(
        self,
        session_id: str,
        response: str,
        notes: list
    ) -> Optional[SessionState]:
        """Add agent's response to session"""
        session = self.sessions.get(session_id)
        if session:
            async with self._lock:
                # Add response as a message
                agent_message = Message(
                    sender="user",
                    text=response,
                    timestamp=datetime.now().isoformat()
                )
                session.conversation_history.append(agent_message)
                session.messages_exchanged += 1
                session.agent_notes.extend(notes)
                session.last_activity = datetime.now()
        return session
    
    async def complete_engagement(self, session_id: str) -> Optional[SessionState]:
        """Mark engagement as complete and trigger callback"""
        session = self.sessions.get(session_id)
        if not session:
            raise SessionNotFoundError(session_id)
        
        if not session.engagement_complete:
            session.engagement_complete = True
            session.engagement_phase = EngagementPhase.COMPLETE
            await self._trigger_callback_with_retry(session)
        
        return session
    
    async def _trigger_callback_with_retry(self, session: SessionState) -> bool:
        """Send callback with exponential backoff retry"""
        if session.callback_sent:
            return True
        
        max_retries = CALLBACK_CONFIG["max_retries"]
        base_backoff = CALLBACK_CONFIG["retry_backoff_base"]
        max_backoff = CALLBACK_CONFIG["retry_backoff_max"]
        timeout = CALLBACK_CONFIG["timeout_seconds"]
        
        # Generate agent summary
        agent_notes = agent.generate_agent_summary(session)
        
        # Prepare payload
        payload = {
            "sessionId": session.session_id,
            "scamDetected": session.scam_detected,
            "totalMessagesExchanged": session.messages_exchanged,
            "extractedIntelligence": {
                "bankAccounts": session.extracted_intelligence.bankAccounts,
                "upiIds": session.extracted_intelligence.upiIds,
                "phishingLinks": session.extracted_intelligence.phishingLinks,
                "phoneNumbers": session.extracted_intelligence.phoneNumbers,
                "suspiciousKeywords": session.extracted_intelligence.suspiciousKeywords,
            },
            "agentNotes": agent_notes
        }
        
        for attempt in range(1, max_retries + 1):
            session.callback_attempts = attempt
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        GUVI_CALLBACK_URL,
                        json=payload,
                        timeout=timeout,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        session.callback_sent = True
                        api_logger.log_callback(
                            session.session_id,
                            success=True,
                            status_code=response.status_code,
                            attempt=attempt
                        )
                        
                        # Store session analytics
                        self._store_completed_session(session)
                        
                        return True
                    else:
                        api_logger.log_callback(
                            session.session_id,
                            success=False,
                            status_code=response.status_code,
                            error=response.text[:100],
                            attempt=attempt
                        )
                        
            except httpx.TimeoutException:
                api_logger.log_callback(
                    session.session_id,
                    success=False,
                    error="Timeout",
                    attempt=attempt
                )
            except Exception as e:
                api_logger.log_callback(
                    session.session_id,
                    success=False,
                    error=str(e)[:100],
                    attempt=attempt
                )
            
            # Calculate backoff delay
            if attempt < max_retries:
                delay = min(base_backoff ** attempt, max_backoff)
                logger.warning(f"Callback retry {attempt}/{max_retries}, waiting {delay}s")
                await asyncio.sleep(delay)
        
        # All retries exhausted
        logger.error(f"Callback failed after {max_retries} attempts for session {session.session_id}")
        return False
    
    def log_metrics(self, session: SessionState) -> None:
        """Track real metrics per session for production monitoring (Step 3)"""
        try:
            import json
            import os
            import re
            
            # Calculate quality score using the extractor
            quality_score = extractor.calculate_quality_score(session.extracted_intelligence)
            
            # Count intelligence items
            extraction_count = (
                len(session.extracted_intelligence.phoneNumbers) +
                len(session.extracted_intelligence.upiIds) +
                len(session.extracted_intelligence.phishingLinks) +
                len(session.extracted_intelligence.bankAccounts)
            )
            
            # Calculate average response time
            avg_resp_time = 0
            if session.analytics.messageTimings:
                avg_resp_time = sum(session.analytics.messageTimings) / len(session.analytics.messageTimings)
            
            # Check if any advanced model was used (indicated by agent notes)
            ai_used = any("Success:" in note for note in session.agent_notes)
            fallback_used = any("fallback" in note.lower() for note in session.agent_notes)
            
            # --- Calculate Response Quality Metrics ---
            response_quality = self._calculate_response_quality(session)
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "session_id": session.session_id,
                "scam_type": session.scam_type,
                "persona": session.persona,
                "ai_used": ai_used,
                "fallback_used": fallback_used,
                "quality_score": round(quality_score, 2),
                "extraction_count": extraction_count,
                "response_time_avg": round(avg_resp_time, 2),
                "messages_exchanged": session.messages_exchanged,
                "threat_level": session.threat_level.value,
                "detection_risk": round(session.analytics.detectionRisk, 2),
                "response_quality": {
                    "persona_consistency": round(response_quality.persona_consistency, 2),
                    "extraction_attempts": response_quality.extraction_attempts,
                    "realism_score": round(response_quality.realism_score, 2),
                    "stalling_effectiveness": round(response_quality.stalling_effectiveness, 2),
                    "tactics_used": response_quality.tactics_used,
                    "hinglish_ratio": round(response_quality.hinglish_ratio, 2)
                },
                "scammer_profile": {
                    "patience_level": session.scammer_profile.patience_level,
                    "script_flexibility": session.scammer_profile.script_flexibility,
                    "authority_claim": session.scammer_profile.authority_claim,
                    "payment_method": session.scammer_profile.payment_method,
                    "threat_escalation": session.scammer_profile.threat_escalation
                }
            }
            
            # Append to a metrics file
            with open("session_metrics.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(metrics) + "\n")
                
            logger.info(f"Metrics logged for session {session.session_id}: Q={quality_score:.2f}, E={extraction_count}, PC={response_quality.persona_consistency:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to log metrics: {e}")

    def _calculate_response_quality(self, session: SessionState) -> ResponseQuality:
        """Calculate response quality metrics for AI performance tracking"""
        import re
        
        quality = ResponseQuality()
        
        # Get all bot responses
        bot_responses = [msg.text for msg in session.conversation_history if msg.sender == "user"]
        
        if not bot_responses:
            return quality
        
        # --- 1. Persona Consistency ---
        persona_keywords = {
            "naive_victim": ["sir", "madam", "bhaiya", "ji", "help", "confused", "beta", "arre"],
            "tech_skeptic": ["verify", "check", "confirm", "husband", "manager", "office", "id"],
            "desperate_borrower": ["loan", "wedding", "daughter", "urgent", "need money"],
            "curious_elder": ["arrey", "yaar", "actually", "matlab", "son", "heating"],
            "angry_uncle": ["ARRE", "OYE", "army", "colonel", "nonsense", "yelling"]
        }
        
        persona_hits = 0
        target_keywords = persona_keywords.get(session.persona, [])
        all_text = " ".join(bot_responses).lower()
        for kw in target_keywords:
            if kw.lower() in all_text:
                persona_hits += 1
        quality.persona_consistency = min(1.0, persona_hits / max(len(target_keywords), 1))
        
        # --- 2. Extraction Attempts ---
        extraction_patterns = [
            r"upi", r"account", r"bank", r"number", r"branch", r"phone", r"name", r"office", r"id card"
        ]
        for response in bot_responses:
            for pattern in extraction_patterns:
                if re.search(pattern, response.lower()):
                    quality.extraction_attempts += 1
                    break
        
        # --- 3. Realism Score ---
        # Based on naturalness indicators
        realism_indicators = 0
        for response in bot_responses:
            if "..." in response: realism_indicators += 0.5
            if re.search(r"(arre|yaar|matlab|actually|sorry)", response.lower()): realism_indicators += 0.5
            if len(response) > 20 and len(response) < 200: realism_indicators += 0.5
            if not response.isupper(): realism_indicators += 0.5
        
        quality.realism_score = min(1.0, realism_indicators / (len(bot_responses) * 2))
        
        # --- 4. Stalling Effectiveness ---
        stalling_keywords = [
            "wait", "one minute", "heating", "doorbell", "kitchen", "milk", "son", "husband",
            "manager", "charger", "battery", "screen", "broken", "slow", "otp not coming"
        ]
        stalling_hits = 0
        tactics = []
        for response in bot_responses:
            for kw in stalling_keywords:
                if kw in response.lower():
                    stalling_hits += 1
                    if kw not in tactics:
                        tactics.append(kw)
                    break
        
        quality.stalling_effectiveness = min(1.0, stalling_hits / max(len(bot_responses), 1))
        quality.tactics_used = tactics[:5]  # Top 5 tactics
        
        # --- 5. Hinglish Ratio ---
        hinglish_words = [
            "matlab", "arre", "yaar", "bhaiya", "ji", "kya", "hai", "main", "mera", 
            "aap", "theek", "accha", "bas", "ruko", "samajh", "bhagwan", "shanti", 
            "beta", "beti", "dhakal", "faltu", "sahi", "tension", "nahi", "haan",
            "kijiye", "batao", "kaun", "yahan", "wahan", "kaise", "kab", "kyun",
            "toh", "bhi", "isliye", "lekin", "par", "raha", "rahi", "rhe", "thoda",
            "bahut", "theek", "sahi", "bilkul", "bol", "kar", "ho", "gaya", "gye",
            "kuch", "sab", "apna", "apni", "hoga", "hogi"
        ]
        total_words = sum(len(r.split()) for r in bot_responses)
        hinglish_count = 0
        for r in bot_responses:
            # Clean and split
            words = re.findall(r'\w+', r.lower())
            for word in words:
                if word in hinglish_words:
                    hinglish_count += 1
        
        quality.hinglish_ratio = hinglish_count / max(total_words, 1)
        
        # Update session's response quality
        session.response_quality = quality
        
        return quality


    def _store_completed_session(self, session: SessionState) -> None:
        """Store analytics from completed session for learning"""
        # First log the metrics (Step 3)
        self.log_metrics(session)
        
        summary = {
            "session_id": session.session_id,
            "scam_type": session.scam_type,
            "threat_level": session.threat_level.value,
            "messages": session.messages_exchanged,
            "duration_seconds": (session.last_activity - session.start_time).total_seconds(),
            "persona_used": session.persona,
            "intel_quality": session.intelligence_quality_score,
            "final_phase": session.engagement_phase.value,
            "phone_count": len(session.extracted_intelligence.phoneNumbers),
            "upi_count": len(session.extracted_intelligence.upiIds),
            "completed_at": datetime.now().isoformat(),
        }
        
        self.completed_sessions.append(summary)
        
        # Keep only last 100 sessions
        if len(self.completed_sessions) > 100:
            self.completed_sessions = self.completed_sessions[-100:]
    
    async def cleanup_stale_sessions(self) -> List[str]:
        """Remove sessions that have timed out"""
        cutoff = datetime.now() - timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        cleaned = []
        
        async with self._lock:
            stale_sessions = [
                sid for sid, session in self.sessions.items()
                if session.last_activity < cutoff
            ]
            
            for sid in stale_sessions:
                session = self.sessions[sid]
                if not session.engagement_complete and session.scam_detected:
                    # Trigger callback before removing
                    await self._trigger_callback_with_retry(session)
                del self.sessions[sid]
                cleaned.append(sid)
                logger.info(f"Cleaned up stale session: {sid}")
        
        return cleaned
    
    def get_session_metrics(self, session_id: str) -> dict:
        """Get engagement metrics for a session"""
        session = self.sessions.get(session_id)
        if not session:
            return {
                "engagementDurationSeconds": 0,
                "totalMessagesExchanged": 0,
                "currentPhase": None,
                "phaseProgress": None,
            }
        
        duration = (session.last_activity - session.start_time).total_seconds()
        
        # Calculate phase progress
        phase = session.engagement_phase
        phase_progress = None
        if phase != EngagementPhase.COMPLETE:
            from config import ENGAGEMENT_PHASES
            phase_config = ENGAGEMENT_PHASES.get(phase.value, {})
            min_msg, max_msg = phase_config.get("range", (1, 20))
            phase_progress = min(1.0, (session.messages_exchanged - min_msg + 1) / (max_msg - min_msg + 1))
        
        return {
            "engagementDurationSeconds": int(duration),
            "totalMessagesExchanged": session.messages_exchanged,
            "currentPhase": phase.value,
            "phaseProgress": round(phase_progress, 2) if phase_progress else None,
        }
    
    def get_analytics_summary(self) -> dict:
        """Get overall analytics summary"""
        active_sessions = len(self.sessions)
        scam_sessions = sum(1 for s in self.sessions.values() if s.scam_detected)
        completed = sum(1 for s in self.sessions.values() if s.engagement_complete)
        
        # Aggregate from completed sessions
        scam_types = {}
        total_intel = {"phones": 0, "upis": 0, "links": 0}
        avg_duration = 0
        
        if self.completed_sessions:
            for summary in self.completed_sessions:
                st = summary.get("scam_type", "Unknown")
                scam_types[st] = scam_types.get(st, 0) + 1
                total_intel["phones"] += summary.get("phone_count", 0)
                total_intel["upis"] += summary.get("upi_count", 0)
            
            avg_duration = sum(s.get("duration_seconds", 0) for s in self.completed_sessions) / len(self.completed_sessions)
        
        return {
            "activeSessions": active_sessions,
            "scamSessionsDetected": scam_sessions,
            "completedEngagements": completed + len(self.completed_sessions),
            "averageSessionDuration": round(avg_duration, 1),
            "topScamTypes": dict(sorted(scam_types.items(), key=lambda x: x[1], reverse=True)[:5]),
            "totalIntelligence": total_intel,
            "knownScammerProfiles": len(self.scammer_profiles),
        }


# Global instance
session_manager = SessionManager()
