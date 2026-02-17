"""
GF Classifier: determines whether each menu item is safe based on a sensitivity profile.

Takes raw extracted menu items from OCR and applies dietary rules to produce
a classification result per item.
"""

import logging
import re
from dataclasses import dataclass

from app.integrations.openai_vision import ExtractedMenuItem
from app.services.gf_analysis.sensitivity_profiles import SensitivityProfile

logger = logging.getLogger(__name__)

# Known gluten-containing keywords for heuristic fallback
GLUTEN_KEYWORDS = {
    "wheat", "barley", "rye", "malt", "triticale", "semolina", "durum",
    "spelt", "farro", "kamut", "einkorn", "bulgur", "couscous", "seitan",
    "flour tortilla", "bread", "breadcrumb", "breaded", "panko", "crouton",
    "pasta", "noodle", "spaghetti", "penne", "fettuccine", "linguine",
    "ravioli", "gnocchi", "udon", "ramen", "soy sauce", "teriyaki",
    "beer batter", "tempura", "dumpling", "wonton", "gyoza",
    "pita", "naan", "biscuit", "croissant", "muffin", "cake", "pie crust",
    "pretzel", "waffle", "pancake", "crepe",
}

OAT_KEYWORDS = {"oat", "oats", "oatmeal", "oat flour", "granola", "muesli"}

GF_LABEL_PATTERNS = [
    re.compile(r"\bGF\b", re.IGNORECASE),
    re.compile(r"gluten[\s-]?free", re.IGNORECASE),
    re.compile(r"celiac[\s-]?safe", re.IGNORECASE),
    re.compile(r"\*GF", re.IGNORECASE),
]


@dataclass
class ClassifiedItem:
    """Result of classifying a single menu item against a sensitivity profile."""
    name: str
    description: str | None
    price: float | None
    is_safe: bool
    is_gluten_free: bool
    cross_contact_risk: str
    gf_label_on_menu: str | None
    confidence: float
    reasoning: str
    excluded_reason: str | None = None


def _text_contains_gluten(text: str) -> bool:
    """Heuristic: check if text mentions known gluten-containing ingredients."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in GLUTEN_KEYWORDS)


def _text_contains_oats(text: str) -> bool:
    """Check if text mentions oat-based ingredients."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in OAT_KEYWORDS)


def _detect_gf_label(text: str) -> str | None:
    """Detect GF labeling in text using known patterns."""
    for pattern in GF_LABEL_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return None


def classify_item(
    item: ExtractedMenuItem,
    profile: SensitivityProfile,
) -> ClassifiedItem:
    """
    Classify a single menu item against a sensitivity profile.

    Uses the AI classification from OpenAI Vision as the primary signal,
    with heuristic keyword checks as a safety net.
    """
    # Start with AI classification
    is_gf = item.is_gluten_free
    risk = item.cross_contact_risk
    confidence = item.confidence
    reasons: list[str] = []

    # Heuristic safety net: if AI says GF but text contains gluten keywords
    combined_text = f"{item.name} {item.description or ''}"
    if is_gf and _text_contains_gluten(combined_text):
        is_gf = False
        confidence = max(0.3, confidence - 0.3)
        reasons.append("Heuristic override: gluten keywords found in item text")

    # Detect GF labels
    gf_label = item.gf_label_on_menu or _detect_gf_label(combined_text)

    # Apply profile rules
    is_safe = is_gf
    excluded_reason = None

    if not is_gf:
        is_safe = False
        excluded_reason = "Item classified as containing gluten"
    elif confidence < profile.min_confidence:
        is_safe = False
        excluded_reason = (
            f"Confidence {confidence:.2f} below threshold {profile.min_confidence:.2f}"
        )
    elif risk == "high" and not profile.allow_cross_contact_high:
        is_safe = False
        excluded_reason = "High cross-contact risk not allowed by profile"
    elif risk == "low" and not profile.allow_cross_contact_low:
        is_safe = False
        excluded_reason = "Low cross-contact risk not allowed by strict profile"

    # Oat check (v1 readiness)
    if is_safe and profile.exclude_oats and _text_contains_oats(combined_text):
        is_safe = False
        excluded_reason = "Contains oats/oat derivatives (excluded by profile)"

    if reasons:
        reasoning = f"{item.reasoning}; {'; '.join(reasons)}"
    else:
        reasoning = item.reasoning

    return ClassifiedItem(
        name=item.name,
        description=item.description,
        price=item.price,
        is_safe=is_safe,
        is_gluten_free=is_gf,
        cross_contact_risk=risk,
        gf_label_on_menu=gf_label,
        confidence=confidence,
        reasoning=reasoning,
        excluded_reason=excluded_reason,
    )


def classify_menu(
    items: list[ExtractedMenuItem],
    profile: SensitivityProfile,
) -> list[ClassifiedItem]:
    """Classify all items in a menu against a sensitivity profile."""
    return [classify_item(item, profile) for item in items]
