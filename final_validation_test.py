"""
Final End-to-End Validation Test for GUVI Hackathon
Tests all requirements from the problem statement
"""
import requests
import json
from datetime import datetime, timezone
import time

API_URL = "http://127.0.0.1:8000"
API_KEY = "YOUR_SECRET_API_KEY"

def test_health():
    """Test 1: Health endpoint"""
    print("=" * 60)
    print("TEST 1: Health Check")
    print("=" * 60)
    
    response = requests.get(f"{API_URL}/api/health")
    if response.status_code == 200:
        data = response.json()
        print(f"  Status: {data.get('status')}")
        print(f"  Model Trained: {data.get('model_trained')}")
        print(f"  AI Configured: {data.get('gemini_configured')}")
        print(f"  RESULT: PASS")
        return True
    else:
        print(f"  RESULT: FAIL - Status {response.status_code}")
        return False

def test_api_auth():
    """Test 2: API Key Authentication"""
    print("\n" + "=" * 60)
    print("TEST 2: API Key Authentication")
    print("=" * 60)
    
    # Without key
    response = requests.post(f"{API_URL}/api/message", json={})
    if response.status_code == 422:
        print("  Without key: Correctly rejected (422)")
    
    # With wrong key
    response = requests.post(
        f"{API_URL}/api/message",
        json={"sessionId": "test", "message": {"sender": "scammer", "text": "test", "timestamp": datetime.now(timezone.utc).isoformat()}},
        headers={"X-API-Key": "wrong-key"}
    )
    if response.status_code in [401, 500]:
        print("  Wrong key: Correctly rejected")
        print(f"  RESULT: PASS")
        return True
    
    print(f"  RESULT: FAIL")
    return False

def test_scam_detection():
    """Test 3: Scam Detection"""
    print("\n" + "=" * 60)
    print("TEST 3: Scam Detection")
    print("=" * 60)
    
    payload = {
        "sessionId": f"e2e-test-{int(time.time())}",
        "message": {
            "sender": "scammer",
            "text": "URGENT: Your SBI account is blocked! Share OTP 123456 to reactivate. Call +91-9876543210 or pay Rs 500 to unblock@upi",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "Hinglish",
            "locale": "IN"
        }
    }
    
    response = requests.post(
        f"{API_URL}/api/message",
        json=payload,
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"  Scam Detected: {data.get('scamDetected')}")
        print(f"  Status: {data.get('status')}")
        
        classification = data.get('scamClassification', {})
        print(f"  Scam Type: {classification.get('scamType')}")
        print(f"  Confidence: {classification.get('confidence')}")
        
        if data.get('scamDetected'):
            print(f"  RESULT: PASS")
            return True
    
    print(f"  RESULT: FAIL")
    return False

def test_agent_response():
    """Test 4: AI Agent Response"""
    print("\n" + "=" * 60)
    print("TEST 4: AI Agent Response (reply field)")
    print("=" * 60)
    
    payload = {
        "sessionId": f"e2e-agent-{int(time.time())}",
        "message": {
            "sender": "scammer",
            "text": "Hello, I am Inspector Kumar from CBI. Your Aadhaar is linked to money laundering case. Send Rs 50000 to avoid arrest.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "conversationHistory": [],
        "metadata": {"channel": "WhatsApp", "language": "Hinglish", "locale": "IN"}
    }
    
    start = time.time()
    response = requests.post(
        f"{API_URL}/api/message",
        json=payload,
        headers={"X-API-Key": API_KEY},
        timeout=60
    )
    duration = time.time() - start
    
    if response.status_code == 200:
        data = response.json()
        reply = data.get('reply')
        
        print(f"  Response Time: {duration:.2f}s")
        print(f"  Has 'reply' field: {reply is not None}")
        if reply:
            print(f"  Reply Preview: \"{reply[:80]}...\"")
        print(f"  Agent Notes: {data.get('agentNotes', 'N/A')[:60]}...")
        
        if reply and len(reply) > 10:
            print(f"  RESULT: PASS")
            return True
    
    print(f"  RESULT: FAIL")
    return False

def test_intelligence_extraction():
    """Test 5: Intelligence Extraction"""
    print("\n" + "=" * 60)
    print("TEST 5: Intelligence Extraction")
    print("=" * 60)
    
    payload = {
        "sessionId": f"e2e-intel-{int(time.time())}",
        "message": {
            "sender": "scammer",
            "text": "Send payment to UPI: fraud@paytm or bank account 1234567890123456 IFSC HDFC0001234. Call +91-8899776655. Visit http://fake-bank.xyz/verify",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "conversationHistory": [],
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
    }
    
    response = requests.post(
        f"{API_URL}/api/message",
        json=payload,
        headers={"X-API-Key": API_KEY},
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        intel = data.get('extractedIntelligence', {})
        
        print(f"  UPI IDs: {intel.get('upiIds', [])}")
        print(f"  Bank Accounts: {intel.get('bankAccounts', [])}")
        print(f"  Phone Numbers: {intel.get('phoneNumbers', [])}")
        print(f"  Phishing Links: {intel.get('phishingLinks', [])}")
        print(f"  Keywords: {intel.get('suspiciousKeywords', [])[:5]}")
        
        # Check if at least some intelligence was extracted
        total_intel = (
            len(intel.get('upiIds', [])) +
            len(intel.get('phoneNumbers', [])) +
            len(intel.get('phishingLinks', [])) +
            len(intel.get('bankAccounts', []))
        )
        
        if total_intel >= 2:
            print(f"  Total Items Extracted: {total_intel}")
            print(f"  RESULT: PASS")
            return True
    
    print(f"  RESULT: FAIL")
    return False

def test_multi_turn():
    """Test 6: Multi-Turn Conversation"""
    print("\n" + "=" * 60)
    print("TEST 6: Multi-Turn Conversation")
    print("=" * 60)
    
    session_id = f"e2e-multiturn-{int(time.time())}"
    history = []
    
    messages = [
        "Hello, I am from SBI bank security team.",
        "Your account has suspicious transaction. Verify now!",
        "Send Rs 1000 to security@upi to unfreeze account."
    ]
    
    for i, msg_text in enumerate(messages):
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": msg_text,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "conversationHistory": history,
            "metadata": {"channel": "SMS", "language": "Hinglish", "locale": "IN"}
        }
        
        response = requests.post(
            f"{API_URL}/api/message",
            json=payload,
            headers={"X-API-Key": API_KEY},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            reply = data.get('reply', '')
            metrics = data.get('engagementMetrics', {})
            
            print(f"  Turn {i+1}: Messages={metrics.get('totalMessagesExchanged')}, Phase={metrics.get('currentPhase')}")
            
            # Add to history
            history.append({"sender": "scammer", "text": msg_text, "timestamp": datetime.now(timezone.utc).isoformat()})
            if reply:
                history.append({"sender": "user", "text": reply, "timestamp": datetime.now(timezone.utc).isoformat()})
        else:
            print(f"  Turn {i+1}: FAILED - {response.status_code}")
            print(f"  RESULT: FAIL")
            return False
    
    # Check final metrics
    final_metrics = data.get('engagementMetrics', {})
    if final_metrics.get('totalMessagesExchanged', 0) >= 3:
        print(f"  Final Message Count: {final_metrics.get('totalMessagesExchanged')}")
        print(f"  Engagement Duration: {final_metrics.get('engagementDurationSeconds')}s")
        print(f"  RESULT: PASS")
        return True
    
    print(f"  RESULT: FAIL")
    return False

def test_response_structure():
    """Test 7: Response Structure Validation"""
    print("\n" + "=" * 60)
    print("TEST 7: Response Structure (All Required Fields)")
    print("=" * 60)
    
    payload = {
        "sessionId": f"e2e-structure-{int(time.time())}",
        "message": {
            "sender": "scammer",
            "text": "You won lottery! Pay Rs 5000 to collect Rs 50 lakh prize. UPI: lottery@ybl",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "conversationHistory": [],
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
    }
    
    response = requests.post(
        f"{API_URL}/api/message",
        json=payload,
        headers={"X-API-Key": API_KEY},
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        
        required_fields = [
            'status',
            'scamDetected',
            'reply',
            'engagementMetrics',
            'extractedIntelligence'
        ]
        
        missing = [f for f in required_fields if f not in data]
        
        print(f"  Status: {data.get('status')}")
        print(f"  Has 'reply': {'reply' in data}")
        print(f"  Has 'scamDetected': {'scamDetected' in data}")
        print(f"  Has 'engagementMetrics': {'engagementMetrics' in data}")
        print(f"  Has 'extractedIntelligence': {'extractedIntelligence' in data}")
        
        if not missing:
            print(f"  All required fields present!")
            print(f"  RESULT: PASS")
            return True
        else:
            print(f"  Missing fields: {missing}")
    
    print(f"  RESULT: FAIL")
    return False

def main():
    print("\n")
    print("=" * 60)
    print("   FINAL END-TO-END VALIDATION TEST")
    print("   GUVI Honeypot Hackathon")
    print("=" * 60)
    print(f"   Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    results = {
        "Health Check": test_health(),
        "API Authentication": test_api_auth(),
        "Scam Detection": test_scam_detection(),
        "AI Agent Response": test_agent_response(),
        "Intelligence Extraction": test_intelligence_extraction(),
        "Multi-Turn Conversation": test_multi_turn(),
        "Response Structure": test_response_structure(),
    }
    
    print("\n")
    print("=" * 60)
    print("   FINAL RESULTS")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "PASS" if result else "FAIL"
        icon = "[OK]" if result else "[X]"
        print(f"  {icon} {test}: {status}")
    
    print("=" * 60)
    print(f"   SCORE: {passed}/{total} tests passed")
    
    if passed == total:
        print("   STATUS: READY FOR SUBMISSION!")
    else:
        print("   STATUS: SOME TESTS FAILED")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    main()
