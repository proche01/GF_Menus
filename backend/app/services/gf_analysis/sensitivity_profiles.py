"""
Sensitivity profiles define dietary filtering rulesets.

Each profile specifies which menu items pass the filter for a given user type.
Designed to be extended in v1 (NCGS, CUSTOM) and v2 (MULTI_RESTRICTION).
"""

from dataclasses import dataclass, field
from enum import Enum


class ProfileType(str, Enum):
    STRICT_CELIAC = "STRICT_CELIAC"
    STANDARD_GF = "STANDARD_GF"
    # v1 additions
    NCGS = "NCGS"
    CUSTOM = "CUSTOM"


@dataclass
class SensitivityProfile:
    """Defines the rules for filtering menu items by dietary safety."""

    profile_type: ProfileType
    name: str
    description: str

    allow_cross_contact_low: bool = False
    allow_cross_contact_high: bool = False
    min_confidence: float = 0.5

    # v1: specific ingredient exclusions
    exclude_oats: bool = False
    exclude_oat_derivatives: bool = False
    additional_exclusions: list[str] = field(default_factory=list)


# Pre-built profiles for v0
STRICT_CELIAC = SensitivityProfile(
    profile_type=ProfileType.STRICT_CELIAC,
    name="Strict Celiac",
    description=(
        "No cross-contact tolerated. Only items with no/low cross-contact risk "
        "and high confidence of being gluten-free. Excludes oats by default."
    ),
    allow_cross_contact_low=False,
    allow_cross_contact_high=False,
    min_confidence=0.7,
    exclude_oats=True,
)

STANDARD_GF = SensitivityProfile(
    profile_type=ProfileType.STANDARD_GF,
    name="Standard Gluten-Free",
    description=(
        "Avoids gluten ingredients but tolerates low cross-contact risk. "
        "Suitable for those with gluten sensitivity who aren't celiac."
    ),
    allow_cross_contact_low=True,
    allow_cross_contact_high=False,
    min_confidence=0.5,
    exclude_oats=False,
)


PROFILES: dict[str, SensitivityProfile] = {
    ProfileType.STRICT_CELIAC: STRICT_CELIAC,
    ProfileType.STANDARD_GF: STANDARD_GF,
}


def get_profile(profile_type: str) -> SensitivityProfile:
    """Look up a profile by type name. Falls back to STRICT_CELIAC."""
    return PROFILES.get(profile_type, STRICT_CELIAC)
