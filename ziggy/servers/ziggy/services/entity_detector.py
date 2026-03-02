"""Consolidated EntityDetector - mention detection and entity type classification.

Combines:
- EntityMentionDetector (was ziggy/capture/entity_mention_detector.py)
  -> detect_mentions(text)
- EntityDetector (was ziggy/capture/entity_detector.py)
  -> detect_entity_type(text, duration_hours)
"""

import re
from collections import Counter
from typing import Dict, List, Set, TypedDict

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Types from EntityMentionDetector
# ---------------------------------------------------------------------------

class EntityMention(TypedDict):
    """A detected entity mention in text."""

    text: str
    type_hint: str | None
    signals: list[str]
    triage_score: int
    start: int
    end: int


# ---------------------------------------------------------------------------
# Types from EntityDetector
# ---------------------------------------------------------------------------

class DetectionResult(BaseModel):
    """Result of entity type detection."""

    entity_type: str = Field(..., description="Detected entity type")
    detected_domains: List[str] = Field(
        default_factory=list, description="Detected domain associations"
    )
    confidence: float = Field(..., description="Detection confidence (0.0-1.0)")
    signals: List[str] = Field(
        default_factory=list, description="Detection signals found"
    )
    explanation: str = Field(..., description="Human-readable explanation")


# ---------------------------------------------------------------------------
# EntityDetector
# ---------------------------------------------------------------------------

class EntityDetector:
    """Combined entity detection: mention detection + entity type classification.

    Provides:
    - detect_mentions(text) -> list[EntityMention]
      Finds named entity mentions (people, properties, orgs) in text.

    - detect_entity_type(text) -> DetectionResult
      Classifies text as initiative/goal/commitment/routine/project/task.
    """

    # ================================================================== #
    # MENTION DETECTION constants (from EntityMentionDetector)
    # ================================================================== #

    ACTION_VERBS = [
        "call",
        "email",
        "text",
        "message",
        "contact",
        "meet",
        "schedule",
        "ask",
        "tell",
        "remind",
        "follow up",
        "check with",
        "reach out",
        "talk to",
        "speak with",
        "ping",
        "notify",
        "update",
        "invoice",
        "pay",
        "bill",
    ]

    SUBJECT_PREPOSITIONS = [
        "for",
        "about",
        "regarding",
        "at",
        "with",
        "from",
        "to",
        "on",
    ]

    PROPERTY_PATTERNS = [
        r"\b(\d+[A-Za-z]?\s+[A-Z][a-z]+(?:\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl))?)\b",
        r"\b((?:The\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Estate|Manor|House|Building|Complex|Property))\b",
    ]

    ORG_SUFFIXES = [
        "Inc",
        "LLC",
        "Corp",
        "Company",
        "Co",
        "Ltd",
        "School",
        "Academy",
        "University",
        "College",
        "Hospital",
        "Clinic",
        "Bank",
        "Church",
        "Foundation",
        "Institute",
        "Center",
        "Centre",
        "Group",
        "Association",
        "Club",
        "Team",
    ]

    # ================================================================== #
    # ENTITY TYPE DETECTION constants (from EntityDetector)
    # ================================================================== #

    DOMAIN_KEYWORDS: Dict[str, List[str]] = {
        "home": [
            "home",
            "house",
            "apartment",
            "garden",
            "yard",
            "cleaning",
            "maintenance",
            "repair",
            "renovation",
            "decor",
            "furniture",
            "organize",
            "declutter",
        ],
        "health": [
            "health",
            "fitness",
            "exercise",
            "workout",
            "gym",
            "mental",
            "therapy",
            "meditation",
            "yoga",
            "nutrition",
            "diet",
            "wellness",
            "medical",
            "doctor",
            "checkup",
        ],
        "personal": [
            "personal",
            "learn",
            "study",
            "read",
            "hobby",
            "skill",
            "growth",
            "development",
            "practice",
            "course",
            "book",
            "creative",
            "art",
            "music",
        ],
        "family": [
            "family",
            "kids",
            "children",
            "spouse",
            "partner",
            "parent",
            "sibling",
            "marriage",
            "relationship",
            "childcare",
            "school",
            "vacation",
            "quality time",
        ],
        "work": [
            "work",
            "business",
            "company",
            "client",
            "customer",
            "revenue",
            "sales",
            "marketing",
            "product",
            "team",
            "employee",
            "hire",
            "meeting",
            "project",
            "deadline",
        ],
        "finances": [
            "finances",
            "finance",
            "financial",
            "money",
            "budget",
            "investment",
            "savings",
            "tax",
            "retirement",
            "expense",
            "income",
            "debt",
            "loan",
            "mortgage",
            "insurance",
            "portfolio",
        ],
        "social": [
            "social",
            "friends",
            "community",
            "network",
            "event",
            "party",
            "gathering",
            "volunteer",
            "charity",
            "church",
            "group",
            "club",
            "membership",
            "neighbor",
        ],
    }

    # ================================================================== #
    # MENTION DETECTION (from EntityMentionDetector)
    # ================================================================== #

    def detect_mentions(self, text: str) -> list[EntityMention]:
        """Detect entity mentions in text.

        Args:
            text: Input text to scan for entity mentions

        Returns:
            List of EntityMention dicts with text, type_hint, signals,
            triage_score, start, and end positions
        """
        mentions: list[EntityMention] = []

        mentions.extend(self._detect_properties(text))
        mentions.extend(self._detect_organizations(text))
        mentions.extend(self._detect_persons(text, mentions))

        self._detect_action_signals(text, mentions)
        self._detect_subject_signals(text, mentions)

        mentions = self._consolidate_mentions(mentions)
        self._calculate_triage_scores(mentions)

        return mentions

    def _detect_properties(self, text: str) -> list[EntityMention]:
        """Detect property/address mentions."""
        mentions = []

        for pattern in self.PROPERTY_PATTERNS:
            for match in re.finditer(pattern, text):
                mentions.append(
                    EntityMention(
                        text=match.group(1),
                        type_hint="property",
                        signals=[],
                        triage_score=0,
                        start=match.start(1),
                        end=match.end(1),
                    )
                )

        return mentions

    def _detect_organizations(self, text: str) -> list[EntityMention]:
        """Detect organization mentions."""
        mentions = []

        suffix_pattern = "|".join(re.escape(s) for s in self.ORG_SUFFIXES)
        org_pattern = rf"\b((?:[A-Z][a-z]+\s+)+(?:{suffix_pattern}))\b"

        for match in re.finditer(org_pattern, text):
            mentions.append(
                EntityMention(
                    text=match.group(1).strip(),
                    type_hint="organization",
                    signals=[],
                    triage_score=0,
                    start=match.start(1),
                    end=match.end(1),
                )
            )

        multi_cap_pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"

        sentence_starters = {
            "Call",
            "Email",
            "Text",
            "Message",
            "Contact",
            "Meet",
            "Schedule",
            "Ask",
            "Tell",
            "Remind",
            "Check",
            "Please",
            "Also",
            "The",
            "This",
            "That",
            "These",
            "Those",
        }

        for match in re.finditer(multi_cap_pattern, text):
            phrase = match.group(1)
            start_pos = match.start(1)
            end_pos = match.end(1)

            if self._overlaps_existing(start_pos, end_pos, mentions):
                continue

            words = phrase.split()
            if len(words) < 2:
                continue

            if words[0] in sentence_starters:
                is_sentence_start = start_pos == 0
                if not is_sentence_start and start_pos > 0:
                    char_before = text[start_pos - 1]
                    is_sentence_start = char_before in ".!?\n"
                    if not is_sentence_start and start_pos >= 2:
                        is_sentence_start = text[start_pos - 2 : start_pos] == ". "

                if is_sentence_start:
                    remaining_words = words[1:]
                    if len(remaining_words) >= 2:
                        first_word_len = len(words[0]) + 1
                        phrase = " ".join(remaining_words)
                        start_pos = start_pos + first_word_len
                    else:
                        continue

            mentions.append(
                EntityMention(
                    text=phrase,
                    type_hint="organization",
                    signals=[],
                    triage_score=0,
                    start=start_pos,
                    end=end_pos,
                )
            )

        return mentions

    def _detect_persons(
        self, text: str, existing_mentions: list[EntityMention]
    ) -> list[EntityMention]:
        """Detect person name mentions (single capitalized words)."""
        mentions = []

        common_words = {
            "The",
            "This",
            "That",
            "These",
            "Those",
            "There",
            "Here",
            "What",
            "When",
            "Where",
            "Why",
            "How",
            "Who",
            "Which",
            "If",
            "Then",
            "Also",
            "And",
            "But",
            "Or",
            "So",
            "Yet",
            "For",
            "Nor",
            "As",
            "At",
            "By",
            "In",
            "Of",
            "On",
            "To",
            "Up",
            "It",
            "Is",
            "Are",
            "Was",
            "Were",
            "Be",
            "Been",
            "Being",
            "Have",
            "Has",
            "Had",
            "Do",
            "Does",
            "Did",
            "Will",
            "Would",
            "Could",
            "Should",
            "May",
            "Might",
            "Must",
            "Can",
            "All",
            "Any",
            "Some",
            "No",
            "Not",
            "Only",
            "Just",
            "More",
            "Most",
            "Other",
            "Such",
            "Than",
            "Too",
            "Very",
            "About",
            "Check",
            "Call",
            "Email",
            "Fix",
            "Buy",
            "Get",
            "Make",
            "Set",
            "Put",
            "Take",
            "Send",
            "Find",
            "Give",
            "Tell",
            "Ask",
            "Try",
            "Use",
            "Need",
            "Want",
            "Start",
            "Stop",
            "Plan",
            "Create",
            "Update",
            "Delete",
            "Change",
            "Move",
            "Add",
            "Remove",
            "Review",
            "Submit",
            "Complete",
            "Finish",
            "Cancel",
            "Return",
            "Order",
            "Book",
            "Pay",
            "Test",
            "Making",
            "Going",
            "Looking",
            "Getting",
            "Doing",
            "Having",
            "Being",
            "Trying",
            "Working",
            "Thinking",
            "Waiting",
            "Running",
            "Coming",
            "Leaving",
            "Starting",
            "Cleaning",
            "Organizing",
        }

        name_pattern = r"\b([A-Z][a-z]+)\b"

        for match in re.finditer(name_pattern, text):
            name = match.group(1)
            start = match.start(1)
            end = match.end(1)

            if name in common_words:
                continue

            if self._overlaps_existing(start, end, existing_mentions):
                continue

            mentions.append(
                EntityMention(
                    text=name,
                    type_hint="person",
                    signals=[],
                    triage_score=0,
                    start=start,
                    end=end,
                )
            )

        return mentions

    def _overlaps_existing(
        self, start: int, end: int, mentions: list[EntityMention]
    ) -> bool:
        """Check if a position range overlaps with existing mentions."""
        for mention in mentions:
            if start < mention["end"] and end > mention["start"]:
                return True
        return False

    def _detect_action_signals(
        self, text: str, mentions: list[EntityMention]
    ) -> None:
        """Add action_verb signals to mentions preceded by action verbs."""
        text_lower = text.lower()

        for verb in self.ACTION_VERBS:
            verb_pattern = rf"\b{re.escape(verb)}\b"
            for verb_match in re.finditer(verb_pattern, text_lower):
                verb_end = verb_match.end()

                for mention in mentions:
                    if (
                        mention["start"] > verb_end
                        and mention["start"] - verb_end < 50
                    ):
                        if "action_verb" not in mention["signals"]:
                            mention["signals"].append("action_verb")

    def _detect_subject_signals(
        self, text: str, mentions: list[EntityMention]
    ) -> None:
        """Add subject_of_task signals to mentions following subject prepositions."""
        text_lower = text.lower()

        for prep in self.SUBJECT_PREPOSITIONS:
            prep_pattern = rf"\b{re.escape(prep)}\b"
            for prep_match in re.finditer(prep_pattern, text_lower):
                prep_end = prep_match.end()

                for mention in mentions:
                    if (
                        mention["start"] > prep_end
                        and mention["start"] - prep_end < 20
                    ):
                        if "subject_of_task" not in mention["signals"]:
                            mention["signals"].append("subject_of_task")

    def _consolidate_mentions(
        self, mentions: list[EntityMention]
    ) -> list[EntityMention]:
        """Consolidate multiple mentions of the same entity."""
        mention_counts = Counter(m["text"] for m in mentions)

        seen: dict[str, EntityMention] = {}

        for mention in mentions:
            text = mention["text"]
            if text not in seen:
                seen[text] = mention.copy()
                if mention_counts[text] > 1:
                    seen[text]["signals"].append("multiple_mentions")
            else:
                for signal in mention["signals"]:
                    if signal not in seen[text]["signals"]:
                        seen[text]["signals"].append(signal)

        return list(seen.values())

    def _calculate_triage_scores(self, mentions: list[EntityMention]) -> None:
        """Calculate triage scores based on signals.

        Scoring:
        - multiple_mentions: +3
        - action_verb: +3
        - subject_of_task: +2
        - no signals (single mention): +1
        """
        for mention in mentions:
            score = 0

            if "multiple_mentions" in mention["signals"]:
                score += 3
            if "action_verb" in mention["signals"]:
                score += 3
            if "subject_of_task" in mention["signals"]:
                score += 2

            if score == 0:
                score = 1

            mention["triage_score"] = score

    # ================================================================== #
    # ENTITY TYPE DETECTION (from ziggy/capture/entity_detector.py)
    # ================================================================== #

    def detect_entity_type(self, text: str) -> DetectionResult:
        """Detect entity type from text using scope-out priority.

        Detection priority (scope-out):
        1. Initiative - Multi-domain, large scope
        2. Goal - Quarterly/annual timeframe
        3. Commitment - Recurring behavioral change
        4. Routine - Process/system
        5. Project - >4 hours, deliverable
        6. Task - Default, single action

        Args:
            text: Natural language text to analyze

        Returns:
            DetectionResult with entity type and explanation
        """
        text_lower = text.lower()
        detected_domains = self._detect_domains(text_lower)

        signals = []

        initiative_signals = self._check_initiative_signals(text_lower, detected_domains)
        if initiative_signals:
            signals.extend(initiative_signals)
            explanation = self._explain_signals("initiative", signals)
            return DetectionResult(
                entity_type="initiative",
                detected_domains=detected_domains,
                confidence=0.9,
                signals=signals,
                explanation=explanation,
            )

        goal_signals = self._check_goal_signals(text_lower)
        if goal_signals:
            signals.extend(goal_signals)
            explanation = self._explain_signals("goal", signals)
            return DetectionResult(
                entity_type="goal",
                detected_domains=detected_domains,
                confidence=0.85,
                signals=signals,
                explanation=explanation,
            )

        commitment_signals = self._check_commitment_signals(text_lower)
        routine_signals = self._check_routine_signals(text_lower)

        if routine_signals:
            signals.extend(routine_signals)
            explanation = self._explain_signals("routine", signals)
            return DetectionResult(
                entity_type="routine",
                detected_domains=detected_domains,
                confidence=0.75,
                signals=signals,
                explanation=explanation,
            )

        if commitment_signals:
            signals.extend(commitment_signals)
            explanation = self._explain_signals("commitment", signals)
            return DetectionResult(
                entity_type="commitment",
                detected_domains=detected_domains,
                confidence=0.8,
                signals=signals,
                explanation=explanation,
            )

        project_signals = self._check_project_signals(text_lower)
        if project_signals:
            signals.extend(project_signals)
            explanation = self._explain_signals("project", signals)
            return DetectionResult(
                entity_type="project",
                detected_domains=detected_domains,
                confidence=0.7,
                signals=signals,
                explanation=explanation,
            )

        return DetectionResult(
            entity_type="task",
            detected_domains=detected_domains,
            confidence=0.5,
            signals=["default_case"],
            explanation="No strong signals detected - defaulting to task (single action item)",
        )

    def _detect_domains(self, text_lower: str) -> List[str]:
        """Detect domain associations from keywords."""
        detected = []
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower):
                    detected.append(domain)
                    break
        return detected

    def _check_initiative_signals(
        self, text_lower: str, detected_domains: List[str]
    ) -> List[str]:
        """Check for initiative signals."""
        signals = []

        if len(detected_domains) >= 2:
            signals.append(f"multiple domains ({', '.join(detected_domains)})")

        multi_person = [
            "company-wide",
            "company wide",
            "organization",
            "organizational",
            "enterprise",
            "all-hands",
            "department",
            "division",
            "cross-team",
            "multi-team",
        ]
        for keyword in multi_person:
            if keyword in text_lower:
                signals.append(f"multi-person keyword: {keyword}")
                break

        scope_words = [
            "initiative",
            "program",
            "campaign",
            "launch",
            "rollout",
            "transformation",
            "overhaul",
        ]
        for word in scope_words:
            if word in text_lower:
                signals.append(f"scope word: {word}")
                break

        if len(signals) == 0:
            return []
        if len(signals) == 1 and "multiple domains" in signals[0] and len(detected_domains) < 3:
            return []
        return signals

    def _check_goal_signals(self, text_lower: str) -> List[str]:
        """Check for goal signals."""
        signals = []

        quarterly = ["q1", "q2", "q3", "q4", "quarterly", "quarter"]
        for keyword in quarterly:
            if keyword in text_lower:
                signals.append(f"quarterly keyword: {keyword}")
                break

        annual = [
            "annual",
            "yearly",
            "year",
            "2024",
            "2025",
            "2026",
            "2027",
            "2028",
        ]
        for keyword in annual:
            if keyword in text_lower:
                signals.append(f"annual keyword: {keyword}")
                break

        goal_words = ["goal", "target", "objective", "aim", "okr", "kpi"]
        for word in goal_words:
            if word in text_lower:
                signals.append(f"goal keyword: {word}")
                break

        return signals

    def _check_commitment_signals(self, text_lower: str) -> List[str]:
        """Check for commitment signals."""
        signals = []

        frequency_patterns = [
            r"\d+x\s+per\s+week",
            r"\d+x\s+per\s+month",
            r"\d+x\s+weekly",
            r"every\s+day",
            r"every\s+week",
            r"every\s+month",
            r"daily",
            r"weekly",
            r"monthly",
        ]
        for pattern in frequency_patterns:
            match = re.search(pattern, text_lower)
            if match:
                signals.append(f"frequency pattern: {match.group()}")
                break

        behavioral = [
            "commit",
            "pledge",
            "promise",
            "dedicate",
            "vow",
            "resolve",
            "starting",
            "beginning",
        ]
        for keyword in behavioral:
            if keyword in text_lower:
                signals.append(f"behavioral keyword: {keyword}")
                break

        habit_words = ["habit", "regular", "consistent", "consistently", "regularly"]
        for word in habit_words:
            if word in text_lower:
                signals.append(f"habit keyword: {word}")
                break

        return signals

    def _check_routine_signals(self, text_lower: str) -> List[str]:
        """Check for routine signals."""
        signals = []

        process_words = [
            "routine",
            "process",
            "workflow",
            "checklist",
            "steps",
            "standup",
        ]
        for word in process_words:
            if word in text_lower:
                signals.append(f"process keyword: {word}")
                break

        recurring = [
            "recurring",
            "repeat",
            "ongoing",
            "continuous",
            "perpetual",
            "standing",
        ]
        for keyword in recurring:
            if keyword in text_lower:
                signals.append(f"recurring keyword: {keyword}")
                break

        howto = ["how to", "steps to", "checklist", "template", "standard"]
        for keyword in howto:
            if keyword in text_lower:
                signals.append(f"how-to keyword: {keyword}")
                break

        return signals

    def _check_project_signals(self, text_lower: str) -> List[str]:
        """Check for project signals."""
        signals = []

        duration_patterns = [
            r"(\d+)\s*hours?",
            r"(\d+)\s*hrs?",
            r"(\d+)\s*days?",
            r"(\d+)\s*weeks?",
            r"(\d+)\s*months?",
        ]
        for pattern in duration_patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = int(match.group(1))
                unit = "hours"
                if "day" in match.group():
                    value *= 8
                    unit = "days"
                elif "week" in match.group():
                    value *= 40
                    unit = "weeks"
                elif "month" in match.group():
                    value *= 160
                    unit = "months"

                if value > 4:
                    signals.append(f"duration: {match.group()} (>{value} hours)")
                    break

        project_words = [
            "project",
            "deliverable",
            "milestone",
            "initiative",
            "build",
            "create",
            "develop",
            "design",
            "implement",
        ]
        for word in project_words:
            if word in text_lower:
                signals.append(f"project keyword: {word}")
                break

        multistep = [
            "phases",
            "stages",
            "steps",
            "multi-step",
            "multi-phase",
            "roadmap",
        ]
        for keyword in multistep:
            if keyword in text_lower:
                signals.append(f"multi-step keyword: {keyword}")
                break

        return signals

    def _explain_signals(self, entity_type: str, signals: List[str]) -> str:
        """Generate human-readable explanation from signals."""
        if not signals:
            return f"Detected as {entity_type} (no specific signals)"

        signal_text = "; ".join(signals)
        return f"Detected as {entity_type} based on: {signal_text}"
