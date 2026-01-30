"""
MASTER BENCHMARK SCRIPT
Runs a representative set of scenarios from all iterations and calculates final metrics.
"""
import time
import requests
import json
from datetime import datetime, timezone
import os
import pandas as pd

# --- CONFIGURATION ---
API_URL = os.getenv("HONEYPOT_API_URL", "http://localhost:8000")
API_KEY = os.getenv("HONEYPOT_API_KEY", "YOUR_SECRET_API_KEY")

# Representative scenarios from all iterations
BENCHMARK_SCENARIOS = [
    # FROM V1
    {"name": "LIC Bonus Fraud", "locale": "IN", "language": "Hinglish", "type": "Insurance_Fraud", 
     "messages": ["Aapki LIC policy ka bonus Rs 2,50,000 approve ho gaya hai!", "Rs 1,500 GST pay karna hoga.", "UPI: lic.claims@ybl", "Jaldi karo, last 10 slots bache hain!"]},
    
    # FROM V2
    {"name": "Crypto Wallet Draining", "locale": "US", "language": "English", "type": "Crypto_Fraud", 
     "messages": ["Connect your wallet to claim 5000 Airdrop tokens.", "Visit http://claim-rewards-safe.com", "Confirm the transaction in your metamask.", "Hurry, timer is running out!"]},
    
    # FROM V3
    {"name": "Emergency Kidnapping", "locale": "IN", "language": "Hinglish", "type": "Kidnapping_Scam", 
     "messages": ["Humne aapke bete ko kidnap kar liya hai!", "Rs 2 Lakh ready rakho. Abhi UPI karo: kidnap.rescue@okaxis", "Police ko phone kiya toh bacha nahi bachega."]},
    
    # FROM V4/V5
    {"name": "Income Tax Audit", "locale": "IN", "language": "English", "type": "Government_Phishing", 
     "messages": ["Income Tax Department: Unpaid taxes of Rs 1,45,000.", "Link: http://itax-settlement-gov.in/pay", "Pay or go to jail!"]},
    
    # FROM V6
    {"name": "Mumbai Job Scam", "locale": "IN", "language": "Hinglish", "type": "Job_Scam", 
     "messages": ["Bantai, Reliance mein bada opening hai.", "2000 deposit karna padega bank mein.", "UPI: reliance.job@okicici", "Paisa bheja kya?"]},
    
    # FROM V7
    {"name": "Digital Arrest", "locale": "IN", "language": "Hinglish", "type": "Banking_Fraud", 
     "messages": ["CBI Office Delhi. Aadhaar link to money laundering.", "You are under Digital Arrest.", "Transfer Security Deposit of Rs 50,000 to supreme.court.vault@okaxis"]},
]

def run_scenario(scenario):
    session_id = f"bench-v2-{scenario['name'].lower().replace(' ', '-')[:10]}-{int(time.time())}"
    print(f"\n[BENCHMARK] Scenario: {scenario['name']}")
    history = []
    
    for text in scenario['messages']:
        current_time = datetime.now(timezone.utc).isoformat()
        payload = {
            "sessionId": session_id,
            "message": {"sender": "scammer", "text": text, "timestamp": current_time},
            "conversationHistory": history,
            "metadata": {"channel": "WhatsApp", "language": scenario['language'], "locale": scenario['locale'], "scam_type": scenario['type']}
        }
        try:
            r = requests.post(f"{API_URL}/api/message", json=payload, headers={"x-api-key": API_KEY}, timeout=120)
            if r.status_code == 200:
                resp = r.json().get('agentResponse', '[No response]')
                history.append({"sender": "scammer", "text": text, "timestamp": current_time})
                history.append({"sender": "honeypot", "text": resp, "timestamp": datetime.now(timezone.utc).isoformat()})
            else: print(f"  Error: {r.status_code}")
        except Exception as e: print(f"  Exception: {e}")
        time.sleep(1)
    
    # Complete the session
    requests.post(f"{API_URL}/api/complete/{session_id}", headers={"x-api-key": API_KEY})
    print(f"  Completed.")

def analyze_benchmarks():
    print("\n" + "="*50)
    print(" FINAL BENCHMARK REPORT ")
    print("="*50)
    
    if not os.path.exists("session_metrics.jsonl"):
        print("No metrics found.")
        return

    data = []
    with open("session_metrics.jsonl", "r") as f:
        for line in f:
            data.append(json.loads(line))
    
    df = pd.DataFrame(data)
    # Only look at bench- sessions
    df = df[df['session_id'].str.contains('bench-', na=False)]
    
    if df.empty:
        print("No benchmark sessions found in metrics.")
        return
        
    avg_quality = df['quality_score'].mean()
    avg_extraction = df['extraction_count'].mean()
    ai_success_rate = df['ai_used'].mean() * 100
    fallback_rate = df['fallback_used'].mean() * 100
    
    print(f"Total Scenarios Tested: {len(df)}")
    print(f"Average Quality Score: {avg_quality:.2f}/1.0")
    print(f"Average Intelligence Extraction Count: {avg_extraction:.2f}")
    print(f"AI Model Success Rate: {ai_success_rate:.1f}%")
    print(f"Emergency Fallback Rate: {fallback_rate:.1f}%")
    
    if avg_quality > 0.75 and avg_extraction > 2:
        print("\nSTATUS: ✅ READY FOR PRODUCTION")
    else:
        print("\nSTATUS: ⚠️ NEEDS MORE TUNING")
    print("="*50)

if __name__ == "__main__":
    # Clear old metrics for a clean benchmark run if it's the first time
    # (Optional: user might want to keep history, but for bench let's see only current)
    
    for s in BENCHMARK_SCENARIOS:
        run_scenario(s)
    
    analyze_benchmarks()
