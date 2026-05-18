"""
Validated Response Builder for Honey-Pot
Ensures all API responses strictly follow the required schema.
"""
from typing import Dict, Any, List
from datetime import datetime

def build_validated_response(
    status: str = "success",
    scam_detected: bool = False,
    reply: str = "",
    session_id: str = "",
    scam_type: str = "General_Scam",
    confidence: float = 0.0,
    indicators: List[str] = None,
    intelligence: Dict[str, Any] = None,
    metrics: Dict[str, Any] = None,
    agent_notes: str = None
) -> Dict[str, Any]:
    """Builds a schema-compliant response dictionary."""

    indicators = indicators or []
    intelligence = intelligence or {}
    metrics = metrics or {}

    return {
        "status": status,
        "scamDetected": scam_detected,
        "reply": reply,
        "sessionId": session_id,
        "scamClassification": {
            "scamType": scam_type,
            "confidence": round(confidence, 4),
            "tacticsIdentified": indicators
        },
        "extractedIntelligence": {
            "bankAccounts": intelligence.get("bankAccounts", []),
            "upiIds": intelligence.get("upiIds", []),
            "phishingLinks": intelligence.get("phishingLinks", []),
            "phoneNumbers": intelligence.get("phoneNumbers", []),
            "cryptoWallets": intelligence.get("cryptoWallets", []),
            "suspiciousKeywords": intelligence.get("suspiciousKeywords", []),
        },
        "engagementMetrics": {
            "engagementDurationSeconds": metrics.get("duration", 0),
            "totalMessagesExchanged": metrics.get("total_messages", 0),
            "currentPhase": metrics.get("phase", "detecting")
        },
        "agentNotes": agent_notes,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
