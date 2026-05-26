"""
Resilient Processing Pipeline for Honey-Pot
Coordinates detection, extraction, and agent response with full fault tolerance.
"""
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from models import (
    Message,
    SessionState,
    EngagementPhase,
    ThreatLevel,
    ExtractedIntelligence,
    ScamClassification,
    ThreatAssessment,
    EngagementMetrics
)
from logging_config import get_logger
from response_schema import build_validated_response

logger = get_logger("honeypot.core.pipeline")

class ResilientPipeline:
    def __init__(self, detector, extractor, agent, session_mgr):
        self.detector = detector
        self.extractor = extractor
        self.agent = agent
        self.session_mgr = session_mgr

    async def process(
        self,
        conversation_id: str,
        message: str,
        sender_id: str = "scammer",
        history: List[Any] = None
    ) -> Dict[str, Any]:
        start_time = time.time()

        # 1. Get or create session
        session = await self.session_mgr.get_or_create_session(conversation_id)

        # 2. Update session with incoming message
        incoming_msg = Message(sender=sender_id, text=message, timestamp=datetime.utcnow().isoformat())
        session.conversation_history.append(incoming_msg)
        session.messages_exchanged += 1

        # 3. Detect Scam
        is_scam, confidence, scam_type, keywords, classification, threat_level = self.detector.detect(
            message,
            [m.text for m in session.conversation_history[:-1]]
        )

        session.scam_detected = is_scam
        session.scam_confidence = confidence
        session.scam_type = scam_type
        session.threat_level = threat_level

        # 4. Extract Intelligence
        new_intel = self.extractor.extract(message)
        # Merge intelligence
        for attr in ["bankAccounts", "upiIds", "phishingLinks", "phoneNumbers", "cryptoWallets", "suspiciousKeywords"]:
            existing = getattr(session.extracted_intelligence, attr)
            new_vals = getattr(new_intel, attr)
            for val in new_vals:
                if val not in existing:
                    existing.append(val)

        # 5. Update Persona and Generate Response
        self.agent.update_persona_emotion(session, message)

        # Determine if we should reply
        if is_scam:
            reply_text, agent_notes, delay_ms = await self.agent.generate_response(session, message)
            if agent_notes:
                session.agent_notes.extend(agent_notes)
        else:
            reply_text = "Hello! How can I help you today?"
            delay_ms = 0

        # Add agent response to history
        agent_msg = Message(sender="user", text=reply_text, timestamp=datetime.utcnow().isoformat())
        session.conversation_history.append(agent_msg)
        session.messages_exchanged += 1

        # 6. Update Analytics and Metrics
        duration = time.time() - start_time
        intel_count = len(session.extracted_intelligence.bankAccounts) + \
                      len(session.extracted_intelligence.upiIds) + \
                      len(session.extracted_intelligence.phishingLinks) + \
                      len(session.extracted_intelligence.phoneNumbers)

        # 7. Check for engagement completion
        if session.messages_exchanged >= 10 and intel_count >= 1:
            session.engagement_complete = True

        engagement_status = "active"
        if session.engagement_complete:
            engagement_status = "completed"
        elif is_scam:
            engagement_status = "engaging"

        # 8. Build and return response using shared response schema
        return build_validated_response(
            status="success",
            scam_detected=is_scam,
            reply=reply_text,
            session_id=conversation_id,
            scam_type=scam_type,
            confidence=confidence,
            indicators=keywords,
            intelligence=session.extracted_intelligence.model_dump(),
            metrics={
                "duration": round(duration, 2),
                "total_messages": session.messages_exchanged,
                "phase": engagement_status
            },
            agent_notes="; ".join(session.agent_notes[-3:]) if session.agent_notes else None
        )

# Maintain build_final_response as an alias if needed by main.py exception handlers
def build_final_response(**kwargs):
    # Mapping old field names to new build_validated_response names
    mapped = {
        "scam_detected": kwargs.get("is_scam", False),
        "confidence": kwargs.get("confidence", 0.0),
        "scam_type": kwargs.get("scam_type", "General_Scam"),
        "indicators": kwargs.get("indicators", []),
        "session_id": kwargs.get("conversation_id", "unknown"),
        "reply": kwargs.get("response_message", ""),
        "intelligence": kwargs.get("intelligence", {}),
        "metrics": {
            "duration": kwargs.get("duration", 0),
            "total_messages": kwargs.get("total_turns", 0),
            "phase": kwargs.get("engagement_status", "error")
        }
    }
    return build_validated_response(**mapped)
