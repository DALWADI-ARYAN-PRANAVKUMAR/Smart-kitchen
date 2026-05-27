import { DEFAULT_RECIPES, DEFAULT_SUBS } from "./data";
import type { Pantry, Recipe, Subs } from "./types";

const PANTRY_KEY = "sk.pantry.v1";
const RECIPES_KEY = "sk.recipes.v1";
const SUBS_KEY = "sk.subs.v1";

function safeGet<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function safeSet(key: string, value: unknown) {
  if (typeof window === "undefined") return;
  try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* ignore */ }
}

export const loadPantry = (): Pantry => safeGet<Pantry>(PANTRY_KEY, {});
export const savePantry = (p: Pantry) => safeSet(PANTRY_KEY, p);

export const loadRecipes = (): Recipe[] => safeGet<Recipe[]>(RECIPES_KEY, DEFAULT_RECIPES);
export const saveRecipes = (r: Recipe[]) => safeSet(RECIPES_KEY, r);

export const loadSubs = (): Subs => safeGet<Subs>(SUBS_KEY, DEFAULT_SUBS);
export const saveSubs = (s: Subs) => safeSet(SUBS_KEY, s);

export function resetAll() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(PANTRY_KEY);
  localStorage.removeItem(RECIPES_KEY);
  localStorage.removeItem(SUBS_KEY);
}
