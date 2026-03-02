"""CaptureOrchestrator — capture pipeline coordination for ziggy-plugin.

Adapted from ziggy/orchestrators/capture_orchestrator.py.
Linear/DraftCreator/Foundation dependencies removed.
"""

import re
from typing import List, Dict, Any, Optional

from ziggy.services.entity_detector import EntityDetector


class CaptureOrchestrator:
    """Orchestrates the capture pipeline without Linear or Foundation dependencies.

    Pattern: Skill makes decisions -> Orchestrator executes

    Provides:
    - analyze(text)           Full analysis: entity type, priority, domain, owner
    - calculate_priority(text) Multi-signal priority scoring
    - match_domain(text)       Keyword-based domain matching
    - suggest_owner(domain)    Config-based owner suggestion
    - extract_items(raw_text)  Text splitting utility
    - parse_time_mentions(text) Inline time extraction
    """

    # Tentative language patterns
    TENTATIVE_PATTERNS = [
        r"\bmaybe\b", r"\bprobably\b", r"\bperhaps\b", r"\bmight\b",
        r"\bthinking about\b", r"\bconsidering\b", r"\bcould\b",
        r"\bshould probably\b", r"\bi guess\b"
    ]

    # Priority keywords
    BLOCKING_KEYWORDS = ["blocking", "need this before", "waiting on", "blocked by"]
    SEASONAL_KEYWORDS = ["before winter", "before summer", "before spring", "before fall"]
    TIME_SENSITIVE_KEYWORDS = ["running low", "closes", "spots filling", "deadline", "due"]

    # Domain keywords
    DOMAIN_KEYWORDS = {
        "home": ["home", "house", "garage", "garden", "yard", "clean", "repair",
                 "fix", "maintenance", "faucet", "organize", "declutter", "furniture"],
        "health": ["health", "doctor", "fitness", "exercise", "workout", "gym",
                   "medical", "therapy", "medication", "checkup", "wellness"],
        "personal": ["learn", "read", "book", "course", "hobby", "practice",
                     "skill", "creative", "music", "art", "study"],
        "family": ["family", "kids", "children", "birthday", "spouse", "partner",
                   "school", "vacation", "holiday", "thanksgiving", "christmas"],
        "work": ["work", "client", "meeting", "project", "deadline", "email",
                 "presentation", "report", "team", "boss", "office", "business"],
        "finances": ["finances", "finance", "financial", "money", "budget", "bank", "tax",
                     "investment", "bill", "payment", "insurance", "savings", "expense",
                     "debt", "loan", "mortgage", "retirement", "income", "portfolio"],
        "social": ["social", "friends", "community", "network", "event", "party",
                   "gathering", "volunteer", "charity", "church", "group", "club"]
    }

    # Score contributions
    DEADLINE_SCORE = 0.8
    BLOCKING_SCORE = 0.6
    SEASONAL_SCORE = 0.5
    TIME_SENSITIVE_SCORE = 0.4

    # Thresholds
    URGENT_THRESHOLD = 0.6
    HIGH_THRESHOLD = 0.3

    def __init__(self, config: dict | None = None):
        """Initialize with optional user config for owner suggestions."""
        self.config = config or {}
        self.entity_detector = EntityDetector()

    # =========================================================================
    # Analysis methods
    # =========================================================================

    def analyze(self, text: str) -> Dict[str, Any]:
        """Full analysis of a capture item.

        Returns dict with is_clear_task, entity_detection, priority, domain,
        owner, duration, entity_mentions.
        """
        # Get entity type detection
        entity_result = self.entity_detector.detect_entity_type(text)

        # Get priority
        priority = self.calculate_priority(text)

        # Get domain
        domain = self.match_domain(text)

        # Check for tentative language
        text_lower = text.lower()
        has_tentative = any(re.search(p, text_lower) for p in self.TENTATIVE_PATTERNS)

        if has_tentative:
            entity_result.signals.append("tentative language detected")

        # Determine owner
        owner_suggestion = self.suggest_owner(domain["matched"])
        needs_clarification = owner_suggestion == "Both"

        # A task is "clear" if:
        # - It's detected as a task (not project, commitment, etc.)
        # - No tentative language present
        is_clear_task = (
            entity_result.entity_type == "task" and
            not has_tentative
        )

        # Parse duration estimate (inline, no TimeParser dependency)
        duration = self.parse_time_mentions(text)

        # Detect entity mentions
        entity_mentions = self.entity_detector.detect_mentions(text)

        return {
            "is_clear_task": is_clear_task,
            "entity_detection": {
                "type": entity_result.entity_type,
                "confidence": entity_result.confidence,
                "signals": entity_result.signals,
                "explanation": entity_result.explanation
            },
            "priority": priority,
            "domain": domain,
            "owner": {
                "suggested": owner_suggestion,
                "reason": f"{domain['matched']} domain default",
                "needs_clarification": needs_clarification
            },
            "duration": duration,
            "entity_mentions": entity_mentions
        }

    def calculate_priority(self, text: str) -> Dict[str, Any]:
        """Calculate priority from text signals.

        Returns dict with score (0-1), level (URGENT/HIGH/MEDIUM/LOW), signals.
        """
        text_lower = text.lower()
        score = 0.0
        signals = []

        # Check for deadline keywords
        deadline_patterns = [
            r"by tomorrow", r"due tomorrow", r"by today", r"due today",
            r"in \d+ days?", r"this week", r"end of week"
        ]
        for pattern in deadline_patterns:
            if re.search(pattern, text_lower):
                score += self.DEADLINE_SCORE
                signals.append("deadline approaching")
                break

        # Check for blocking keywords
        if any(kw in text_lower for kw in self.BLOCKING_KEYWORDS):
            score += self.BLOCKING_SCORE
            signals.append("blocking others")

        # Check for seasonal constraints
        if any(kw in text_lower for kw in self.SEASONAL_KEYWORDS):
            score += self.SEASONAL_SCORE
            signals.append("seasonal constraint")

        # Check for time-sensitive
        if any(kw in text_lower for kw in self.TIME_SENSITIVE_KEYWORDS):
            if "deadline approaching" not in signals:  # Don't double count
                score += self.TIME_SENSITIVE_SCORE
                signals.append("time-sensitive")

        # Map score to level
        if score >= self.URGENT_THRESHOLD:
            level = "URGENT"
        elif score >= self.HIGH_THRESHOLD:
            level = "HIGH"
        else:
            level = "MEDIUM"  # Default to medium, not low

        return {
            "score": min(score, 1.0),
            "level": level,
            "signals": signals
        }

    def match_domain(self, text: str) -> Dict[str, Any]:
        """Match text to a domain based on keywords.

        Returns dict with matched domain, confidence, keywords_found.
        Uses word boundary matching to avoid false positives (e.g., "art" in "start").
        Counts matches per domain and picks the one with most matches.
        """
        text_lower = text.lower()

        # Count keyword matches per domain
        domain_matches: Dict[str, List[str]] = {}

        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            matched_keywords = []
            for keyword in keywords:
                # Use word boundaries to avoid substring matches
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower):
                    matched_keywords.append(keyword)
            if matched_keywords:
                domain_matches[domain] = matched_keywords

        if not domain_matches:
            return {
                "matched": "home",  # Default
                "confidence": "low",
                "keywords_found": []
            }

        # Pick domain with most keyword matches
        # If tied, prefer domain-name keywords (e.g., "finances" > "clean")
        best_domain = None
        best_score = 0
        best_keywords = []

        for domain, keywords in domain_matches.items():
            # Score: count of matches, plus bonus if domain name itself is matched
            score = len(keywords)
            if domain in keywords or domain + "s" in keywords or domain[:-1] in keywords:
                score += 10  # Strong bonus for domain name match

            if score > best_score:
                best_score = score
                best_domain = domain
                best_keywords = keywords

        return {
            "matched": best_domain,
            "confidence": "high" if best_score > 1 else "medium",
            "keywords_found": best_keywords
        }

    def suggest_owner(self, domain: str) -> str | None:
        """Suggest owner based on config. Returns None if no config."""
        owners = self.config.get("household", {}).get("domain_owners", {})
        return owners.get(domain)

    def extract_items(self, raw_text: str) -> List[str]:
        """Split raw text into distinct actionable items.

        Simple sentence/line splitting — no decision-making.

        Args:
            raw_text: Messy brain dump text

        Returns:
            List of individual item strings
        """
        items = []

        # Split by periods followed by space or newline
        sentences = re.split(r'[.]\s+|\n+', raw_text.strip())

        for sentence in sentences:
            sentence = sentence.strip()
            # Skip empty or very short
            if len(sentence) > 10:
                items.append(sentence)

        return items

    def parse_time_mentions(self, text: str) -> dict:
        """Extract time-related info from text."""
        minutes_match = re.search(r'(\d+)\s*min(ute)?s?', text, re.IGNORECASE)
        hours_match = re.search(r'(\d+)\s*hours?', text, re.IGNORECASE)
        estimate = None
        confidence = "low"
        if minutes_match:
            estimate = int(minutes_match.group(1))
            confidence = "high"
        elif hours_match:
            estimate = int(hours_match.group(1)) * 60
            confidence = "high"
        return {"estimate_minutes": estimate, "confidence": confidence}
