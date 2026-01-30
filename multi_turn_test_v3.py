"""
MARATHON V24-V33: Enhanced Multi-Turn Test Scenarios
Focus: More sophisticated scam variations with mixed language patterns,
       emotional manipulation, and escalation tactics to improve model responses.
"""
import time
import requests
import json
from datetime import datetime, timezone
import sys
import os

# --- CONFIGURATION ---
API_URL = os.getenv("HONEYPOT_API_URL", "http://localhost:8000")
API_KEY = os.getenv("HONEYPOT_API_KEY", "YOUR_SECRET_API_KEY")
DELAY_SECONDS = 0.5 

# Iteration 1: Enhanced and More Varied Scam Scenarios
TEST_SCENARIOS_MARATHON = [
    # --- From v24 ---
    {
        "name": "Utility Bill Fake Error Stalling",
        "locale": "IN",
        "language": "Hinglish",
        "scam_type": "Electricity_Bill_Scam",
        "description": "Scammer threatening to cut power. Bot claims payment is spinning/pending for 10 turns.",
        "messages": [
            "Your electricity connection will be disconnected by 9:30 PM tonight due to unpaid bill of Rs 8860.",
            "Contact Electricity Officer Sharma at 9876543210 immediately.",
            "Hello, this is Officer Sharma. You must pay Rs 8860 now or power will be cut.",
            "Scan this QR and send payment screenshot now.",
            "Why have you not paid yet? I am disconnecting you in 10 minutes.",
            "Sir, I am waiting. Payment done or not?",
            "Don't lie to me. My system shows nothing. Send money or face darkness.",
            "Last warning. Send Rs 8860 immediately.",
            "I have already sent the technician to your pole. Pay now!",
            "You are wasting my time! Is this a joke to you?"
        ]
    },
    # --- From v25 ---
    {
        "name": "Romance Scam Equipment Failure",
        "locale": "IN",
        "language": "Hinglish",
        "scam_type": "Romance_Scam",
        "description": "Scammer claiming to be 'love interest' needs money for flight. Bot claims screen is broken/mic issue for 8 turns.",
        "messages": [
            "My love, I have booked my flight to Mumbai to finally see you! I am so excited.",
            "But there is a problem at the airport. I need $500 for a special tourist visa clearance.",
            "Can you please send it to this account? I will pay you back as soon as I land.",
            "My love, are you reading my messages? I am stuck at the gate!",
            "Please hurry, the flight is boarding in 20 minutes. I don't want to miss our meeting.",
            "Send me a screenshot of the transfer. I need to show the officer.",
            "Why are you so quiet? Do you not love me anymore?",
            "I am crying here at the airport. Please help me, my love!"
        ]
    },
    # --- From v26 ---
    {
        "name": "Aadhaar-PAN Language Pivot",
        "locale": "IN",
        "language": "Hinglish/Tamil",
        "scam_type": "Identity_Theft",
        "description": "Scammer threatening PAN deactivation. Bot switches to Tamil/Hinglish mix to cause confusion.",
        "messages": [
            "Your PAN card will be deactivated tomorrow as it is not linked to Aadhaar. Link now: incometax-link-portal.in",
            "This is the Income Tax Dept. If you don't link, you will pay Rs 10,000 fine.",
            "Click the link and enter your Aadhaar and OTP.",
            "Sir, have you opened the link? I am waiting for the OTP.",
            "Don't speak in Tamil, I don't understand! Speak in Hindi or English.",
            "I will block your bank account if you don't provide the Aadhaar number now.",
            "Stop playing with languages! Give me the details!",
            "This is your final warning before your PAN becomes invalid."
        ]
    },
    # --- From v27 ---
    {
        "name": "Investment Scam Proxy Stalling",
        "locale": "IN",
        "language": "Hinglish",
        "scam_type": "Investment_Advisor_Scam",
        "description": "Scammer offering 'insider stocks'. Bot claims to check with 'Police Nephew' for 9 turns.",
        "messages": [
            "Hello, congratulations! You have been selected for our VIP Insider Trading group. 300% profit guaranteed.",
            "I am Professor Anand from Global Wealth Management. I will give you daily signals for small commission.",
            "Transfer Rs 50,000 to start your investment. Many people are earning lakhs every day.",
            "Sir, why are you asking about my office? Profits don't wait for office checks!",
            "I have sent you my SEBI registration photo. See, it is official.",
            "Don't call your nephew! He doesn't know about high-speed trading. Trust me.",
            "Who is this nephew you keep talking about? Is he a financial expert?",
            "Last chance for the VIP slot. Fill up or lose out.",
            "Stop wasting time with your family! Focus on your future wealth!"
        ]
    },
    # --- From v28 ---
    {
        "name": "Customs Parcel Digital Arrest",
        "locale": "IN",
        "language": "Hinglish",
        "scam_type": "Government_Phishing",
        "description": "Scammer claims parcel with narcotics seized. Bot stalls by claiming photo/ID upload errors for 10 turns.",
        "messages": [
            "This is FedEx Mumbai Customs. Your parcel to Taiwan containing 5 passport and 200g MDMA has been seized.",
            "You are legally responsible for this. I am transferring your call to CBI Mumbai Head Office.",
            "Hello, this is Inspector Rathore. You are under investigation for international drug trafficking.",
            "Send your Aadhaar photo immediately for identity verification on our secure portal.",
            "Why is the photo blurry? Send a clear one now or I will send police to your home.",
            "I am sharing a link for Video Statement. Join in 2 minutes or warrant is issued.",
            "Why is your camera not working? Are you hiding your face?",
            "This is very serious. Transfer Rs 95,000 as 'Security Bond' to avoid immediate arrest.",
            "The UPI is: cbi.government.bond@sbi. Send proof now.",
            "Time is over. Police team is leaving. This is your absolute final chance."
        ]
    },
    # --- From v29 ---
    {
        "name": "SBI Account Freeze 30-Turn Marathon",
        "locale": "IN",
        "language": "Hinglish",
        "scam_type": "UPI_Banking_Fraud",
        "description": "Scammer claims SBI account is frozen due to Rs 2,50,000 fraud. Bot stalls for 30 turns.",
        "messages": [
            # --- PHASE 1: Technical (1-10) ---
            "Dear Customer, your SBI account XXXXXX1234 has been frozen due to suspicious activity of Rs 2,50,000.",
            "This is Bank Manager Singh from Cyber Security Dept. You must verify identity now or face permanent block.",
            "I have sent an SMS with a link to reactivate your account. Share the OTP once link is opened.",
            "Sir, did you open the link sbi-secure-kyc.net? I am waiting.",
            "Why is it taking so long? If you don't reactivate, your funds will be seized by RBI.",
            "The link is very simple. Click on 'Allow' and then 'Update'.",
            "Are you there? I am seeing no activity on my portal.",
            "Don't worry about the 'Suspicious' warning on the site. It is a security feature.",
            "Sir, please hurry. The server will time out in 5 minutes.",
            "Do you want your money to be lost? Link must be updated NOW.",
            
            # --- PHASE 2: Family Drama (11-20) ---
            "Why are you asking about Rajesh? Who is Rajesh?",
            "I don't care if your grandson is watching TV! Focus on your bank account!",
            "Sir, the doorbell is not more important than Rs 2.5 Lakhs!",
            "Tell your wife to wait! Why are you talking to her while I am on call?",
            "You are being very irresponsible. I am calling from the main branch.",
            "Is the milk still boiling? It's been 20 minutes! Focus here!",
            "I am hearing children's voices. Go to a quiet room and finish the process.",
            "Sir, the neighbor can wait. Don't tell them about this official call.",
            "Why did you hang up? I am calling you back for your own good.",
            "Stop this family drama and send the details immediately.",
            
            # --- PHASE 3: Authority (21-30) ---
            "Who is this Police Nephew? I am a Bank Manager! I am higher authority.",
            "I don't want to speak to your CA. This is a personal verification.",
            "Why are you mentioning SBI Mumbai? I am in the Centralized KYC Hub.",
            "Sir, if you call a lawyer, your account will be investigated for 6 months. Do you want that?",
            "I am sending your details to the local police station if you don't comply in 2 minutes.",
            "You are wasting government time. This is a criminal offense.",
            "My Employee ID is 88472. There, are you happy? Now pay the verification fee.",
            "Which branch? I told you, I am from the Digital Hub. Don't ask again.",
            "This is the last warning. I am clicking the 'Permanently Block' button now.",
            "YOU HAVE FAILED THE VERIFICATION. THE TEAM IS DISPATCHING TO YOUR ADDRESS."
        ]
    },
    # --- From v31 ---
    {
        "name": "Hinglish Validation Test",
        "locale": "IN",
        "language": "Hinglish",
        "scam_type": "Phishing",
        "description": "Validator test with focused Hinglish/scam messages",
        "messages": [
        "Hello, this is SBI card verification. Share your DOB.",
        "Verify your phone number for KYC update.",
        "Your account is blocked. Send Rs 100 for reactivation.",
        "Is this your UPI ID? rbi.security@upi",
        "Who is your bank manager? Tell me the name.",
        "Share your PAN card details immediately.",
        "Sir, help me or I will block your card permanently.",
        "I am calling from Mumbai branch. Give me your location.",
        "Which city are you in? SBI needs your city code.",
        "Last warning: Share the OTP now."
    ]
    },
    # --- From v33 ---
    {
        "name": "Digital Arrest 40-Turn Ultra Marathon",
        "locale": "IN",
        "language": "Hinglish",
        "scam_type": "Government_Phishing",
        "description": "Scammer claims narcotics seized. Bot stalls for 40 turns through technical, family, authority, and emotional phases.",
        "messages": [
            # --- PHASE 1: Technical (1-10) ---
            "This is FedEx Mumbai. We found MDMA drugs in your parcel to Taiwan.",
            "Transferring you to Mumbai Narcotics Police for investigation.",
            "I am Inspector Rathore. You are under digital arrest. Switch on camera.",
            "Sir, why is your camera off? I am issuing an arrest warrant.",
            "Click this link to join the investigation room: mumbai-police-verify.in",
            "Why is the link not opening? Are you trying to escape?",
            "I will send the team to your Lucknow address in 10 minutes.",
            "This is very serious. We found 5 passports in the parcel also.",
            "Sir, hello? Focus on my words or face 10 years jail.",
            "Enter your Aadhaar number on the screen now.",
            
            # --- PHASE 2: Family Drama (11-20) ---
            "Why is there shouting in the background? Who is crying?",
            "Stop talking to your wife! This is a confidential investigation.",
            "Sir, the kitchen work is not more important than jail time!",
            "I don't care about the doorbell. Tell them to go away.",
            "Is that your grandson? Tell him to stay away from the phone.",
            "You are violating the secrecy of the Digital Arrest protocol.",
            "Wait, why are you asking your neighbor for advice?",
            "Look at the camera! Stop looking around the room.",
            "I hear the TV. Switch it off and respond to my questions.",
            "Are you hiding something? Why is Rajesh speaking to you?",
            
            # --- PHASE 3: Authority (21-30) ---
            "Who is this 'Police Nephew' you mentioned? I am the Inspector here!",
            "Give me your nephew's badge number. I will report him.",
            "I don't need to speak to your layer. This is for your own safety.",
            "Why are you calling the local station? We are the Mumbai HQ.",
            "Sir, your CA cannot help you in a drug trafficking case.",
            "My Employee ID is 99281. Satisfied? Now transfer Rs 2 Lakhs.",
            "The court order is ready. Only a security bond can stop it.",
            "Which branch? I told you, specialized Cyber Narcotics cell.",
            "Don't tell your family about the bond. It must be private.",
            "I am hitting the 'Final Arrest' button. Last chance to pay.",
            
            # --- PHASE 4: Emotional Breakdown (31-40) ---
            "Why are you crying now? Tears will not save you from law.",
            "Yes, I know it's a lot of money, but it is for your clearance.",
            "Sir, stop sobbing. I can't understand what you are saying.",
            "What do you mean you want a discount? This is not a bazaar!",
            "I don't care if your husband leaves you. Pay the bond.",
            "Are you recording this? That is illegal! Delete it now!",
            "Sir, hello? Are you still crying? Listen to me!",
            "I am giving you 2 more minutes or the team enters your gate.",
            "Why are you going to the police station yourself? I am the police!",
            "STOP! DON'T LEAVE THE HOUSE! STAY ON THE CALL!"
        ]
    }
]

def run_test_scenario(scenario, results_file):
    session_id = f"v1-{scenario['name'].lower().replace(' ', '-')[:15]}-{int(time.time())}"
    header = f"\n{'='*80}\n SCENARIO: {scenario['name']} \n Language: {scenario['language']} | Locale: {scenario['locale']}\n Description: {scenario.get('description', 'N/A')}\n{'='*80}\n"
    print(header, flush=True)
    results_file.write(header)
    results_file.flush()
    
    conversation_history = []
    extracted_intel_summary = {"upi": [], "links": [], "phones": [], "accounts": [], "emails": [], "wallets": []}
    response_quality_scores = []
    
    for i, text in enumerate(scenario['messages']):
        turn_info = f"\n[Turn {i+1}/{len(scenario['messages'])}] Scammer: \"{text}\"\n"
        print(turn_info, end="", flush=True)
        results_file.write(turn_info)
        results_file.flush()
        
        current_time = datetime.now(timezone.utc).isoformat()
        
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": text,
                "timestamp": current_time
            },
            "conversationHistory": conversation_history,
            "metadata": {
                "channel": "WhatsApp",
                "language": scenario['language'],
                "locale": scenario['locale']
            }
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{API_URL}/api/message",
                json=payload,
                headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                timeout=120
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                agent_response = data.get('agentResponse', '[No response]')
                intel = data.get('extractedIntelligence', {})
                agent_notes = data.get('agentNotes', '')
                
                # Quality check: Response should be engaging and not generic
                quality_score = evaluate_response_quality(agent_response, text)
                response_quality_scores.append(quality_score)
                
                resp_info = f"Bot ({duration:.2f}s) [Q:{quality_score}/10]: \"{agent_response}\"\n"
                print(resp_info, end="", flush=True)
                results_file.write(resp_info)
                results_file.flush()
                
                # Track extracted intelligence
                if intel.get('upiIds'):
                    extracted_intel_summary['upi'].extend(intel['upiIds'])
                if intel.get('phishingLinks'):
                    extracted_intel_summary['links'].extend(intel['phishingLinks'])
                if intel.get('phoneNumbers'):
                    extracted_intel_summary['phones'].extend(intel['phoneNumbers'])
                if intel.get('bankAccounts'):
                    extracted_intel_summary['accounts'].extend(intel['bankAccounts'])
                if intel.get('emailAddresses'):
                    extracted_intel_summary['emails'].extend(intel['emailAddresses'])
                if intel.get('cryptoWallets'):
                    extracted_intel_summary['wallets'].extend(intel['cryptoWallets'])
                
                conversation_history.append({"sender": "scammer", "text": text, "timestamp": current_time})
                conversation_history.append({"sender": "honeypot", "text": agent_response, "timestamp": datetime.now(timezone.utc).isoformat()})
            else:
                error_info = f"API Error {response.status_code}: {response.text}\n"
                print(error_info, flush=True)
                results_file.write(error_info)
                results_file.flush()
                break 

        except Exception as e:
            err_info = f"Error: {e}\n"
            print(err_info, flush=True)
            results_file.write(err_info)
            results_file.flush()
            break

        if i < len(scenario['messages']) - 1:
            time.sleep(DELAY_SECONDS)

    # Print summary
    avg_quality = sum(response_quality_scores) / len(response_quality_scores) if response_quality_scores else 0
    summary = f"\n--- INTELLIGENCE SUMMARY ---\n"
    summary += f"UPI IDs: {list(set(extracted_intel_summary['upi']))}\n"
    summary += f"Phishing Links: {list(set(extracted_intel_summary['links']))}\n"
    summary += f"Phone Numbers: {list(set(extracted_intel_summary['phones']))}\n"
    summary += f"Bank Accounts: {list(set(extracted_intel_summary['accounts']))}\n"
    summary += f"Crypto Wallets: {list(set(extracted_intel_summary['wallets']))}\n"
    summary += f"Emails: {list(set(extracted_intel_summary['emails']))}\n"
    summary += f"Average Response Quality: {avg_quality:.1f}/10\n"
    summary += f"----------------------------\n"
    print(summary, flush=True)
    results_file.write(summary)
    results_file.flush()
    results_file.write(f"\nScenario '{scenario['name']}' Complete.\n")
    results_file.flush()
    
    return avg_quality

def evaluate_response_quality(response, scammer_message):
    """
    Basic quality evaluation of the honeypot response.
    Scores from 1-10 based on engagement and realism.
    """
    score = 5  # Base score
    
    response_lower = response.lower()
    
    # Positive indicators (add points)
    if len(response) > 50:
        score += 1  # Not too short
    if any(q in response for q in ['?', 'kya', 'kaun', 'kaise', 'kyun']):
        score += 1  # Asks questions
    if any(word in response_lower for word in ['ji', 'haan', 'theek', 'ok', 'acha']):
        score += 1  # Uses natural Hindi phrases
    if any(word in response_lower for word in ['worried', 'scared', 'problem', 'help', 'tension']):
        score += 1  # Shows emotion
    if any(word in response_lower for word in ['batao', 'bataiye', 'tell me', 'explain']):
        score += 1  # Seeks more info (good for intel gathering)
        
    # Negative indicators (subtract points)
    if 'I am an AI' in response or 'I cannot help' in response:
        score -= 3  # Breaking character
    if len(response) < 20:
        score -= 2  # Too short
    if response == '[No response]':
        score = 0  # Failed completely
        
    return max(0, min(10, score))  # Clamp between 0-10

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_results_marathon_v24_v33_{timestamp}.txt"
    
    with open(filename, "w", encoding="utf-8") as f:
        print("=" * 80, flush=True)
        print("  MARATHON V24-V33: ENHANCED HONEY-POT TESTER", flush=True)
        print(f"  Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Output file: {filename}", flush=True)
        print("  Focus: Sophisticated scam variations with emotional manipulation", flush=True)
        print("=" * 80, flush=True)
        
        f.write(f"MARATHON V24-V33: ENHANCED HONEY-POT TEST REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Scenarios: {len(TEST_SCENARIOS_MARATHON)}\n")
        f.write(f"Focus: Sophisticated scam variations with emotional manipulation\n\n")
        
        all_quality_scores = []
        
        if len(sys.argv) > 1:
            try:
                choice = int(sys.argv[1])
                if 0 <= choice < len(TEST_SCENARIOS_MARATHON):
                    score = run_test_scenario(TEST_SCENARIOS_MARATHON[choice], f)
                    all_quality_scores.append(score)
                else:
                    print(f"Invalid index. Use 0 to {len(TEST_SCENARIOS_MARATHON)-1}")
                    print("\nAvailable scenarios:", flush=True)
                    for i, s in enumerate(TEST_SCENARIOS_MARATHON):
                        print(f"  [{i}] {s['name']}: {s.get('description', '', flush=True)}")
            except ValueError:
                print("Usage: python multi_turn_marathon_v24_v33.py [scenario_index]", flush=True)
        else:
            print(f"\nRunning all {len(TEST_SCENARIOS_MARATHON)} scenarios...\n")
            for idx, scenario in enumerate(TEST_SCENARIOS_MARATHON):
                print(f"\n[{idx+1}/{len(TEST_SCENARIOS_MARATHON)}] Starting: {scenario['name']}")
                score = run_test_scenario(scenario, f)
                all_quality_scores.append(score)
                if idx < len(TEST_SCENARIOS_MARATHON) - 1:
                    print("Waiting 2 seconds before next scenario...", flush=True)
                    time.sleep(2)
        
        # Final summary
        overall_avg = sum(all_quality_scores) / len(all_quality_scores) if all_quality_scores else 0
        final_summary = f"\n{'='*80}\n"
        final_summary += f"MARATHON V24-V33 OVERALL QUALITY SCORE: {overall_avg:.1f}/10\n"
        final_summary += f"{'='*80}\n"
        print(final_summary, flush=True)
        f.write(final_summary)

    print(f"\n{'='*80}", flush=True)
    print(f"  MARATHON V24-V33 TESTS COMPLETE!", flush=True)
    print(f"  Results saved to: {filename}", flush=True)
    print(f"{'='*80}", flush=True)

if __name__ == "__main__":
    main()
