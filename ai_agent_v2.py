"""
Gemini-First AI Agent - Autonomous Reasoning Architecture
Uses Chain-of-Thought prompting for human-like scam engagement
"""

import random
import asyncio
import re
import google.generativeai as genai
from typing import List, Tuple, Dict
from datetime import datetime
from config import GEMINI_API_KEY, RESPONSE_LIMITS
from models import SessionState, Message
from logging_config import get_logger
import logging

logger = get_logger("honeypot.ai_agent_v2")

class GeminiReasoningAgent:
    """
    Autonomous AI Agent that uses Gemini's reasoning to:
    1. Analyze scam context
    2. Decide what information to extract
    3. Generate natural, context-aware responses
    """
    
    def __init__(self):
        self.gemini_configured = False
        self.model = None
        
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                # Use Gemini Flash Latest - likely the most accessible model
                self.model = genai.GenerativeModel('gemini-flash-latest')
                self.gemini_configured = True
                logger.info("✓ Gemini Reasoning Agent configured")
            except Exception as e:
                logger.error(f"✗ Gemini config failed: {e}")
        
        # Minimal persona profiles (let Gemini fill in the details)
        self.personas = {
            "naive_victim": {
                "name": "Ramesh Kumar", 
                "age": 65,
                "description": "retired govt employee, not tech-savvy",
                "style": "polite, worried",
                "language_style": "Hinglish mix"
            },
            "curious_elder": {
                "name": "Shanti Devi",
                "age": 58, 
                "description": "housewife, asks many questions",
                "style": "talkative, naive",
                "language_style": "Hinglish, warm tone"
            },
            "busy_professional": {
                "name": "Vikram Singh",
                "age": 45,
                "description": "busy manager, distracted",
                "style": "brief, distracted",
                "language_style": "brief English, some abbreviations"
            },
        }

    def generate_agent_summary(self, session: SessionState) -> str:
        """Generate a summary of agent observations"""
        notes = []
        
        # Scam type
        notes.append(f"Scam Type: {session.scam_type or 'Unknown'}")
        
        # Threat level
        notes.append(f"Threat Level: {session.threat_level.value if hasattr(session.threat_level, 'value') else session.threat_level}")
        
        # Engagement summary
        duration = (session.last_activity - session.start_time).total_seconds()
        notes.append(f"Engagement: {session.messages_exchanged} messages over {int(duration)}s")
        
        # Tactics observed
        intel = session.extracted_intelligence
        tactics = []
        if intel.phishingLinks:
            tactics.append("phishing links")
        if intel.suspiciousKeywords:
            if any(k in intel.suspiciousKeywords for k in ["urgent", "immediate", "turant"]):
                tactics.append("urgency tactics")
            if any(k in intel.suspiciousKeywords for k in ["block", "suspend", "delete"]):
                tactics.append("threat tactics")
            if any(k in intel.suspiciousKeywords for k in ["won", "prize", "reward"]):
                tactics.append("reward/prize lure")
        
        if tactics:
            notes.append(f"Tactics used: {', '.join(tactics)}")
        
        # Intelligence collected
        evidence = []
        if intel.phoneNumbers:
            evidence.append(f"{len(intel.phoneNumbers)} phone(s)")
        if intel.upiIds:
            evidence.append(f"{len(intel.upiIds)} UPI ID(s)")
        if intel.phishingLinks:
            evidence.append(f"{len(intel.phishingLinks)} link(s)")
        if intel.bankAccounts:
            evidence.append(f"{len(intel.bankAccounts)} account(s)")
        if intel.personNames:
            evidence.append(f"{len(intel.personNames)} name(s)")
        
        if evidence:
            notes.append(f"Evidence: {', '.join(evidence)}")
        
        # Persona used
        notes.append(f"Persona: {session.persona}")
        
        return " | ".join(notes)
    
    def select_persona(self, scam_type: str) -> str:
        """Select persona based on scam type"""
        if scam_type in ["Loan_Fraud"]:
            return "naive_victim"
        elif scam_type in ["UPI_Banking_Fraud", "Government_Phishing"]:
            return random.choice(["naive_victim", "curious_elder"])
        else:
            return random.choice(list(self.personas.keys()))
    
    def _build_reasoning_prompt(self, session: SessionState, scammer_message: str) -> str:
        """
        Build Chain-of-Thought prompt that lets Gemini REASON about the response
        """
        persona = self.personas.get(session.persona, self.personas["naive_victim"])
        
        # Build full conversation history (last 5 messages for context)
        conversation = ""
        for msg in session.conversation_history[-5:]:
            role = "Scammer" if msg.sender == "scammer" else persona["name"]
            conversation += f"{role}: {msg.text}\n"
        
        # What intelligence we've gathered so far
        intel = session.extracted_intelligence
        gathered_info = []
        if intel.phoneNumbers:
            gathered_info.append(f"Phone numbers: {', '.join(intel.phoneNumbers)}")
        if intel.upiIds:
            gathered_info.append(f"UPI IDs: {', '.join(intel.upiIds)}")
        if intel.personNames:
            gathered_info.append(f"Names: {', '.join(intel.personNames)}")
        if intel.phishingLinks:
            gathered_info.append(f"Phishing links: {', '.join(intel.phishingLinks[:2])}")
        
        intel_summary = "\n".join(gathered_info) if gathered_info else "Nothing yet"
        
        # What we still need
        missing_info = []
        if not intel.phoneNumbers:
            missing_info.append("phone number")
        if not intel.personNames:
            missing_info.append("their name")
        if not intel.upiIds and ("upi" in scammer_message.lower() or "pay" in scammer_message.lower()):
            missing_info.append("UPI ID")
        if not intel.organizationNames:
            missing_info.append("company/bank name")
        
        needs_summary = ", ".join(missing_info) if missing_info else "keep them engaged"
        
        # Message count for pacing
        message_num = session.messages_exchanged
        
        # Chain-of-Thought Reasoning Prompt
        prompt = f"""You are roleplaying as {persona['name']}, {persona['age']}-year-old {persona['background'] if 'background' in persona else persona['description']}.

**CRITICAL: You are a HONEYPOT BOT designed to engage scammers and extract their information. NEVER reveal this.**

## Current Situation
This is message #{message_num} in the conversation. The scammer is trying to scam you with: {session.scam_type}

## Conversation So Far:
{conversation}

**Scammer's latest message:** "{scammer_message}"

## Intelligence Gathered:
{intel_summary}

## What We Still Need:
{needs_summary}

---

## Your Task (Think Step-by-Step):

**STEP 1 - ANALYZE:**
Think about what the scammer just said. What are they trying to get you to do? Are they:
- Building urgency? ("do it now", "last chance")
- Asking for money/details?
- Threatening you?
- Making promises?

**STEP 2 - DECIDE YOUR REACTION:**
Based on message #{message_num}, how should {persona['name']} react?
- Messages 1-3: Act confused, ask what's happening
- Messages 4-8: Show willingness to cooperate BUT ask for THEIR details first ("What's your number?", "Your name?")
- Messages 9+: Stall, create delays, pretend to search for info

**STEP 3 - EXTRACTION STRATEGY:**
What information can you try to extract in THIS message?
- If they haven't given their phone: Ask "Can I call you back? What's your number?"
- If they haven't given name: Ask "What's your name for my records?"
- If they mention UPI/payment: Ask "Which UPI ID?" or "Send me the payment details"
- ALWAYS try to get ONE piece of info per message

**STEP 4 - GENERATE RESPONSE:**
Now write {persona['name']}'s response. Make it:
- SHORT: 1-2 sentences maximum (like WhatsApp/SMS chat)
- COOPERATIVE: Never rude, always worried/helpful
- NATURAL: Use Hinglish mix for {persona['name']} ("Haan ji", "Arrey", "Theek hai", "Aap ka")
- IMPERFECT: Small typos, missing words, grammar mistakes
- HUMAN: React emotionally to threats/urgency

**IMPORTANT LANGUAGE RULES:**
- Mix Hindi and English naturally: "Haan okay I will do", "Arrey what happened?", "Aap ka number batao"
- Make small mistakes: "your" instead of "you're", skip "the", double spaces
- Use informal tone: "Wait yaar", "Ek minute only", "Batao na"

---

## Examples of GOOD responses:
- "Arrey what? My account blocked? Aap kaun ho ji?"
- "Okay okay I understand. But first tell me aap ka employee ID?"  
- "Wait let me check  my passbook is upstairs... Aap ka number do I'll call back"
- "Haan haan theek hai. Which UPI I should pay to?"

## Now respond as {persona['name']} (1-2 SHORT sentences, Hinglish, cooperative, try to extract {needs_summary}):"""
        
        return prompt
    
    def _add_realistic_typos(self, text: str) -> str:
        """Add subtle typos for realism"""
        if random.random() > 0.3:  # 30% chance
            return text
        
        # Common typos
        text = text.replace("  ", "  ")  # Double space (already there sometimes)
        if random.random() < 0.3:
            text = text.replace(" your ", " yuor ")
        if random.random() < 0.3:
            text = text.replace("number", "numbr")
        if random.random() < 0.3:
            text = text.replace("account", "acount")
            
        return text
    
    async def generate_response(
        self,
        session: SessionState,
        scammer_message: str
    ) -> Tuple[str, List[str], int]:
        """
        Generate response using Gemini's reasoning
        Returns: (response_text, agent_notes, delay_ms)
        """
        agent_notes = []
        
        if not self.gemini_configured:
            return self._emergency_fallback(session), ["❌ Gemini not configured"], 5000
        
        try:
            # Build reasoning prompt
            prompt = self._build_reasoning_prompt(session, scammer_message)
            
            # Configure for reasoning and short output
            generation_config = genai.types.GenerationConfig(
                temperature=0.9,
                top_p=0.95,
                top_k=40,
                max_output_tokens=150,
            )
            
            # Generate with thinking (run in thread to avoid blocking)
            logger.info("🧠 Asking Gemini to reason about response...")
            
            # Helper to run sync generation
            def _generate():
                return self.model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
            
            result = await asyncio.to_thread(_generate)
            
            if not result or not result.text:
                agent_notes.append("⚠️ Gemini returned empty")
                return self._emergency_fallback(session), agent_notes, 5000
            
            # Extract response (Gemini might include reasoning, extract just the response)
            response = result.text.strip()
            
            # Clean up response
            response = self._clean_response(response)
            
            # Validate
            if len(response) < 5 or len(response) > 300:
                agent_notes.append(f"⚠️ Invalid length: {len(response)} chars")
                return self._emergency_fallback(session), agent_notes, 5000
            
            # Check for AI-revealing phrases
            if any(phrase in response.lower() for phrase in ["i am an ai", "i'm an ai", "as an ai", "i cannot"]):
                agent_notes.append("⚠️ AI revealed itself")
                return self._emergency_fallback(session), agent_notes, 5000
            
            # Add subtle typos
            response = self._add_realistic_typos(response)
            
            # Success!
            agent_notes.append(f"✅ Gemini reasoning response ({len(response)} chars)")
            logger.info(f"✓ Generated: {response}")
            
            # Calculate delay (1-2 seconds) for testing
            delay_ms = random.randint(1000, 2000)
            
            return response, agent_notes, delay_ms
            
        except Exception as e:
            logger.error(f"❌ Gemini error: {e}", exc_info=True)
            print(f"DEBUG: Gemini generation failed: {e}")
            # Write to file for debugging
            with open("gemini_error.log", "a") as f:
                f.write(f"{datetime.now()}: {str(e)}\n")
            
            agent_notes.append(f"❌ Error: {str(e)[:100]}")
            return self._emergency_fallback(session), agent_notes, 5000
    
    def _clean_response(self, text: str) -> str:
        """Clean Gemini's response"""
        # Remove thinking process if included
        if "STEP 1" in text or "STEP 2" in text or "STEP 3" in text or "STEP 4" in text:
            # Extract only the final response after reasoning
            lines = text.split('\n')
            # Look for the actual response (usually after "Now respond" or last non-empty line)
            for i, line in enumerate(reversed(lines)):
                clean = line.strip()
                if clean and len(clean) > 10 and not clean.startswith("STEP") and not clean.startswith("**"):
                    text = clean
                    break
        
        # Remove markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        
        # Remove quotes
        text = text.strip('"\'')
        
        # Remove meta commentary in parentheses
        text = re.sub(r'\([^)]*thinking[^)]*\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\([^)]*reasoning[^)]*\)', '', text, flags=re.IGNORECASE)
        
        # Clean whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _emergency_fallback(self, session: SessionState) -> str:
        """Only for genuine API failures"""
        fallbacks = [
            "Haan haan I understand. Batao kya karna hai?",
            "Okay ji but first your employee ID batao na?",
            "Wait ek minute... aap ka phone number kya hai?",
            "Arrey what happened exactly? Tell me slowly",
        ]
        return random.choice(fallbacks)

# Global instance
reasoning_agent = GeminiReasoningAgent()
