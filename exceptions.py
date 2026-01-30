"""
Custom Exception Classes for Honey-Pot API
Provides structured error handling with specific error codes
"""
from typing import Optional, Dict, Any


class HoneypotException(Exception):
    """Base exception for all honeypot errors"""
    
    error_code: str = "HONEYPOT_ERROR"
    status_code: int = 500
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.error_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ScamDetectionError(HoneypotException):
    """Errors during scam detection process"""
    error_code = "SCAM_DETECTION_ERROR"
    status_code = 500


class ModelNotTrainedError(ScamDetectionError):
    """ML model not trained or not available"""
    error_code = "MODEL_NOT_TRAINED"
    
    def __init__(self, message: str = "Scam detection model is not trained"):
        super().__init__(message)


class ModelPredictionError(ScamDetectionError):
    """Error during ML model prediction"""
    error_code = "MODEL_PREDICTION_ERROR"


class IntelligenceExtractionError(HoneypotException):
    """Errors during intelligence extraction"""
    error_code = "INTELLIGENCE_EXTRACTION_ERROR"
    status_code = 500


class PatternExtractionError(IntelligenceExtractionError):
    """Error extracting specific pattern (regex, NER)"""
    error_code = "PATTERN_EXTRACTION_ERROR"


class SessionManagementError(HoneypotException):
    """Errors in session handling"""
    error_code = "SESSION_ERROR"
    status_code = 500


class SessionNotFoundError(SessionManagementError):
    """Session ID not found"""
    error_code = "SESSION_NOT_FOUND"
    status_code = 404
    
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session not found: {session_id}",
            details={"session_id": session_id}
        )


class SessionExpiredError(SessionManagementError):
    """Session has expired"""
    error_code = "SESSION_EXPIRED"
    status_code = 410
    
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session has expired: {session_id}",
            details={"session_id": session_id}
        )


class SessionLimitError(SessionManagementError):
    """Session limit exceeded"""
    error_code = "SESSION_LIMIT_EXCEEDED"
    status_code = 429


class CallbackError(HoneypotException):
    """Errors during GUVI callback"""
    error_code = "CALLBACK_ERROR"
    status_code = 500


class CallbackTimeoutError(CallbackError):
    """Callback request timed out"""
    error_code = "CALLBACK_TIMEOUT"


class CallbackRetryExhaustedError(CallbackError):
    """All retry attempts for callback exhausted"""
    error_code = "CALLBACK_RETRY_EXHAUSTED"
    
    def __init__(self, session_id: str, attempts: int):
        super().__init__(
            message=f"Callback failed after {attempts} attempts for session: {session_id}",
            details={"session_id": session_id, "attempts": attempts}
        )


class AgentError(HoneypotException):
    """Errors in AI agent processing"""
    error_code = "AGENT_ERROR"
    status_code = 500


class GeminiAPIError(AgentError):
    """Error from Gemini API"""
    error_code = "GEMINI_API_ERROR"


class PersonaNotFoundError(AgentError):
    """Requested persona not found"""
    error_code = "PERSONA_NOT_FOUND"
    status_code = 404


class ResponseGenerationError(AgentError):
    """Failed to generate response"""
    error_code = "RESPONSE_GENERATION_ERROR"


class ResponseValidationError(AgentError):
    """Generated response failed validation"""
    error_code = "RESPONSE_VALIDATION_ERROR"


class ValidationError(HoneypotException):
    """Input validation errors"""
    error_code = "VALIDATION_ERROR"
    status_code = 400


class InvalidAPIKeyError(ValidationError):
    """Invalid or missing API key"""
    error_code = "INVALID_API_KEY"
    status_code = 401


class RateLimitError(HoneypotException):
    """Rate limit exceeded"""
    error_code = "RATE_LIMIT_EXCEEDED"
    status_code = 429
    
    def __init__(self, retry_after: Optional[int] = None):
        super().__init__(
            message="Rate limit exceeded. Please slow down.",
            details={"retry_after_seconds": retry_after} if retry_after else {}
        )


class DatabaseError(HoneypotException):
    """Database operation errors"""
    error_code = "DATABASE_ERROR"
    status_code = 500


class ConfigurationError(HoneypotException):
    """Configuration/setup errors"""
    error_code = "CONFIGURATION_ERROR"
    status_code = 500
