"""
Unit Tests for Intelligence Extractor Module
"""
import pytest
from intelligence_extractor import IntelligenceExtractor, extractor
from models import Message


class TestIntelligenceExtractor:
    """Test intelligence extraction functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.extractor = IntelligenceExtractor()
    
    def test_phone_number_extraction_indian(self):
        """Test extraction of Indian phone numbers"""
        text = "Call me at 9876543210 or +91 8765432109"
        extracted = self.extractor.extract_from_text(text)
        
        assert len(extracted['phone_numbers']) >= 1
    
    def test_phone_number_extraction_with_context(self):
        """Test phone extraction with contextual confidence"""
        text = "My number is 9876543210. Please call me."
        extracted = self.extractor.extract_from_text(text)
        
        assert len(extracted['phone_numbers']) >= 1
        # Check confidence score exists
        phone_conf_keys = [k for k in extracted['confidence_scores'] if k.startswith('phone:')]
        assert len(phone_conf_keys) >= 1
    
    def test_upi_id_extraction(self):
        """Test extraction of UPI IDs"""
        text = "Send payment to myupi@paytm or payment@oksbi"
        extracted = self.extractor.extract_from_text(text)
        
        assert len(extracted['upi_ids']) >= 1
        assert any('@paytm' in upi or '@oksbi' in upi for upi in extracted['upi_ids'])
    
    def test_phishing_link_extraction(self):
        """Test extraction of suspicious links"""
        text = "Click here: http://verify-your-bank.xyz/login or bit.ly/secure123"
        extracted = self.extractor.extract_from_text(text)
        
        assert len(extracted['phishing_links']) >= 1
    
    def test_legitimate_link_filtering(self):
        """Test that legitimate links are handled correctly"""
        text = "Visit https://www.google.com for help"
        extracted = self.extractor.extract_from_text(text)
        
        # Legitimate links without suspicious keywords should be filtered
        suspicious = [l for l in extracted['phishing_links'] if 'verify' in l.lower() or 'secure' in l.lower() or 'login' in l.lower()]
        # google.com without suspicious keywords should not appear
        assert not any('google.com' in l and 'verify' not in l.lower() for l in extracted['phishing_links'])
    
    def test_bank_account_extraction(self):
        """Test extraction of bank account numbers"""
        text = "A/C No: 123456789012 IFSC: SBIN0001234"
        extracted = self.extractor.extract_from_text(text)
        
        # Should extract IFSC code at minimum
        assert len(extracted['bank_accounts']) >= 1 or 'SBIN0001234' in str(extracted)
    
    def test_email_extraction(self):
        """Test extraction of email addresses"""
        text = "Contact support@fraudbank.com for assistance"
        extracted = self.extractor.extract_from_text(text)
        
        assert len(extracted['email_addresses']) >= 1
        assert 'support@fraudbank.com' in extracted['email_addresses']
    
    def test_person_name_extraction(self):
        """Test extraction of person names"""
        text = "I am Mr. Rahul Sharma from State Bank customer care"
        extracted = self.extractor.extract_from_text(text)
        
        assert len(extracted['person_names']) >= 1
    
    def test_organization_extraction(self):
        """Test extraction of organization names"""
        text = "This is from State Bank customer service department"
        extracted = self.extractor.extract_from_text(text)
        
        assert len(extracted['organization_names']) >= 1 or 'State Bank' in str(extracted)
    
    def test_payment_platform_extraction(self):
        """Test extraction of payment platform mentions"""
        text = "Pay using Paytm or PhonePe to this number"
        extracted = self.extractor.extract_from_text(text)
        
        assert len(extracted['payment_platforms']) >= 1
        assert any(p.lower() in ['paytm', 'phonepe'] for p in extracted['payment_platforms'])
    
    def test_geographic_extraction(self):
        """Test extraction of geographic indicators"""
        text = "I am calling from Mumbai office, area code 022"
        extracted = self.extractor.extract_from_text(text)
        
        indicators = extracted['geographic_indicators']
        assert len(indicators) >= 1
    
    def test_reference_number_extraction(self):
        """Test extraction of reference numbers"""
        text = "Your case reference number is REF123456789"
        extracted = self.extractor.extract_from_text(text)
        
        assert len(extracted['reference_numbers']) >= 1
    
    def test_suspicious_keyword_extraction(self):
        """Test extraction of suspicious keywords"""
        text = "URGENT: Verify your OTP immediately or account will be blocked"
        extracted = self.extractor.extract_from_text(text)
        
        keywords = extracted['suspicious_keywords']
        assert len(keywords) >= 2
        assert any(kw in keywords for kw in ['urgent', 'verify', 'otp', 'blocked'])
    
    def test_conversation_extraction(self):
        """Test extraction from full conversation"""
        messages = [
            Message(sender="scammer", text="Hello, I am Rahul from SBI", timestamp="2025-01-01T10:00:00Z"),
            Message(sender="user", text="Yes, what is it?", timestamp="2025-01-01T10:01:00Z"),
            Message(sender="scammer", text="Your account 12345678901 is blocked. Call 9876543210", timestamp="2025-01-01T10:02:00Z"),
        ]
        
        intel = self.extractor.extract_from_conversation(messages)
        
        assert len(intel.phoneNumbers) >= 1
        assert len(intel.personNames) >= 1
        assert intel.confidenceScores is not None
    
    def test_intelligence_merge(self):
        """Test merging of intelligence from multiple sources"""
        from models import ExtractedIntelligence
        
        intel1 = ExtractedIntelligence(
            phoneNumbers=["9876543210"],
            upiIds=["test@paytm"],
        )
        intel2 = ExtractedIntelligence(
            phoneNumbers=["8765432109"],
            upiIds=["test@paytm"],  # Duplicate
            personNames=["Rahul"],
        )
        
        merged = self.extractor.merge_intelligence(intel1, intel2)
        
        assert len(merged.phoneNumbers) == 2
        assert len(merged.upiIds) == 1  # Deduplicated
        assert len(merged.personNames) == 1
    
    def test_quality_score_calculation(self):
        """Test intelligence quality score calculation"""
        from models import ExtractedIntelligence
        
        intel = ExtractedIntelligence(
            phoneNumbers=["9876543210", "8765432109"],
            upiIds=["test@paytm"],
            personNames=["Rahul Sharma"],
        )
        
        score = self.extractor.calculate_quality_score(intel)
        
        assert 0 <= score <= 1
        assert score > 0.3  # Should have decent score with phone + UPI + name
    
    def test_confidence_scoring(self):
        """Test that confidence scores are calculated correctly"""
        text = "My mobile number is 9876543210"  # With context
        extracted = self.extractor.extract_from_text(text)
        
        # Should have higher confidence due to context
        phone_conf_keys = [k for k in extracted['confidence_scores'] if k.startswith('phone:')]
        if phone_conf_keys:
            conf = extracted['confidence_scores'][phone_conf_keys[0]]
            assert conf >= 0.5
    
    def test_hindi_keyword_extraction(self):
        """Test extraction of Hindi keywords"""
        text = "तुरंत verify करें, आपका खाता ब्लॉक हो जाएगा"
        extracted = self.extractor.extract_from_text(text)
        
        keywords = extracted['suspicious_keywords']
        # Should detect Hindi keywords
        assert len(keywords) >= 1


class TestGlobalExtractor:
    """Test global extractor instance"""
    
    def test_extractor_initialized(self):
        """Test that global extractor is initialized"""
        assert extractor is not None
    
    def test_extractor_has_patterns(self):
        """Test that extractor has patterns defined"""
        assert hasattr(extractor, 'patterns')
        assert 'phone_numbers' in extractor.patterns
        assert 'upi_ids' in extractor.patterns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
