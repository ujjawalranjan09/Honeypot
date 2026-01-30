"""Quick test script with detailed output"""
import requests
import json

BASE_URL = "http://localhost:8000"
API_KEY = "your-secret-api-key-here"

def test_api():
    # Test health
    print("=" * 60)
    print("🏥 Testing health endpoint...")
    r = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
    print()

    # Test scam message
    print("=" * 60)
    print("🚨 Testing scam detection (banking fraud)...")
    payload = {
        "sessionId": "test-session-001",
        "message": {
            "sender": "scammer",
            "text": "Your bank account will be blocked today. Verify immediately at www.bank-secure.com",
            "timestamp": "2026-01-29T10:15:30Z"
        },
        "conversationHistory": [],
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
    }

    r = requests.post(
        f"{BASE_URL}/api/message",
        headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
        json=payload
    )
    print(f"Status: {r.status_code}")
    result = r.json()
    print(f"Scam Detected: {result['scamDetected']}")
    print(f"Agent Response: {result.get('agentResponse', 'N/A')}")
    print(f"Intelligence: {json.dumps(result['extractedIntelligence'], indent=2)}")
    print()

    # Test follow-up
    print("=" * 60)
    print("📨 Testing follow-up message...")
    payload2 = {
        "sessionId": "test-session-001",
        "message": {
            "sender": "scammer",
            "text": "Share your UPI ID to avoid suspension. Call +91-9876543210 urgently!",
            "timestamp": "2026-01-29T10:17:30Z"
        },
        "conversationHistory": [
            {"sender": "scammer", "text": "Your bank account will be blocked today.", "timestamp": "2026-01-29T10:15:30Z"},
            {"sender": "user", "text": "Oh dear, what happened?", "timestamp": "2026-01-29T10:16:30Z"}
        ],
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
    }

    r = requests.post(
        f"{BASE_URL}/api/message",
        headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
        json=payload2
    )
    print(f"Status: {r.status_code}")
    result = r.json()
    print(f"Scam Detected: {result['scamDetected']}")
    print(f"Agent Response: {result.get('agentResponse', 'N/A')}")
    print(f"Messages Exchanged: {result['engagementMetrics']['totalMessagesExchanged']}")
    print(f"Phone Numbers Found: {result['extractedIntelligence']['phoneNumbers']}")
    print()

    # Test Hindi message
    print("=" * 60)
    print("🇮🇳 Testing Hindi scam message...")
    payload3 = {
        "sessionId": "test-session-003",
        "message": {
            "sender": "scammer",
            "text": "आपका बैंक खाता आज ब्लॉक हो जाएगा। तुरंत सत्यापित करें www.bank-verify.com",
            "timestamp": "2026-01-29T10:15:30Z"
        },
        "conversationHistory": [],
        "metadata": {"channel": "SMS", "language": "Hindi", "locale": "IN"}
    }

    r = requests.post(
        f"{BASE_URL}/api/message",
        headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
        json=payload3
    )
    print(f"Status: {r.status_code}")
    result = r.json()
    print(f"Scam Detected: {result['scamDetected']}")
    print(f"Agent Response: {result.get('agentResponse', 'N/A')}")
    print()

    # Test legitimate message
    print("=" * 60)
    print("✅ Testing legitimate message...")
    payload4 = {
        "sessionId": "test-session-004",
        "message": {
            "sender": "scammer",
            "text": "Hi! Hope you are doing well. Let me know when you are free for coffee.",
            "timestamp": "2026-01-29T10:15:30Z"
        },
        "conversationHistory": [],
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
    }

    r = requests.post(
        f"{BASE_URL}/api/message",
        headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
        json=payload4
    )
    print(f"Status: {r.status_code}")
    result = r.json()
    print(f"Scam Detected: {result['scamDetected']}")
    print(f"Agent Response: {result.get('agentResponse', 'N/A')}")
    print()

    # Test session status
    print("=" * 60)
    print("📊 Testing session status...")
    r = requests.get(
        f"{BASE_URL}/api/session/test-session-001",
        headers={"x-api-key": API_KEY}
    )
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
    print()

    # Test stats
    print("=" * 60)
    print("📈 Testing API stats...")
    r = requests.get(
        f"{BASE_URL}/api/stats",
        headers={"x-api-key": API_KEY}
    )
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
    
    print()
    print("=" * 60)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_api()
