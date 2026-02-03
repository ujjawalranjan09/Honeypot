"""
Honey-Pot API - Main Application
Enhanced with production features, structured logging, and comprehensive error handling
"""
import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, Dict
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Header, Depends, BackgroundTasks, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
import os

from config import (
    API_KEY,
    MIN_ENGAGEMENT_MESSAGES,
    RATE_LIMIT_CONFIG,
    SESSION_CLEANUP_INTERVAL_SECONDS,
    GUVI_CALLBACK_URL,
)
from models import (
    IncomingRequest,
    APIResponse,
    EngagementMetrics,
    ScamClassification,
    ThreatAssessment,
    APIStats,
)
from scam_detector import detector
from ai_agent import reasoning_agent as agent
from session_manager import session_manager
from exceptions import (
    HoneypotException,
    SessionNotFoundError,
    InvalidAPIKeyError,
    RateLimitError,
    ValidationError,
)
from logging_config import (
    setup_logging,
    get_logger,
    log_with_context,
    api_logger,
)
import logging
import httpx

# Initialize logging
setup_logging()
logger = get_logger("honeypot.main")


# ============== Rate Limiting ==============

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.session_requests: Dict[str, list] = defaultdict(list)
        self.ip_requests: Dict[str, list] = defaultdict(list)
    
    def _cleanup_old_requests(self, requests: list, window_seconds: int = 60):
        """Remove requests older than the window"""
        cutoff = time.time() - window_seconds
        return [r for r in requests if r > cutoff]
    
    def check_rate_limit(self, session_id: str, client_ip: str) -> bool:
        """Check if request is within rate limits. Returns True if allowed."""
        if not RATE_LIMIT_CONFIG.get("enabled", True):
            return True
        
        now = time.time()
        
        # Check session rate limit
        self.session_requests[session_id] = self._cleanup_old_requests(
            self.session_requests[session_id]
        )
        if len(self.session_requests[session_id]) >= RATE_LIMIT_CONFIG.get("requests_per_session_per_minute", 30):
            return False
        
        # Check IP rate limit
        self.ip_requests[client_ip] = self._cleanup_old_requests(
            self.ip_requests[client_ip]
        )
        if len(self.ip_requests[client_ip]) >= RATE_LIMIT_CONFIG.get("requests_per_ip_per_minute", 100):
            return False
        
        # Record this request
        self.session_requests[session_id].append(now)
        self.ip_requests[client_ip].append(now)
        
        return True


rate_limiter = RateLimiter()


# ============== GUVI Callback ==============

async def send_guvi_callback(session_id: str, session):
    """
    Send final extracted intelligence to GUVI evaluation endpoint.
    This is MANDATORY for hackathon scoring.
    """
    if session.callback_sent:
        logger.info(f"Callback already sent for session {session_id}")
        return True
    
    try:
        intel = session.extracted_intelligence
        payload = {
            "sessionId": session_id,
            "scamDetected": session.scam_detected,
            "totalMessagesExchanged": session.messages_exchanged,
            "extractedIntelligence": {
                "bankAccounts": intel.bankAccounts,
                "upiIds": intel.upiIds,
                "phishingLinks": intel.phishingLinks,
                "phoneNumbers": intel.phoneNumbers,
                "suspiciousKeywords": intel.suspiciousKeywords
            },
            "agentNotes": "; ".join(session.agent_notes[-5:]) if session.agent_notes else "No notes"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                GUVI_CALLBACK_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                session.callback_sent = True
                logger.info(f"GUVI callback SUCCESS for session {session_id}")
                return True
            else:
                logger.warning(f"GUVI callback failed: {response.status_code} - {response.text[:100]}")
                session.callback_attempts += 1
                return False
                
    except Exception as e:
        logger.error(f"GUVI callback error for {session_id}: {e}")
        session.callback_attempts += 1
        return False


# ============== Lifespan ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting Honey-Pot API...")
    
    # Train model if needed
    if not detector.is_trained:
        logger.info("Training scam detection model...")
        detector.train_model()
    
    # Start background cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    logger.info("Honey-Pot API is ready!")
    yield
    
    # Cleanup on shutdown
    cleanup_task.cancel()
    logger.info("Honey-Pot API shutting down...")


async def periodic_cleanup():
    """Periodically clean up stale sessions"""
    while True:
        await asyncio.sleep(SESSION_CLEANUP_INTERVAL_SECONDS)
        try:
            cleaned = await session_manager.cleanup_stale_sessions()
            if cleaned:
                logger.info(f"Cleaned up {len(cleaned)} stale sessions")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


# ============== FastAPI App ==============

app = FastAPI(
    title="Agentic Honey-Pot API",
    description="""
## AI-Powered Honeypot for Scam Detection and Intelligence Extraction

This API provides:
- **Scam Detection**: ML + rule-based hybrid detection with contextual analysis
- **Autonomous Engagement**: AI agent with multiple personas to engage scammers
- **Intelligence Extraction**: Extract phone numbers, UPI IDs, links, and more
- **Session Management**: Track multi-turn conversations with intelligent completion

### Authentication
All endpoints (except `/api/health`) require an API key in the `X-API-Key` header.
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Exception Handlers ==============

@app.exception_handler(HoneypotException)
async def honeypot_exception_handler(request: Request, exc: HoneypotException):
    """Handle custom honeypot exceptions"""
    log_with_context(
        logger, logging.WARNING,
        f"Honeypot exception: {exc.message}",
        error_code=exc.error_code,
        path=request.url.path
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation errors with custom response"""
    body = await request.body()
    log_with_context(
        logger, logging.WARNING,
        f"Validation error: {str(exc)}",
        path=request.url.path,
        body=body.decode()[:500] if body else "None"
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Invalid request body format",
            "details": exc.errors(),
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    log_with_context(
        logger, logging.ERROR,
        f"Unhandled exception: {str(exc)}",
        path=request.url.path,
        error_type=type(exc).__name__
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
        }
    )


# ============== Dependencies ==============

async def verify_api_key(x_api_key: str = Header(..., description="API Key for authentication", alias="x-api-key")):
    """Verify API key from header"""
    if x_api_key != API_KEY:
        raise InvalidAPIKeyError("Invalid or missing API key")
    return x_api_key


async def check_rate_limit(request: Request):
    """Check rate limit for request"""
    client_ip = request.client.host if request.client else "unknown"
    # Session ID will be checked per-endpoint if available
    return client_ip


# ============== Endpoints ==============

@app.get("/api/health", tags=["System"])
async def health_check():
    """
    Health check endpoint (no authentication required)
    
    Returns system status including:
    - API health status
    - Model training status
    - Gemini AI configuration status
    - Active session count
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model_trained": detector.is_trained,
        "gemini_configured": agent.configured,
        "active_sessions": len(session_manager.sessions),
        "version": "2.0.0"
    }

@app.get("/api/model_status", tags=["System"])
async def model_status(x_api_key: str = Header(None)):
    """Get detailed AI model status and queue"""
    await verify_api_key(x_api_key)
    return agent.get_model_health_status()


@app.post("/api/message", response_model=APIResponse, tags=["Core"])
@app.post("//api/message", response_model=APIResponse, include_in_schema=False)
async def process_message(
    request_body: IncomingRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key),
    client_ip: str = Depends(check_rate_limit)
):
    """
    Process incoming message from scammer
    
    This is the main endpoint that:
    1. Detects if the message is a scam
    2. Extracts intelligence from the conversation
    3. Generates an AI agent response if scam detected
    4. Tracks the engagement session
    """
    start_time = time.time()
    
    # Handle flexible message format (str or Message object)
    if isinstance(request_body.message, str):
        message = Message(text=request_body.message, sender="scammer")
    else:
        message = request_body.message
        
    session_id = request_body.sessionId
    
    # Rate limit check
    if not rate_limiter.check_rate_limit(session_id, client_ip):
        raise RateLimitError(retry_after=60)
    
    # Log incoming request
    api_logger.log_request(
        method="POST",
        path="/api/message",
        session_id=session_id,
        body={"sender": message.sender, "text_length": len(message.text)}
    )
    
    try:
        # Get conversation context
        context = [msg.text for msg in request_body.conversationHistory]
        
        # Detect scam with enhanced analysis (Rule-based first)
        is_scam, confidence, scam_type, keywords, classification, threat_level = detector.detect(
            message.text, context=context
        )
        
        # 🧠 HYBRID UPGRADE: If Rule-based missed it, check Semantic Intent with LLM
        # Only check if message is substantial (>20 chars) and not already flagged
        if not is_scam and len(message.text) > 20 and agent.configured:
            llm_is_scam, llm_conf, llm_reason = await agent.analyze_scam_intent(message.text)
            
            if llm_is_scam and llm_conf > 0.4:
                logger.warning(f"Semantic Override: LLM detected scam where Rules failed. Reason: {llm_reason}")
                is_scam = True
                confidence = max(confidence, llm_conf)
                scam_type = "Sophisticated_Scam" # Generic type for LLM catch
                keywords.append("AI_SEMANTIC_DETECTION")
                classification.scamType = scam_type
                classification.confidence = llm_conf
        
        # Log detection result
        api_logger.log_scam_detection(
            session_id=session_id,
            is_scam=is_scam,
            confidence=confidence,
            scam_type=scam_type,
            keywords=keywords
        )
        
        # Update session
        forced_persona = request_body.metadata.forcedPersona if request_body.metadata else None
        
        session = await session_manager.update_session(
            session_id=session_id,
            message=message,
            is_scam=is_scam,
            confidence=confidence,
            scam_type=scam_type,
            keywords=keywords,
            threat_level=threat_level,
            forced_persona=forced_persona
        )
        
        # Build response
        response = APIResponse(
            status="success",
            scamDetected=session.scam_detected,
            engagementMetrics=EngagementMetrics(**session_manager.get_session_metrics(session_id)),
            extractedIntelligence=session.extracted_intelligence,
            engagementComplete=session.engagement_complete,
            scamClassification=classification,
            threatAssessment=ThreatAssessment(
                level=threat_level,
                sophisticationScore=session.analytics.scammerEngagementLevel,
                indicators=keywords[:5]
            ),
            detectedLanguage=session.detected_language
        )
        
        # Generate agent response for EVERY message (not just scam detected)
        # This ensures we always engage and never return None
        # Generate agent response ONLY if scam is detected or simulation is active
        # This acts as a "Silent Observer" for benign messages
        if (is_scam or session.scam_detected) and not session.engagement_complete:
            try:
                agent_response, agent_notes, delay_ms = await agent.generate_response(session, message.text)
                
                # Apply delay to simulate human typing
                await asyncio.sleep(delay_ms / 1000.0)
                
                await session_manager.add_agent_response(session_id, agent_response, agent_notes)
                response.reply = agent_response
                response.agentNotes = "; ".join(agent_notes)
                response.responseDelay = delay_ms
                
            except Exception as e:
                logger.error(f"Agent response generation failed: {e}", exc_info=True)
                response.reply = "Haan ji bhaiya, ek minute ruko... main abhi busy hun. Aap kaun?"
                response.agentNotes = f"Agent error, used inline fallback: {str(e)}"
        else:
            response.reply = None
            response.agentNotes = "Msg ignored (Not a scam)"
        
        # Generate summary if past minimum messages
        if session.messages_exchanged >= MIN_ENGAGEMENT_MESSAGES:
            response.agentNotes = agent.generate_agent_summary(session)
        
        # Log response
        duration_ms = (time.time() - start_time) * 1000
        api_logger.log_response(
            status_code=200,
            duration_ms=duration_ms,
            session_id=session_id
        )
        
        # Log intelligence extraction
        intel = session.extracted_intelligence
        api_logger.log_intelligence_extraction(
            session_id=session_id,
            phone_count=len(intel.phoneNumbers),
            upi_count=len(intel.upiIds),
            link_count=len(intel.phishingLinks),
            account_count=len(intel.bankAccounts)
        )
        
        # GUVI Callback - Send when engagement is complete or sufficient data collected
        # Trigger conditions:
        # 1. Scam detected AND engagement complete
        # 2. Scam detected AND messages >= 5 AND any intelligence extracted
        should_callback = (
            session.scam_detected and 
            not session.callback_sent and
            (
                session.engagement_complete or
                (session.messages_exchanged >= 5 and (
                    len(intel.phoneNumbers) > 0 or
                    len(intel.upiIds) > 0 or
                    len(intel.phishingLinks) > 0 or
                    len(intel.bankAccounts) > 0
                ))
            )
        )
        
        if should_callback:
            background_tasks.add_task(send_guvi_callback, session_id, session)
            logger.info(f"Scheduled GUVI callback for session {session_id}")
        
        return response
        
    except HoneypotException:
        raise
    except Exception as e:
        logger.exception(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@app.get("/api/session/{session_id}", tags=["Sessions"])
async def get_session_status(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get current status of a session
    
    Returns detailed session information including:
    - Scam detection status and type
    - Persona being used
    - Messages exchanged
    - Extracted intelligence
    - Analytics
    """
    session = session_manager.sessions.get(session_id)
    if not session:
        raise SessionNotFoundError(session_id)
    
    return {
        "sessionId": session_id,
        "scamDetected": session.scam_detected,
        "scamType": session.scam_type,
        "scamConfidence": round(session.scam_confidence, 4),
        "threatLevel": session.threat_level.value,
        "persona": session.persona,
        "engagementPhase": session.engagement_phase.value,
        "messagesExchanged": session.messages_exchanged,
        "engagementComplete": session.engagement_complete,
        "intelligenceQualityScore": round(session.intelligence_quality_score, 2),
        "extractedIntelligence": session.extracted_intelligence.model_dump(),
        "analytics": {
            "scammerEngagementLevel": round(session.analytics.scammerEngagementLevel, 2),
            "detectionRisk": round(session.analytics.detectionRisk, 2),
            "newInfoEmerging": session.analytics.newInfoEmergence,
        },
        "startTime": session.start_time.isoformat(),
        "lastActivity": session.last_activity.isoformat(),
        "callbackSent": session.callback_sent,
    }


@app.post("/api/complete/{session_id}", tags=["Sessions"])
async def complete_engagement(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Manually complete engagement and trigger GUVI callback
    
    Use this to force-complete a session before the automatic
    completion threshold is reached.
    """
    try:
        session = await session_manager.complete_engagement(session_id)
        return {
            "status": "completed",
            "sessionId": session_id,
            "callbackTriggered": True,
            "callbackSuccess": session.callback_sent,
            "summary": agent.generate_agent_summary(session)
        }
    except SessionNotFoundError:
        raise


@app.post("/api/train", tags=["ML Model"])
async def train_model(api_key: str = Depends(verify_api_key)):
    """
    Retrain the ML model on the dataset
    
    This will:
    1. Load the scam dataset
    2. Train a new Gradient Boosting model
    3. Save the model for future use
    """
    try:
        accuracy = detector.train_model()
        if accuracy:
            return {
                "status": "success",
                "accuracy": f"{accuracy:.2%}",
                "message": "Model trained successfully"
            }
        raise HTTPException(status_code=500, detail="Training failed")
    except Exception as e:
        logger.exception(f"Training error: {e}")
        raise HTTPException(status_code=500, detail=f"Training error: {str(e)}")


@app.get("/api/stats", response_model_exclude_none=True, tags=["Analytics"])
async def get_stats(api_key: str = Depends(verify_api_key)):
    """
    Get comprehensive API statistics
    
    Returns analytics including:
    - Active and completed sessions
    - Top scam types detected
    - Intelligence gathered
    - Known scammer profiles
    """
    analytics = session_manager.get_analytics_summary()
    
    return {
        **analytics,
        "modelTrained": detector.is_trained,
        "geminiEnabled": agent.configured,
    }


@app.get("/api/scammer-profiles", tags=["Analytics"])
async def get_scammer_profiles(
    limit: int = 15,
    api_key: str = Depends(verify_api_key)
):
    """
    Get known scammer profiles from persistent cross-session analysis
    """
    from scammer_profiler import profiler
    all_profiles = []
    
    # Flatten categories from persistent DB
    for cat in ["upi", "phone", "wallet"]:
        for identifier, data in profiler.profiles.get(cat, {}).items():
            all_profiles.append({
                "identifier": identifier[:4] + "****" + identifier[-4:] if len(identifier) > 10 else identifier,
                "category": cat,
                "sessionsCount": data.get("hit_count", 0),
                "scamTypes": list(data.get("scam_types", [])),
                "firstSeen": data.get("first_seen"),
                "lastSeen": data.get("last_seen")
            })
            
    # Sort by hit count
    top_profiles = sorted(all_profiles, key=lambda x: x["sessionsCount"], reverse=True)[:limit]
    
    return {
        "totalProfiles": len(all_profiles),
        "profiles": top_profiles
    }


@app.get("/api/personas", tags=["Configuration"])
async def get_available_personas(api_key: str = Depends(verify_api_key)):
    """
    Get list of available agent personas
    
    Returns details about each persona including:
    - Name and age
    - Description and traits
    - Language style
    """
    personas = []
    for key, data in agent.personas.items():
        personas.append({
            "id": key,
            "name": data["name"],
            "age": data["age"],
            "description": data["description"],
            "style": data["style"],
            "languageStyle": data["language_style"],
        })
    
    return {"personas": personas}


# ============== Frontend ==============

# Mount frontend if directory exists
if os.path.isdir("frontend"):
    try:
        app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
        logger.info("Frontend mounted successfully")
    except Exception as e:
        logger.error(f"Failed to mount frontend: {e}")


# ============== Custom OpenAPI Schema ==============

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication"
        }
    }
    
    # Apply security to all endpoints except health
    for path in openapi_schema["paths"]:
        if path != "/api/health":
            for method in openapi_schema["paths"][path]:
                openapi_schema["paths"][path][method]["security"] = [{"ApiKeyAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# ============== Main Entry Point ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
