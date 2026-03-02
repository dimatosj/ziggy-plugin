"""Foundation pillar models."""
from enum import Enum


class PillarName(str, Enum):
    """The 5 foundation pillars."""
    REALITY = "reality"
    FAMILY = "family"
    CONTEXT = "context"
    CAPABILITY = "capability"
    VISION = "vision"
