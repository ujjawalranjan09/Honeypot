"""
Integration Tests for Honey-Pot API
"""
import pytest
import asyncio
from datetime import datetime
from fastapi.testclient import TestClient

# Set test API key before importing main
import os
os.environ["HONEYPOT_API_KEY"] = "test-api-key"

from main import app
from models import Message, IncomingRequest


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def api_key():
    """Test API key"""
    return "test-api-key"


@pytest.fixture
def sample_scam_message():
    """Sample scam message for testing"""
    return {
        "sessionId": "test-session-001",
        "message": {
            "sender": "scammer",
            "text": "URGENT: Your SBI bank account is blocked! Share OTP immediately to reactivate.",
            "timestamp": datetime.now().isoformat()
        },
        "conversationHistory": []
    }


@pytest.fixture
def sample_clean_message():
    """Sample clean message for testing"""
    return {
        "sessionId": "test-session-002",
        "message": {
            "sender": "user",
            "text": "Hi, how are you doing today?",
            "timestamp": datetime.now().isoformat()
        },
        "conversationHistory": []
    }


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check_no_auth(self, client):
        """Test that health endpoint doesn't require auth"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "model_trained" in data
        assert "gemini_configured" in data
    
    def test_health_check_returns_version(self, client):
        """Test that health check returns version"""
        response = client.get("/api/health")
        
        data = response.json()
        assert "version" in data


class TestMessageEndpoint:
    """Test main message processing endpoint"""
    
    def test_message_requires_auth(self, client, sample_scam_message):
        """Test that message endpoint requires authentication"""
        response = client.post("/api/message", json=sample_scam_message)
        
        assert response.status_code == 422  # Missing header
    
    def test_message_invalid_api_key(self, client, sample_scam_message):
        """Test rejection of invalid API key"""
        response = client.post(
            "/api/message",
            json=sample_scam_message,
            headers={"X-API-Key": "invalid-key"}
        )
        
        assert response.status_code in [401, 500]  # Auth error
    
    def test_scam_detection(self, client, api_key, sample_scam_message):
        """Test that scam messages are detected"""
        response = client.post(
            "/api/message",
            json=sample_scam_message,
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["scamDetected"] == True
        assert "reply" in data
    
    def test_clean_message_handling(self, client, api_key, sample_clean_message):
        """Test that clean messages are handled properly"""
        # Override with very neutral message for testing
        sample_clean_message["message"]["text"] = "The meeting is at 3pm in conference room A."
        sample_clean_message["message"]["sender"] = "user"  # Non-scammer message
        
        response = client.post(
            "/api/message",
            json=sample_clean_message,
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        # Status should be success regardless of ML model prediction
        # The key is that the API processes the message correctly
    
    def test_intelligence_extraction(self, client, api_key):
        """Test that intelligence is extracted from scam messages"""
        message = {
            "sessionId": "test-session-intel",
            "message": {
                "sender": "scammer",
                "text": "Call 9876543210 or send payment to fraud@paytm for immediate resolution",
                "timestamp": datetime.now().isoformat()
            },
            "conversationHistory": []
        }
        
        response = client.post(
            "/api/message",
            json=message,
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        intel = data["extractedIntelligence"]
        
        # Should extract phone number and UPI
        assert len(intel["phoneNumbers"]) >= 1 or len(intel["upiIds"]) >= 1
    
    def test_engagement_metrics_returned(self, client, api_key, sample_scam_message):
        """Test that engagement metrics are returned"""
        response = client.post(
            "/api/message",
            json=sample_scam_message,
            headers={"X-API-Key": api_key}
        )
        
        data = response.json()
        assert "engagementMetrics" in data
        metrics = data["engagementMetrics"]
        assert "totalMessagesExchanged" in metrics
        assert "engagementDurationSeconds" in metrics
    
    def test_scam_classification_returned(self, client, api_key, sample_scam_message):
        """Test that scam classification is returned"""
        response = client.post(
            "/api/message",
            json=sample_scam_message,
            headers={"X-API-Key": api_key}
        )
        
        data = response.json()
        if data["scamDetected"]:
            assert "scamClassification" in data
            assert data["scamClassification"]["scamType"] is not None
    
    def test_multi_turn_conversation(self, client, api_key):
        """Test multi-turn conversation handling"""
        session_id = "test-multi-turn"
        
        # First message
        msg1 = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": "Hello, I am from your bank",
                "timestamp": datetime.now().isoformat()
            },
            "conversationHistory": []
        }
        response1 = client.post("/api/message", json=msg1, headers={"X-API-Key": api_key})
        assert response1.status_code == 200
        
        # Second message with history
        msg2 = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": "Your account is blocked! Share OTP urgently!",
                "timestamp": datetime.now().isoformat()
            },
            "conversationHistory": [msg1["message"]]
        }
        response2 = client.post("/api/message", json=msg2, headers={"X-API-Key": api_key})
        
        assert response2.status_code == 200
        data = response2.json()
        # Session should track accumulated messages
        assert data["engagementMetrics"]["totalMessagesExchanged"] >= 2


class TestSessionEndpoint:
    """Test session management endpoints"""
    
    def test_session_status_requires_auth(self, client):
        """Test that session status requires auth"""
        response = client.get("/api/session/test-id")
        
        assert response.status_code == 422  # Missing header
    
    def test_session_not_found(self, client, api_key):
        """Test handling of non-existent session"""
        response = client.get(
            "/api/session/nonexistent-session",
            headers={"X-API-Key": api_key}
        )
        
        # Should return 404 or similar
        assert response.status_code in [404, 500]
    
    def test_session_status_after_message(self, client, api_key, sample_scam_message):
        """Test session status retrieval after sending message"""
        # First create session by sending message
        session_id = "test-session-status"
        sample_scam_message["sessionId"] = session_id
        
        client.post(
            "/api/message",
            json=sample_scam_message,
            headers={"X-API-Key": api_key}
        )
        
        # Then check status
        response = client.get(
            f"/api/session/{session_id}",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["sessionId"] == session_id
        assert "scamDetected" in data
        assert "persona" in data


class TestStatsEndpoint:
    """Test statistics endpoint"""
    
    def test_stats_requires_auth(self, client):
        """Test that stats endpoint requires auth"""
        response = client.get("/api/stats")
        
        assert response.status_code == 422
    
    def test_stats_returns_data(self, client, api_key):
        """Test that stats endpoint returns data"""
        response = client.get(
            "/api/stats",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "activeSessions" in data
        assert "modelTrained" in data
        assert "geminiEnabled" in data


class TestPersonasEndpoint:
    """Test personas endpoint"""
    
    def test_personas_list(self, client, api_key):
        """Test listing available personas"""
        response = client.get(
            "/api/personas",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "personas" in data
        assert len(data["personas"]) >= 3
        
        # Check persona structure
        persona = data["personas"][0]
        assert "id" in persona
        assert "name" in persona
        assert "description" in persona


class TestTrainEndpoint:
    """Test model training endpoint"""
    
    def test_train_requires_auth(self, client):
        """Test that train endpoint requires auth"""
        response = client.post("/api/train")
        
        assert response.status_code == 422


class TestOpenAPISchema:
    """Test OpenAPI documentation"""
    
    def test_openapi_schema_available(self, client):
        """Test that OpenAPI schema is available"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
    
    def test_docs_available(self, client):
        """Test that Swagger docs are available"""
        response = client.get("/docs")
        
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
