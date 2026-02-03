"""
Indian Environment Refining Test - V3.5
Verifies specialized Indian scam patterns (RTO, SIM Swap, QR Code, Loan Apps)
"""
import requests
import json
import time

API_URL = "http://127.0.0.1:8000/api/message"
API_KEY = "your-secret-api-key-here"

scenarios = [
    {
        "name": "RTO/Traffic Fine",
        "input": "Dear Citizen, a traffic challan has been issued against vehicle MH12AB1234. Unpaid fine of Rs 2500. Pay immediately at bit.ly/rto-pay or your license will be blocked.",
        "expected_type": "Utility_Bill_Scam",
        "expect_vehicle": "MH12AB1234"
    },
    {
        "name": "SIM Swap/5G Upgrade",
        "input": "Airtel Customer Care: Your 4G SIM will be deactivated today. To upgrade to 5G for free, please share your eSIM activation code or scan the QR code sent on your email. Agent ID: AR7742.",
        "expected_type": "General_Scam",
        "expect_emp_id": "AR7742"
    },
    {
        "name": "OLX/QR Scam",
        "input": "I am interested in your sofa set on OLX. I am sending you a QR code for Rs 15,000. Just scan it to receive the payment into your bank account immediately.",
        "expected_type": "Marketplace_Fraud"
    },
    {
        "name": "Predatory Loan App",
        "input": "URGENT: Your Instant Loan of Rs 50,000 is approved. No documents needed. Just download our app and give contacts/gallery access to get credit. Hurry, offer expires in 2 hours!",
        "expected_type": "Loan_Fraud"
    }
]

def test_scenarios():
    print("="*70)
    print("🚀 STARTING INDIAN ENVIRONMENT REFINEMENT TEST")
    print("="*70)
    
    for scenario in scenarios:
        print(f"\n[Test] Scenario: {scenario['name']}")
        print(f"      Input: \"{scenario['input'][:60]}...\"")
        
        payload = {
            "sessionId": f"refine-test-{int(time.time())}",
            "message": {
                "sender": "scammer",
                "text": scenario["input"],
                "timestamp": "2026-02-03T01:50:00Z"
            }
        }
        
        headers = {"X-API-Key": API_KEY}
        
        try:
            start_time = time.time()
            response = requests.post(API_URL, json=payload, headers=headers)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                detection = data.get("scamDetected", False)
                scam_type = data.get("scamClassification", {}).get("scamType", "None")
                intel = data.get("extractedIntelligence", {})
                
                # Check specifics
                vehicle_found = scenario.get("expect_vehicle") in str(intel.get("vehicleNumbers", [])) if scenario.get("expect_vehicle") else True
                emp_id_found = scenario.get("expect_emp_id") in str(intel.get("employeeIds", [])) if scenario.get("expect_emp_id") else True
                
                if detection and scam_type == scenario["expected_type"] and vehicle_found and emp_id_found:
                    print(f"      ✅ Success ({duration:.1f}s)")
                    print(f"      Detection: {detection} ({scam_type})")
                    if scenario.get("expect_vehicle"): print(f"      Vehicle Extracted: {intel.get('vehicleNumbers')}")
                    if scenario.get("expect_emp_id"): print(f"      Emp ID Extracted: {intel.get('employeeIds')}")
                else:
                    print(f"      ❌ Failed Validation")
                    print(f"      Detected: {detection}, Type: {scam_type}")
                    print(f"      Intel: {intel}")
            else:
                print(f"      ❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"      ❌ Exception: {str(e)}")
            
    print("\n" + "="*70)

if __name__ == "__main__":
    test_scenarios()
