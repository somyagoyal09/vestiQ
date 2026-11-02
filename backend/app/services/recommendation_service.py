# Purpose: outfit ranking: normalises categories, colours and domains
from __future__ import annotations

from datetime import datetime, timezone
from itertools import product

# Vestiq Recommendation Engine
# Context-aware wardrobe ranking for women and men.


# -----------------------------
# Category vocabulary
# -----------------------------

TOPS = {
    "top", "t-shirt", "shirt", "shirt_blouse", "blouse", "crop_top",
    "casual_top", "tank_top", "polo", "sweater", "cardigan", "jacket",
    "coat", "hoodie", "kurti", "women_kurta", "men_kurta", "kurta",
    "nehru_jacket", "tunic", "vest", "waistcoat",
}

BOTTOMS = {
    "jeans", "straight_fit_jeans", "wide_leg_jeans", "bell_bottom",
    "flared_jeans", "pants", "trousers", "shorts", "skirt", "palazzo",
    "leggings", "leggings_salwar", "salwar", "dhoti_pants", "culottes",
    "joggers", "cargo_pants", "track_pants",
}

ONE_PIECE = {
    "dress", "gown", "jumpsuit", "romper", "playsuit", "saree", "lehenga",
    "sherwani", "anarkali", "kaftan", "maxi_dress", "midi_dress",
    "mini_dress", "shirt_dress", "wrap_dress", "co_ord_set", "co_ords",
    "coord_set", "ethnic_set", "ethnic_sets", "kurta_set", "salwar_suit",
    "suit_set", "pant_suit", "formal_suit", "tuxedo", "three_piece_suit",
    "tracksuit", "pajama_set", "dhoti_kurta_set", "sharara_set",
    "anarkali_set",
}

TRADITIONAL = {
    "kurti", "women_kurta", "men_kurta", "kurta", "nehru_jacket",
    "blouse", "leggings_salwar", "salwar", "palazzo", "dhoti_pants",
    "saree", "lehenga", "sherwani", "anarkali", "kaftan", "ethnic_set",
    "ethnic_sets", "kurta_set", "salwar_suit", "sharara_set",
    "anarkali_set", "dhoti_kurta_set",
}

WESTERN = TOPS | BOTTOMS | {
    "dress", "gown", "jumpsuit", "romper", "playsuit", "co_ord_set",
    "co_ords", "coord_set", "suit_set", "pant_suit", "formal_suit",
    "tuxedo", "three_piece_suit", "tracksuit", "pajama_set",
}

STYLE_KEYWORDS = {
    "casual": {"casual", "daily", "everyday", "comfortable", "comfort"},
    "minimal": {"minimal", "simple", "clean", "low_key", "lowkey"},
    "cute": {"cute", "sweet", "soft"},
    "trendy": {"trendy", "fashionable", "stylish", "cool", "gen_z"},
    "elegant": {"elegant", "classy", "graceful", "polished"},
    "chill": {"chill", "relaxed", "laid_back"},
    "dressy": {"dressy", "party", "glam", "glamorous"},
    "traditional": {"traditional", "ethnic", "indian", "desi"},
    "modern": {"modern", "contemporary", "western"},
    "formal": {"formal", "office", "business", "professional"},
    "bold": {"bold", "statement", "bright"},
}

COLOR_COMPATIBILITY = {
    "black": {
        "white", "grey", "gray", "beige", "cream", "red", "pink",
        "blue", "navy", "green", "brown", "purple",
    },
    "white": {
        "black", "blue", "navy", "red", "pink", "green", "brown",
        "grey", "gray", "beige", "cream", "purple",
    },
    "blue": {
        "white", "black", "beige", "cream", "grey", "gray", "brown",
        "pink", "navy",
    },
    "navy": {
        "white", "beige", "cream", "grey", "gray", "pink", "brown", "blue",
    },
    "red": {
        "white", "black", "beige", "cream", "navy", "grey", "gray", "blue",
    },
    "green": {"white", "beige", "cream", "brown", "black", "navy"},
    "pink": {
        "white", "black", "grey", "gray", "navy", "beige", "blue",
    },
    "purple": {"white", "black", "grey", "gray", "beige", "cream"},
    "yellow": {"white", "black", "blue", "navy", "brown", "beige"},
    "orange": {"white", "black", "blue", "navy", "brown", "beige"},
    "brown": {
        "white", "beige", "cream", "blue", "black", "green", "navy",
    },
    "beige": {
        "black", "white", "brown", "navy", "blue", "green", "pink", "red",
    },
    "cream": {"black", "brown", "navy", "blue", "green", "red", "pink"},
    "grey": {"black", "white", "navy", "blue", "pink", "red", "purple"},
    "gray": {"black", "white", "navy", "blue", "pink", "red", "purple"},
}

COLOR_ALIASES = {
    "grey": "gray",
    "charcoal": "gray",
    "off_white": "cream",
    "offwhite": "cream",
    "ivory": "cream",
    "peach": "pink",
    "maroon": "red",
    "wine": "red",
    "sky_blue": "blue",
    "light_blue": "blue",
    "dark_blue": "navy",
}

CATEGORY_ALIASES = {
    "tshirts": "t-shirt",
    "t_shirt": "t-shirt",
    "tee": "t-shirt",
    "tees": "t-shirt",
    "shirts": "shirt",
    "tops": "top",
    "casual_tops": "casual_top",
    "jean": "jeans",
    "straight_jeans": "straight_fit_jeans",
    "straight_fit": "straight_fit_jeans",
    "wide_leg": "wide_leg_jeans",
    "wide_leg_pants": "wide_leg_jeans",
    "bell_bottom_jeans": "bell_bottom",
    "flare": "flared_jeans",
    "flared": "flared_jeans",
    "trouser": "trousers",
    "pant": "pants",
    "skirts": "skirt",
    "kurtis": "kurti",
    "sarees": "saree",
    "dresses": "dress",
    "jumpsuits": "jumpsuit",
    "ethnic": "ethnic_set",
    "ethnic_sets": "ethnic_set",
    "co_ords": "co_ord_set",
    "co-ords": "co_ord_set",
    "coord": "co_ord_set",
    "coord_set": "co_ord_set",
    "leggings_salwar": "leggings_salwar",
    "dhoti": "dhoti_pants",
    "dhoti_pant": "dhoti_pants",
}


# -----------------------------
# Normalization helpers
# -----------------------------

def normalize(value):
    if value is None:
        return ""
    text = str(value).strip().lower()
    for old, new in (("-", "_"), ("/", "_"), (" ", "_")):
        text = text.replace(old, new)
    return text


def canonical_category(value):
    category = normalize(value)
    return CATEGORY_ALIASES.get(category, category)


def canonical_color(value):
    color = normalize(value)
    return COLOR_ALIASES.get(color, color)


def matches_requested_color(item, requested_color):
    """Require the selected colour when a colour preference is explicit."""
    if not requested_color:
        return True

    actual = canonical_color(item.get("color"))
    wanted = canonical_color(requested_color)

    return bool(actual and wanted and actual == wanted)


def as_set(value):
    if value is None:
        return set()
    if isinstance(value, (list, tuple, set)):
        return {normalize(x) for x in value if normalize(x)}
    return {
        normalize(x)
        for x in str(value).split(",")
        if normalize(x)
    }


def item_text(item):
    fields = (
        "name", "category", "style", "domain", "occasion",
        "occasion_tags", "description",
    )
    return " ".join(str(item.get(key, "")) for key in fields).lower()


def infer_gender(item):
    return normalize(
        item.get("gender")
        or item.get("target_gender")
        or item.get("for_gender")
    )


def infer_domain(item):
    explicit = normalize(item.get("domain"))

    if explicit in {"western", "traditional", "indo_western", "fusion"}:
        return explicit

    if canonical_category(item.get("category")) in TRADITIONAL:
        return "traditional"

    text = item_text(item)
    if any(value in text for value in ("indo-western", "indo_western", "fusion")):
        return "indo_western"

    return "western"


def infer_style(item):
    explicit = normalize(item.get("style"))
    if explicit:
        return explicit

    category = canonical_category(item.get("category"))

    if category in TRADITIONAL:
        return "traditional"

    if category in {
        "dress", "jumpsuit", "romper", "playsuit", "gown",
        "suit_set", "formal_suit", "tuxedo",
    }:
        return "elegant"

    if category in {
        "t-shirt", "jeans", "wide_leg_jeans", "straight_fit_jeans",
        "bell_bottom", "flared_jeans", "hoodie", "joggers", "shorts",
    }:
        return "casual"

    return "classic"


def infer_weight(item):
    explicit = normalize(
        item.get("outfit_weight")
        or item.get("weight")
        or item.get("fabric_weight")
    )

    if explicit in {"light", "medium", "heavy"}:
        return explicit

    category = canonical_category(item.get("category"))

    if category in {
        "coat", "sweater", "jacket", "lehenga", "sherwani",
        "gown", "suit_set", "formal_suit", "tuxedo",
    }:
        return "heavy"

    if category in {
        "t-shirt", "tank_top", "shorts", "skirt", "blouse",
        "romper", "playsuit",
    }:
        return "light"

    return "medium"


def is_one_piece(item):
    category = canonical_category(item.get("category"))
    if category in ONE_PIECE:
        return True

    text = item_text(item)
    phrases = (
        "one piece", "one-piece", "full dress", "full outfit",
        "complete set", "co ord", "co-ord", "coord set",
        "ethnic set", "suit set", "kurta set", "salwar suit",
        "tracksuit", "pajama set",
    )
    return any(phrase in text for phrase in phrases)


def is_top(item):
    if is_one_piece(item):
        return False
    return canonical_category(item.get("category")) in TOPS


def is_bottom(item):
    if is_one_piece(item):
        return False
    return canonical_category(item.get("category")) in BOTTOMS


def is_complete_set(item):
    return is_one_piece(item)


def item_length(item):
    text = item_text(item)
    explicit = normalize(
        item.get("length")
        or item.get("fit")
        or item.get("silhouette")
    )
    combined = f"{text} {explicit}"

    if any(value in combined for value in (
        "mini", "short", "cropped", "crop_top", "crop",
    )):
        return "short"

    if any(value in combined for value in (
        "midi", "regular_length", "regular",
    )):
        return "medium"

    if any(value in combined for value in (
        "long", "maxi", "floor_length", "ankle_length",
    )):
        return "long"

    return "unknown"


def bottom_shape(item):
    category = canonical_category(item.get("category"))
    text = item_text(item)

    if category in {"bell_bottom", "flared_jeans"} or any(
        value in text for value in ("bell bottom", "bell_bottom", "flare", "flared")
    ):
        return "flared"

    if category in {
        "wide_leg_jeans", "wide_leg_pants", "palazzo", "culottes",
    } or any(value in text for value in (
        "wide leg", "wide_leg", "palazzo", "culotte",
    )):
        return "wide"

    if category == "straight_fit_jeans" or "straight fit" in text:
        return "straight"

    if category == "skinny_jeans" or "skinny" in text:
        return "skinny"

    return category


def gender_allowed(item, user_gender):
    gender = normalize(user_gender)
    item_gender = infer_gender(item)

    if (
        not gender
        or gender in {"any", "unisex", "both"}
        or not item_gender
        or item_gender in {"any", "unisex", "both"}
    ):
        return True

    aliases = {
        "female": {"female", "woman", "women", "girl"},
        "male": {"male", "man", "men", "boy"},
    }

    target = (
        "female" if gender in aliases["female"]
        else "male" if gender in aliases["male"]
        else gender
    )

    return (
        item_gender in {target, ""}
        or item_gender in aliases.get(target, {target})
    )


# -----------------------------
# Occasion and category helpers
# -----------------------------

def occasion_family(occasion):
    o = normalize(occasion)

    if o in {"college", "everyday", "daily", "casual"}:
        return "casual"
    if o in {"office", "business", "formal", "work"}:
        return "formal"
    if o in {"party", "parties", "college_party", "date", "night_out"}:
        return "party"
    if o in {
        "wedding", "weddings", "family_events", "family_event",
        "festival", "festivals", "festive", "ethnic",
    }:
        return "festive"
    if o in {"travel", "trip"}:
        return "travel"

    return o


def requested_category(value):
    v = canonical_category(value)

    aliases = {
        "casual_top": {
            "top", "t-shirt", "shirt", "casual_top", "crop_top",
        },
        "jeans": {
            "jeans", "straight_fit_jeans", "wide_leg_jeans",
            "bell_bottom", "flared_jeans",
        },
        "trousers": {"trousers", "pants", "wide_leg_pants"},
        "dress": {"dress", "gown", "jumpsuit", "romper", "playsuit"},
        "traditional": TRADITIONAL,
    }

    return aliases.get(v, {v} if v else set())

# -----------------------------
# Style Me request parser
# -----------------------------

def parse_stylist_request(prompt):
    import re

    raw = str(prompt or "").strip().lower()
    text = normalize(raw)

    styles = set()

    for style, keywords in STYLE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            styles.add(style)

    colors = set()

    for color in set(COLOR_COMPATIBILITY) | set(COLOR_ALIASES):
        pattern = r"\b" + re.escape(color.replace("_", " ")) + r"\b"
        if re.search(pattern, raw):
            colors.add(canonical_color(color))

    weight = None

    if any(k in text for k in ("light", "lightweight", "airy", "cool")):
        weight = "light"
    elif any(k in text for k in ("heavy", "warm", "covered", "winter")):
        weight = "heavy"

    # Correctly read Style Me popup labels.
    top_label = re.search(
        r"\btop\s+preference\s*:\s*([^.;]+)", raw
    )
    bottom_label = re.search(
        r"\bbottom\s+preference\s*:\s*([^.;]+)", raw
    )

    top_value = top_label.group(1).strip() if top_label else ""
    bottom_value = bottom_label.group(1).strip() if bottom_label else ""

    def parse_top_value(value):
        v = value.lower().strip()

        if not v or v in {"anything", "no preference", "no top", "none"}:
            return None
        if "indo-western" in v or "indo western" in v or "fusion" in v:
            return "traditional"
        if "traditional" in v or "ethnic" in v:
            return "traditional"
        if any(k in v for k in ("t-shirt", "t shirt", "tee")):
            return "t-shirt"
        if v == "shirt" or v.startswith("shirt "):
            return "shirt"
        if "kurti" in v or "kurta" in v:
            return "kurti"
        if "anarkali" in v:
            return "anarkali"
        if "saree" in v or "sari" in v:
            return "saree"
        if "lehenga" in v:
            return "lehenga"
        if v == "dress" or v.startswith("dress "):
            return "dress"

        return normalize(v)

    def parse_bottom_value(value):
        v = value.lower().strip()

        if not v or v in {"anything", "no preference", "none"}:
            return None
        if v in {
            "no bottom", "one-piece", "one piece",
            "no bottom / one-piece",
        }:
            return None
        if any(k in v for k in ("bell-bottom", "bell bottom", "flared", "flare")):
            return "bell_bottom"
        if "wide-leg" in v or "wide leg" in v:
            return "wide_leg_jeans"
        if "straight-fit" in v or "straight fit" in v:
            return "straight_fit_jeans"
        if "jeans" in v:
            return "jeans"
        if "trouser" in v or "pants" in v:
            return "trousers"
        if "palazzo" in v:
            return "palazzo"
        if "skirt" in v:
            return "skirt"

        return normalize(v)

    top = parse_top_value(top_value)
    bottom = parse_bottom_value(bottom_value)

    one_piece_preference = bottom_value.lower().strip() in {
        "no bottom", "one-piece", "one piece", "no bottom / one-piece",
    }

    # Fallback parsing for free-text requests.
    if not top:
        if any(k in raw for k in ("t-shirt", "t shirt", "tee")):
            top = "t-shirt"
        elif re.search(r"\bshirt\b", raw):
            top = "shirt"
        elif "kurti" in raw or "kurta" in raw:
            top = "kurti"
        elif "anarkali" in raw:
            top = "anarkali"
        elif "saree" in raw or "sari" in raw:
            top = "saree"
        elif "lehenga" in raw:
            top = "lehenga"
        elif re.search(r"\bdress\b", raw):
            top = "dress"
        elif any(k in raw for k in ("traditional", "ethnic", "indian", "desi")):
            top = "traditional"

    if not bottom:
        if any(k in raw for k in ("bell-bottom", "bell bottom", "flared", "flare")):
            bottom = "bell_bottom"
        elif "wide-leg" in raw or "wide leg" in raw:
            bottom = "wide_leg_jeans"
        elif "straight-fit" in raw or "straight fit" in raw:
            bottom = "straight_fit_jeans"
        elif re.search(r"\bjeans\b", raw):
            bottom = "jeans"
        elif "trouser" in raw or re.search(r"\bpants\b", raw):
            bottom = "trousers"
        elif "palazzo" in raw:
            bottom = "palazzo"
        elif "skirt" in raw:
            bottom = "skirt"

    # Identify the domain.
    domain = None

    if "indo-western" in raw or "indo western" in raw:
        domain = "indo_western"
    elif "fusion" in raw:
        domain = "fusion"
    elif "western" in raw and "indo" not in raw:
        domain = "western"
    elif any(k in raw for k in ("traditional", "ethnic", "indian", "desi")):
        domain = "traditional"

    # Extract separate colours for top and bottom.
    color_names = sorted(
        set(COLOR_COMPATIBILITY) | set(COLOR_ALIASES),
        key=len,
        reverse=True,
    )

    top_color = None
    bottom_color = None

    top_words = (
        r"(?:top|shirt|t[\s-]?shirt|tee|blouse|kurti|kurta|"
        r"crop[\s_-]?top|sweater|hoodie|jacket)"
    )
    bottom_words = (
        r"(?:jeans|trousers|pants|leggings|palazzo|skirt|"
        r"shorts|joggers|culottes)"
    )

    for color in color_names:
        variants = {
            color.replace("_", " "),
            color.replace("_", "-"),
            color,
        }

        for variant in sorted(variants, key=len, reverse=True):
            c = re.escape(variant)

            if top_color is None and re.search(
                rf"\b{c}\b\s+{top_words}\b", raw
            ):
                top_color = canonical_color(color)

            if top_color is None and re.search(
                rf"\b{top_words}\b\s+(?:in\s+)?{c}\b", raw
            ):
                top_color = canonical_color(color)

            if bottom_color is None and re.search(
                rf"\b{c}\b\s+{bottom_words}\b", raw
            ):
                bottom_color = canonical_color(color)

            if bottom_color is None and re.search(
                rf"\b{bottom_words}\b\s+(?:in\s+)?{c}\b", raw
            ):
                bottom_color = canonical_color(color)

    return {
        "styles": sorted(styles),
        "preferred_color": sorted(colors)[0] if colors else None,
        "preferred_top_color": top_color,
        "preferred_bottom_color": bottom_color,
        "preferred_weight": weight,
        "preferred_top": top,
        "preferred_bottom": bottom,
        "one_piece_preference": one_piece_preference,
        "preferred_domain": domain,
        "short_preference": any(
            k in text for k in ("short", "cropped", "crop_top", "small_top")
        ),
        "long_preference": any(
            k in text for k in ("long", "full_length", "maxi")
        ),
    }


# -----------------------------
# Scoring functions
# -----------------------------

def weather_score(item, temperature, weather_condition, rain_probability):
    cat = canonical_category(item.get("category"))
    weight = infer_weight(item)
    score = 0.0

    if temperature >= 32:
        score += 18 if weight == "light" else -14 if weight == "heavy" else 5
    elif temperature >= 28:
        score += 14 if weight == "light" else -7 if weight == "heavy" else 5
    elif temperature >= 23:
        score += 8 if weight in {"light", "medium"} else 2
    elif temperature >= 18:
        score += 8 if weight in {"medium", "heavy"} else 2
    else:
        score += 16 if weight == "heavy" else 8 if weight == "medium" else -8

    condition = normalize(weather_condition)

    if any(k in condition for k in ("rain", "storm", "thunder")) or rain_probability >= 50:
        if cat in {
            "shorts", "skirt", "palazzo", "wide_leg_jeans", "flared_jeans",
        }:
            score -= 3
        if cat in {"trousers", "pants", "jeans", "jacket", "coat"}:
            score += 4

    return score


def occasion_score(item, occasion):
    cat = canonical_category(item.get("category"))
    style = infer_style(item)
    family = occasion_family(occasion)
    score = 0.0

    if family == "casual":
        if cat in {
            "t-shirt", "top", "casual_top", "shirt", "jeans",
            "straight_fit_jeans", "wide_leg_jeans", "bell_bottom",
            "flared_jeans", "trousers", "pants", "skirt", "dress",
            "jumpsuit", "romper", "hoodie", "joggers",
        }:
            score += 15
        if cat in {"sherwani", "lehenga", "gown", "tuxedo", "formal_suit"}:
            score -= 12

    elif family == "formal":
        if cat in {
            "shirt", "trousers", "pants", "blazer", "jacket",
            "formal_suit", "pant_suit", "tuxedo", "dress", "gown",
        }:
            score += 18
        if cat in {"t-shirt", "shorts", "joggers", "hoodie"}:
            score -= 14

    elif family == "festive":
        if cat in TRADITIONAL or cat in {"dress", "gown", "suit_set"}:
            score += 20
        if cat in {"shorts", "joggers", "hoodie"}:
            score -= 8

    elif family == "party":
        if cat in {
            "dress", "gown", "jumpsuit", "romper", "shirt", "top",
            "t-shirt", "skirt", "trousers", "jeans", "suit_set",
            "formal_suit",
        }:
            score += 13

    elif family == "travel":
        if cat in {
            "t-shirt", "shirt", "top", "jeans", "pants", "trousers",
            "joggers", "dress", "jumpsuit", "hoodie", "shorts",
        }:
            score += 12

    if style == "formal" and family == "formal":
        score += 5

    return score


def style_score(item, preferred_styles):
    styles = as_set(preferred_styles)

    if not styles:
        return 0.0

    item_style = infer_style(item)

    if item_style in styles:
        return 18.0
    if item_style == "casual" and "minimal" in styles:
        return 8.0
    if item_style == "traditional" and "elegant" in styles:
        return 6.0

    return -3.0


def color_score(item, preferred_color=None):
    if not preferred_color:
        return 0.0

    wanted = canonical_color(preferred_color)
    actual = canonical_color(item.get("color"))

    if actual == wanted:
        return 16.0

    return 0.0


def pair_color_score(a, b):
    ca = canonical_color(a.get("color"))
    cb = canonical_color(b.get("color"))

    if not ca or not cb:
        return 2.0

    if ca == cb:
        return 5.0

    compatible = COLOR_COMPATIBILITY.get(ca, set()) | {
        color
        for color, matches in COLOR_COMPATIBILITY.items()
        if ca in matches
    }

    if cb not in compatible:
        return -8.0

    # Strong neutral pairings
    neutrals = {"black", "white", "gray", "grey", "beige", "cream"}

    if cb in neutrals or ca in neutrals:
        return 18.0

    # Particularly versatile combinations
    preferred_pairs = {
        frozenset(("pink", "blue")),
        frozenset(("pink", "navy")),
        frozenset(("blue", "white")),
        frozenset(("navy", "white")),
        frozenset(("green", "beige")),
        frozenset(("brown", "cream")),
        frozenset(("red", "black")),
    }

    if frozenset((ca, cb)) in preferred_pairs:
        return 16.0

    return 12.0


def wear_score(item):
    last = item.get("last_worn_at") or item.get("worn_at")

    if not last:
        return 7.0

    try:
        if isinstance(last, datetime):
            dt = last
        else:
            dt = datetime.fromisoformat(
                str(last).replace("Z", "+00:00")
            )

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        days = max(
            0.0,
            (
                datetime.now(timezone.utc)
                - dt.astimezone(timezone.utc)
            ).total_seconds() / 86400,
        )

        if days < 1:
            return -12.0
        if days < 2:
            return -9.0
        if days < 3:
            return -6.0
        if days < 5:
            return -3.0
        if days < 7:
            return 2.0

        return 7.0

    except (TypeError, ValueError, OverflowError):
        return 0.0


def preference_score(
    item,
    preferred_top=None,
    preferred_bottom=None,
    specific_request=None,
):
    cat = canonical_category(item.get("category"))
    score = 0.0

    top_set = requested_category(preferred_top)
    bottom_set = requested_category(preferred_bottom)

    if top_set and cat in top_set:
        score += 42

    if bottom_set and cat in bottom_set:
        score += 42

    req = parse_stylist_request(specific_request or "")

    if req["preferred_top"] and cat in requested_category(req["preferred_top"]):
        score += 36

    if req["preferred_bottom"] and cat in requested_category(req["preferred_bottom"]):
        score += 36

    if req["short_preference"] and item_length(item) == "short":
        score += 24

    if req["long_preference"] and item_length(item) == "long":
        score += 24

    return score

def vibe_penalty(item, vibe):
    v = normalize(vibe)

    if not v:
        return 0

    cat = canonical_category(item.get("category"))

    if v in {
        "simple", "simple_&_comfortable", "simple_and_comfortable",
        "comfortable", "keep_it_simple",
    }:
        return (
            8
            if infer_weight(item) != "heavy"
            and cat not in {"sherwani", "lehenga", "tuxedo", "gown"}
            else -8
        )

    if v in {
        "trendy", "cute", "chill", "elegant", "dressy",
        "casual", "minimal", "traditional", "modern",
    }:
        return style_score(item, {v})

    return 0


def pair_compatibility(
    top,
    bottom,
    occasion,
    user_gender=None,
    requested_top=None,
    requested_bottom=None,
    specific_request="",
):
    tc = canonical_category(top.get("category"))
    bc = canonical_category(bottom.get("category"))

    td = infer_domain(top)
    bd = infer_domain(bottom)

    family = occasion_family(occasion)
    req = parse_stylist_request(specific_request)

    explicit_fusion = any(
        x in normalize(specific_request)
        for x in ("indo western", "indo-western", "fusion")
    )

    if is_one_piece(top) or is_one_piece(bottom):
        return -100.0

    western_good = {
        "t-shirt": {
            "jeans", "straight_fit_jeans", "wide_leg_jeans",
            "bell_bottom", "flared_jeans", "trousers",
            "pants", "skirt", "shorts",
        },
        "top": {
            "jeans", "straight_fit_jeans", "wide_leg_jeans",
            "bell_bottom", "flared_jeans", "trousers",
            "pants", "skirt", "shorts",
        },
        "casual_top": {
            "jeans", "straight_fit_jeans", "wide_leg_jeans",
            "bell_bottom", "flared_jeans", "trousers",
            "pants", "skirt",
        },
        "shirt": {
            "jeans", "straight_fit_jeans", "wide_leg_jeans",
            "bell_bottom", "flared_jeans", "trousers",
            "pants", "skirt", "shorts",
        },
        "blouse": {"skirt", "trousers", "pants", "jeans", "palazzo"},
        "sweater": {"jeans", "trousers", "pants", "skirt"},
        "hoodie": {"jeans", "joggers", "cargo_pants", "shorts"},
        "jacket": {"jeans", "trousers", "pants", "skirt"},
        "kurti": {
            "jeans", "straight_fit_jeans", "wide_leg_jeans",
            "palazzo", "leggings_salwar", "trousers", "pants",
        },
        "women_kurta": {
            "jeans", "palazzo", "leggings_salwar", "trousers", "pants",
        },
        "men_kurta": {"jeans", "trousers", "pants", "dhoti_pants"},
        "nehru_jacket": {"trousers", "pants", "dhoti_pants", "jeans"},
    }

    allowed = western_good.get(tc, set())

    if bc in allowed:
        score = 32.0

        if (
            tc in {"kurti", "women_kurta", "men_kurta", "nehru_jacket"}
            and bd == "western"
        ):
            score += (
                8
                if explicit_fusion or req["preferred_top"] in {"kurti", "kurta"}
                else 3
            )

        if td != bd and not explicit_fusion:
            score -= 2

        if family == "formal" and bc in {"jeans", "shorts"}:
            score -= 18

        if requested_top and tc in requested_category(requested_top):
            score += 5

        if requested_bottom and bc in requested_category(requested_bottom):
            score += 5

        return score

    traditional_good = {
        "kurti": {"leggings_salwar", "palazzo", "jeans", "trousers", "pants"},
        "women_kurta": {
            "leggings_salwar", "palazzo", "jeans", "trousers", "pants",
        },
        "men_kurta": {"dhoti_pants", "trousers", "pants", "jeans"},
        "nehru_jacket": {"dhoti_pants", "trousers", "pants", "jeans"},
        "blouse": {"palazzo", "leggings_salwar", "skirt"},
    }

    if bc in traditional_good.get(tc, set()):
        return 30.0

    return -100.0


def occasion_tag_score(item, occasion):
    tags = as_set(item.get("occasion_tags") or item.get("occasions"))

    if not tags:
        return 0.0

    wanted = normalize(occasion)

    aliases = {
        "college": {"college", "casual", "everyday"},
        "everyday": {"everyday", "casual"},
        "office": {"office", "formal", "work"},
        "family_events": {"family", "family_event", "family_function"},
        "parties": {"party", "parties", "casual_outing", "night_out"},
        "weddings": {"wedding", "weddings"},
        "festivals": {"festive", "festival", "festivals"},
        "travel": {"travel", "trip"},
    }

    wanted_tags = aliases.get(wanted, {wanted})

    if tags & wanted_tags:
        return 24.0

    return -3.0


def item_score(
    item,
    temperature,
    weather_condition,
    occasion,
    rain_probability,
    preferred_styles=None,
    preferred_color=None,
    preferred_weight=None,
    preferred_top=None,
    preferred_bottom=None,
    vibe=None,
    specific_request=None,
):
       
    raw_score = (
        weather_score(
            item, temperature, weather_condition, rain_probability
        )
        + occasion_score(item, occasion)
        + occasion_tag_score(item, occasion)
        + style_score(item, preferred_styles)
        + color_score(item, preferred_color)
        + wear_score(item)
        + preference_score(
            item, preferred_top, preferred_bottom, specific_request
        )
        + vibe_penalty(item, vibe)
        + (
            22.0
            if preferred_weight
            and infer_weight(item) == normalize(preferred_weight)
            else 0.0
        )
    )
    return max(0, min(100, round(raw_score)))


def build_reasons(
    item,
    temperature,
    weather_condition,
    occasion,
    preferred_styles=None,
    preferred_color=None,
    preferred_weight=None,
    preferred_top=None,
    preferred_bottom=None,
    vibe=None,
    specific_request=None,
):
    reasons = []
    cat = canonical_category(item.get("category"))
    family = occasion_family(occasion)

    if preferred_top and cat in requested_category(preferred_top):
        reasons.append(
            f"Matches your {str(preferred_top).replace('_', ' ')} preference."
        )
    elif preferred_bottom and cat in requested_category(preferred_bottom):
        reasons.append(
            f"Matches your {str(preferred_bottom).replace('_', ' ')} preference."
        )

    req = parse_stylist_request(specific_request or "")

    if req["preferred_top"] and cat in requested_category(req["preferred_top"]):
        reasons.append("Matches what you asked for.")

    if req["preferred_bottom"] and cat in requested_category(req["preferred_bottom"]):
        reasons.append("Matches the bottom style you requested.")

    if req["short_preference"] and item_length(item) == "short":
        reasons.append("Fits your request for something short.")

    if family == "casual" and cat not in {
        "sherwani", "lehenga", "tuxedo", "gown",
    }:
        reasons.append("Suitable for the occasion.")

    if family == "festive" and (cat in TRADITIONAL or is_one_piece(item)):
        reasons.append("Fits the occasion's dressing level.")

    if family == "formal" and cat in {
        "shirt", "trousers", "pants", "formal_suit",
        "tuxedo", "dress", "gown",
    }:
        reasons.append("Appropriate for a formal setting.")

    if preferred_styles and infer_style(item) in as_set(preferred_styles):
        reasons.append(f"Matches your {infer_style(item)} style.")

    if preferred_weight and infer_weight(item) == normalize(preferred_weight):
        reasons.append(f"Matches your {infer_weight(item)} outfit preference.")

    if preferred_color and canonical_color(item.get("color")) == canonical_color(preferred_color):
        reasons.append(f"Matches your preferred {preferred_color} colour.")

    if temperature >= 28 and infer_weight(item) == "light":
        reasons.append("Works well for today's warm weather.")
    elif temperature < 20 and infer_weight(item) == "heavy":
        reasons.append("Adds useful coverage for cooler weather.")

    if not item.get("last_worn_at") and not item.get("worn_at"):
        reasons.append("It has not been worn recently.")

    return list(dict.fromkeys(reasons))[:4]


# -----------------------------
# Candidate selection helpers
# -----------------------------

def _candidate_key(a, b=None):
    aid = str(a.get("_id", a.get("id", "")))

    if b is None:
        return f"one:{aid}"

    bid = str(b.get("_id", b.get("id", "")))
    return f"pair:{aid}:{bid}"


def _select_diverse(candidates, limit=9):
    remaining = list(candidates)
    selected = []
    used_keys = set()
    item_counts = {}

    while remaining and len(selected) < limit:
        best = None
        best_score = float("-inf")

        for candidate in remaining:
            key = candidate.get("candidate_key")

            if key in used_keys:
                continue

            item_ids = []

            for item in (
                candidate.get("top"),
                candidate.get("bottom"),
            ):
                if item:
                    item_id = item.get("_id", item.get("id"))

                    if item_id is not None:
                        item_ids.append(str(item_id))

          
            repeat_penalty = sum(
                item_counts.get(item_id, 0) * 25
                for item_id in item_ids
            )

            rank_score = (
                candidate.get("score", 0.0) - repeat_penalty
            )

            if rank_score > best_score:
                best = candidate
                best_score = rank_score

        if best is None:
            break

        chosen = dict(best)
        chosen["rank_score"] = best_score
        selected.append(chosen)

        used_keys.add(best.get("candidate_key"))
        remaining.remove(best)

        for item in (
            best.get("top"),
            best.get("bottom"),
        ):
            if item:
                item_id = item.get("_id", item.get("id"))

                if item_id is not None:
                    item_id = str(item_id)
                    item_counts[item_id] = (
                        item_counts.get(item_id, 0) + 1
                    )

    return selected


def _matches_requested_top(item, preferred_top, preferred_domain=None):
    if not preferred_top:
        return True

    wanted = normalize(preferred_top)
    cat = canonical_category(item.get("category"))

    if wanted in {"traditional", "ethnic"}:
        return (
            cat in TRADITIONAL
            or (
                is_one_piece(item)
                and infer_domain(item)
                in {"traditional", "indo_western", "fusion"}
            )
        )

    if wanted in {"indo_western", "fusion"}:
        return infer_domain(item) in {"indo_western", "fusion"}

    return cat in requested_category(wanted)


def _matches_requested_bottom(item, preferred_bottom):
    if not preferred_bottom:
        return True

    return (
        canonical_category(item.get("category"))
        in requested_category(preferred_bottom)
    )


def _domain_matches(item, preferred_domain):
    if not preferred_domain:
        return True

    domain = infer_domain(item)

    if preferred_domain == "traditional":
        return domain in {"traditional", "indo_western", "fusion"}

    if preferred_domain == "indo_western":
        return domain in {"indo_western", "fusion"}

    return domain == preferred_domain

# -----------------------------
# Main recommendation generator
# -----------------------------

def generate_outfits(
    wardrobe,
    temperature,
    weather_condition,
    occasion,
    rain_probability=0,
    preferred_styles=None,
    preferred_color=None,
    preferred_weight=None,
    preferred_top=None,
    preferred_bottom=None,
    vibe=None,
    specific_request=None,
    user_gender=None,
    top_color=None,
    bottom_color=None,
    one_piece=False,
):
    preferred_styles = preferred_styles or []

    items = [
        item for item in wardrobe
        if gender_allowed(item, user_gender)
    ]

    if not items:
        items = list(wardrobe)

    req = parse_stylist_request(specific_request or "")

    preferred_top = preferred_top or req["preferred_top"]
    preferred_bottom = preferred_bottom or req["preferred_bottom"]

    top_color = top_color or req.get("preferred_top_color")
    bottom_color = bottom_color or req.get("preferred_bottom_color")

    one_piece_preference = bool(
        one_piece or req.get("one_piece_preference")
    )

    preferred_domain = req.get("preferred_domain")

    complete_sets = [
        item for item in items
        if is_complete_set(item)
        and _domain_matches(item, preferred_domain)
        and _matches_requested_top(
            item, preferred_top, preferred_domain
        )
        and matches_requested_color(item, top_color)
    ]

    tops = [
        item for item in items
        if is_top(item)
        and _domain_matches(item, preferred_domain)
        and _matches_requested_top(
            item, preferred_top, preferred_domain
        )
        and matches_requested_color(item, top_color)
    ]

    bottoms = [
        item for item in items
        if is_bottom(item)
        and _domain_matches(item, preferred_domain)
        and _matches_requested_bottom(item, preferred_bottom)
        and matches_requested_color(item, bottom_color)
    ]

    if one_piece_preference:
        tops = []
        bottoms = []

        complete_sets = [
            item for item in items
            if is_complete_set(item)
            and _domain_matches(item, preferred_domain)
            and matches_requested_color(item, top_color)
        ]

    exact_top_available = bool(preferred_top and (complete_sets or tops))
    exact_bottom_available = bool(preferred_bottom and bottoms)

    if preferred_bottom and exact_bottom_available and not one_piece_preference:
        complete_sets = []

    if preferred_top and not exact_top_available and not one_piece_preference:
        complete_sets = [
            item for item in items
            if is_complete_set(item)
            and _domain_matches(item, preferred_domain)
            and matches_requested_color(item, top_color)
        ]

        tops = [
            item for item in items
            if is_top(item)
            and _domain_matches(item, preferred_domain)
            and matches_requested_color(item, top_color)
        ]

    if preferred_bottom and not exact_bottom_available and not one_piece_preference:
        bottoms = [
            item for item in items
            if is_bottom(item)
            and _domain_matches(item, preferred_domain)
            and matches_requested_color(item, bottom_color)
        ]

    candidates = []

    for item in complete_sets:
        score = item_score(
            item, temperature, weather_condition, occasion,
            rain_probability, preferred_styles, preferred_color,
            preferred_weight, preferred_top, preferred_bottom,
            vibe, specific_request,
        )

        reasons = build_reasons(
            item, temperature, weather_condition, occasion,
            preferred_styles, preferred_color, preferred_weight,
            preferred_top, preferred_bottom, vibe, specific_request,
        )

        candidates.append({
            "top": item,
            "bottom": None,
            "outfit_type": "one_piece",
            "score": score,
            "reasons": reasons,
            "candidate_key": _candidate_key(item),
        })

    if not one_piece_preference:
        for top, bottom in product(tops, bottoms):
            if not matches_requested_color(top, top_color):
                continue

            if not matches_requested_color(bottom, bottom_color):
                continue

            if (
                preferred_top
                and exact_top_available
                and not _matches_requested_top(
                    top, preferred_top, preferred_domain
                )
            ):
                continue

            if (
                preferred_bottom
                and exact_bottom_available
                and not _matches_requested_bottom(
                    bottom, preferred_bottom
                )
            ):
                continue

            if preferred_domain and (
                not _domain_matches(top, preferred_domain)
                or not _domain_matches(bottom, preferred_domain)
            ):
                if preferred_domain not in {"indo_western", "fusion"}:
                    continue

            pair_score = pair_compatibility(
                top, bottom, occasion, user_gender,
                preferred_top, preferred_bottom, specific_request,
            )

            if pair_score < 0:
                continue

            score = (
                item_score(
                    top, temperature, weather_condition, occasion,
                    rain_probability, preferred_styles, preferred_color,
                    preferred_weight, preferred_top, preferred_bottom,
                    vibe, specific_request,
                )
                + item_score(
                    bottom, temperature, weather_condition, occasion,
                    rain_probability, preferred_styles, preferred_color,
                    preferred_weight, preferred_top, preferred_bottom,
                    vibe, specific_request,
                )
                + pair_score
                + pair_color_score(top, bottom)
            )

            if preferred_top and _matches_requested_top(
                top, preferred_top, preferred_domain
            ):
                score += 70

            if preferred_bottom and _matches_requested_bottom(
                bottom, preferred_bottom
            ):
                score += 70

            if preferred_domain and (
                _domain_matches(top, preferred_domain)
                and _domain_matches(bottom, preferred_domain)
            ):
                score += 25

            reasons = (
                build_reasons(
                    top, temperature, weather_condition, occasion,
                    preferred_styles, preferred_color, preferred_weight,
                    preferred_top, preferred_bottom, vibe, specific_request,
                )
                + build_reasons(
                    bottom, temperature, weather_condition, occasion,
                    preferred_styles, preferred_color, preferred_weight,
                    preferred_top, preferred_bottom, vibe, specific_request,
                )
            )

            candidates.append({
                "top": top,
                "bottom": bottom,
                "outfit_type": "two_piece",
                "score": score,
                "reasons": list(dict.fromkeys(reasons))[:4],
                "candidate_key": _candidate_key(top, bottom),
            })

    if not candidates:
        requested_color_missing = (
            (
                top_color
                and not any(
                    matches_requested_color(item, top_color)
                    and (is_top(item) or is_complete_set(item))
                    for item in items
                )
            )
            or (
                bottom_color
                and not any(
                    matches_requested_color(item, bottom_color)
                    and is_bottom(item)
                    for item in items
                )
            )
        )

        if requested_color_missing or one_piece_preference:
            return _select_diverse(candidates, 9)

        fallback_items = []

        if preferred_top:
            fallback_items = [
                item for item in items
                if is_complete_set(item)
                and _domain_matches(item, preferred_domain)
                and matches_requested_color(item, top_color)
            ]

            if not fallback_items:
                fallback_items = [
                    item for item in items
                    if is_top(item)
                    and _domain_matches(item, preferred_domain)
                    and matches_requested_color(item, top_color)
                ]

        elif preferred_bottom:
            fallback_items = [
                item for item in items
                if is_bottom(item)
                and _domain_matches(item, preferred_domain)
                and matches_requested_color(item, bottom_color)
            ]

        else:
            fallback_items = [
                item for item in items
                if (is_complete_set(item) or is_top(item))
                and matches_requested_color(item, top_color)
            ]

        for item in fallback_items:
            score = item_score(
                item, temperature, weather_condition, occasion,
                rain_probability, preferred_styles, preferred_color,
                preferred_weight, preferred_top, preferred_bottom,
                vibe, specific_request,
            ) - 25

            candidates.append({
                "top": item,
                "bottom": None,
                "outfit_type": "fallback",
                "score": score,
                "reasons": [
                    "No exact complete combination matched your request; "
                    "this is the closest suitable wardrobe item."
                ],
                "candidate_key": _candidate_key(item),
            })

    return _select_diverse(candidates, 9)


# -----------------------------
# Backwards-compatible helper
# -----------------------------

def calculate_outfit_score(top, bottom=None, **kwargs):
    temperature = kwargs.get("temperature", 25)
    weather_condition = kwargs.get("weather_condition", "clear")
    occasion = kwargs.get("occasion", "everyday")
    rain_probability = kwargs.get("rain_probability", 0)
    preferred_styles = kwargs.get("preferred_styles", [])
    preferred_color = kwargs.get("preferred_color")
    preferred_weight = kwargs.get("preferred_weight")
    preferred_top = kwargs.get("preferred_top")
    preferred_bottom = kwargs.get("preferred_bottom")
    vibe = kwargs.get("vibe")
    specific_request = kwargs.get("specific_request")

    if bottom is None:
        return item_score(
            top,
            temperature,
            weather_condition,
            occasion,
            rain_probability,
            preferred_styles,
            preferred_color,
            preferred_weight,
            preferred_top,
            preferred_bottom,
            vibe,
            specific_request,
        )

    return (
        item_score(
            top,
            temperature,
            weather_condition,
            occasion,
            rain_probability,
            preferred_styles,
            preferred_color,
            preferred_weight,
            preferred_top,
            preferred_bottom,
            vibe,
            specific_request,
        )
        + item_score(
            bottom,
            temperature,
            weather_condition,
            occasion,
            rain_probability,
            preferred_styles,
            preferred_color,
            preferred_weight,
            preferred_top,
            preferred_bottom,
            vibe,
            specific_request,
        )
        + pair_compatibility(
            top,
            bottom,
            occasion,
            kwargs.get("user_gender"),
            preferred_top,
            preferred_bottom,
            specific_request or "",
        )
        + pair_color_score(top, bottom)
    )