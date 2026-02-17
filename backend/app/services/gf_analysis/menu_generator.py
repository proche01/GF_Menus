"""
Generated GF Menu builder.

Takes classified menu items and produces a structured GF menu document
for a given sensitivity profile.
"""

import logging
from dataclasses import dataclass, asdict

from app.services.gf_analysis.classifier import ClassifiedItem, classify_menu
from app.services.gf_analysis.sensitivity_profiles import (
    SensitivityProfile,
    get_profile,
)
from app.integrations.openai_vision import ExtractedMenuItem

logger = logging.getLogger(__name__)


@dataclass
class GeneratedMenu:
    """The final generated GF menu for a restaurant + profile combo."""
    sensitivity_profile: str
    total_menu_items: int
    safe_item_count: int
    safe_items: list[dict]
    unsafe_items: list[dict]
    has_gf_section: bool
    gluten_mentioned: bool


def generate_gf_menu(
    extracted_items: list[ExtractedMenuItem],
    profile_type: str = "STRICT_CELIAC",
    has_gf_section: bool = False,
    gluten_mentioned: bool = False,
) -> GeneratedMenu:
    """
    Generate a GF menu from extracted items using a given sensitivity profile.

    Args:
        extracted_items: Raw items from OCR/Vision extraction.
        profile_type: Name of the sensitivity profile to apply.
        has_gf_section: Whether the original menu had a GF section.
        gluten_mentioned: Whether the original menu mentions gluten at all.

    Returns:
        A GeneratedMenu with safe and unsafe items separated.
    """
    profile = get_profile(profile_type)
    classified = classify_menu(extracted_items, profile)

    safe_items = [
        _item_to_dict(item) for item in classified if item.is_safe
    ]
    unsafe_items = [
        _item_to_dict(item) for item in classified if not item.is_safe
    ]

    return GeneratedMenu(
        sensitivity_profile=profile_type,
        total_menu_items=len(classified),
        safe_item_count=len(safe_items),
        safe_items=safe_items,
        unsafe_items=unsafe_items,
        has_gf_section=has_gf_section,
        gluten_mentioned=gluten_mentioned,
    )


def generate_multiple_profiles(
    extracted_items: list[ExtractedMenuItem],
    profile_types: list[str] | None = None,
    has_gf_section: bool = False,
    gluten_mentioned: bool = False,
) -> dict[str, GeneratedMenu]:
    """Generate GF menus for multiple sensitivity profiles at once."""
    if profile_types is None:
        profile_types = ["STRICT_CELIAC", "STANDARD_GF"]

    results = {}
    for pt in profile_types:
        results[pt] = generate_gf_menu(
            extracted_items, pt, has_gf_section, gluten_mentioned
        )
    return results


def _item_to_dict(item: ClassifiedItem) -> dict:
    """Convert a ClassifiedItem to a JSON-serializable dict."""
    return {
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "is_safe": item.is_safe,
        "is_gluten_free": item.is_gluten_free,
        "cross_contact_risk": item.cross_contact_risk,
        "gf_label_on_menu": item.gf_label_on_menu,
        "confidence": item.confidence,
        "reasoning": item.reasoning,
        "excluded_reason": item.excluded_reason,
    }
