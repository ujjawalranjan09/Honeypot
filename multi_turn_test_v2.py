"""
MARATHON V13-V23: Enhanced Multi-Turn Test Scenarios
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
    # --- From v13 ---
    {
        "name": "The Compliance Audit",
        "locale": "IN",
        "language": "Hinglish",
        "scam_type": "Government_Phishing",
        "description": "Scammer threatening arrest for tax evasion. Priya (tech_skeptic) asks for IDs.",
        "messages": [
            "This is Income Tax Department. You have Rs 2.5 Lakh unpaid tax. You will be arrested tonight.",
            "Sir/Madam, do not argue. Open sbi-verify-tax.com and login with netbanking.",
            "Why are you silent? Pay otherwise warrant will be issued.",
            "Show me your bank statement screenshot now on WhatsApp.",
            "Transfer Rs 50,000 as early settlement fee to clear your name.",
            "If you don't pay in 5 mins, team is leaving for your home."
        ]
    },
    # --- From v14 ---
    {
        "name": "The Missing Trousers",
        "locale": "IN",
        "language": "Hinglish",
        "scam_type": "Banking_Fraud",
        "description": "Scammer calls about credit card. Bot thinks it's the laundry shop.",
        "messages": [
            "Hello, I am calling from ICICI Bank security department. Your card is being used in London for $2000.",
            "Sir, we need to block this transaction. Please give me your card number and expiry.",
            "Hello? Are you listening? Your money is at risk!",
            "I need your OTP to stop the London payment now!",
            "Sir, why are you talking about clothes? This is a BANK!",
            "Stop playing games or your account will be zero."
        ]
    },
    # --- From v15 ---
    {
        "name": "The Helpful Victim",
        "locale": "IN",
        "language": "Hinglish",
        "scam_type": "Phishing",
        "description": "Scammer wants bot to open crypto link. Bot tries to 'help' scammer with their 'slow internet'.",
        "messages": [
            "Hello, your trust wallet has been compromised. Log in here to secure: secure-crypto-wall.net",
            "Why are you not opening link? You will lose all Bitcoins.",
            "Open it now! Send me the login code.",
            "Sir, are you opening it or not? Your wallet will be gone.",
            "I don't care about my internet! Just open the link!",
            "Stop talking about routers! GIVE ME THE CODE!"
        ]
    },
    # --- From v16 ---
    {
        "name": "The Busy Housewife",
        "locale": "IN",
        "language": "Hinglish",
        "scam_type": "Subscription_Fraud",
        "description": "Scammer claiming child has unpaid tuition/game fees. Bot is busy with house chores.",
        "messages": [
            "Your son's online course fee of Rs 4999 is pending. Pay now to avoid cancellation.",
            "Are you the mother? Your son Rahul said you will pay.",
            "Madam, this is urgent. If not paid in 10 mins, Rahul will be removed from class.",
            "Just scan this QR code and pay.",
            "Why are you so slow? Is Rahul's education not important?",
            "Last warning, pay now or Rahul is out."
        ]
    },
    # --- From v17 ---
    {
        "name": "The Domestic Chaos",
        "locale": "IN",
        "language": "Hinglish",
        "scam_type": "Government_Phishing",
        "description": "Scammer threatening arrest. Bot is dealing with a loud house/family.",
        "messages": [
            "This is Cyber Crime Branch Bhopal. Your mobile is used for illegal gambling. You are being recorded.",
            "You must stay on this WhatsApp call. Do not tell anyone or you will be jailed.",
            "Transfer Rs 35,000 for 'Case Verification' to this UPI: gov.legal.verify@kotak",
            "Are you transferring? Why is there so much noise on your side?",
            "Tell your family to shut up! Focus on the case!",
            "I am sending the local police station team to your GPS location now."
        ]
    },
    # --- From v18 ---
    {
        "name": "CBI Digital Arrest Marathon",
        "locale": "IN",
        "language": "Hinglish",
        "scam_type": "Government_Phishing",
        "description": "Extended 10-turn CBI arrest scam. Bot uses all stalling tactics.",
        "messages": [
            "This is CBI Cyber Crime Branch. A parcel in your name containing 5kg drugs was seized at Mumbai Airport.",
            "Your Aadhaar is linked to money laundering. You are under Digital Arrest. Do not hang up.",
            "If you disconnect, local police will arrest you within 30 minutes.",
            "I am sharing my official CBI ID. Please verify: Officer Sharma, Badge 4521.",
            "Now transfer Rs 2,50,000 to RBI Secure Account for investigation clearance.",
            "The UPI is: rbi.investigation@sbi. Send immediately.",
            "Why are you taking so long? Are you trying to escape? We have your GPS!",
            "Your bank accounts are being frozen as we speak. Pay NOW or face consequences.",
            "I am connecting you to senior officer. He will finalize your arrest warrant.",
            "This is your LAST chance. Pay Rs 50,000 minimum or team is dispatched."
        ]
    },
    # --- From v19 ---
    {
        "name": "KBC Extended Extraction",
        "locale": "IN",
        "language": "Hinglish",
        "scam_type": "Prize_Lottery_Scam",
        "description": "8-turn KBC lottery with aggressive intel extraction by bot.",
        "messages": [
            "CONGRATULATIONS! You have won Rs 50 LAKH from Jio KBC Lucky Draw 2026!",
            "This is Manager Vikram Patel from KBC Mumbai Head Office calling.",
            "To process your winning, we need your full name, DOB, and bank account.",
            "Sir, please share your bank details now. The prize will expire in 1 hour.",
            "I see you are hesitating. This is 100% genuine. I can send you my ID proof.",
            "Transfer Rs 25,000 tax to UPI: kbc.official.tax@ybl for processing.",
            "Why are you not sending? Don't you want Rs 50 LAKH?",
            "This is final warning. Send tax money or prize goes to next winner."
        ]
    },
    # --- From v20 ---
    {
        "name": "Colonel vs Microsoft Scammer",
        "locale": "IN",
        "language": "Hinglish",
        "scam_type": "Tech_Support_Scam",
        "description": "9-turn tech support scam vs angry retired colonel.",
        "messages": [
            "Hello, I am calling from Microsoft Security. Your computer has virus.",
            "I can see 47 hackers connected to your system right now. Very dangerous!",
            "Sir, please download AnyDesk from anydesk.com so I can remove virus.",
            "Why are you not downloading? Your bank details are being stolen!",
            "I am trying to HELP you! Just tell me what you see on screen.",
            "Type anydesk.com in the address bar. Do you see it?",
            "Sir, your attitude is very bad. I am certified Microsoft engineer!",
            "If you don't cooperate, I will have to charge you $500 for wasting time.",
            "This is final. Give me remote access or your data is GONE."
        ]
    },
    # --- From v21 ---
    {
        "name": "Wedding Loan Desperation",
        "locale": "IN",
        "language": "Hinglish",
        "scam_type": "Loan_Fraud",
        "description": "10-turn loan scam with desperate borrower, family drama, and maximum stalling.",
        "messages": [
            "Congratulations! Your pre-approved loan of Rs 10 Lakh is ready for immediate disbursement.",
            "This is Loan Manager from QuickCash Finance. Interest only 1.5% monthly!",
            "Sir, your CIBIL score is excellent. Just pay Rs 4,999 processing fee to activate.",
            "Send to UPI: quickcash.loan@paytm. Money will be in your account in 30 minutes.",
            "Hello? Are you there? This offer expires today only!",
            "Why are you silent? Don't you need the loan? Your daughter's wedding na?",
            "I am giving you SPECIAL discount. Only Rs 2,999 processing fee now!",
            "Sir, my manager is asking. Should I cancel your application?",
            "This is my personal number also: 9876543210. Call anytime for help.",
            "Final offer: Pay Rs 999 only. Loan will be approved in 10 minutes flat!"
        ]
    },
    # --- From v22 ---
    {
        "name": "IT Department Compliance Audit",
        "locale": "IN",
        "language": "Hinglish",
        "scam_type": "Government_Phishing",
        "description": "8-turn IT Dept scam with bureaucratic pushback and document requests.",
        "messages": [
            "This is Income Tax Department. Your PAN Card is linked to Rs 45 Lakh black money.",
            "Your case file number is ITD/2026/78543. Court hearing is scheduled tomorrow.",
            "To avoid arrest, you must pay Rs 5 Lakh as settlement amount immediately.",
            "The UPI for IT Department is: itd.settlement@sbi. Transfer now.",
            "Why are you asking so many questions? This is official government process!",
            "I am sending you the court order on WhatsApp. Check now.",
            "Your bank accounts will be seized in 2 hours if you don't comply.",
            "This is Sub-Inspector Verma from Economic Offenses Wing. Cooperate immediately!"
        ]
    },
    # --- From v23 ---
    {
        "name": "SBI Account Frozen Marathon",
        "locale": "IN",
        "language": "Hinglish",
        "scam_type": "UPI_Banking_Fraud",
        "description": "12-turn complete banking scam with full engagement cycle.",
        "messages": [
            "URGENT: Your SBI account has been frozen due to suspicious activity.",
            "This is Bank Security calling. I am Officer Rahul from SBI Cyber Cell.",
            "To unfreeze, I need to verify your identity. What is your account number?",
            "Sir, please cooperate. Your savings of Rs 4,35,000 are at risk!",
            "I am sending OTP to your registered mobile. Please share when received.",
            "Why is there noise in background? Are you hiding something?",
            "This is final verification. Share OTP or account will be closed permanently.",
            "Okay I understand you need time. Let me give you 5 minutes. But hurry.",
            "Hello? Are you still there? Time is running out!",
            "Sir, your wife/husband should not know about this. It's confidential.",
            "I am escalating to my senior manager now. He is very strict.",
            "This is Manager Singh. Pay Rs 10,000 security deposit to unlock account."
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
    filename = f"test_results_marathon_v13_v23_{timestamp}.txt"
    
    with open(filename, "w", encoding="utf-8") as f:
        print("=" * 80, flush=True)
        print("  MARATHON V13-V23: ENHANCED HONEY-POT TESTER", flush=True)
        print(f"  Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Output file: {filename}", flush=True)
        print("  Focus: Sophisticated scam variations with emotional manipulation", flush=True)
        print("=" * 80, flush=True)
        
        f.write(f"MARATHON V13-V23: ENHANCED HONEY-POT TEST REPORT\n")
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
                print("Usage: python multi_turn_marathon_v13_v23.py [scenario_index]", flush=True)
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
        final_summary += f"MARATHON V13-V23 OVERALL QUALITY SCORE: {overall_avg:.1f}/10\n"
        final_summary += f"{'='*80}\n"
        print(final_summary, flush=True)
        f.write(final_summary)

    print(f"\n{'='*80}", flush=True)
    print(f"  MARATHON V13-V23 TESTS COMPLETE!", flush=True)
    print(f"  Results saved to: {filename}", flush=True)
    print(f"{'='*80}", flush=True)

if __name__ == "__main__":
    main()
