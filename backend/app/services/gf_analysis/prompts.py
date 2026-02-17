"""
Prompt templates for OpenAI Vision interactions.

Centralized here so they can be versioned and tuned independently
of the integration client code.
"""

MENU_PHOTO_OCR_AND_CLASSIFY = """\
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
- Sauces and dressings may contain hidden gluten (flour thickener, soy sauce)
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

INGREDIENT_ANALYSIS = """\
You are a food safety expert specializing in gluten-free dining.
Analyze the following ingredient list and determine if the dish is safe
for someone with celiac disease.

Consider:
- Obvious gluten sources (wheat, barley, rye, malt, triticale)
- Hidden gluten sources (modified food starch, hydrolyzed protein, soy sauce,
  malt vinegar, some seasonings)
- Cross-contact risk based on preparation method

Ingredients: {ingredients}
Dish name: {dish_name}

Respond with JSON:
{{
  "is_gluten_free": boolean,
  "cross_contact_risk": "none|low|high",
  "gluten_sources_found": ["list of problematic ingredients"],
  "confidence": number,
  "reasoning": "explanation"
}}
"""

REVIEW_GF_KNOWLEDGE_ANALYSIS = """\
Analyze the following restaurant review for information about how the restaurant
handles gluten-free dining:

Review: {review_text}

Extract:
1. Does the staff seem knowledgeable about gluten-free needs?
2. Are there mentions of cross-contamination prevention?
3. Are there mentions of dedicated GF preparation areas or fryers?
4. Overall sentiment about GF dining at this restaurant.

Respond with JSON:
{{
  "staff_knowledgeable": boolean or null,
  "cross_contact_awareness": boolean or null,
  "dedicated_gf_prep": boolean or null,
  "shared_fryers_mentioned": boolean or null,
  "gf_sentiment": "positive|neutral|negative|unknown",
  "key_quotes": ["relevant quotes from the review"],
  "reasoning": "explanation"
}}
"""
