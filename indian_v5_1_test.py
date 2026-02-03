import requests
import json
import time

URL = "http://localhost:8000/api/message"
HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": "your-secret-api-key-here" 
}

# Define V5.1 Test Scenarios
SCENARIOS = [
    {
        "name": "Credit Card Reward Points Scam",
        "input": "Dear Customer, Your HDFC Bank Reward Points of Rs 5990 will expire today. Redeem now into cash by clicking http://hdfc-redeem-points.com - HDFC Bank",
        "expected_type": "Credit_Card_Rewards_Scam",
        "min_confidence": 0.95
    },
    {
        "name": "FASTag KYC Update Scam",
        "input": "Alert: Your FASTag wallet has been blocked/deactivated due to incomplete KYC. Update immediately to avoid penalty: http://fastag-kyc-update.cn/ - NHAI",
        "expected_type": "FASTag_KYC_Fraud",
        "min_confidence": 0.95
    },
    {
        "name": "Income Tax Refund Phishing",
        "input": "IT Dept: An Income Tax Refund of Rs 15,400 has been approved. Your account number is incorrect. Update bank details to claim: http://incometax-refund-claim.org",
        "expected_type": "Income_Tax_Refund_Scam",
        "min_confidence": 0.98
    },
    {
        "name": "Ram Mandir / Religious VIP Scam",
        "input": "Jai Shri Ram! Special VIP Darshan passes available for Ayodhya Ram Mandir. Skip the queue and get Prasad home delivered. Book now: http://ayodhya-vip-pass.in",
        "expected_type": "Religious_Donation_Scam",
        "min_confidence": 0.90
    }
]

def run_tests():
    print("="*80)
    print("🛡️ V5.1 BHARAT SHIELD - EXTENDED ENVIRONMENT TEST SUITE")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for test in SCENARIOS:
        print(f"\n[TEST] {test['name']}")
        print(f"       Input: \"{test['input'][:65]}...\"")
        
        payload = {
            "sessionId": "test_v5_1_session",
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
                print(f"       scamDetected: {scam_detected}, Type: {detected_type}, Conf: {confidence}")
                
                # Check criteria
                type_match = detected_type == test['expected_type']
                conf_match = confidence >= test['min_confidence']
                
                if type_match and conf_match:
                    print(f"       ✅ PASS ({elapsed:.1f}s)")
                    print(f"       Detected: {detected_type} @ {int(confidence*100)}% confidence")
                    if bot_reply:
                        print(f"       Bot: \"{bot_reply[:80]}...\"")
                    passed += 1
                else:
                    print(f"       ❌ FAIL")
                    print(f"       Expected: {test['expected_type']} >= {test['min_confidence']}")
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
