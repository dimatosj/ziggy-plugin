"""EntityService — index, profile, resolution, and enrichment.

Adapted from ziggy/services/entities/entity_service.py for the ziggy-plugin
local storage environment. Matrix verification code and YAML dependency removed.
"""
import json
import re
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Optional


class EntityService:
    """Unified entity service combining index, profile, resolution, and enrichment.

    Stores entities in a local JSON index and generates plain markdown profiles
    (no YAML frontmatter, no Obsidian vault dependency, no Matrix verification).

    Previously five separate services:
    - EntityIndexService      -> create/get/update/delete/get_all/get_by_type/resolve_alias/find_candidates/fuzzy_match
    - EntityProfileService    -> get_profile_path/profile_exists/create_profile/read_profile/update_profile_section/add_history_entry
    - EntityResolutionService -> resolve/create_entity/add_relationship
    - TaskEnrichmentService   -> enrich_task (simplified: direct name matching, no EntityDetector)
    """

    # ------------------------------------------------------------------ #
    # Resolution / confidence constants
    # ------------------------------------------------------------------ #
    EXACT_MATCH_CONFIDENCE = 1.0
    FUZZY_MATCH_THRESHOLD = 0.7
    AMBIGUOUS_THRESHOLD = 0.9

    # ------------------------------------------------------------------ #
    # Profile constants
    # ------------------------------------------------------------------ #
    TYPE_FOLDERS = {
        "person": "people",
        "property": "properties",
        "organization": "organizations",
        "account": "accounts",
        "medical": "medical",
        "vehicle": "vehicles",
    }

    # ------------------------------------------------------------------ #
    # Init
    # ------------------------------------------------------------------ #

    def __init__(self, data_dir: Path):
        """Initialize the service.

        Args:
            data_dir: Base directory for all entity data. Index goes to
                      data_dir/entities/index.json and profiles go to
                      data_dir/entities/profiles/{type_folder}/.
        """
        self.data_dir = Path(data_dir)
        self.index_file = self.data_dir / "entities" / "index.json"
        self._ensure_index_exists()

    # ================================================================== #
    # INDEX METHODS (from EntityIndexService)
    # ================================================================== #

    def _ensure_index_exists(self) -> None:
        """Create index file if it doesn't exist."""
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.index_file.exists():
            self._save_index({"entities": {}})

    def _load_index(self) -> dict:
        """Load the index from disk."""
        try:
            with open(self.index_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            empty_index = {"entities": {}}
            self._save_index(empty_index)
            return empty_index

    def _save_index(self, data: dict) -> None:
        """Save the index to disk."""
        try:
            with open(self.index_file, "w") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            raise RuntimeError(f"Failed to save entity index: {e}")

    def create(
        self,
        entity_id: str,
        name: str,
        entity_type: str,
        subtype: Optional[str] = None,
        aliases: Optional[list] = None,
        domain: Optional[str] = None,
        note_path: Optional[str] = None,
        relationships: Optional[list] = None,
        contact_info: Optional[dict] = None,
    ) -> dict:
        """Create a new entity in the index."""
        index = self._load_index()

        normalized_aliases = [a.lower() for a in (aliases or [])]
        if name.lower() not in normalized_aliases:
            normalized_aliases.insert(0, name.lower())

        entity = {
            "id": entity_id,
            "name": name,
            "type": entity_type,
            "subtype": subtype,
            "aliases": normalized_aliases,
            "domain": domain or "personal",
            "note_path": note_path,
            "relationships": relationships or [],
            "contact_info": contact_info or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "enrichment_status": "light",
        }

        index["entities"][entity_id] = entity
        self._save_index(index)
        return entity

    def get(self, entity_id: str) -> Optional[dict]:
        """Get an entity by ID."""
        index = self._load_index()
        return index["entities"].get(entity_id)

    def update(self, entity_id: str, updates: dict) -> Optional[dict]:
        """Update an existing entity."""
        index = self._load_index()
        if entity_id not in index["entities"]:
            return None

        entity = index["entities"][entity_id]
        entity.update(updates)
        entity["updated_at"] = datetime.now().isoformat()

        self._save_index(index)
        return entity

    def delete(self, entity_id: str) -> bool:
        """Delete an entity from the index."""
        index = self._load_index()
        if entity_id not in index["entities"]:
            return False

        del index["entities"][entity_id]
        self._save_index(index)
        return True

    def get_all(self) -> list:
        """Get all entities."""
        index = self._load_index()
        return list(index["entities"].values())

    def get_by_type(self, entity_type: str) -> list:
        """Get all entities of a specific type."""
        return [e for e in self.get_all() if e["type"] == entity_type]

    def resolve_alias(
        self,
        alias: str,
        context_domain: Optional[str] = None,
        context_type: Optional[str] = None,
    ) -> Optional[dict]:
        """Resolve an alias to an entity.

        Args:
            alias: The alias to resolve (case-insensitive)
            context_domain: Optional domain hint for disambiguation
            context_type: Optional type hint for disambiguation

        Returns:
            The matched entity, or None if not found or ambiguous
        """
        alias_lower = alias.lower().strip()
        candidates = []

        for entity in self.get_all():
            if alias_lower in entity["aliases"]:
                candidates.append(entity)

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        if context_domain:
            domain_matches = [e for e in candidates if e.get("domain") == context_domain]
            if len(domain_matches) == 1:
                return domain_matches[0]

        if context_type:
            type_matches = [e for e in candidates if e.get("type") == context_type]
            if len(type_matches) == 1:
                return type_matches[0]

        return None

    def find_candidates(self, alias: str) -> list:
        """Find all entities matching an alias.

        Args:
            alias: The alias to search for (case-insensitive)

        Returns:
            List of matching entities (may be empty)
        """
        alias_lower = alias.lower().strip()
        candidates = []

        for entity in self.get_all():
            if alias_lower in entity["aliases"]:
                candidates.append(entity)

        return candidates

    def _compute_fuzzy_score(self, query: str, target: str) -> float:
        """Compute fuzzy match score between query and target."""
        score = SequenceMatcher(None, query, target).ratio()

        if target.startswith(query):
            partial_score = 0.7 + (0.3 * len(query) / len(target))
            score = max(score, partial_score)

        query_words = query.split()
        target_words = target.split()

        if query_words and target_words:
            matched_words = 0
            for qw in query_words:
                for tw in target_words:
                    if tw.startswith(qw) or SequenceMatcher(None, qw, tw).ratio() >= 0.8:
                        matched_words += 1
                        break

            if matched_words == len(query_words):
                token_score = 0.7 + (0.3 * matched_words / len(target_words))
                score = max(score, token_score)

        return score

    def fuzzy_match(
        self,
        query: str,
        threshold: float = 0.6,
        max_results: int = 5,
    ) -> list:
        """Find entities using fuzzy string matching.

        Args:
            query: The search query
            threshold: Minimum similarity score (0-1)
            max_results: Maximum number of results to return

        Returns:
            List of dicts with 'entity' and 'score' keys, sorted by score
        """
        query_lower = query.lower().strip()
        results = []

        for entity in self.get_all():
            best_score = 0

            name_score = self._compute_fuzzy_score(query_lower, entity["name"].lower())
            best_score = max(best_score, name_score)

            for alias in entity["aliases"]:
                alias_score = self._compute_fuzzy_score(query_lower, alias.lower())
                best_score = max(best_score, alias_score)

            if best_score >= threshold:
                results.append({
                    "entity": entity,
                    "score": best_score,
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:max_results]

    # ================================================================== #
    # PROFILE METHODS (from EntityProfileService, no YAML)
    # ================================================================== #

    def _name_to_filename(self, name: str) -> str:
        """Convert entity name to filename-safe format."""
        filename = name.replace(" ", "-")
        return f"{filename}.md"

    def get_profile_path(self, name: str, entity_type: str) -> Path:
        """Get the expected path for an entity profile."""
        folder = self.TYPE_FOLDERS.get(entity_type, entity_type)
        return self.data_dir / "entities" / "profiles" / folder / self._name_to_filename(name)

    def profile_exists(self, name: str, entity_type: str) -> bool:
        """Check if a profile exists for the given entity."""
        return self.get_profile_path(name, entity_type).exists()

    def _build_profile_content(
        self,
        name: str,
        entity_type: str,
        subtype: str = "",
        domain: str = "",
        description: str = "",
        contact_info: Optional[dict] = None,
        aliases: Optional[list] = None,
    ) -> str:
        """Build profile markdown content without YAML frontmatter."""
        lines = [f"# {name}\n"]
        lines.append(f"**Type:** {entity_type}")
        if subtype:
            lines.append(f"**Subtype:** {subtype}")
        if domain:
            lines.append(f"**Domain:** {domain}")
        if aliases:
            lines.append(f"**Aliases:** {', '.join(aliases)}")
        lines.append("")
        if description:
            lines.append(f"## About\n\n{description}\n")
        if contact_info:
            lines.append("## Contact\n")
            for key, value in contact_info.items():
                lines.append(f"- **{key}:** {value}")
            lines.append("")
        lines.append("## Notes\n\n")
        lines.append("## History\n\n")
        return "\n".join(lines)

    def create_profile(
        self,
        entity_id: str,
        name: str,
        entity_type: str,
        subtype: Optional[str] = None,
        domain: Optional[str] = None,
        aliases: Optional[list] = None,
        description: Optional[str] = None,
        contact_info: Optional[dict] = None,
        **extra_fields: Any,
    ) -> Path:
        """Create a new entity profile.

        Returns:
            Path to the created profile
        """
        profile_path = self.get_profile_path(name, entity_type)
        profile_path.parent.mkdir(parents=True, exist_ok=True)

        content = self._build_profile_content(
            name=name,
            entity_type=entity_type,
            subtype=subtype or "",
            domain=domain or "",
            description=description or "",
            contact_info=contact_info,
            aliases=aliases,
        )
        profile_path.write_text(content)

        return profile_path

    def read_profile(self, name: str, entity_type: str) -> Optional[str]:
        """Read the content of an entity profile.

        Returns:
            Profile content as string, or None if not found
        """
        profile_path = self.get_profile_path(name, entity_type)
        if not profile_path.exists():
            return None
        return profile_path.read_text()

    def update_profile_section(
        self,
        name: str,
        entity_type: str,
        section: str,
        content: str,
    ) -> bool:
        """Update a specific section in an entity profile.

        Returns:
            True if updated successfully, False if profile not found
        """
        profile_path = self.get_profile_path(name, entity_type)
        if not profile_path.exists():
            return False

        current_content = profile_path.read_text()

        section_header = f"## {section}"
        if section_header not in current_content:
            current_content = current_content.rstrip() + f"\n\n{section_header}\n\n{content}\n"
        else:
            lines = current_content.split("\n")
            new_lines = []
            in_section = False

            for line in lines:
                if line.startswith("## "):
                    if line == section_header:
                        in_section = True
                        new_lines.append(line)
                        new_lines.append("")
                        new_lines.append(content)
                        continue
                    elif in_section:
                        in_section = False

                if not in_section:
                    new_lines.append(line)

            current_content = "\n".join(new_lines)

        profile_path.write_text(current_content)
        return True

    def add_history_entry(
        self,
        name: str,
        entity_type: str,
        entry: str,
        date: Optional[str] = None,
    ) -> bool:
        """Add an entry to the History section of a profile.

        Returns:
            True if added successfully, False if profile not found
        """
        profile_path = self.get_profile_path(name, entity_type)
        if not profile_path.exists():
            return False

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        current_content = profile_path.read_text()
        history_header = "## History"

        if history_header not in current_content:
            current_content = current_content.rstrip() + f"\n\n{history_header}\n\n- {date}: {entry}\n"
        else:
            lines = current_content.split("\n")
            new_lines = []
            history_entry_added = False

            for i, line in enumerate(lines):
                new_lines.append(line)
                if line == history_header and not history_entry_added:
                    if i + 1 < len(lines) and lines[i + 1] == "":
                        continue
                    new_lines.append("")
                    new_lines.append(f"- {date}: {entry}")
                    history_entry_added = True

            if not history_entry_added:
                new_lines.append(f"- {date}: {entry}")

            current_content = "\n".join(new_lines)

        profile_path.write_text(current_content)
        return True

    # ================================================================== #
    # RESOLUTION METHODS (from EntityResolutionService)
    # ================================================================== #

    def _generate_id(self, name: str, entity_type: str) -> str:
        """Generate a slug-based ID for an entity."""
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower())
        slug = slug.strip("-")
        return f"{entity_type}-{slug}"

    def resolve(
        self,
        mention: str,
        context_domain: Optional[str] = None,
        context_type: Optional[str] = None,
    ) -> dict:
        """Resolve a mention to an entity.

        Tries resolution strategies in order:
        1. Exact alias match -> "resolved"
        2. Multiple candidates -> "ambiguous"
        3. Fuzzy match -> "fuzzy_match" (or "ambiguous" if top 2 are close)
        4. Nothing -> "unknown"

        Args:
            mention: The text mention to resolve (e.g., "maria", "my accountant")
            context_domain: Optional domain hint for disambiguation
            context_type: Optional type hint for disambiguation

        Returns:
            Dict with keys:
                - status: "resolved", "ambiguous", "fuzzy_match", or "unknown"
                - entity: The matched entity (if resolved or fuzzy_match)
                - candidates: List of candidates (if ambiguous)
                - confidence: Match confidence (for fuzzy_match)
        """
        exact_candidates = self.find_candidates(mention)

        if len(exact_candidates) == 1:
            return {
                "status": "resolved",
                "entity": exact_candidates[0],
                "confidence": self.EXACT_MATCH_CONFIDENCE,
            }

        if len(exact_candidates) > 1:
            if context_domain:
                domain_matches = [
                    e for e in exact_candidates if e.get("domain") == context_domain
                ]
                if len(domain_matches) == 1:
                    return {
                        "status": "resolved",
                        "entity": domain_matches[0],
                        "confidence": self.EXACT_MATCH_CONFIDENCE,
                    }

            if context_type:
                type_matches = [
                    e for e in exact_candidates if e.get("type") == context_type
                ]
                if len(type_matches) == 1:
                    return {
                        "status": "resolved",
                        "entity": type_matches[0],
                        "confidence": self.EXACT_MATCH_CONFIDENCE,
                    }

            return {
                "status": "ambiguous",
                "entity": None,
                "candidates": exact_candidates,
            }

        fuzzy_results = self.fuzzy_match(mention, threshold=self.FUZZY_MATCH_THRESHOLD)

        if not fuzzy_results:
            return {
                "status": "unknown",
                "entity": None,
            }

        if len(fuzzy_results) == 1:
            return {
                "status": "fuzzy_match",
                "entity": fuzzy_results[0]["entity"],
                "confidence": fuzzy_results[0]["score"],
            }

        top_score = fuzzy_results[0]["score"]
        second_score = fuzzy_results[1]["score"]

        if top_score - second_score < (1.0 - self.AMBIGUOUS_THRESHOLD):
            return {
                "status": "ambiguous",
                "entity": None,
                "candidates": [r["entity"] for r in fuzzy_results],
            }

        return {
            "status": "fuzzy_match",
            "entity": fuzzy_results[0]["entity"],
            "confidence": fuzzy_results[0]["score"],
        }

    def create_entity(
        self,
        name: str,
        entity_type: str,
        subtype: Optional[str] = None,
        aliases: Optional[list] = None,
        domain: Optional[str] = None,
        relationships: Optional[list] = None,
        contact_info: Optional[dict] = None,
        description: Optional[str] = None,
        **extra_fields: Any,
    ) -> dict:
        """Create an entity in both the index and as a local markdown profile.

        Args:
            name: Display name for the entity
            entity_type: Type of entity (person, property, organization, etc.)
            subtype: Optional subtype (e.g., "professional", "owned")
            aliases: Optional list of alternative names
            domain: Optional domain (e.g., "finances", "family")
            relationships: Optional list of relationship dicts
            contact_info: Optional contact information dict
            description: Optional free-text description
            **extra_fields: Additional fields (accepted but not used in profile)

        Returns:
            The created entity dict from the index
        """
        entity_id = self._generate_id(name, entity_type)

        profile_path = self.create_profile(
            entity_id=entity_id,
            name=name,
            entity_type=entity_type,
            subtype=subtype,
            domain=domain,
            aliases=aliases,
            description=description,
            contact_info=contact_info,
        )

        entity = self.create(
            entity_id=entity_id,
            name=name,
            entity_type=entity_type,
            subtype=subtype,
            aliases=aliases,
            domain=domain,
            note_path=str(profile_path),
            relationships=relationships,
            contact_info=contact_info,
        )

        return entity

    def add_relationship(
        self,
        entity_id: str,
        related_entity_id: str,
        relationship_type: str,
        role: Optional[str] = None,
    ) -> bool:
        """Create a bidirectional relationship between two entities.

        Returns:
            True if relationships were created, False if either entity not found
        """
        entity = self.get(entity_id)
        related_entity = self.get(related_entity_id)

        if not entity or not related_entity:
            return False

        relationships = entity.get("relationships", [])
        relationships.append(
            {
                "entity_id": related_entity_id,
                "type": relationship_type,
                "role": role,
            }
        )
        self.update(entity_id, {"relationships": relationships})

        inverse_relationships = related_entity.get("relationships", [])
        inverse_relationships.append(
            {
                "entity_id": entity_id,
                "type": relationship_type,
                "role": f"inverse_{role}" if role else None,
            }
        )
        self.update(related_entity_id, {"relationships": inverse_relationships})

        return True

    # ================================================================== #
    # ENRICHMENT METHODS (from TaskEnrichmentService)
    # ================================================================== #

    def enrich_task(
        self,
        title: str,
        description: str,
    ) -> dict:
        """Enrich a task with entity information.

        Uses simple name/alias matching against the index (no EntityDetector
        import). Scans the task title for any entity name or alias.

        Returns dict with:
            - title: Original title
            - description: Enriched description with contact info and context
            - entities: List of resolved entities
        """
        title_lower = title.lower()
        # Tokenise title into words for token-level matching
        title_words = set(re.findall(r"[a-z0-9']+", title_lower))
        entities = []
        enrichment_lines = []

        for entity in self.get_all():
            matched = False
            # Check entity name (full substring)
            if entity["name"].lower() in title_lower:
                matched = True
            # Check individual words of entity name against title words
            # (e.g. "Maria" from "Maria Chen" matches title "Call Maria about taxes")
            if not matched:
                name_words = [
                    w for w in re.findall(r"[a-z0-9']+", entity["name"].lower())
                    if len(w) >= 3  # skip very short words to reduce false positives
                ]
                if name_words and any(w in title_words for w in name_words):
                    matched = True
            # Check aliases (full substring and token-level)
            if not matched:
                for alias in entity.get("aliases", []):
                    alias_lower = alias.lower()
                    if alias_lower in title_lower:
                        matched = True
                        break
                    alias_words = [
                        w for w in re.findall(r"[a-z0-9']+", alias_lower)
                        if len(w) >= 3
                    ]
                    if alias_words and any(w in title_words for w in alias_words):
                        matched = True
                        break

            if matched:
                entities.append(entity)
                lines = self._format_entity_context(entity)
                if lines:
                    enrichment_lines.extend(lines)

        if enrichment_lines:
            enrichment_block = "\n".join(enrichment_lines)
            if description:
                enriched_description = f"{enrichment_block}\n\n---\n\n{description}"
            else:
                enriched_description = enrichment_block
        else:
            enriched_description = description

        return {
            "title": title,
            "description": enriched_description,
            "entities": entities,
        }

    def _format_entity_context(self, entity: dict) -> list:
        """Format entity context for task description."""
        lines = []

        contact_info = entity.get("contact_info", {})

        if contact_info.get("phone"):
            lines.append(f"Phone: {entity['name']}: {contact_info['phone']}")
        if contact_info.get("email"):
            lines.append(f"Email: {contact_info['email']}")
        if contact_info.get("address"):
            lines.append(f"Address: {contact_info['address']}")

        context_parts = []
        if entity.get("subtype"):
            context_parts.append(entity["subtype"])
        if entity.get("domain"):
            context_parts.append(f"{entity['domain']} domain")

        if context_parts:
            lines.append(f"Context: {', '.join(context_parts)}")

        return lines
