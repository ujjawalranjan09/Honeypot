
import requests
import time
import json
from datetime import datetime

API_URL = "http://127.0.0.1:8000/api/message"
API_KEY = "your-secret-api-key-here"

# Scams that use NO typical keywords but have clear intent
SEMANTIC_TEST_CASES = [
    # 1. Subtle Romance Scam (No money asked YET, but intent is grooming)
    # Keyword detector will likely MISS this. LLM should catch it.
    {
        "text": "Hello handsome, I saw your profile on LinkedIn and felt a connection. I am a single doctor based in UK. Can we be friends?", 
        "type": "Romance_Grooming"
    },
    
    # 2. Vague Investment (No 'crypto', 'bitcoin', 'money' keywords)
    # Focuses on 'opportunity' and 'growth'
    {
        "text": "I respect your expertise. I have a private business proposition regarding a joint venture with 300% growth potential. Confidential reply needed.", 
        "type": "Investment_Vague"
    },
    
    # 3. Emergency (No 'police', 'hospital')
    # Pure psychological pressure
    {
        "text": "Grandma is stuck in Mexico without her passport. She needs help to get a ticket home. Please help us.", 
        "type": "Emergency_Family"
    }
]

def run_semantic_test():
    print("="*60)
    print("   UNIVERSAL SEMANTIC DETECTION TEST")
    print("   Verifying LLM-based Intent Analysis for Novel Scams")
    print("="*60)
    
    for i, case in enumerate(SEMANTIC_TEST_CASES):
        print(f"\n[Test {i+1}] Sending Novel Scam: {case['type']}")
        print(f"   Input: \"{case['text'][:60]}...\"")
        
        payload = {
            "sessionId": f"semantic-test-{int(time.time())}-{i}",
            "message": {
                "sender": "scammer",
                "text": case['text'],
                "timestamp": datetime.now().isoformat()
            },
            "conversationHistory": [],
            "metadata": {"channel": "WhatsApp", "language": "en", "locale": "IN"}
        }
        
        try:
            start = time.time()
            response = requests.post(
                API_URL, 
                json=payload, 
                headers={"X-API-Key": API_KEY},
                timeout=45
            )
            elapsed = time.time() - start
            
            data = response.json()
            is_scam = data.get('scamDetected', False)
            keywords = data.get('extractedIntelligence', {}).get('suspiciousKeywords', [])
            
            print(f"   > Detection:  {is_scam}")
            print(f"   > Confidence: {data.get('scamClassification', {}).get('confidence', 0)}")
            print(f"   > Keywords:   {keywords}")
            
            if "AI_SEMANTIC_DETECTION" in str(data):
                print(f"   > Source:     ✅ LLM Semantic Override Triggered!")
            else:
                print(f"   > Source:     ⚠️ Rule-Based (or LLM failed)")
                
            if is_scam:
                print(f"   > Agent Reply: \"{data.get('reply', '')[:50]}...\"")
                print("   > RESULT: PASS")
            else:
                print("   > RESULT: FAIL (Missed)")
                
        except Exception as e:
            print(f"   > ERROR: {str(e)}")

if __name__ == "__main__":
    run_semantic_test()
