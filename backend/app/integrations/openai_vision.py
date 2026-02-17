"""OpenAI Vision API integration for menu OCR and GF classification."""

import base64
import json
import logging
from dataclasses import dataclass

from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ExtractedMenuItem:
    name: str
    description: str | None
    price: float | None
    is_gluten_free: bool
    cross_contact_risk: str  # "none", "low", "high"
    gf_label_on_menu: str | None
    confidence: float
    reasoning: str


@dataclass
class MenuOCRResult:
    raw_text: str
    items: list[ExtractedMenuItem]
    has_gf_section: bool
    gluten_mentioned: bool


MENU_EXTRACTION_PROMPT = """\
You are an expert at reading restaurant menus and identifying gluten-free items.
Analyze the menu photo and extract ALL menu items.

For each item, determine:
1. **name**: The item name exactly as written
2. **description**: Brief description if visible
3. **price**: Numeric price if visible (null if not)
4. **is_gluten_free**: Whether this item is likely gluten-free
5. **cross_contact_risk**: "none" if naturally GF and simple prep, "low" if probably GF \
but shared kitchen, "high" if contains or likely contains gluten
6. **gf_label_on_menu**: Any GF marking on the menu (e.g., "GF", "gluten-free", \
asterisk, etc.) or null
7. **confidence**: Your confidence in the GF classification (0.0 to 1.0)
8. **reasoning**: Brief explanation of why you classified it this way

Also determine:
- **has_gf_section**: Whether the menu has a dedicated gluten-free section
- **gluten_mentioned**: Whether gluten/GF is mentioned anywhere on the menu

IMPORTANT classification rules:
- Plain grilled meats, fish, vegetables, rice, and potatoes are typically GF
- Anything breaded, with pasta, bread, flour tortillas, soy sauce, or beer batter is NOT GF
- Fried items from shared fryers have HIGH cross-contact risk
- If unsure, default to cross_contact_risk="high" and is_gluten_free=false

Respond ONLY with valid JSON matching this schema:
{
  "raw_text": "full OCR text of the menu",
  "has_gf_section": boolean,
  "gluten_mentioned": boolean,
  "items": [
    {
      "name": "string",
      "description": "string or null",
      "price": number or null,
      "is_gluten_free": boolean,
      "cross_contact_risk": "none|low|high",
      "gf_label_on_menu": "string or null",
      "confidence": number,
      "reasoning": "string"
    }
  ]
}
"""


class OpenAIVisionClient:
    """Client for OpenAI Vision API to perform menu OCR and GF analysis."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def analyze_menu_photo(
        self, image_bytes: bytes, mime_type: str = "image/jpeg"
    ) -> MenuOCRResult:
        """
        Send a menu photo to OpenAI Vision for OCR + GF classification.
        Returns structured extraction of all menu items.
        """
        client = self._get_client()
        b64_image = base64.b64encode(image_bytes).decode("utf-8")

        for attempt in range(3):
            try:
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": MENU_EXTRACTION_PROMPT},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{b64_image}",
                                        "detail": "high",
                                    },
                                },
                            ],
                        }
                    ],
                    max_tokens=4096,
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )
                break
            except Exception as exc:
                logger.warning(
                    "OpenAI Vision attempt %d failed: %s", attempt + 1, exc
                )
                if attempt == 2:
                    raise

        raw_content = response.choices[0].message.content or "{}"
        data = json.loads(raw_content)

        items = [
            ExtractedMenuItem(
                name=item.get("name", ""),
                description=item.get("description"),
                price=item.get("price"),
                is_gluten_free=item.get("is_gluten_free", False),
                cross_contact_risk=item.get("cross_contact_risk", "high"),
                gf_label_on_menu=item.get("gf_label_on_menu"),
                confidence=item.get("confidence", 0.0),
                reasoning=item.get("reasoning", ""),
            )
            for item in data.get("items", [])
        ]

        return MenuOCRResult(
            raw_text=data.get("raw_text", ""),
            items=items,
            has_gf_section=data.get("has_gf_section", False),
            gluten_mentioned=data.get("gluten_mentioned", False),
        )

    async def classify_text_menu(self, menu_text: str) -> MenuOCRResult:
        """Classify an already-extracted text menu (no image needed)."""
        client = self._get_client()

        prompt = (
            MENU_EXTRACTION_PROMPT
            + "\n\nHere is the menu text (already extracted via OCR):\n\n"
            + menu_text
        )

        for attempt in range(3):
            try:
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4096,
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )
                break
            except Exception as exc:
                logger.warning(
                    "OpenAI text classification attempt %d failed: %s",
                    attempt + 1,
                    exc,
                )
                if attempt == 2:
                    raise

        raw_content = response.choices[0].message.content or "{}"
        data = json.loads(raw_content)

        items = [
            ExtractedMenuItem(
                name=item.get("name", ""),
                description=item.get("description"),
                price=item.get("price"),
                is_gluten_free=item.get("is_gluten_free", False),
                cross_contact_risk=item.get("cross_contact_risk", "high"),
                gf_label_on_menu=item.get("gf_label_on_menu"),
                confidence=item.get("confidence", 0.0),
                reasoning=item.get("reasoning", ""),
            )
            for item in data.get("items", [])
        ]

        return MenuOCRResult(
            raw_text=data.get("raw_text", menu_text),
            items=items,
            has_gf_section=data.get("has_gf_section", False),
            gluten_mentioned=data.get("gluten_mentioned", False),
        )
