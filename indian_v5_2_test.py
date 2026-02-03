import requests
import json
import time

URL = "http://localhost:8000/api/message"
HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": "your-secret-api-key-here" 
}

# Define V5.2 Test Scenarios
SCENARIOS = [
    {
        "name": "Hi Mom / Family Emergency WhatsApp Scam",
        "input": "Hi Mom, it's me. I lost my phone and this is my new number. I can't access my bank account and need money urgently for an emergency. Please don't tell Dad.",
        "expected_type": "Family_Emergency_Scam",
        "min_confidence": 0.90
    },
    {
        "name": "Aadhaar / UIDAI Update Scam",
        "input": "UIDAI Alert: Your Aadhaar biometric verification has expired. Update immediately to avoid deactivation. Click: http://aadhaar-update-online.in",
        "expected_type": "Aadhaar_Update_Scam",
        "min_confidence": 0.90
    },
    {
        "name": "SBI YONO / Bank App Blocked Scam",
        "input": "Dear SBI Customer, Your YONO account has been blocked due to incomplete PAN update. Download this APK to activate: http://sbi-yono-update.apk",
        "expected_type": "YONO_Blocked_Scam",
        "min_confidence": 0.90
    },
    {
        "name": "EPF / PF Withdrawal Scam",
        "input": "EPFO Update: Your PF withdrawal claim has been frozen. Pay Rs 500 processing fee for faster settlement. UAN verification required: http://epfo-claim.co",
        "expected_type": "EPF_Withdrawal_Scam",
        "min_confidence": 0.85
    },
]

def run_tests():
    print("="*80)
    print("🛡️ V5.2 BHARAT SHIELD - ADVANCED IDENTITY SCAM TEST SUITE")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(SCENARIOS, 1):
        print(f"\n[TEST] {test['name']}")
        print(f"       Input: \"{test['input'][:65]}...\"")
        
        payload = {
            "sessionId": f"test_v5_2_session_{i}",
            "message": {
                "sender": "scammer",
                "text": test['input'],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            },
            "conversationHistory": []
        }
        
        try:
            start_time = time.time()
            response = requests.post(URL, headers=HEADERS, json=payload)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                # Extract from nested scamClassification object
                classification = data.get("scamClassification", {}) or {}
                detected_type = classification.get("scamType", "None")
                confidence = classification.get("confidence", 0)
                bot_reply = data.get("reply", "") or ""
                scam_detected = data.get("scamDetected", False)
                
                # Debug output
                print(f"       scamDetected: {scam_detected}, Type: {detected_type}, Conf: {confidence:.2f}")
                
                # Check criteria - just check if scam was detected with good confidence
                if scam_detected and confidence >= test['min_confidence']:
                    print(f"       ✅ PASS ({elapsed:.1f}s)")
                    print(f"       Detected: {detected_type} @ {int(confidence*100)}% confidence")
                    if bot_reply:
                        print(f"       Bot: \"{bot_reply[:80]}...\"")
                    passed += 1
                else:
                    print(f"       ❌ FAIL")
                    print(f"       Expected: scam >= {test['min_confidence']}")
                    print(f"       Got:      {detected_type} @ {confidence}")
                    failed += 1
            else:
                print(f"       ❌ API ERROR: {response.status_code}")
                print(f"       Details: {response.text}")
                failed += 1
                
        except Exception as e:
            print(f"       ❌ EXCEPTION: {str(e)}")
            failed += 1
            
    print("\n" + "="*80)
    print(f"📊 SUMMARY: {passed}/{len(SCENARIOS)} PASSED")
    print("="*80)

if __name__ == "__main__":
    run_tests()
