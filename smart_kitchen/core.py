"""
Smart Kitchen — core logic.

Pure Python: lists, dicts, functions, file I/O, dataclasses.
No external dependencies. All UI lives in main.py.
"""

import json
import os
import random
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PANTRY_FILE = os.path.join(DATA_DIR, "pantry.json")
RECIPES_FILE = os.path.join(DATA_DIR, "recipes.json")
SUBS_FILE = os.path.join(DATA_DIR, "substitutions.json")


# ---------- Data types ----------

@dataclass
class PantryItem:
    qty: float
    expires: Optional[str] = None  # ISO date string "YYYY-MM-DD"


@dataclass
class Recipe:
    name: str
    ingredients: dict           # {ingredient_name: quantity}
    steps: list
    tags: list = field(default_factory=list)
    time_minutes: int = 20


@dataclass
class MatchResult:
    recipe: Recipe
    have: list
    missing: list
    substituted: dict           # {original: pantry_item_used}
    expiring_used: list
    match_pct: float
    can_cook: bool


# ---------- File I/O ----------

def _read_json(path, fallback):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return fallback


def _write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_pantry():
    raw = _read_json(PANTRY_FILE, {})
    return {k: PantryItem(**v) for k, v in raw.items()}


def save_pantry(pantry):
    raw = {k: {"qty": v.qty, "expires": v.expires} for k, v in pantry.items()}
    _write_json(PANTRY_FILE, raw)


def load_recipes():
    raw = _read_json(RECIPES_FILE, [])
    return [Recipe(**r) for r in raw]


def save_recipes(recipes):
    raw = [{"name": r.name, "ingredients": r.ingredients,
            "steps": r.steps, "tags": r.tags,
            "time_minutes": r.time_minutes} for r in recipes]
    _write_json(RECIPES_FILE, raw)


def load_subs():
    return _read_json(SUBS_FILE, {})


# ---------- Helpers ----------

def norm(s):
    return s.strip().lower()


def days_until(expires):
    if not expires:
        return None
    try:
        d = datetime.strptime(expires, "%Y-%m-%d").date()
    except ValueError:
        return None
    return (d - date.today()).days


def equivalents(ingredient, subs):
    n = norm(ingredient)
    out = {n}
    for s in subs.get(n, []):
        out.add(norm(s))
    return out


# ---------- Matching ----------

def match_recipe(recipe, pantry, subs, warn_days=3):
    have, missing, substituted, expiring_used = [], [], {}, []
    pantry_norm = {norm(k): k for k, v in pantry.items() if v.qty > 0}

    for ing in recipe.ingredients:
        n = norm(ing)
        if n in pantry_norm:
            have.append(ing)
            key = pantry_norm[n]
            d = days_until(pantry[key].expires)
            if d is not None and d <= warn_days:
                expiring_used.append(ing)
        else:
            alt = None
            for cand in equivalents(ing, subs):
                if cand != n and cand in pantry_norm:
                    alt = pantry_norm[cand]
                    break
            if alt:
                substituted[ing] = alt
            else:
                missing.append(ing)

    total = len(recipe.ingredients) or 1
    match_pct = 100 * (len(have) + len(substituted)) / total
    return MatchResult(
        recipe=recipe,
        have=have,
        missing=missing,
        substituted=substituted,
        expiring_used=expiring_used,
        match_pct=match_pct,
        can_cook=len(missing) == 0,
    )


def rank_recipes(recipes, pantry, subs, dietary=None, max_time=None):
    dietary = set((dietary or []))
    filtered = []
    for r in recipes:
        if dietary:
            tags = {t.lower() for t in r.tags}
            if not dietary.issubset(tags):
                continue
        if max_time is not None and r.time_minutes > max_time:
            continue
        filtered.append(r)

    results = [match_recipe(r, pantry, subs) for r in filtered]
    results.sort(key=lambda m: (
        not m.can_cook,
        -len(m.expiring_used),
        len(m.missing),
        -m.match_pct,
    ))
    return results


def shopping_list(matches):
    out = {}
    for m in matches:
        for ing in m.missing:
            out[ing] = out.get(ing, 0) + m.recipe.ingredients.get(ing, 1)
    return dict(sorted(out.items()))


def cook(recipe, pantry, subs):
    m = match_recipe(recipe, pantry, subs)
    if not m.can_cook:
        return False, f"Missing: {', '.join(m.missing)}", pantry
    lookup = {norm(k): k for k in pantry}
    for ing, qty in recipe.ingredients.items():
        key = lookup.get(norm(ing)) or m.substituted.get(ing)
        if not key or key not in pantry:
            continue
        pantry[key].qty = max(0, pantry[key].qty - qty)
        if pantry[key].qty <= 0:
            del pantry[key]
    return True, f"Cooked {recipe.name}. Pantry updated.", pantry


def surprise_me(recipes, pantry, subs):
    cookable = [m for m in rank_recipes(recipes, pantry, subs) if m.can_cook]
    return random.choice(cookable) if cookable else None


def add_to_pantry(pantry, name, qty, expires=None):
    key = name.strip()
    if not key:
        return pantry
    if key in pantry:
        pantry[key].qty += qty
        if expires:
            pantry[key].expires = expires
    else:
        pantry[key] = PantryItem(qty=qty, expires=expires)
    return pantry


def parse_ingredient_list(text):
    """Parse 'eggs 4, milk 200, butter' -> {'eggs': 4, 'milk': 200, 'butter': 1}"""
    out = {}
    for chunk in text.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.rsplit(" ", 1)
        if len(parts) == 2 and parts[1].replace(".", "", 1).isdigit():
            out[parts[0].strip()] = float(parts[1])
        else:
            out[chunk] = 1
    return out
