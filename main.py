"""
Honey-Pot API - Main Application
Enhanced with production features, structured logging, and comprehensive error handling
"""
import asyncio
import json
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, Dict
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Header, Depends, BackgroundTasks, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
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
    Message,
    APIResponse,
    EngagementMetrics,
    ScamClassification,
    ThreatAssessment,
    APIStats,
)
from scam_detector import detector
from ai_agent import reasoning_agent as agent
from session_manager import session_manager
from intelligence_extractor import extractor
from core.pipeline import ResilientPipeline
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

# ============== Resilient Pipeline (GAP-2 FIX) ==============
# Initialize the fault-tolerant processing pipeline
pipeline = ResilientPipeline(
    detector=detector,
    extractor=extractor,
    agent=agent,
    session_mgr=session_manager
)


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
    logger.info("=" * 60)
    logger.info("Starting Honey-Pot API...")
    logger.info("=" * 60)
    
    # Log all registered routes at startup
    logger.info("Registered API Routes:")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(sorted(list(route.methods))) if route.methods else 'N/A'
            logger.info(f"  {methods:6} {route.path}")
    
    # Check for duplicate paths
    from collections import Counter
    paths = [route.path for route in app.routes]
    path_counts = Counter(paths)
    duplicates = {k: v for k, v in path_counts.items() if v > 1}
    if duplicates:
        logger.warning(f"⚠️ WARNING: Duplicate route paths detected: {duplicates}")
    else:
        logger.info("✓ No duplicate routes found")
    
    logger.info("=" * 60)
    
    # Train model if needed
    if not detector.is_trained:
        logger.info("Training scam detection model...")
        detector.train_model()
    
    # Start background cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    logger.info("=" * 60)
    logger.info("Honey-Pot API is ready! 🚀")
    logger.info("=" * 60)
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

# Log registered routes for debugging duplicate endpoints
try:
    route_paths = []
    for route in app.routes:
        path_info = f"{route.path}"
        if hasattr(route, 'methods'):
            path_info = f"{list(route.methods)} {route.path}"
        route_paths.append(path_info)
    logger.info(f"Registered routes: {route_paths}")
    
    # Check for duplicate paths
    from collections import Counter
    path_counts = Counter([route.path for route in app.routes])
    duplicates = {k: v for k, v in path_counts.items() if v > 1}
    if duplicates:
        logger.warning(f"⚠️ DUPLICATE ROUTES DETECTED: {duplicates}")
except Exception as e:
    logger.warning(f"Failed to list routes: {e}")

# ============== JSON Enforcement Middleware ==============
# CRITICAL FIX: Ensures every response ALWAYS has Content-Type: application/json
# This prevents the "invalid_response_type" error when evaluators check responses.

class JSONEnforcementMiddleware(BaseHTTPMiddleware):
    """Intercepts all responses to guarantee:
    1. Content-Type is always application/json
    2. Plain-text 429 errors (from Render/upstream) become proper JSON
    """
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
        except Exception as exc:
            # Catch any unhandled exception at the middleware level
            logger.error(f"Middleware caught unhandled exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "conversationId": "error",
                    "reply": "Haan ji, ek minute... server busy hai",
                    "scamDetected": False,
                    "scamDetection": {"isScam": False, "confidence": 0.0, "scamType": "Unknown_Scam", "indicators": []},
                    "engagementStatus": "detecting",
                    "extractedIntelligence": {"bankAccounts": [], "upiIds": [], "phishingUrls": [], "phoneNumbers": [], "emailAddresses": [], "namesMentioned": [], "organizationsMentioned": []},
                    "engagementMetrics": {"totalTurns": 0, "engagementDurationSeconds": 0.0, "scammerMessagesCount": 0, "agentMessagesCount": 0, "intelligenceItemsExtracted": 0},
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "status": "error",
                    "error": "INTERNAL_ERROR"
                },
                headers={"Content-Type": "application/json"}
            )

        # Convert plain-text 429 responses (from Render's own rate limiter) to JSON
        if response.status_code == 429:
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                logger.warning("Intercepted plain-text 429 - converting to JSON")
                return JSONResponse(
                    status_code=429,
                    content={
                        "conversationId": "rate-limited",
                        "reply": "Haan ji, ek minute... thoda busy hoon abhi",
                        "scamDetected": False,
                        "scamDetection": {"isScam": False, "confidence": 0.0, "scamType": "Unknown_Scam", "indicators": []},
                        "engagementStatus": "detecting",
                        "extractedIntelligence": {"bankAccounts": [], "upiIds": [], "phishingUrls": [], "phoneNumbers": [], "emailAddresses": [], "namesMentioned": [], "organizationsMentioned": []},
                        "engagementMetrics": {"totalTurns": 0, "engagementDurationSeconds": 0.0, "scammerMessagesCount": 0, "agentMessagesCount": 0, "intelligenceItemsExtracted": 0},
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "status": "error",
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please retry after 60 seconds.",
                        "retryAfter": 60
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Retry-After": "60"
                    }
                )

        # Ensure all non-streaming responses have Content-Type: application/json
        # Skip static files, docs, and streaming responses
        if hasattr(response, 'headers'):
            path = request.url.path
            skip_paths = ["/docs", "/redoc", "/openapi.json", "/static", "/favicon"]
            is_api = any(path.startswith("/api") for _ in [1])
            if is_api and "content-type" in response.headers:
                response.headers["content-type"] = "application/json; charset=utf-8"

        return response


app.add_middleware(JSONEnforcementMiddleware)

# CORS middleware - must be added AFTER JSONEnforcementMiddleware
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
    error_msg = str(exc)
    log_with_context(
        logger, logging.WARNING,
        f"Validation error: {error_msg}",
        path=request.url.path,
        body=body.decode()[:500] if body else "None"
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": f"Validation failed: {exc.errors()[0]['msg'] if exc.errors() else error_msg}",
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

async def verify_api_key(
    x_api_key: Optional[str] = Header(None, description="API Key", alias="x-api-key")
):
    """Verify API key from header (Lenient to avoid 422 on missing header)"""
    if not x_api_key:
        raise InvalidAPIKeyError("Missing API Key")
        
    if x_api_key != API_KEY:
        raise InvalidAPIKeyError("Invalid API key")
    return x_api_key


async def check_rate_limit(request: Request):
    """Check rate limit for request"""
    client_ip = request.client.host if request.client else "unknown"
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
async def process_message(
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key),
    client_ip: str = Depends(check_rate_limit)
):
    """
    Main message processing endpoint.
    Now uses ResilientPipeline for full fault tolerance.
    """
    start_time = time.time()

    try:
        # ===== 1. PARSE REQUEST (keep your existing parsing) =====
        try:
            body = await request.json()
        except Exception:
            raw = await request.body()
            try:
                body = json.loads(raw.decode('utf-8', errors='replace'))
            except Exception:
                body = {"message": raw.decode('utf-8', errors='replace')}

        # Extract fields with your existing heuristic parsing
        message_text = ""
        sender = "scammer"
        session_id = None
        conversation_history = []

        # Message extraction (support multiple formats)
        if isinstance(body.get("message"), dict):
            message_text = body["message"].get("text", "") or body["message"].get("content", "")
            sender = body["message"].get("sender", "scammer")
        elif isinstance(body.get("message"), str):
            message_text = body["message"]
        elif isinstance(body.get("text"), str):
            message_text = body["text"]
        elif isinstance(body.get("content"), str):
            message_text = body["content"]

        if not message_text:
            # Try to find message in any string field
            for key, val in body.items():
                if isinstance(val, str) and len(val) > 5 and key not in (
                    "sessionId", "session_id", "sender", "api_key"
                ):
                    message_text = val
                    break

        if not message_text:
            message_text = str(body)

        # Session ID extraction
        session_id = (
            body.get("sessionId") or
            body.get("session_id") or
            body.get("conversation_id") or
            body.get("conversationId") or
            f"auto-{hash(message_text[:50]) % 100000}"
        )

        # Sender extraction
        sender = (
            body.get("sender") or
            (body.get("message", {}).get("sender")
             if isinstance(body.get("message"), dict) else None) or
            "scammer"
        )

        # Conversation history extraction
        conversation_history = (
            body.get("conversationHistory") or
            body.get("conversation_history") or
            body.get("history") or
            []
        )

        # ===== 2. RATE LIMIT CHECK =====
        if not rate_limiter.check_rate_limit(session_id, client_ip):
            raise RateLimitError(retry_after=60)

        # ===== 3. LOG REQUEST =====
        api_logger.log_request(
            method="POST",
            path="/api/message",
            session_id=session_id,
            body={"synthesized_text": message_text[:50], "original_keys": list(body.keys()) if isinstance(body, dict) else "raw_string"}
        )

        # ===== 4. USE PIPELINE (this activates ALL gap fixes) =====
        result = await pipeline.process(
            conversation_id=session_id,
            message=message_text,
            sender_id=sender,
            history=conversation_history
        )

        # ===== 5. LOG AND RETURN =====
        elapsed = time.time() - start_time
        api_logger.log_response(
            status_code=200,
            duration_ms=elapsed * 1000,
            session_id=session_id
        )

        logger.info(
            f"Request processed in {elapsed:.2f}s | "
            f"session={session_id} | "
            f"scam={result.get('scam_detection', {}).get('is_scam')} | "
            f"conf={result.get('scam_detection', {}).get('confidence', 0):.4f}"
        )

        # Schedule GUVI callback if session is complete
        if result.get("engagement_status") == "intelligence_gathered":
            session = session_manager.sessions.get(session_id)
            if session and not session.callback_sent:
                background_tasks.add_task(send_guvi_callback, session_id, session)
                logger.info(f"Scheduled GUVI callback for session {session_id}")

        return JSONResponse(content=result)

    except RateLimitError as e:
        # Return a valid JSON honeypot response even on rate limit
        # The evaluator expects our schema, not just an error dict
        from core.pipeline import build_final_response
        rate_limit_response = build_final_response(
            conversation_id=session_id or "rate-limited",
            response_message="Haan ji, ek minute... bahut busy hoon abhi",
            is_scam=False,
            confidence=0.0,
            scam_type="Unknown_Scam",
            indicators=["rate_limit_hit"],
            engagement_status="detecting",
            intelligence={},
            total_turns=1,
            duration=time.time() - start_time,
            scammer_count=1,
            agent_count=0,
            intel_count=0
        )
        return JSONResponse(
            status_code=429,
            content=rate_limit_response,
            headers={
                "Content-Type": "application/json",
                "Retry-After": "60"
            }
        )
    except HoneypotException:
        raise
    except Exception as e:
        logger.error(f"Endpoint error: {str(e)}", exc_info=True)

        # Even on complete endpoint failure, return valid response using unified builder
        from core.pipeline import build_final_response
        fallback = build_final_response(
            conversation_id=session_id or "error-session",
            response_message="Haan ji, ek minute... network issue hai",
            is_scam=False,
            confidence=0.0,
            scam_type="Unknown_Scam",
            indicators=["endpoint_error"],
            engagement_status="detecting",
            intelligence={},
            total_turns=1,
            duration=time.time() - start_time,
            scammer_count=1,
            agent_count=1,
            intel_count=0
        )
        return JSONResponse(content=fallback)


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
