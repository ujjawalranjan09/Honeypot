"""
Advanced Scam Detection Test Suite - V4.0
Validates detection of sophisticated 2024-2025 scam patterns:
- Pig Butchering (Romance + Investment)
- Honeytrap Video Call Sextortion
- AI Voice Cloning / Deepfake Emergency
- CEO/BEC Fraud
- Viral Video Link Malware
- TRAI/DND Deactivation Scam
"""
import requests
import json
import time

API_URL = "http://127.0.0.1:8000/api/message"
API_KEY = "your-secret-api-key-here"

advanced_scenarios = [
    # 1. Pig Butchering (Romance + Crypto Investment)
    {
        "name": "Pig Butchering (Romance)",
        "input": "Hey dear, I've been thinking about you since we matched. I know we haven't met, but I trust you. I am lonely here overseas as a widower. I want to share an investment opportunity with you - my crypto platform gives guaranteed returns. Can you invest $500 to start? I love you.",
        "expected_type": "Pig_Butchering_Scam",
        "expected_confidence": 0.9
    },
    # 2. Honeytrap Video Call Sextortion
    {
        "name": "Honeytrap Video Call",
        "input": "I have recorded you during our video call last night. I have screenshots of your nude and intimate moments. If you don't pay 50000 rupees, I will viral this to your contacts and share with friends and family. Your Facebook leak is ready.",
        "expected_type": "Honeytrap_Video_Sextortion",
        "expected_confidence": 0.95
    },
    # 3. AI Voice Cloning
    {
        "name": "AI Voice Cloning (Fake Son)",
        "input": "Mom help! Dad I need money urgently! I am in the hospital after an accident. I am in trouble with police custody. They are asking for bail money. Please send immediately to this account. Don't tell anyone about this.",
        "expected_type": "Voice_Cloning_Deepfake",
        "expected_confidence": 0.95
    },
    # 4. CEO/BEC Fraud
    {
        "name": "CEO/Boss Fraud",
        "input": "Hi, this is your CEO. I am in a meeting right now and can't call. I need you to handle this personally and do not discuss with anyone. There is a confidential transaction - an urgent wire transfer of $12,000 to this vendor payment account. Reply to my personal email.",
        "expected_type": "CEO_BEC_Fraud",
        "expected_confidence": 0.9
    },
    # 5. Viral Video Link Malware
    {
        "name": "Viral Link Malware",
        "input": "OMG! Have you seen this? Your 7 minute viral video is everywhere! This is shocking video! You are in this video, everyone is watching it. Click this link to see who viewed your profile: bit.ly/see-video-now",
        "expected_type": "Viral_Link_Malware",
        "expected_confidence": 0.85
    },
    # 6. TRAI/DND Scam
    {
        "name": "TRAI/DND Simulator",
        "input": "This call is from TRAI Telecom Department. Your mobile number will be disconnected within 24 hours due to regulatory compliance violations. Your DND was activated using fraudulent means. Press 1 to speak to an officer or your SIM will be deactivated.",
        "expected_type": "TRAI_DND_Scam",
        "expected_confidence": 0.85
    },
    # 7. FedEx/Courier Digital Arrest (Existing but rechecking)
    {
        "name": "FedEx Courier Scam",
        "input": "This is a call from FedEx courier. A parcel registered to your Aadhaar number was intercepted at Mumbai customs. It contains illegal drugs and banned items. We are transferring you to the Mumbai Police Cyber Cell. Your arrest warrant is ready. Stay on the line.",
        "expected_type": "Digital_Arrest_Scam",
        "expected_confidence": 0.95
    }
]

def run_advanced_tests():
    print("=" * 80)
    print("🔬 ADVANCED SCAM DETECTION TEST SUITE - V4.0 (2024-2025 Threats)")
    print("=" * 80)
    
    results = {"passed": 0, "failed": 0, "details": []}
    
    for scenario in advanced_scenarios:
        print(f"\n[TEST] {scenario['name']}")
        print(f"       Input: \"{scenario['input'][:65]}...\"")
        
        payload = {
            "sessionId": f"v4-test-{int(time.time())}-{scenario['name'][:3]}",
            "message": {
                "sender": "scammer",
                "text": scenario["input"],
                "timestamp": "2026-02-03T02:00:00Z"
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
                bot_reply = data.get("agentResponse", {}).get("responseText", "")[:60]
                
                type_match = scam_type == scenario["expected_type"]
                conf_match = confidence >= scenario["expected_confidence"]
                
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
    print(f"📊 SUMMARY: {results['passed']}/{len(advanced_scenarios)} PASSED")
    print("=" * 80)
    for d in results["details"]:
        status_icon = "✅" if d["status"] == "PASS" else ("⚠️" if d["status"] == "WRONG_TYPE" else "❌")
        extra = f" (Expected: {d.get('expected')}, Got: {d.get('got')})" if d["status"] == "WRONG_TYPE" else ""
        print(f"  {status_icon} {d['name']}{extra}")
    
    return results

if __name__ == "__main__":
    run_advanced_tests()
