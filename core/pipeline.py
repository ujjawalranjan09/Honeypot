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

logger = get_logger("honeypot.core.pipeline")

def build_final_response(
    conversation_id: str,
    response_message: str,
    is_scam: bool,
    confidence: float,
    scam_type: str,
    indicators: List[str],
    engagement_status: str,
    intelligence: Dict[str, Any],
    total_turns: int,
    duration: float,
    scammer_count: int,
    agent_count: int,
    intel_count: int
) -> Dict[str, Any]:
    """Helper to build a validated JSON response compliant with the API schema."""

    # Ensure intelligence has all required fields for the schema
    intel_obj = {
        "bankAccounts": intelligence.get("bankAccounts", []),
        "upiIds": intelligence.get("upiIds", []),
        "phishingLinks": intelligence.get("phishingLinks", []) or intelligence.get("phishingUrls", []),
        "phoneNumbers": intelligence.get("phoneNumbers", []),
        "cryptoWallets": intelligence.get("cryptoWallets", []),
        "suspiciousKeywords": intelligence.get("suspiciousKeywords", []),
        "emailAddresses": intelligence.get("emailAddresses", []),
        "personNames": intelligence.get("personNames", []),
        "organizationNames": intelligence.get("organizationNames", []),
    }

    return {
        "status": "success",
        "conversationId": conversation_id,
        "sessionId": conversation_id, # Added for compatibility
        "scamDetected": is_scam,
        "reply": response_message,
        "scamDetection": {
            "isScam": is_scam,
            "confidence": round(confidence, 4),
            "scamType": scam_type,
            "indicators": indicators
        },
        # Added for compatibility with models.APIResponse
        "scamClassification": {
            "scamType": scam_type,
            "confidence": round(confidence, 4),
            "tacticsIdentified": indicators
        },
        "engagementStatus": engagement_status,
        "extractedIntelligence": intel_obj,
        "engagementMetrics": {
            "totalTurns": total_turns,
            "totalMessagesExchanged": total_turns, # Added for compatibility
            "engagementDurationSeconds": round(duration, 2),
            "scammerMessagesCount": scammer_count,
            "agentMessagesCount": agent_count,
            "intelligenceItemsExtracted": intel_count
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

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

        # 8. Build and return response
        return build_final_response(
            conversation_id=conversation_id,
            response_message=reply_text,
            is_scam=is_scam,
            confidence=confidence,
            scam_type=scam_type,
            indicators=keywords,
            engagement_status=engagement_status,
            intelligence=session.extracted_intelligence.model_dump(),
            total_turns=session.messages_exchanged,
            duration=duration,
            scammer_count=session.messages_exchanged // 2,
            agent_count=session.messages_exchanged // 2,
            intel_count=intel_count
        )
