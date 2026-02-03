"""
Pydantic Models for API Request/Response
Enhanced with engagement phases, threat levels, and confidence scoring
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


# ============== Enums ==============

class EngagementPhase(str, Enum):
    """Current phase of scammer engagement"""
    CONFUSION = "confusion"           # Messages 1-3
    COMPLIANCE = "compliance"         # Messages 4-8
    FAKE_INFO = "fake_info"           # Messages 9-15
    STALLING = "stalling"             # Messages 16-20
    COMPLETE = "complete"             # Engagement finished


class ThreatLevel(str, Enum):
    """Scam sophistication/threat level"""
    LOW = "low"                       # Basic, obvious scam
    MEDIUM = "medium"                 # Moderately sophisticated
    HIGH = "high"                     # Highly sophisticated, targeted


class SenderType(str, Enum):
    """Message sender type"""
    SCAMMER = "scammer"
    USER = "user"


# ============== Request Models ==============

class Message(BaseModel):
    """Single message in the conversation"""
    sender: str = Field(default="scammer", description="Either 'scammer' or 'user'")
    text: str = Field(..., description="Message content")
    timestamp: Optional[Any] = Field(default=None, description="Epoch time in ms or ISO-8601 string")


class Metadata(BaseModel):
    """Optional metadata about the conversation"""
    channel: Optional[str] = Field(default="SMS", description="SMS/WhatsApp/Email/Chat")
    language: Optional[str] = Field(default="English", description="Language used")
    locale: Optional[str] = Field(default="IN", description="Country/region code")
    forcedPersona: Optional[str] = Field(default=None, description="Force a specific persona for testing")


class IncomingRequest(BaseModel):
    """Incoming API request representing a message in conversation"""
    sessionId: str = Field(
        default_factory=lambda: f"session-{int(datetime.now().timestamp())}", 
        description="Unique session identifier",
        alias="session_id"
    )
    message: Union[Message, str] = Field(..., description="The latest incoming message (object or string)")
    conversationHistory: List[Message] = Field(
        default=[], 
        description="Previous messages",
        alias="conversation_history"
    )
    metadata: Optional[Metadata] = Field(default=None, description="Additional context")

    class Config:
        populate_by_name = True  # Allows both sessionId and session_id


# ============== Response Models ==============

class EngagementMetrics(BaseModel):
    """Metrics about the engagement"""
    engagementDurationSeconds: int = Field(default=0)
    totalMessagesExchanged: int = Field(default=0)
    currentPhase: Optional[str] = Field(default=None, description="Current engagement phase")
    phaseProgress: Optional[float] = Field(default=None, description="Progress within current phase (0-1)")


class IntelligenceConfidence(BaseModel):
    """Confidence scores for extracted intelligence"""
    phoneNumbers: Dict[str, float] = Field(default_factory=dict, description="Phone -> confidence")
    upiIds: Dict[str, float] = Field(default_factory=dict, description="UPI ID -> confidence")
    bankAccounts: Dict[str, float] = Field(default_factory=dict, description="Account -> confidence")
    phishingLinks: Dict[str, float] = Field(default_factory=dict, description="Link -> confidence")
    cryptoWallets: Dict[str, float] = Field(default_factory=dict, description="Wallet -> confidence")
    overallScore: float = Field(default=0.0, description="Overall intelligence quality score")


class ExtractedIntelligence(BaseModel):
    """Intelligence extracted from scammer"""
    bankAccounts: List[str] = Field(default=[])
    upiIds: List[str] = Field(default=[])
    phishingLinks: List[str] = Field(default=[])
    phoneNumbers: List[str] = Field(default=[])
    cryptoWallets: List[str] = Field(default=[], description="Extracted crypto wallet addresses")
    suspiciousKeywords: List[str] = Field(default=[])
    # New fields
    emailAddresses: List[str] = Field(default=[], description="Extracted email addresses")
    personNames: List[str] = Field(default=[], description="Extracted person names")
    organizationNames: List[str] = Field(default=[], description="Claimed organizations")
    paymentPlatforms: List[str] = Field(default=[], description="Payment platform mentions")
    socialMediaHandles: List[str] = Field(default=[], description="Social media handles")
    geographicIndicators: List[str] = Field(default=[], description="Cities, area codes")
    referenceNumbers: List[str] = Field(default=[], description="Case/reference numbers")
    vehicleNumbers: List[str] = Field(default=[], description="Extracted vehicle numbers")
    employeeIds: List[str] = Field(default=[], description="Extracted employee/agent IDs")
    confidenceScores: Optional[IntelligenceConfidence] = Field(default=None)


class ThreatAssessment(BaseModel):
    """Assessment of scam threat level"""
    level: ThreatLevel = Field(default=ThreatLevel.MEDIUM)
    sophisticationScore: float = Field(default=0.5, description="0-1 score of scam sophistication")
    indicators: List[str] = Field(default=[], description="Threat level indicators")
    recommendation: Optional[str] = Field(default=None, description="Recommended action")


class ScamClassification(BaseModel):
    """Detailed scam classification with confidence"""
    scamType: str = Field(default="General_Scam")
    confidence: float = Field(default=0.0)
    alternativeTypes: List[Dict[str, float]] = Field(default=[], description="Alternative classifications")
    tacticsIdentified: List[str] = Field(default=[])


class APIResponse(BaseModel):
    """Standard API response - GUVI compliant format"""
    status: str = Field(default="success")
    scamDetected: bool = Field(default=False)
    reply: Optional[str] = Field(default=None, description="AI agent's reply to scammer (GUVI spec)")
    engagementMetrics: EngagementMetrics = Field(default_factory=EngagementMetrics)
    extractedIntelligence: ExtractedIntelligence = Field(default_factory=ExtractedIntelligence)
    agentNotes: Optional[str] = Field(default=None)
    engagementComplete: bool = Field(default=False, description="Whether engagement has concluded")
    # New fields
    scamClassification: Optional[ScamClassification] = Field(default=None)
    threatAssessment: Optional[ThreatAssessment] = Field(default=None)
    detectedLanguage: Optional[str] = Field(default=None)
    responseDelay: Optional[int] = Field(default=None, description="Simulated delay in ms")


# ============== Internal Models ==============

class PersonaState(BaseModel):
    """State tracking for persona consistency"""
    currentMood: str = Field(default="neutral")
    trustLevel: float = Field(default=0.3, description="0-1 trust in scammer")
    suspicionLevel: float = Field(default=0.0, description="0-1 apparent suspicion")
    previousStatements: List[str] = Field(default=[], description="Key statements made")
    fakeInfoProvided: Dict[str, str] = Field(default={}, description="Fake info already shared")
    emotionalProgression: List[str] = Field(default=[], description="Emotional journey")


class ScammerProfile(BaseModel):
    """Profile of scammer behavior across sessions"""
    identifiers: List[str] = Field(default=[], description="Phone/UPI IDs used")
    scamTypesUsed: List[str] = Field(default=[])
    tacticsUsed: List[str] = Field(default=[])
    averageSessionLength: float = Field(default=0.0)
    firstSeen: Optional[datetime] = Field(default=None)
    lastSeen: Optional[datetime] = Field(default=None)
    totalSessions: int = Field(default=0)
    sophisticationScore: float = Field(default=0.5)
    
    # New patterns from user request
    patience_level: str = Field(default="medium", description="high/medium/low based on turn count")
    script_flexibility: str = Field(default="medium", description="high/medium/low based on adaptation to pivots")
    authority_claim: Optional[str] = Field(default=None, description="e.g. CBI Officer, Bank Manager")
    payment_method: Optional[str] = Field(default=None, description="UPI/Bank details extracted")
    threat_escalation: List[str] = Field(default=[], description="Stages of threat used")


class ConversationAnalytics(BaseModel):
    """Analytics for conversation patterns"""
    messageTimings: List[float] = Field(default=[], description="Time between messages in seconds")
    messageLengths: List[int] = Field(default=[], description="Length of each message")
    urgencyProgression: List[float] = Field(default=[], description="Urgency score per message")
    scammerEngagementLevel: float = Field(default=1.0, description="0-1 how engaged scammer is")
    newInfoEmergence: bool = Field(default=True, description="Is new info still emerging")
    detectionRisk: float = Field(default=0.0, description="0-1 risk of being detected as bot")
    scammer_sentiment: str = Field(default="neutral", description="Detected scammer mood: frustrated, threatening, neutral, bored")
    tactics_seen: List[str] = Field(default_factory=list, description="Unique novel tactics (social_*) identified in this session")



class ResponseQuality(BaseModel):
    """Quality metrics for AI-generated responses"""
    persona_consistency: float = Field(default=0.0, description="0-1 how well bot stayed in character")
    extraction_attempts: int = Field(default=0, description="Count of times bot asked for UPI/bank/phone")
    realism_score: float = Field(default=0.0, description="0-1 natural language quality")
    stalling_effectiveness: float = Field(default=0.0, description="0-1 how long scammer stayed engaged")
    tactics_used: List[str] = Field(default=[], description="List of stalling tactics used")
    hinglish_ratio: float = Field(default=0.0, description="0-1 ratio of Hinglish usage")


class SessionState(BaseModel):
    """Internal state for tracking a conversation session"""
    session_id: str
    scam_detected: bool = False
    scam_confidence: float = 0.0
    messages_exchanged: int = 0
    start_time: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    conversation_history: List[Message] = Field(default_factory=list)
    extracted_intelligence: ExtractedIntelligence = Field(default_factory=ExtractedIntelligence)
    scam_type: Optional[str] = None
    persona: str = "naive_victim"
    agent_notes: List[str] = Field(default_factory=list)
    engagement_complete: bool = False
    # New enhanced fields
    engagement_phase: EngagementPhase = Field(default=EngagementPhase.CONFUSION)
    threat_level: ThreatLevel = Field(default=ThreatLevel.MEDIUM)
    persona_state: PersonaState = Field(default_factory=PersonaState)
    analytics: ConversationAnalytics = Field(default_factory=ConversationAnalytics)
    intelligence_quality_score: float = Field(default=0.0, description="0-1 quality of extracted intel")
    cumulative_scam_confidence: List[float] = Field(default_factory=list, description="Confidence over time")
    detected_language: str = Field(default="English")
    callback_sent: bool = Field(default=False)
    callback_attempts: int = Field(default=0)
    response_quality: ResponseQuality = Field(default_factory=ResponseQuality)
    scammer_profile: ScammerProfile = Field(default_factory=ScammerProfile)


class GUVICallbackPayload(BaseModel):
    """Payload for GUVI callback endpoint"""
    sessionId: str
    scamDetected: bool
    totalMessagesExchanged: int
    extractedIntelligence: dict
    agentNotes: str


# ============== Analytics Models ==============

class SessionSummary(BaseModel):
    """Summary of a completed session"""
    sessionId: str
    scamType: Optional[str]
    threatLevel: ThreatLevel
    messagesExchanged: int
    durationSeconds: int
    intelligenceQualityScore: float
    keyEvidence: List[str]
    tacticsUsed: List[str]


class APIStats(BaseModel):
    """API statistics response"""
    activeSessions: int
    scamSessionsDetected: int
    completedEngagements: int
    modelTrained: bool
    geminiEnabled: bool
    averageSessionDuration: float = Field(default=0.0)
    topScamTypes: Dict[str, int] = Field(default_factory=dict)
    intelligenceExtracted: Dict[str, int] = Field(default_factory=dict)
