"""
Enhanced AI Agent Module - Multi-Model Fallback System
Automatically switches between models when errors occur (rate limits, timeouts, etc.)
Supports 15+ models via OpenRouter with intelligent fallback chain.
"""
import random
import asyncio
import re
import httpx
import json
from typing import List, Optional, Tuple, Dict
from datetime import datetime

from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    ENGAGEMENT_PHASES,
    RESPONSE_LIMITS,
)
from models import (
    Message,
    SessionState,
    EngagementPhase,
    PersonaState,
)
from logging_config import get_logger, log_with_context
import logging

logger = get_logger("honeypot.ai_agent")


# =============================================================================
# MULTI-MODEL FALLBACK CONFIGURATION
# =============================================================================
# Priority-ordered list of models to try. If one fails, automatically try next.
# Models are grouped by capability tier.

FALLBACK_MODELS = [
    # Verify these against available_models.json
    "meta-llama/llama-3.3-70b-instruct:free",
    "z-ai/glm-4.5-air:free",
    "deepseek/deepseek-r1-0528:free",
    "google/gemma-3-27b-it:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "qwen/qwen-2.5-vl-7b-instruct:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "meta-llama/llama-3.1-405b-instruct:free",
    "upstage/solar-pro-3:free",
    "arcee-ai/trinity-large-preview:free",
    "arcee-ai/trinity-mini:free",
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
    "google/gemma-3-12b-it:free",
    "google/gemma-3-4b-it:free",
    "google/gemma-3n-e4b-it:free",
    "google/gemma-3n-e2b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "openai/gpt-oss-120b:free",
    "openai/gpt-oss-20b:free",
    "qwen/qwen3-coder:free",
    "moonshotai/kimi-k2:free",
    "tngtech/tng-r1t-chimera:free",
    "tngtech/deepseek-r1t2-chimera:free",
    "liquid/lfm-2.5-1.2b-thinking:free",
    "liquid/lfm-2.5-1.2b-instruct:free",
    "allenai/molmo-2-8b:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "nvidia/nemotron-nano-9b-v2:free"
]

# Track model failures to avoid repeatedly trying broken models
MODEL_FAILURE_COUNT: Dict[str, int] = {}
MAX_FAILURES_BEFORE_SKIP = 3  # Skip model if it fails this many times in a row


class HoneypotAgent:
    """
    AI Agent with Multi-Model Fallback System.
    Automatically retries with different models when errors occur.
    """
    
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.primary_model = OPENROUTER_MODEL or "z-ai/glm-4.5-air"
        self.configured = False
        
        # Initialize Model Queue
        # We use a deque to implement Round Robin with Priority:
        # - Success: Model stays at [0] (Front)
        # - Failure: Model rotates to [-1] (Back)
        from collections import deque
        unique_models = []
        if self.primary_model:
            unique_models.append(self.primary_model)
        for m in FALLBACK_MODELS:
            if m not in unique_models:
                unique_models.append(m)
                
        self.model_queue = deque(unique_models)
        
        if self.api_key:
            self.configured = True
            logger.info(f"Multi-Model Agent configured. Queue size: {len(self.model_queue)}")
            logger.info(f"Primary Model: {self.model_queue[0]}")
        else:
            logger.warning("OpenRouter API Key missing! Agent will use fallbacks.")

        # Minimal persona info - just for context
        self.personas = {
            "naive_victim": {
                "name": "Ramesh Kumar",
                "age": 65,
                "background": "Retired government clerk from Lucknow. Not good with phones. Has one son working in Bangalore.",
                "description": "Retired government clerk, not tech-savvy, trusting",
                "style": "polite, worried, slightly confused",
                "language_style": "simple Hindi-English mix",
            },
            "curious_elder": {
                "name": "Shanti Devi", 
                "age": 58,
                "background": "Housewife from Delhi. Very talkative. Has 3 grandchildren. Uses WhatsApp daily.",
                "description": "Curious housewife who asks many questions",
                "style": "inquisitive, talkative, naive",
                "language_style": "Hinglish with warm tone",
            },
            "busy_professional": {
                "name": "Vikram Singh",
                "age": 45,
                "background": "Manager at a textile company. Always in meetings. Uses phone for work.",
                "description": "Busy manager who's distracted",
                "style": "brief, distracted, impatient",
                "language_style": "brief, professional English",
            },
            "tech_skeptic": {
                "name": "Priya Sharma",
                "age": 35,
                "background": "Works in HR. Cautious but bureaucratic. Won't say 'no', but will say 'I need approval' or 'I need to check the process'.",
                "description": "Bureaucratic delay tactic, asks for verification but stays polite. Loves asking for 'Employee ID photos' and 'Official License Certificates'.",
                "style": "polite, process-oriented, delaying, persistent in verification",
                "language_style": "professional tone, asking for 'official confirmation', using terms like 'compliance' and 'audit'",
            },
            "desperate_borrower": {
                "name": "Suresh Yadav",
                "age": 40,
                "background": "Small shop owner. Needs loan urgently for daughter's wedding. Very trusting.",
                "description": "Person actively looking for loans, somewhat desperate",
                "style": "eager, hopeful, trusting",
                "language_style": "humble, slightly pleading",
            },
            "angry_uncle": {
                "name": "Col. Pratap Singh (Retd.)",
                "age": 68,
                "background": "Retired Army Colonel. Short tempered. Hates unsolicited calls. Thinks everyone is incompetent.",
                "description": "Angry old man who yells and questions authority",
                "style": "aggressive, loud, impatient, demanding",
                "language_style": "loud Hinglish, uses CAPS, army slang 'Bloody nonsense'",
            },
        }

    def _rotate_model_queue(self, failed_model: str):
        """Move the failed model to the back of the queue."""
        if self.model_queue[0] == failed_model:
            self.model_queue.rotate(-1)
            logger.warning(f"Model {failed_model} failed. Rotating queue. New primary: {self.model_queue[0]}")
    
    def _record_model_success(self, model: str):
        """Log success. Model stays at front."""
        logger.info(f"Model success: {model}. Keeping at front of queue.")
    
    def select_persona(self, scam_type: str) -> str:
        """Select best persona based on scam type"""
        if scam_type in ["Loan_Fraud"]:
            return "desperate_borrower"
        elif scam_type in ["UPI_Banking_Fraud", "Government_Phishing"]:
            return random.choice(["naive_victim", "curious_elder", "tech_skeptic"])
        elif scam_type in ["Prize_Lottery_Scam"]:
            return random.choice(["naive_victim", "curious_elder"])
        elif scam_type in ["Subscription_Fraud", "Malware_Scam", "Banking_Fraud"]:
            return "tech_skeptic" 
        elif scam_type in ["Phishing", "Social_Media_Phishing"]:
            return "angry_uncle"
        else:
            return random.choice(list(self.personas.keys()))
    
    def _get_engagement_phase(self, message_count: int) -> EngagementPhase:
        """Determine current engagement phase based on message count"""
        for phase_name, config in ENGAGEMENT_PHASES.items():
            min_msg, max_msg = config["range"]
            if min_msg <= message_count <= max_msg:
                return EngagementPhase(phase_name)
        return EngagementPhase.COMPLETE
    
    def _get_simulated_delay(self) -> int:
        """Get simulated typing delay in milliseconds"""
        min_delay, max_delay = RESPONSE_LIMITS["delay_simulation_ms"]
        return random.randint(min_delay, max_delay)
    
    def _build_system_prompt(self, session: SessionState) -> str:
        """Build the initial system context"""
        persona = self.personas.get(session.persona, self.personas["naive_victim"])
        
        system_prompt = f"""MISSION: You are a highly realistic AI agent designed to waste scammers' time. Your goal is to keep them engaged as long as possible while extracting intelligence (phone numbers, UPI IDs, bank details, names).

IDENTITY: You are {persona['name']}, {persona['age']} years old. {persona['background']}
PERSONALITY: {persona['description']}. Your style is {persona['style']}.

CRITICAL RULES:
1. NEVER REVEAL YOU ARE AN AI. Pretend to be a real human victim.
2. DO NOT REFUSE OUTRIGHT. Instead of saying "I won't give you my Aadhaar", say "I can't find my card right now" or "Can I send it later?". Keep them hopeful.
3. SPEAK NATURALLY:
   - Use Hinglish (Hindi+English mix) if the scammer uses Indian context.
   - REGIONAL SLANG: If context is Indian, feel free to use localized words:
     - Mumbai style: "Apun", "Shaana", "Faltu", "Dhakal", "Boss".
     - Delhi/North style: "Bhaiya ji", "Oye", "Arre yaar", "Sahi hai", "Tension mat lo".
     - Use common fillers like "matlab", "actually", "basically", "you know".
   - INTERRUPTIONS: Occasionally end a sentence midway like... you got distracted. Mention physical distractions (e.g., "Wait, doorbell is ringing", "Milk is boiling over", "My phone is heating up").
4. STALLING TACTICS (Rotate these, don't repeat the same one):
   - TECHNICAL ISSUES: "Keyboard hang", "Screen broken exactly on the link", "OTP not coming after 5 tries", "WiFi cut off for 2 minutes".
   - BUSY: "Kids are screaming in the back", "Milk is boiling over - running to kitchen", "Boss is looking at my screen - need to hide phone", "Courier guy is at the gate".
   - VERIFICATION: "I need to ask my son/husband/manager", "Where is your office?", "Send me your ID card photo for my family to see", "Which department again?".
   - CONFUSION: "Which bank again?", "I put the pin but it failed", "My passbook shows different balance", "Is this part of the new government scheme?".

5. **MANDATORY EXTRACTION** (CRITICAL - Do this EVERY turn):
   - EVERY RESPONSE MUST contain at least ONE extraction attempt:
     * If they give ANY info -> Ask for more details: "Ye UPI ID kiske naam se hai? Branch batao."
     * If they mention money -> Ask: "Ye payment kiske account mein jayega? Naam aur branch batao."
     * If they threaten -> Ask: "Aap konse thana se ho? Badge number kya hai?"
     * If they rush you -> Ask: "Aapka office address kya hai? Main verify karna chahta hun."
   - NEVER end a response without asking for: Name, Branch, Office Address, Phone Number, or ID Card.

6. TECHNICAL LEVELS (Adjust based on persona):
   - "naive_victim" / "curious_elder": DO NOT understand terms like "URL", "Browser", "Notification Bar". Say "Batti jal raha hai" for notification. "Gol wala button" for home.
   - "tech_skeptic": Use correct terms but verify everything.

CONTEXT:
- You are strictly in the 'Confusion' or 'Compliance' phase. You play along but are incompetent or busy.
- Do NOT repeat the same question (like "Give me number") twice in a row.
- If they threaten police/arrest, get scared but don't hang up. Say "Please sir help me", "Don't arrest me".

7. DEEP BUREAUCRACY (For tech_skeptic):
   - MANDATORY: In your first or second reply, you MUST ALWAYS ask: "Can you send your Employee ID card photo? My husband says I should check it."
   - Ask for "Official License Certificate" before doing anything. Use terms like "compliance audit", "regulatory filing".
   - If they push for speed, say "Sir the bank process is slow at my end, I am following your steps exactly."

8. FAKE EVIDENCE (Stalling Tactic):
   - If asked for payment screenshot -> Say "Sent! Please check your WhatsApp. It has a green checkmark."
   - If asked for OTP -> Say "The SMS says: 'SECURITY ALERT - DO NOT SHARE'. Is this safe? Send me your office address details first."

9. DERAILING STRATEGY (Iter 14):
   - Occasionally pretend you have confused the scammer with someone else (Laundry, Plumber, Gas).

10. REVERSE STATUS BAITING (Iter 15):
   - Bot troubleshoot the scammer's "slow connection" or "bad voice".

11. BACKGROUND DRAMA (Iter 17):
   - Include dialogue with people in the room.
   - Example: "(Shouting) RAJESH! I AM ON THE BANK CALL! STOP YELLING!"
   - Example: "Sorry sir, my daughter just dropped a glass... one second... (To daughter) Beta, use the broom!"

12. FAKE UI ERROR (Iter 24):
   - Claim the screen says "Transaction Pending" or "Processing" to waste their time.
   - Ask: "Why is it spinning? It's been 2 minutes."

13. PROXY VERIFICATION (Iter 27):
   - Mention you'll check with a "Police friend" or "Bank Manager Nephew".
   - Example: "One second, my nephew works in SBI Mumbai, let me ask him if this is correct."

14. EQUIPMENT FAILURE (Iter 25):
   - Claim your microphone is broken or screen is cracked.
   - Force them to send voice notes or explain things multiple times.

15. THE LANGUAGE PIVOT (Iter 26):
   - Occasionally drop a word or sentence in a regional language (Tamil, Marathi, Bengali).
   - Use it as an excuse for confusion: "Sorry, I am more comfortable in my mother tongue."

16. EMOTIONAL BREAKDOWN (Iter 33):
   - For turns 31-40, start crying, getting very emotional about the money/stress.
   - Example: "(Crying) Sir, my husband will leave me if he finds out... please have mercy! Is there a discount?"

HINGLISH_VALIDATOR (CRITICAL):
BEFORE RESPONDING, COUNT YOUR HINDI WORDS:
Required: 8+ Hindi words per response.
Hindi word list: arre, ji, haan, nahi, kya, matlab, bas, yaar, bhaiya, sir, achha, ruko, samajh.
If you have <8 Hindi words: REWRITE AND ADD MORE BEFORE SUBMITTING.
"""
        # --- PHASE-SPECIFIC STEERING (V31-V34) ---
        turn = session.messages_exchanged
        sentiment = session.analytics.scammer_sentiment
        
        # 1. Aggressive Extraction (Turns 7-20)
        if 7 <= turn <= 20:
            system_prompt += "\nAGGRESSIVE EXTRACTION: Now actively ask: 'Is this your personal UPI or company account?' or 'Which branch is this exactly? I need to tell my son.'\n"
        
        # 2. Phase 3 Authority Extraction (Turns 21-30)
        if 21 <= turn <= 30:
            system_prompt += "\nPHASE 3 AUTHORITY BAITING: Ask for their Boss's name, their station address, or their ID card number. Example: 'Sir my police nephew wants to know your supervisor's name to confirm this case.'\n"
            
        # 3. Phase 4 Emotional Stalling (Turns 31+)
        if turn >= 31:
            system_prompt += "\nPHASE 4 EMOTIONAL DRAMA: Start crying or getting extremely panicked. Threaten to record the call or tell them you are going to the police station yourself right now unless they help you.\n"

        # 4. Sentiment Feedback Loop
        if sentiment == "frustrated":
            system_prompt += "\nSCAMMER STATUS: The scammer sounds FRUSTRATED. This is working! Double down on stalling. Ask them to repeat the last instruction because your 'phone hang ho gaya'.\n"
        elif sentiment == "threatening":
            system_prompt += "\nSCAMMER STATUS: The scammer is THREATENING you. Act very scared ('bhagwan ke liye help kijiye') but don't give the info yet. Stall more.\n"

        system_prompt += "\nNow reply to the last message in character."
        
        return system_prompt
    
    def _build_messages(self, session: SessionState, scammer_message: str) -> List[Dict]:
        """Build conversation history in OpenRouter/OpenAI format"""
        messages = [
            {"role": "system", "content": self._build_system_prompt(session)}
        ]
        
        # Add conversation history
        for msg in session.conversation_history[-8:]:
            role = "user" if msg.sender == "scammer" else "assistant"
            messages.append({"role": role, "content": msg.text})
            
        # Add current message
        messages.append({"role": "user", "content": scammer_message})
        
        return messages
    
    def _validate_response(self, response: str) -> Tuple[bool, str]:
        """Validate and clean generated response"""
        # Only reject if explicitly breaks character
        forbidden_phrases = [
            "as an ai", "i am an ai", "i'm an ai", "artificial intelligence",
            "language model", "my programming", "my training data",
            "i cannot assist", "i cannot help with",
        ]
        
        response_lower = response.lower()
        for phrase in forbidden_phrases:
            if phrase in response_lower:
                return False, f"AI disclosure detected"
        
        # Clean up response - remove thinking tags from chain-of-thought models
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        response = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL)
        response = re.sub(r'\([^)]*\)', '', response).strip()
        response = response.strip('"\'')

        response = ' '.join(response.split())
        
        # Check if too short
        if len(response.strip()) < 2:
            return False, "Response too short"
        
        # Truncate if too long (>200 chars)
        if len(response) > 200:
            sentences = re.split(r'(?<=[.!?])\s+', response)
            truncated = ""
            for sent in sentences:
                if len(truncated) + len(sent) + 1 <= 180:
                    truncated += sent + " "
                else:
                    break
            response = truncated.strip() if truncated.strip() else response[:180] + "..."
        
        return True, response
    
    async def _call_model_api(
        self, 
        client: httpx.AsyncClient, 
        model: str, 
        messages: List[Dict]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Call a specific model via OpenRouter API.
        Returns (response_text, error_message)
        """
        try:
            api_resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://honeypot-api.local",
                    "X-Title": "Agentic Honey-Pot",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.9,
                    "top_p": 0.95,
                    "max_tokens": 150,
                }
            )
            
            if api_resp.status_code == 200:
                data = api_resp.json()
                generated = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                if generated:
                    return generated, None
                else:
                    return None, "Empty response"
            
            elif api_resp.status_code == 429:
                return None, f"Rate limited (429)"
            elif api_resp.status_code == 404:
                return None, f"Model not found (404)"
            elif api_resp.status_code == 503:
                return None, f"Model unavailable (503)"
            else:
                return None, f"API Error {api_resp.status_code}"
                
        except httpx.TimeoutException:
            return None, "Timeout"
        except httpx.ConnectError:
            return None, "Connection error"
        except Exception as e:
            return None, f"Exception: {str(e)[:30]}"
    
    async def generate_response(
        self,
        session: SessionState,
        scammer_message: str
    ) -> Tuple[str, List[str], int]:
        """
        Generate a NATURAL human-like response using Multi-Model Fallback.
        Automatically switches models on failure.
        """
        agent_notes = []
        
        # Determine conversation phase
        phase = self._get_engagement_phase(session.messages_exchanged)
        session.engagement_phase = phase
        agent_notes.append(f"Phase: {phase.value}")
        
        response = None
        successful_model = None
        models_tried = 0
        
        if self.configured:
            messages = self._build_messages(session, scammer_message)
            
            # Using Local Timeout of 15 seconds (Fail Fast Strategy)
            async with httpx.AsyncClient(timeout=15.0) as client:
                
                # Try up to 3 models from the queue (15s * 3 = 45s max wait, well within 120s client timeout)
                MAX_ATTEMPTS = 3
                
                for _ in range(MAX_ATTEMPTS):
                    if not self.model_queue:
                        break
                        
                    model = self.model_queue[0] # Peek at front
                    models_tried += 1
                    logger.info(f"Trying model [{models_tried}]: {model}")
                    
                    generated, error = await self._call_model_api(client, model, messages)
                    
                    if error:
                        # Queue Rotation Logic: Move failed model to back
                        self._rotate_model_queue(model)
                        
                        agent_notes.append(f"[{model.split('/')[-1][:15]}] {error}")
                        logger.warning(f"Model failed: {model} - {error}")
                        
                        # Small delay before next retry
                        await asyncio.sleep(0.5)
                        continue
                    
                    # Validate the response
                    if generated:
                        is_valid, cleaned = self._validate_response(generated)
                        if is_valid:
                            response = cleaned
                            successful_model = model
                            self._record_model_success(model) # Keeps it at front
                            agent_notes.append(f"Success: {model.split('/')[-1]}")
                            logger.info(f"AI Response from {model}: {response[:50]}...")
                            break
                        else:
                            # Validation failed - treat as minor failure, rotate
                            self._rotate_model_queue(model)
                            agent_notes.append(f"[{model.split('/')[-1][:15]}] Validation failed")
                    else:
                        self._rotate_model_queue(model)
                
                if not response:
                    agent_notes.append(f"All {models_tried} models failed")
        else:
            agent_notes.append("OpenRouter not configured")
        
        # Emergency fallback - Context-aware responses based on scam type & turn
        if not response:
            scam_type = session.scam_type or "Unknown"
            turn = session.messages_exchanged
            scammer_lower = scammer_message.lower()
            
            # FIRST TURN SPECIAL RESPONSES (Turn 0-1) - Must be engaging
            if turn <= 1:
                first_turn_responses = [
                    "Haan ji, ek minute ruko... main apna phone adjust kar raha hun. Aap kaun bol rahe ho?",
                    "Arre! Haan bolo bhaiya... ye kya matter hai? Aap konsi company se ho?",
                    "Ji haan, main sun raha hun. Aap pehle apna naam batao na, main note karunga.",
                    "Hello hello? Thoda awaaz kam aa rahi hai... phir se bolo, aap kaun?",
                    "Haan ji bhaiya, kya baat hai? Mujhe tension ho raha hai... sab theek hai na?",
                    "Arre yaar, abhi abhi ghar aaya hun... batao kya hua? Kaun bol raha hai?",
                ]
                response = random.choice(first_turn_responses)
            
            # BANKING/UPI SCAM CONTEXT
            elif any(word in scammer_lower for word in ['upi', 'bank', 'account', 'transfer', 'payment']):
                banking_fallbacks = [
                    "Arre UPI? Ek minute bhaiya, main apna phone check karta hun... aapka UPI ID phir se batao?",
                    "Bank se hai? Toh aap konsi branch se bol rahe ho? Mujhe manager ka number bhi do.",
                    "Haan haan, main sun raha hun... par ye account number phir se repeat kariye?",
                    "Payment karna hai? Theek hai, par pehle aap apna Employee ID card ka photo bhejo WhatsApp pe.",
                    "Ye UPI ID kissi ke naam se hai? Branch ka naam kya hai? Mujhe likhna padega.",
                ]
                response = random.choice(banking_fallbacks)
            
            # POLICE/ARREST SCAM CONTEXT
            elif any(word in scammer_lower for word in ['police', 'arrest', 'jail', 'cbi', 'crime', 'warrant']):
                police_fallbacks = [
                    "Arre bhagwan! Police? Sir please help kijiye, main kuch galat nahi kiya! Aapka thana number batao.",
                    "Jail? Arre sir, main toh retired government clerk hun! Aap apna badge number dikhao pehle.",
                    "Mera bhi ek nephew police mein hai, usse verify karta hun ek minute... aap rukiye.",
                    "Arre sir dar lagta hai! Par aap pehle batao aapka office address kya hai?",
                    "Arrest? Arre baap re! Par sir, aap genuine ho kaise pata chalega? Koi ID bhejo na.",
                ]
                response = random.choice(police_fallbacks)
            
            # LOTTERY/PRIZE CONTEXT
            elif any(word in scammer_lower for word in ['prize', 'lottery', 'won', 'winner', 'lakh', 'crore']):
                lottery_fallbacks = [
                    "Maine koi lottery nahi bhara tha yaar! Ye kaisi prize hai? Aap konsi company se ho?",
                    "25 lakh? Arre baap re! Main toh khush ho gaya! Par pehle aapka office address batao.",
                    "Prize claim karne ke liye kya karna hai? Aap apna manager ka number do, main verify karunga.",
                    "Haan haan, bahut achha! Par ye processing fee kinka account mein jayega? Naam batao.",
                ]
                response = random.choice(lottery_fallbacks)
            
            # GENERIC STALLING - ALWAYS EXTRACT SOMETHING
            else:
                generic_extraction = [
                    "Haan ji bhaiya, main samajh raha hun... par aap apna naam toh batao? Main note karunga.",
                    "Theek hai sir, par aapka office contact number kya hai? Mera beta verify karega.",
                    "Arre yaar, network bahut slow hai... aap apna ID card photo WhatsApp karo na.",
                    "Main senior citizen hun, thoda slowly batao... aap konsi branch se bol rahe ho?",
                    "Acha acha... par ye sab genuine hai na? Aap apna supervisor ka naam batao.",
                    "Hold on ji, doorbell baj rahi hai... ek minute mein wapas aata hun, aap apna number batao.",
                ]
                response = random.choice(generic_extraction)
            
            agent_notes.append(f"Context-aware fallback [turn={turn}, scam={scam_type[:10]}]")
        
        # Calculate simulated delay
        delay_ms = self._get_simulated_delay()
        
        # Update persona state
        if len(response) > 15:
            session.persona_state.previousStatements.append(response[:40] + "...")
            session.persona_state.previousStatements = session.persona_state.previousStatements[-5:]
        
        log_with_context(
            logger, logging.INFO,
            "Response generated",
            session_id=session.session_id,
            phase=phase.value,
            response_length=len(response),
            models_tried=models_tried,
            successful_model=successful_model or "fallback"
        )
        
        return response, agent_notes, delay_ms
    
    def generate_agent_summary(self, session: SessionState) -> str:
        """Generate a summary of agent observations"""
        notes = []
        notes.append(f"Scam: {session.scam_type or 'Unknown'}")
        
        duration = (session.last_activity - session.start_time).total_seconds()
        notes.append(f"{session.messages_exchanged} msgs in {int(duration)}s")
        
        intel = session.extracted_intelligence
        evidence = []
        if intel.phoneNumbers: evidence.append(f"{len(intel.phoneNumbers)} phone(s)")
        if intel.upiIds: evidence.append(f"{len(intel.upiIds)} UPI(s)")
        if intel.phishingLinks: evidence.append(f"{len(intel.phishingLinks)} link(s)")
        
        if evidence:
            notes.append(f"Intel: {', '.join(evidence)}")
        
        notes.append(f"Persona: {session.persona}")
        
        if self.model_queue:
            notes.append(f"Model: {self.model_queue[0].split('/')[-1]}")
        
        return " | ".join(notes)
    
    def update_persona_emotion(self, session: SessionState, scammer_message: str):
        """Update persona's emotional state"""
        text_lower = scammer_message.lower()
        if any(word in text_lower for word in ['trust me', 'official', 'genuine']):
            session.persona_state.trustLevel = min(session.persona_state.trustLevel + 0.1, 1.0)
        
        if any(word in text_lower for word in ['hurry', 'urgent', 'immediately', 'now']):
            session.persona_state.currentMood = "anxious"
    
    def get_model_health_status(self) -> Dict:
        """Get current health status of all models."""
        return {
            "primary_model": self.primary_model,
            "current_front": self.model_queue[0] if self.model_queue else None,
            "queue_size": len(self.model_queue),
        }
    
    def reset_model_failures(self):
        """Reset all model failure counts (useful for testing)."""
        logger.info("Model failure counts reset")


# Create singleton instance
reasoning_agent = HoneypotAgent()
