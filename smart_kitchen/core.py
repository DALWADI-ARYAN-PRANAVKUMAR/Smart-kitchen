"""Core logic for Smart Kitchen: pantry, recipes, matching, planner."""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

DATA_DIR = Path(__file__).parent / "data"
RECIPES_FILE = DATA_DIR / "recipes.json"
PANTRY_FILE = DATA_DIR / "pantry.json"
SUBS_FILE = DATA_DIR / "substitutions.json"


# ---------- IO ----------

def _load_json(path: Path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_recipes() -> list[dict]:
    return _load_json(RECIPES_FILE, [])


def save_recipes(recipes: list[dict]) -> None:
    _save_json(RECIPES_FILE, recipes)


def load_pantry() -> dict:
    """Pantry shape: {ingredient: {"qty": float, "expires": "YYYY-MM-DD" | None}}."""
    raw = _load_json(PANTRY_FILE, {})
    # Backward-compat: allow plain numbers
    fixed = {}
    for k, v in raw.items():
        if isinstance(v, (int, float)):
            fixed[k] = {"qty": float(v), "expires": None}
        else:
            fixed[k] = {"qty": float(v.get("qty", 0)), "expires": v.get("expires")}
    return fixed


def save_pantry(pantry: dict) -> None:
    _save_json(PANTRY_FILE, pantry)


def load_substitutions() -> dict[str, list[str]]:
    return _load_json(SUBS_FILE, {})


# ---------- Helpers ----------

def normalize(name: str) -> str:
    return name.strip().lower()


def equivalents(ingredient: str, subs: dict[str, list[str]]) -> set[str]:
    """Return ingredient + its known substitutes (lowercased)."""
    n = normalize(ingredient)
    out = {n}
    out.update(normalize(s) for s in subs.get(n, []))
    return out


def days_until_expiry(expires: str | None) -> int | None:
    if not expires:
        return None
    try:
        d = datetime.strptime(expires, "%Y-%m-%d").date()
    except ValueError:
        return None
    return (d - date.today()).days


# ---------- Matching ----------

@dataclass
class MatchResult:
    recipe: dict
    have: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    substituted: dict[str, str] = field(default_factory=dict)  # needed -> used-from-pantry
    expiring_used: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.recipe.get("ingredients", {}))

    @property
    def match_pct(self) -> float:
        if self.total == 0:
            return 0.0
        return 100 * (len(self.have) + len(self.substituted)) / self.total

    @property
    def can_cook(self) -> bool:
        return not self.missing


def match_recipe(
    recipe: dict,
    pantry: dict,
    subs: dict[str, list[str]],
    expiry_warn_days: int = 3,
) -> MatchResult:
    have, missing, substituted, expiring_used = [], [], {}, []
    pantry_keys = {normalize(k) for k, v in pantry.items() if v["qty"] > 0}

    for ingredient in recipe.get("ingredients", {}):
        n = normalize(ingredient)
        if n in pantry_keys:
            have.append(ingredient)
            d = days_until_expiry(pantry.get(ingredient, {}).get("expires"))
            if d is not None and d <= expiry_warn_days:
                expiring_used.append(ingredient)
        else:
            # try substitutes
            alt_pool = equivalents(ingredient, subs) - {n}
            sub_found = next((a for a in alt_pool if a in pantry_keys), None)
            if sub_found:
                substituted[ingredient] = sub_found
            else:
                missing.append(ingredient)
    return MatchResult(recipe, have, missing, substituted, expiring_used)


def rank_recipes(
    recipes: list[dict],
    pantry: dict,
    subs: dict[str, list[str]],
    dietary: Iterable[str] = (),
    max_time: int | None = None,
    prioritize_expiring: bool = True,
) -> list[MatchResult]:
    dietary = {d.lower() for d in dietary}
    results = []
    for r in recipes:
        if dietary and not dietary.issubset({t.lower() for t in r.get("tags", [])}):
            continue
        if max_time is not None and r.get("time_minutes", 0) > max_time:
            continue
        results.append(match_recipe(r, pantry, subs))

    def sort_key(m: MatchResult):
        expiry_bonus = len(m.expiring_used) if prioritize_expiring else 0
        return (-int(m.can_cook), -expiry_bonus, len(m.missing), -m.match_pct)

    results.sort(key=sort_key)
    return results


# ---------- Shopping list & cooking ----------

def shopping_list(matches: Iterable[MatchResult]) -> dict[str, float]:
    """Sum quantities of all *missing* ingredients across selected recipes."""
    total: dict[str, float] = {}
    for m in matches:
        for ing in m.missing:
            qty = m.recipe["ingredients"][ing]
            total[ing] = total.get(ing, 0) + float(qty)
    return dict(sorted(total.items()))


def cook(recipe: dict, pantry: dict, subs: dict[str, list[str]]) -> tuple[bool, str]:
    """Deduct ingredients from pantry. Uses substitutes if needed."""
    m = match_recipe(recipe, pantry, subs)
    if not m.can_cook:
        return False, f"Missing: {', '.join(m.missing)}"

    for ing, qty in recipe["ingredients"].items():
        key = ing if ing in pantry else m.substituted.get(ing)
        if key is None:
            # find canonical pantry key (case-insensitive)
            for pk in pantry:
                if normalize(pk) == normalize(ing):
                    key = pk
                    break
        if key and key in pantry:
            pantry[key]["qty"] = max(0.0, pantry[key]["qty"] - float(qty))
            if pantry[key]["qty"] == 0:
                del pantry[key]
    save_pantry(pantry)
    return True, f"Cooked {recipe['name']}. Pantry updated."


def surprise_me(recipes: list[dict], pantry: dict, subs: dict[str, list[str]]) -> MatchResult | None:
    cookable = [m for m in rank_recipes(recipes, pantry, subs) if m.can_cook]
    return random.choice(cookable) if cookable else None


# ---------- Pantry mutations ----------

def add_to_pantry(pantry: dict, name: str, qty: float = 1, expires: str | None = None) -> None:
    key = name.strip()
    if not key:
        return
    if key in pantry:
        pantry[key]["qty"] += qty
        if expires:
            pantry[key]["expires"] = expires
    else:
        pantry[key] = {"qty": float(qty), "expires": expires}
    save_pantry(pantry)


def remove_from_pantry(pantry: dict, name: str) -> None:
    pantry.pop(name, None)
    save_pantry(pantry)


def parse_ingredient_list(text: str) -> list[str]:
    """Split a comma/newline list into clean ingredient names."""
    parts = [p.strip() for chunk in text.splitlines() for p in chunk.split(",")]
    return [p for p in parts if p]
