"""
Enhanced Intelligence Extractor Module
Extracts actionable intelligence with NER, context awareness, and confidence scoring
"""
import re
from typing import List, Set, Dict, Tuple, Optional
from models import ExtractedIntelligence, Message, IntelligenceConfidence
from config import PAYMENT_PLATFORMS, INDIAN_CITIES, INDIAN_CITY_CODES
from logging_config import get_logger, log_with_context
import logging

logger = get_logger("honeypot.intelligence_extractor")


class IntelligenceExtractor:
    """
    Enhanced intelligence extraction from scam conversations:
    - Bank account numbers with validation
    - UPI IDs with context verification
    - Phishing links with deobfuscation
    - Phone numbers with area code analysis
    - Person/organization names via pattern matching
    - Payment platform mentions
    - Social media handles
    - Geographic indicators
    - Confidence scoring for each piece
    """
    
    def __init__(self):
        # Regex patterns for extraction
        self.patterns = {
            'phone_numbers': [
                r'(?:\+91[\s-]?)?[6-9]\d{9}',  # Standard Indian mobile
                r'\b[6-9]\d{9}\b',             # 10-digit Indian mobile format
                r'(?:\+\d{1,3}[\s-]?)?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}',  # International
            ],
            'upi_ids': [
                r'[a-zA-Z0-9._-]+@(?:upi|paytm|oksbi|okaxis|okicici|okhdfcbank|ybl|ibl|axl|sbi|hdfc|icici|kotak|axis|barodampay|apl|rbl|citi|dbs|federal|indus|idbi|pnb|bob|canara|jio|phonepe|gpay|amazonpay)',
                r'[a-zA-Z0-9._-]+@[a-zA-Z]{2,}(?:upi|bank)',
            ],
            'bank_accounts': [
                r'\b\d{9,18}\b',  # Bank account number pattern
                r'[A-Z]{4}0[A-Z0-9]{6}',  # IFSC code pattern
                r'A/C(?:\s+)?(?:No\.?|Number)?(?:\s+)?:?(?:\s+)?\d{9,18}',
            ],
            'phishing_links': [
                r'https?://[^\s<>"{}|\\^`\[\]]+',
                r'www\.[^\s<>"{}|\\^`\[\]]+',
                r'bit\.ly/[a-zA-Z0-9]+',
                r'tinyurl\.com/[a-zA-Z0-9]+',
                r'rb\.gy/[a-zA-Z0-9]+',
                r'is\.gd/[a-zA-Z0-9]+',
            ],
            'email_addresses': [
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            ],
            'social_handles': [
                r'@[a-zA-Z0-9_]{3,30}',  # Twitter/Instagram handle
                r'(?:instagram|twitter|facebook)\.com/([a-zA-Z0-9._]+)',
                r't\.me/([a-zA-Z0-9_]+)',  # Telegram
            ],
            'reference_numbers': [
                r'(?:ref(?:erence)?|case|ticket|complaint)[\s#:.-]*([A-Z0-9]{6,20})',
                r'[A-Z]{2,4}[\d]{8,15}',  # Standard reference format
            ],
            'crypto_wallets': [
                r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b',  # BTC Legacy
                r'\bbc1[a-np-z0-9]{39,59}\b',           # BTC Bech32
                r'\b0x[a-fA-F0-9]{40}\b',               # ETH / ERC20
                r'\bT[A-Za-z1-9]{33}\b',                # TRC20 (USDT)
            ],
            'person_names': [
                r'(?i)(?:Name|Holder|Beneficiary|Agent|Officer)[\s#:.-]*([a-zA-Z\s]{4,30})',
            ],
            'vehicle_numbers': [
                r'\b[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}\b',  # Standard Indian Vehicle Number (e.g., MH12AB1234)
            ],
            'employee_ids': [
                r'(?i)(?:Employee|Agent|ID|Badge)[\s#:.-]*([A-Z0-9]{4,15})',
            ],
        }
        
        # Context phrases that indicate intentional sharing
        self.context_indicators = {
            'phone_context': [
                r'(?:my|our|this)\s+(?:number|phone|mobile|contact)\s+(?:is|:)',
                r'(?:call|contact|reach)\s+(?:me|us)\s+(?:at|on)',
                r'(?:whatsapp|telegram)\s+(?:me|us)?\s*(?:at|on)?',
            ],
            'upi_context': [
                r'(?:my|our)\s+(?:upi|payment)\s+(?:id|address)\s+(?:is|:)',
                r'(?:send|transfer)\s+(?:to|at)',
                r'(?:pay|payment)\s+(?:to|at)',
            ],
            'account_context': [
                r'(?:account|a/c)\s+(?:number|no\.?)\s*(?:is|:)?',
                r'(?:transfer|send)\s+(?:to|in)\s+(?:account|a/c)',
            ]
        }
        
        # Suspicious keywords to track
        self.suspicious_keywords = [
            # Urgency
            "urgent", "immediate", "now", "today", "hurry", "fast", "quick",
            "turant", "abhi", "jaldi", "तुरंत", "अभी", "जल्दी",
            # Threats
            "block", "suspend", "delete", "terminate", "deactivate", "expire",
            "banned", "locked", "frozen", "compromised", "hacked",
            "ब्लॉक", "निलंबित", "हैक",
            # Actions
            "verify", "click", "update", "confirm", "share", "send",
            "download", "install", "call", "transfer", "pay",
            "सत्यापित", "क्लिक", "भेजें", "डाउनलोड",
            # Lures
            "won", "winner", "prize", "lottery", "gift", "reward", "free",
            "selected", "eligible", "approved", "congratulations",
            "जीत", "इनाम", "मुफ्त", "बधाई",
            # Financial
            "otp", "pin", "cvv", "password", "account", "bank", "upi",
            "credit", "debit", "loan", "emi", "interest",
            "पासवर्ड", "खाता", "बैंक",
            # Government
            "aadhaar", "pan", "kyc", "gstin", "income tax", "refund",
            "आधार", "पैन",
        ]
        
        # Person name patterns (common Indian name patterns)
        self.name_patterns = [
            r'(?:i\s+am|this\s+is|my\s+name\s+is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:mr\.?|mrs\.?|ms\.?|shri|smt\.?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:officer|manager|executive|agent)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        # Organization patterns
        self.org_patterns = [
            r'(?:from|at|of)\s+([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*)(?:\s+bank|\s+company|\s+ltd|\s+pvt|\s+inc)',
            r'(?:customer\s+(?:care|service|support)\s+of)\s+([A-Z][a-zA-Z]+)',
            r'(State\s+Bank|HDFC|ICICI|Axis|Kotak|Punjab\s+National|Bank\s+of\s+[A-Za-z]+)',
        ]
        
        # Legitimate domains to filter
        self.legitimate_domains = [
            'google.com', 'facebook.com', 'twitter.com', 'linkedin.com',
            'github.com', 'microsoft.com', 'apple.com', 'amazon.in',
            'flipkart.com', 'sbi.co.in', 'hdfcbank.com', 'icicibank.com',
            'onlinesbi.com', 'netbanking.hdfcbank.com',
        ]
    
    def _has_context(self, text: str, pattern_category: str) -> bool:
        """Check if extraction has contextual support"""
        patterns = self.context_indicators.get(pattern_category, [])
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _calculate_confidence(
        self,
        item: str,
        item_type: str,
        text: str,
        has_context: bool
    ) -> float:
        """Calculate confidence score for extracted item"""
        base_confidence = 0.5
        
        # Context increases confidence
        if has_context:
            base_confidence += 0.25
        
        # Type-specific adjustments
        if item_type == 'phone':
            # Indian mobile numbers starting with 6-9 are more reliable
            if re.match(r'^[6-9]\d{9}$', item.replace('+91', '').replace(' ', '').replace('-', '')):
                base_confidence += 0.15
        
        elif item_type == 'upi':
            # Known UPI handles are more reliable
            known_handles = ['@paytm', '@ybl', '@oksbi', '@okaxis', '@phonepe', '@gpay']
            if any(h in item.lower() for h in known_handles):
                base_confidence += 0.20
        
        elif item_type == 'link':
            # Short URLs are more suspicious
            if any(s in item.lower() for s in ['bit.ly', 'tinyurl', 'rb.gy', 't.co']):
                base_confidence += 0.20
            # IP addresses in URLs are highly suspicious
            if re.search(r'\d+\.\d+\.\d+\.\d+', item):
                base_confidence += 0.30
        
        elif item_type == 'account':
            # Longer account numbers are more likely genuine
            digits = re.sub(r'\D', '', item)
            if 11 <= len(digits) <= 16:
                base_confidence += 0.15
        
        elif item_type == 'crypto':
            base_confidence += 0.20 # High confidence for specialized format
            if item.startswith('bc1'):
                base_confidence += 0.10 # Bech32 is very specific
        
        return min(base_confidence, 1.0)
    
    def _extract_person_names(self, text: str) -> List[Tuple[str, float]]:
        """Extract person names with confidence scores"""
        names = []
        for pattern in self.name_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) >= 3 and not any(c.isdigit() for c in match):
                    # Filter out common false positives
                    if match.lower() not in ['the', 'this', 'that', 'bank', 'officer']:
                        confidence = 0.6 if ' ' in match else 0.4  # Full names have higher confidence
                        names.append((match.strip(), confidence))
        return names
    
    def _extract_organization_names(self, text: str) -> List[Tuple[str, float]]:
        """Extract organization names with confidence"""
        orgs = []
        for pattern in self.org_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) >= 3:
                    # Known banks have higher confidence
                    known_banks = ['sbi', 'hdfc', 'icici', 'axis', 'kotak', 'pnb', 'bob']
                    confidence = 0.8 if any(b in match.lower() for b in known_banks) else 0.5
                    orgs.append((match.strip(), confidence))
        return orgs
    
    def _extract_payment_platforms(self, text: str) -> List[str]:
        """Extract payment platform mentions"""
        text_lower = text.lower()
        found = []
        for platform in PAYMENT_PLATFORMS:
            if platform.lower() in text_lower:
                found.append(platform)
        return list(set(found))
    
    def _extract_geographic_indicators(self, text: str) -> List[str]:
        """Extract geographic indicators (cities, area codes)"""
        indicators = []
        text_lower = text.lower()
        
        # Check for city names
        for city in INDIAN_CITIES:
            if city in text_lower:
                indicators.append(city.title())
        
        # Check for area codes in phone numbers
        for code, city in INDIAN_CITY_CODES.items():
            if code in text:
                indicators.append(f"{city} ({code})")
        
        return list(set(indicators))
    
    def _extract_social_handles(self, text: str) -> List[str]:
        """Extract social media handles"""
        handles = []
        for pattern in self.patterns['social_handles']:
            matches = re.findall(pattern, text)
            handles.extend(matches if isinstance(matches[0] if matches else '', str) else [m[0] for m in matches])
        return list(set(handles))
    
    def _extract_reference_numbers(self, text: str) -> List[str]:
        """Extract reference/case numbers"""
        refs = []
        for pattern in self.patterns['reference_numbers']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) >= 6:
                    refs.append(match.upper())
        return list(set(refs))
    
    def extract_from_text(self, text: str) -> Dict:
        """Extract all intelligence from a single text with confidence scores"""
        extracted = {
            'phone_numbers': set(),
            'upi_ids': set(),
            'bank_accounts': set(),
            'phishing_links': set(),
            'email_addresses': set(),
            'suspicious_keywords': set(),
            'person_names': set(),
            'organization_names': set(),
            'payment_platforms': set(),
            'social_handles': set(),
            'geographic_indicators': set(),
            'reference_numbers': set(),
            'crypto_wallets': set(),
            'vehicle_numbers': set(),
            'employee_ids': set(),
            'confidence_scores': {},
        }
        
        # Extract using regex patterns
        for field, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    extracted[field].add(match)
        
        # Calculate confidence for key items
        phone_context = self._has_context(text, 'phone_context')
        upi_context = self._has_context(text, 'upi_context')
        account_context = self._has_context(text, 'account_context')
        
        for phone in extracted['phone_numbers']:
            conf = self._calculate_confidence(phone, 'phone', text, phone_context)
            extracted['confidence_scores'][f'phone:{phone}'] = conf
        
        for upi in extracted['upi_ids']:
            conf = self._calculate_confidence(upi, 'upi', text, upi_context)
            extracted['confidence_scores'][f'upi:{upi}'] = conf
        
        for link in extracted['phishing_links']:
            conf = self._calculate_confidence(link, 'link', text, False)
            extracted['confidence_scores'][f'link:{link}'] = conf
        
        for wallet in extracted['crypto_wallets']:
            conf = self._calculate_confidence(wallet, 'crypto', text, False)
            extracted['confidence_scores'][f'wallet:{wallet}'] = conf
        
        # Extract suspicious keywords
        text_lower = text.lower()
        for keyword in self.suspicious_keywords:
            if keyword.lower() in text_lower:
                extracted['suspicious_keywords'].add(keyword.lower())
        
        # Extract person names
        for name, conf in self._extract_person_names(text):
            extracted['person_names'].add(name)
            extracted['confidence_scores'][f'name:{name}'] = conf
        
        # Extract organization names
        for org, conf in self._extract_organization_names(text):
            extracted['organization_names'].add(org)
            extracted['confidence_scores'][f'org:{org}'] = conf
        
        # Extract payment platforms
        extracted['payment_platforms'] = set(self._extract_payment_platforms(text))
        
        # Extract geographic indicators
        extracted['geographic_indicators'] = set(self._extract_geographic_indicators(text))
        
        # Extract social handles
        extracted['social_handles'] = set(self._extract_social_handles(text))
        
        # Extract reference numbers
        extracted['reference_numbers'] = set(self._extract_reference_numbers(text))
        
        # Clean up phishing links
        filtered_links = set()
        for link in extracted['phishing_links']:
            is_legitimate = any(domain in link.lower() for domain in self.legitimate_domains)
            # Keep links that look suspicious or aren't from known legitimate sources
            if not is_legitimate or any(sus in link.lower() for sus in ['verify', 'secure', 'login', 'confirm', 'update']):
                filtered_links.add(link)
        extracted['phishing_links'] = filtered_links
        
        # 🚨 CROSS-VERIFICATION: Resolve overlaps between Phone and Bank Account
        final_phones = set()
        final_accounts = set()

        # Step 1: Identify "strong" account matches (context + long length)
        for acc in extracted['bank_accounts']:
            digits = re.sub(r'\D', '', acc)
            if 9 <= len(digits) <= 18:
                # If it has "A/C" prefix, it's almost certainly an account
                if re.search(r'a/c|account|bank', acc.lower()) or account_context:
                    final_accounts.add(acc)
                    conf = self._calculate_confidence(acc, 'account', text, account_context)
                    extracted['confidence_scores'][f'account:{acc}'] = conf
                else:
                    # Generic digits - check if it looks like a phone
                    if not re.match(r'^[6-9]\d{9}$', digits):
                        final_accounts.add(acc)
                        conf = self._calculate_confidence(acc, 'account', text, account_context)
                        extracted['confidence_scores'][f'account:{acc}'] = conf

        # Step 2: Filter phones (must not be in the finalized accounts)
        for phone in extracted['phone_numbers']:
            digits = re.sub(r'\D', '', phone).replace('91', '', 1) if '91' in phone else re.sub(r'\D', '', phone)
            
            # If this exact digit sequence is already confirmed as an account, skip phone extraction
            is_captured_as_acc = any(digits in re.sub(r'\D', '', a) for a in final_accounts)
            
            if not is_captured_as_acc:
                # Basic validation for Indian phone (must start with 6-9 if 10 digits)
                if len(digits) == 10 and re.match(r'^[6-9]', digits):
                    final_phones.add(phone)
                    conf = self._calculate_confidence(phone, 'phone', text, phone_context)
                    extracted['confidence_scores'][f'phone:{phone}'] = conf
                elif len(digits) > 10: # International or prefix
                    final_phones.add(phone)
                    conf = self._calculate_confidence(phone, 'phone', text, phone_context)
                    extracted['confidence_scores'][f'phone:{phone}'] = conf

        extracted['phone_numbers'] = final_phones
        extracted['bank_accounts'] = final_accounts
        
        return extracted
    
    def extract_from_conversation(self, messages: List[Message]) -> ExtractedIntelligence:
        """Extract intelligence from entire conversation history"""
        all_extracted = {
            'phone_numbers': set(),
            'upi_ids': set(),
            'bank_accounts': set(),
            'phishing_links': set(),
            'email_addresses': set(),
            'suspicious_keywords': set(),
            'person_names': set(),
            'organization_names': set(),
            'payment_platforms': set(),
            'social_handles': set(),
            'geographic_indicators': set(),
            'reference_numbers': set(),
        }
        
        all_confidence = {}
        
        for message in messages:
            extracted = self.extract_from_text(message.text)
            for field in all_extracted:
                all_extracted[field].update(extracted.get(field, set()))
            
            # Merge confidence scores (keep highest)
            for key, conf in extracted.get('confidence_scores', {}).items():
                if key not in all_confidence or conf > all_confidence[key]:
                    all_confidence[key] = conf
        
        # Build confidence object
        phone_conf = {k.split(':')[1]: v for k, v in all_confidence.items() if k.startswith('phone:')}
        upi_conf = {k.split(':')[1]: v for k, v in all_confidence.items() if k.startswith('upi:')}
        account_conf = {k.split(':')[1]: v for k, v in all_confidence.items() if k.startswith('account:')}
        link_conf = {k.split(':')[1]: v for k, v in all_confidence.items() if k.startswith('link:')}
        wallet_conf = {k.split(':')[1]: v for k, v in all_confidence.items() if k.startswith('wallet:')}
        
        # Calculate overall quality score
        total_items = sum(len(v) for v in all_extracted.values())
        high_conf_items = sum(1 for v in all_confidence.values() if v >= 0.7)
        overall_score = min(1.0, (high_conf_items * 0.2) + (min(total_items, 10) * 0.08))
        
        confidence = IntelligenceConfidence(
            phoneNumbers=phone_conf,
            upiIds=upi_conf,
            bankAccounts=account_conf,
            phishingLinks=link_conf,
            cryptoWallets=wallet_conf,
            overallScore=round(overall_score, 2)
        )
        
        result = ExtractedIntelligence(
            bankAccounts=list(all_extracted['bank_accounts']),
            upiIds=list(all_extracted['upi_ids']),
            phishingLinks=list(all_extracted['phishing_links']),
            phoneNumbers=list(all_extracted['phone_numbers']),
            suspiciousKeywords=list(all_extracted['suspicious_keywords']),
            emailAddresses=list(all_extracted['email_addresses']),
            personNames=list(all_extracted['person_names']),
            organizationNames=list(all_extracted['organization_names']),
            paymentPlatforms=list(all_extracted['payment_platforms']),
            socialMediaHandles=list(all_extracted['social_handles']),
            geographicIndicators=list(all_extracted['geographic_indicators']),
            referenceNumbers=list(all_extracted['reference_numbers']),
            vehicleNumbers=list(all_extracted.get('vehicle_numbers', set())),
            employeeIds=list(all_extracted.get('employee_ids', set())),
            cryptoWallets=list(all_extracted['crypto_wallets']),
            confidenceScores=confidence
        )
        
        log_with_context(
            logger, logging.DEBUG,
            "Intelligence extraction complete",
            phone_count=len(result.phoneNumbers),
            upi_count=len(result.upiIds),
            link_count=len(result.phishingLinks),
            quality_score=overall_score
        )
        
        return result
    
    def merge_intelligence(
        self,
        existing: ExtractedIntelligence,
        new: ExtractedIntelligence
    ) -> ExtractedIntelligence:
        """Merge new intelligence with existing"""
        # Merge basic lists
        merged = ExtractedIntelligence(
            bankAccounts=list(set(existing.bankAccounts + new.bankAccounts)),
            upiIds=list(set(existing.upiIds + new.upiIds)),
            phishingLinks=list(set(existing.phishingLinks + new.phishingLinks)),
            phoneNumbers=list(set(existing.phoneNumbers + new.phoneNumbers)),
            suspiciousKeywords=list(set(existing.suspiciousKeywords + new.suspiciousKeywords)),
            emailAddresses=list(set(existing.emailAddresses + new.emailAddresses)),
            personNames=list(set(existing.personNames + new.personNames)),
            organizationNames=list(set(existing.organizationNames + new.organizationNames)),
            paymentPlatforms=list(set(existing.paymentPlatforms + new.paymentPlatforms)),
            socialMediaHandles=list(set(existing.socialMediaHandles + new.socialMediaHandles)),
            geographicIndicators=list(set(existing.geographicIndicators + new.geographicIndicators)),
            referenceNumbers=list(set(existing.referenceNumbers + new.referenceNumbers)),
            cryptoWallets=list(set(existing.cryptoWallets + new.cryptoWallets)),
            vehicleNumbers=list(set(existing.vehicleNumbers + new.vehicleNumbers)),
            employeeIds=list(set(existing.employeeIds + new.employeeIds)),
        )
        
        # Merge confidence scores (keep highest)
        if existing.confidenceScores and new.confidenceScores:
            merged_phone_conf = {**existing.confidenceScores.phoneNumbers}
            for k, v in new.confidenceScores.phoneNumbers.items():
                if k not in merged_phone_conf or v > merged_phone_conf[k]:
                    merged_phone_conf[k] = v
            
            merged_upi_conf = {**existing.confidenceScores.upiIds}
            for k, v in new.confidenceScores.upiIds.items():
                if k not in merged_upi_conf or v > merged_upi_conf[k]:
                    merged_upi_conf[k] = v
            
            merged_account_conf = {**existing.confidenceScores.bankAccounts}
            for k, v in new.confidenceScores.bankAccounts.items():
                if k not in merged_account_conf or v > merged_account_conf[k]:
                    merged_account_conf[k] = v
            
            merged_link_conf = {**existing.confidenceScores.phishingLinks}
            for k, v in new.confidenceScores.phishingLinks.items():
                if k not in merged_link_conf or v > merged_link_conf[k]:
                    merged_link_conf[k] = v

            merged_wallet_conf = {**getattr(existing.confidenceScores, 'cryptoWallets', {})}
            for k, v in getattr(new.confidenceScores, 'cryptoWallets', {}).items():
                if k not in merged_wallet_conf or v > merged_wallet_conf[k]:
                    merged_wallet_conf[k] = v
            
            merged.confidenceScores = IntelligenceConfidence(
                phoneNumbers=merged_phone_conf,
                upiIds=merged_upi_conf,
                bankAccounts=merged_account_conf,
                phishingLinks=merged_link_conf,
                cryptoWallets=merged_wallet_conf,
                overallScore=max(
                    existing.confidenceScores.overallScore,
                    new.confidenceScores.overallScore
                )
            )
        elif new.confidenceScores:
            merged.confidenceScores = new.confidenceScores
        elif existing.confidenceScores:
            merged.confidenceScores = existing.confidenceScores
        
        return merged
    
    def calculate_quality_score(self, intel: ExtractedIntelligence) -> float:
        """Calculate overall intelligence quality score"""
        score = 0.0
        
        # High-value items
        if intel.phoneNumbers:
            score += min(len(intel.phoneNumbers) * 0.15, 0.3)
        if intel.upiIds:
            score += min(len(intel.upiIds) * 0.20, 0.4)
        if intel.phishingLinks:
            score += min(len(intel.phishingLinks) * 0.10, 0.2)
        if intel.personNames:
            score += min(len(intel.personNames) * 0.10, 0.2)
        
        # Supporting evidence
        if intel.emailAddresses:
            score += 0.05
        if intel.organizationNames:
            score += 0.05
        if intel.referenceNumbers:
            score += 0.05
        if intel.vehicleNumbers:
            score += 0.10
        if intel.employeeIds:
            score += 0.10
        
        return min(score, 1.0)


# Global instance
extractor = IntelligenceExtractor()
