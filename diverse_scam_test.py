"""
Comprehensive Diverse Scam Testing Script
Verifies: 
1. Customs/Narcotics (Digital Arrest)
2. Electricity Bill Disconnection
3. YouTube/Task Job Fraud
4. Sextortion/Blackmail
5. Crypto Investment Guru
"""
import requests
import time
import json

API_URL = "http://127.0.0.1:8000/api/message"
API_KEY = "your-secret-api-key-here"

scenarios = [
    {
        "name": "Customs/Narcotics (Digital Arrest)",
        "message": "This is Inspector Sharma from Mumbai Customs. We have intercepted a DHL package in your name containing MDMA drugs and 3 fake passports. You are under digital arrest. Connect on Skype immediately for verification.",
        "expected_type": "Digital_Arrest_Scam"
    },
    {
        "name": "Electricity Bill Threat",
        "message": "Dear Consumer, your electricity bill is unpaid. Power will be disconnected tonight at 10:00 PM by electricity office. Contact our SDO officer Mr. Gupta at 9876543210 immediately to avoid disconnection.",
        "expected_type": "Utility_Bill_Scam"
    },
    {
        "name": "YouTube Task/Job Fraud",
        "message": "Work from home opportunity! Earn 2000-5000 daily. Just like YouTube videos and send screenshots. No investment needed. Contact HR Priya on WhatsApp: https://wa.me/911234567890",
        "expected_type": "Job_Task_Scam"
    },
    {
        "name": "Sextortion/Blackmail",
        "message": "I have the video of you from last night. I will leak it to all your Facebook friends and family today. If you want me to delete it, pay 50,000 INR to this UPI: blackmail@okaxis. Don't try to be smart.",
        "expected_type": "Sextortion_Blackmail"
    },
    {
        "name": "Crypto/Investment Guru",
        "message": "I am a professional crypto trader. I can double your investment in 24 hours using private signals on Binance. Just send 500 USDT to my wallet and see the profit. 100% guaranteed returns.",
        "expected_type": "Crypto_Investment_Scam"
    }
]

print("="*70)
print("🚀 STARTING DIVERSE SCAM MARATHON TEST")
print("="*70)

results = []

for scenario in scenarios:
    print(f"\n[Test] Scenario: {scenario['name']}")
    print(f"      Input: \"{scenario['message'][:60]}...\"")
    
    payload = {
        "sessionId": f"marathon-{int(time.time())}-{scenario['name'][:3]}",
        "message": {
            "sender": "scammer",
            "text": scenario['message'],
            "timestamp": "2026-02-03T01:35:00+05:30"
        },
        "conversationHistory": [],
        "metadata": {"channel": "WhatsApp", "language": "en", "locale": "IN"}
    }
    
    try:
        start_time = time.time()
        resp = requests.post(API_URL, json=payload, headers={"X-API-Key": API_KEY}, timeout=90)
        duration = time.time() - start_time
        
        if resp.status_code == 200:
            data = resp.json()
            is_scam = data.get('scamDetected', False)
            detected_type = data.get('scamClassification', {}).get('scamType', 'Unknown')
            reply = data.get('reply', '[No Reply]')
            
            print(f"      ✅ Success ({duration:.1f}s)")
            print(f"      Detection: {is_scam} ({detected_type})")
            print(f"      Bot Reply: \"{reply[:70]}...\"")
            
            results.append({
                "scenario": scenario['name'],
                "is_scam": is_scam,
                "detected_type": detected_type,
                "bot_reply": reply,
                "status": "PASS" if is_scam else "FAIL"
            })
        else:
            print(f"      ❌ Error: {resp.status_code} - {resp.text}")
            results.append({"scenario": scenario['name'], "status": f"ERROR: {resp.status_code}"})
            
    except Exception as e:
        print(f"      ❌ Exception: {e}")
        results.append({"scenario": scenario['name'], "status": f"EXCEPTION: {e}"})

print("\n" + "="*70)
print("📊 MARATHON SUMMARY")
print("="*70)
for r in results:
    print(f"{r['scenario']:<30} | {r.get('status', 'ERROR'):<10} | Type: {r.get('detected_type', 'N/A')}")
print("="*70)
