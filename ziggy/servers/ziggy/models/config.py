"""Configuration data models."""
from typing import Any, Optional

from pydantic import BaseModel, Field


class Household(BaseModel):
    """Household configuration."""
    members: list[str] = Field(default_factory=lambda: [])
    domain_owners: dict[str, Optional[str]] = Field(default_factory=dict)


class ZiggyConfig(BaseModel):
    """User configuration."""
    user_name: str
    household: Household = Field(default_factory=Household)
    preferences: dict[str, str] = Field(default_factory=lambda: {"default_domain": "home"})

    def model_post_init(self, __context: Any = None) -> None:
        """Ensure household.members includes user_name if empty."""
        if not self.household.members:
            self.household.members = [self.user_name]
