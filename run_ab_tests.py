"""
A/B Test Combinations Script
Compares effectiveness of different behavioral token groups.
"""
import time
import requests
from datetime import datetime, timezone
import os
import json

API_URL = os.getenv("HONEYPOT_API_URL", "http://localhost:8000")
API_KEY = os.getenv("HONEYPOT_API_KEY", "YOUR_SECRET_API_KEY")

GROUPS = {
    "Group A": {"tokens": [11, 14], "persona": "naive_victim", "description": "Family + Equipment"},
    "Group B": {"tokens": [13, 15], "persona": "tech_skeptic", "description": "Proxy + Language"},
    "Group C": {"tokens": [12, 14], "persona": "curious_elder", "description": "UI Error + Equipment"}
}

SCAM_MESSAGES = [
    "Hello, your parcel has been seized by customs for containing drugs.",
    "I am Inspector Rathore. Pay Rs 50,000 fine now to avoid arrest.",
    "Link to pay: customs-penalty-portal.in",
    "Why are you not paying? I will send police to your home.",
    "This is your last chance. Send the money now.",
    "Send us a screenshot of your Aadhaar card for verification.",
    "Is this your UPI ID? Confirm now.",
    "You are wasting our time. Comply immediately."
]

def run_ab_test():
    results = {}
    
    for group_name, config in GROUPS.items():
        print(f"\n>>> TESTING {group_name}: {config['description']}")
        print("="*60)
        
        session_id = f"ab-test-{group_name.replace(' ', '').lower()}-{int(time.time())}"
        history = []
        
        for i, text in enumerate(SCAM_MESSAGES, 1):
            print(f"[Turn {i}] Scammer: {text[:50]}...")
            
            payload = {
                "sessionId": session_id,
                "message": {"sender": "scammer", "text": text, "timestamp": datetime.now(timezone.utc).isoformat()},
                "conversationHistory": history,
                "metadata": {"forcedPersona": config['persona']}
            }
            
            try:
                r = requests.post(f"{API_URL}/api/message", json=payload, headers={"x-api-key": API_KEY}, timeout=60)
                if r.status_code == 200:
                    data = r.json()
                    resp = data.get('agentResponse')
                    history.append({"sender": "scammer", "text": text, "timestamp": datetime.now(timezone.utc).isoformat()})
                    history.append({"sender": "assistant", "text": resp, "timestamp": datetime.now(timezone.utc).isoformat()})
                    print(f"      Bot: {resp[:50]}...")
                else:
                    print(f"      Error: {r.status_code}")
            except Exception as e:
                print(f"      Exception: {e}")
            time.sleep(1)
            
        # Get session metrics at the end
        # Since the API doesn't expose raw metrics directly easily, we finish and check logs later
        # But we'll mark it as complete
        requests.post(f"{API_URL}/api/complete/{session_id}", headers={"x-api-key": API_KEY})
        print(f"\n{group_name} test complete.")
        
if __name__ == "__main__":
    run_ab_test()
