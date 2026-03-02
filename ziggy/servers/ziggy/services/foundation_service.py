"""Foundation pillar service for managing life context markdown files."""
from pathlib import Path
from typing import Optional

from ziggy.models.foundation import PillarName


class FoundationService:
    """Read and write foundation pillar markdown files."""

    def __init__(self, data_dir: Path):
        self.foundation_dir = data_dir / "foundation"
        self.foundation_dir.mkdir(parents=True, exist_ok=True)

    def read_pillar(self, pillar: PillarName) -> Optional[str]:
        """Read a foundation pillar file. Returns None if not found."""
        path = self.foundation_dir / f"{pillar.value}.md"
        if not path.exists():
            return None
        return path.read_text()

    def write_pillar(self, pillar: PillarName, content: str) -> None:
        """Write content to a foundation pillar file."""
        path = self.foundation_dir / f"{pillar.value}.md"
        path.write_text(content)

    def read_all(self) -> dict[str, Optional[str]]:
        """Read all foundation pillars. Returns dict of pillar_name -> content."""
        return {pillar.value: self.read_pillar(pillar) for pillar in PillarName}

    def has_foundation(self) -> bool:
        """Check if any foundation pillars exist."""
        return any(
            (self.foundation_dir / f"{p.value}.md").exists()
            for p in PillarName
        )
