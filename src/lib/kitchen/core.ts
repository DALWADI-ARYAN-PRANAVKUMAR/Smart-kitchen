import type { MatchResult, Pantry, Recipe, Subs } from "./types";
import { NUTRITION } from "./data";

export const norm = (s: string) => s.trim().toLowerCase();

export function daysUntil(expires?: string | null): number | null {
  if (!expires) return null;
  const d = new Date(expires + "T00:00:00");
  if (isNaN(d.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((d.getTime() - today.getTime()) / 86_400_000);
}

function equivalents(ing: string, subs: Subs): Set<string> {
  const n = norm(ing);
  const out = new Set<string>([n]);
  (subs[n] ?? []).forEach((s) => out.add(norm(s)));
  return out;
}

export function matchRecipe(recipe: Recipe, pantry: Pantry, subs: Subs, warnDays = 3): MatchResult {
  const have: string[] = [];
  const missing: string[] = [];
  const substituted: Record<string, string> = {};
  const expiringUsed: string[] = [];

  const pantryNorm = new Map<string, string>(); // normalized -> original key
  Object.entries(pantry).forEach(([k, v]) => {
    if (v.qty > 0) pantryNorm.set(norm(k), k);
  });

  for (const ing of Object.keys(recipe.ingredients)) {
    const n = norm(ing);
    if (pantryNorm.has(n)) {
      have.push(ing);
      const d = daysUntil(pantry[pantryNorm.get(n)!]?.expires);
      if (d !== null && d <= warnDays) expiringUsed.push(ing);
    } else {
      const alt = [...equivalents(ing, subs)].find((a) => a !== n && pantryNorm.has(a));
      if (alt) substituted[ing] = pantryNorm.get(alt)!;
      else missing.push(ing);
    }
  }
  const total = Object.keys(recipe.ingredients).length || 1;
  const matchPct = (100 * (have.length + Object.keys(substituted).length)) / total;
  return { recipe, have, missing, substituted, expiringUsed, matchPct, canCook: missing.length === 0 };
}

export function rankRecipes(
  recipes: Recipe[],
  pantry: Pantry,
  subs: Subs,
  opts: { dietary?: string[]; maxTime?: number; prioritizeExpiring?: boolean } = {},
): MatchResult[] {
  const diet = new Set((opts.dietary ?? []).map((d) => d.toLowerCase()));
  const filtered = recipes.filter((r) => {
    if (diet.size) {
      const tags = new Set(r.tags.map((t) => t.toLowerCase()));
      for (const d of diet) if (!tags.has(d)) return false;
    }
    if (opts.maxTime != null && r.time_minutes > opts.maxTime) return false;
    return true;
  });
  const results = filtered.map((r) => matchRecipe(r, pantry, subs));
  results.sort((a, b) => {
    const ac = Number(b.canCook) - Number(a.canCook);
    if (ac) return ac;
    if (opts.prioritizeExpiring) {
      const ex = b.expiringUsed.length - a.expiringUsed.length;
      if (ex) return ex;
    }
    const m = a.missing.length - b.missing.length;
    if (m) return m;
    return b.matchPct - a.matchPct;
  });
  return results;
}

export function shoppingList(matches: MatchResult[]): Record<string, number> {
  const out: Record<string, number> = {};
  for (const m of matches) {
    for (const ing of m.missing) {
      out[ing] = (out[ing] ?? 0) + (m.recipe.ingredients[ing] ?? 1);
    }
  }
  return Object.fromEntries(Object.entries(out).sort(([a], [b]) => a.localeCompare(b)));
}

export function cookRecipe(recipe: Recipe, pantry: Pantry, subs: Subs): { ok: boolean; msg: string; pantry: Pantry } {
  const m = matchRecipe(recipe, pantry, subs);
  if (!m.canCook) return { ok: false, msg: `Missing: ${m.missing.join(", ")}`, pantry };
  const next: Pantry = JSON.parse(JSON.stringify(pantry));
  const lookup = new Map<string, string>();
  Object.keys(next).forEach((k) => lookup.set(norm(k), k));
  for (const [ing, qty] of Object.entries(recipe.ingredients)) {
    const key = lookup.get(norm(ing)) ?? m.substituted[ing] ?? null;
    if (!key || !next[key]) continue;
    next[key].qty = Math.max(0, next[key].qty - qty);
    if (next[key].qty <= 0) delete next[key];
  }
  return { ok: true, msg: `Cooked ${recipe.name}. Pantry updated.`, pantry: next };
}

export function surpriseMe(recipes: Recipe[], pantry: Pantry, subs: Subs): MatchResult | null {
  const cookable = rankRecipes(recipes, pantry, subs).filter((m) => m.canCook);
  if (!cookable.length) return null;
  return cookable[Math.floor(Math.random() * cookable.length)];
}

export function estimateNutrition(recipe: Recipe): { kcal: number; protein: number; carbs: number; fat: number; covered: number; total: number } {
  let kcal = 0, protein = 0, carbs = 0, fat = 0, covered = 0;
  const entries = Object.entries(recipe.ingredients);
  for (const [ing, qty] of entries) {
    const n = NUTRITION[norm(ing)];
    if (!n) continue;
    covered++;
    // qty is "units" (eggs, tbsp, 100g chunks). The table is per-unit; for ingredients
    // measured in grams (pasta, flour, chickpeas, lentils, coconut milk, chicken)
    // qty is grams so we scale per 100g.
    const per100g = ["pasta", "flour", "chicken", "chickpeas", "lentils", "coconut milk", "black beans"];
    const factor = per100g.includes(norm(ing)) ? qty / 100 : qty;
    kcal += n.kcal * factor;
    protein += n.protein * factor;
    carbs += n.carbs * factor;
    fat += n.fat * factor;
  }
  return {
    kcal: Math.round(kcal),
    protein: Math.round(protein),
    carbs: Math.round(carbs),
    fat: Math.round(fat),
    covered,
    total: entries.length,
  };
}
