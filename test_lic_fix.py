"""Quick LIC Scam Test - Verifies the fix for [No response] issue"""
import requests
import time

API_URL = "http://127.0.0.1:8000/api/message"
API_KEY = "your-secret-api-key-here"

test_messages = [
    "Congratulations! Aapki LIC policy ka bonus Rs 2,50,000 approve ho gaya hai!",
    "Ye special COVID relief scheme hai, sirf 48 hours mein expire ho jayega.",
]

print("="*60)
print("   LIC SCAM FIX VERIFICATION TEST")
print("="*60)

for msg in test_messages:
    print(f"\n[Test] Input: \"{msg[:50]}...\"")
    
    payload = {
        "sessionId": f"lic-test-{int(time.time())}",
        "message": {
            "sender": "scammer",
            "text": msg,
            "timestamp": "2026-02-03T01:15:00+05:30"
        },
        "conversationHistory": [],
        "metadata": {"channel": "SMS", "language": "hi", "locale": "IN"}
    }
    
    try:
        start = time.time()
        resp = requests.post(API_URL, json=payload, headers={"X-API-Key": API_KEY}, timeout=60)
        latency = (time.time() - start) * 1000
        
        data = resp.json()
        reply = data.get('reply', '[No Reply]')
        detected = data.get('scamDetected', False)
        
        print(f"   > Status: {resp.status_code}")
        print(f"   > Latency: {latency:.0f}ms")
        print(f"   > Detected: {detected}")
        print(f"   > Reply: \"{reply[:60] if reply else '[None]'}...\"")
        
        if reply and reply != '[No Reply]':
            print("   > RESULT: ✅ PASS")
        else:
            print("   > RESULT: ❌ FAIL (No response)")
            
    except Exception as e:
        print(f"   > ERROR: {e}")

print("\n" + "="*60)
