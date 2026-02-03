"""
V5.0 "Bharat Shield" Indian Environment Test Suite
Validates detection of niche but high-recall Indian scam patterns:
- Stock Market Trading Groups (WhatsApp/Fake Apps)
- Government Welfare (PM-Kisan, Ayushman Bharat)
- Online Rent / Security Deposit Fraud
- Free Recharge / Data Lures
- Election / Voter ID Mandatory Update
"""
import requests
import json
import time

API_URL = "http://127.0.0.1:8000/api/message"
API_KEY = "your-secret-api-key-here"

v5_scenarios = [
    # 1. Stock Market / Trading Group
    {
        "name": "Stock Market WhatsApp Group",
        "input": "Dear Investor, welcome to Adithya Birla Equity Learning Group. Our SEBI registered experts provide exclusive IPO tips and guaranteed stock returns of 500%. To withdraw your profits, pay a 10% withdrawal tax of 15,000 rupees to this UPI ID.",
        "expected_type": "Stock_Market_Fraud",
        "expected_confidence": 0.98
    },
    # 2. Government Welfare (PM-Kisan)
    {
        "name": "PM-Kisan Welfare Fraud",
        "input": "Kisan Samman Nidhi: Your PM Kisan installment of Rs 2000 is pending. To claim your bonus payment and govt subsidy, click this link to register and pay 50 rupees for eligibility check. Don't miss your sarkari yojana benefit.",
        "expected_type": "Welfare_Scheme_Fraud",
        "expected_confidence": 0.95
    },
    # 3. Online Rent / Security Deposit
    {
        "name": "Rent / Security Deposit Scam",
        "input": "Beautiful 2BHK flat in prime area for only 15k rent. To block property and get gate pass for visit, you must pay a security deposit / token amount of Rs 5000 via QR scan. This token is refundable after visit.",
        "expected_type": "Rent_Property_Fraud",
        "expected_confidence": 0.95
    },
    # 4. Free Recharge / Data
    {
        "name": "Free Recharge / Data Lure",
        "input": "Ram Mandir Free Recharge: Congratulations! You have won 3 months free recharge and 50GB data balance from Jio. Click this link to activate your free recharge offer immediately: bit.ly/free-jio-recharge",
        "expected_type": "Free_Recharge_Fraud",
        "expected_confidence": 0.90
    },
    # 5. Election / Voter ID Update
    {
        "name": "Election / Voter ID Fraud",
        "input": "Election Commission Notification: Mandatory update of your Voter ID card is required. Verify your name in the voter list to avoid deactivation. Click here to update your election card details on the govt portal kyc.",
        "expected_type": "Election_Voter_Fraud",
        "expected_confidence": 0.85
    }
]

def run_v5_tests():
    print("=" * 80)
    print("🛡️ V5.0 BHARAT SHIELD - INDIAN ENVIRONMENT TEST SUITE")
    print("=" * 80)
    
    results = {"passed": 0, "failed": 0, "details": []}
    
    for scenario in v5_scenarios:
        print(f"\n[TEST] {scenario['name']}")
        print(f"       Input: \"{scenario['input'][:65]}...\"")
        
        payload = {
            "sessionId": f"v5-test-{int(time.time())}-{scenario['name'][:3]}",
            "message": {
                "sender": "scammer",
                "text": scenario["input"],
                "timestamp": "2026-02-03T02:30:00Z"
            }
        }
        headers = {"X-API-Key": API_KEY}
        
        try:
            start = time.time()
            response = requests.post(API_URL, json=payload, headers=headers, timeout=120)
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                detected = data.get("scamDetected", False)
                scam_type = data.get("scamClassification", {}).get("scamType", "None")
                confidence = data.get("scamClassification", {}).get("confidence", 0)
                bot_reply = data.get("agentResponse", {}).get("responseText", "")[:70]
                
                type_match = scam_type == scenario["expected_type"]
                
                if detected and type_match:
                    print(f"       ✅ PASS ({duration:.1f}s)")
                    print(f"       Detected: {scam_type} @ {confidence:.0%} confidence")
                    print(f"       Bot: \"{bot_reply}...\"")
                    results["passed"] += 1
                    results["details"].append({"name": scenario["name"], "status": "PASS", "type": scam_type})
                elif detected and not type_match:
                    print(f"       ⚠️ PARTIAL (Wrong Type)")
                    print(f"       Expected: {scenario['expected_type']}, Got: {scam_type}")
                    results["failed"] += 1
                    results["details"].append({"name": scenario["name"], "status": "WRONG_TYPE", "expected": scenario["expected_type"], "got": scam_type})
                else:
                    print(f"       ❌ FAIL (Not Detected)")
                    results["failed"] += 1
                    results["details"].append({"name": scenario["name"], "status": "NOT_DETECTED"})
            else:
                print(f"       ❌ API Error: {response.status_code}")
                results["failed"] += 1
        except Exception as e:
            print(f"       ❌ Exception: {str(e)}")
            results["failed"] += 1
    
    # Summary
    print("\n" + "=" * 80)
    print(f"📊 SUMMARY: {results['passed']}/{len(v5_scenarios)} PASSED")
    print("=" * 80)
    for d in results["details"]:
        status_icon = "✅" if d["status"] == "PASS" else ("⚠️" if d["status"] == "WRONG_TYPE" else "❌")
        extra = f" (Expected: {d.get('expected')}, Got: {d.get('got')})" if d["status"] == "WRONG_TYPE" else ""
        print(f"  {status_icon} {d['name']}{extra}")
    
    return results

if __name__ == "__main__":
    run_v5_tests()
