export type Recipe = {
  name: string;
  time_minutes: number;
  tags: string[];
  ingredients: Record<string, number>;
  steps: string[];
  cuisine?: string;
};

export type PantryItem = { qty: number; expires?: string | null };
export type Pantry = Record<string, PantryItem>;
export type Subs = Record<string, string[]>;

export type MatchResult = {
  recipe: Recipe;
  have: string[];
  missing: string[];
  substituted: Record<string, string>;
  expiringUsed: string[];
  matchPct: number;
  canCook: boolean;
};
