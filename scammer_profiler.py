"""
Global Scammer Profiler
Tracks scammer indicators (UPI, Phone, Wallet) across all sessions to identify repeat offenders.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

# Use absolute path for persistence
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scammer_database.json")
logger = logging.getLogger("honeypot.profiler")

class ScammerProfiler:
    def __init__(self):
        self.profiles = self._load_data()
        self.last_save = datetime.now()

    def _load_data(self) -> dict:
        if os.path.exists(DB_PATH):
            try:
                with open(DB_PATH, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load scammer DB: {e}")
                return {"upi": {}, "phone": {}, "wallet": {}}
        return {"upi": {}, "phone": {}, "wallet": {}}

    def save_data(self):
        try:
            with open(DB_PATH, 'w') as f:
                json.dump(self.profiles, f, indent=2)
            self.last_save = datetime.now()
        except Exception as e:
            logger.error(f"Failed to save scammer DB: {e}")

    def update_profile(self, identifier_type: str, identifier: str, session_id: str, scam_type: str):
        """Update or create a profile for a specific indicator"""
        if identifier_type not in self.profiles:
            self.profiles[identifier_type] = {}
        
        normalized_id = identifier.lower().strip()
        
        if normalized_id not in self.profiles[identifier_type]:
            self.profiles[identifier_type][normalized_id] = {
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "sessions": [session_id],
                "scam_types": [scam_type],
                "hit_count": 1,
                "notes": []
            }
        else:
            profile = self.profiles[identifier_type][normalized_id]
            profile["last_seen"] = datetime.now().isoformat()
            if session_id not in profile["sessions"]:
                profile["sessions"].append(session_id)
            if scam_type not in profile["scam_types"]:
                profile["scam_types"].append(scam_type)
            profile["hit_count"] += 1

        # Periodic auto-save
        if (datetime.now() - self.last_save).seconds > 60:
            self.save_data()

    def get_profile_summary(self, identifier: str) -> Optional[dict]:
        """Check if an identifier is a known offender"""
        normalized_id = identifier.lower().strip()
        for cat in ["upi", "phone", "wallet"]:
            if normalized_id in self.profiles.get(cat, {}):
                return {
                    "category": cat,
                    "hit_count": self.profiles[cat][normalized_id]["hit_count"],
                    "known_scam_types": self.profiles[cat][normalized_id]["scam_types"],
                    "is_repeat_offender": self.profiles[cat][normalized_id]["hit_count"] > 1
                }
        return None

# Global instance
profiler = ScammerProfiler()
