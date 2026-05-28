# Smart Kitchen

> Cook with what you already have. A pantry-first recipe & grocery assistant that turns the random ingredients in your kitchen into meals you can actually make tonight — and a smart shopping list for everything you're missing.

![Stack](https://img.shields.io/badge/stack-React%20%2B%20TypeScript-3178c6)
![Styling](https://img.shields.io/badge/style-Tailwind%20CSS-38bdf8)
![Runtime](https://img.shields.io/badge/runtime-TanStack%20Start-ef4444)

---

## ✨ Features

- **Smart Pantry** — Track ingredients with quantities and expiry dates. Color-coded warnings for items about to spoil.
- **Recipe Matching** — Algorithm ranks recipes by what you can cook *now*, prioritizing ingredients that expire soon.
- **Substitution Engine** — Knows that butter↔oil, milk↔yogurt, soy↔tamari, and 20+ other swaps so a missing item doesn't kill a recipe.
- **Meal Planner** — Pick recipes for the week, get one consolidated downloadable shopping list.
- **Recipe Book** — Browse, add, or delete recipes. Includes 12 seeded recipes covering breakfast, lunch, dinner, and dessert.
- **Surprise Me** — Roll the dice for a random recipe you can cook right now.
- **AI Photo Scan** — Snap a photo of your fridge/pantry; an LLM extracts ingredients automatically.
- **AI Recipe Suggestions** — Generate brand-new recipes from your current pantry.
- **Nutrition Estimates** — Rough kcal / protein / carbs / fat per recipe from a heuristic table.
- **Dark / Light Mode** — Toggle with persistence; respects system preference on first load.
- **Glass UI** — Modern frosted-glass surfaces with a warm terracotta & sage palette.
- **Zero backend required for core features** — Everything (pantry, recipes, plans) saved to `localStorage`. AI features use edge functions.

---

## 🧠 The Matching Algorithm

```
for each recipe:
    have      = ingredients present in pantry
    missing   = ingredients not in pantry and no substitution found
    swapped   = ingredients matched via substitution table
    expiring  = ingredients in `have` whose pantry item expires in ≤ 3 days
    match_pct = (have + swapped) / total_ingredients

rank by:
    1. cookable first (missing == 0)
    2. uses the most expiring items   ← reduces food waste
    3. fewest missing ingredients
    4. highest match %
```

Data lives in plain TypeScript objects — easy to read, easy to extend.

---

## 🚀 Run Locally

```bash
bun install      # or: npm install
bun dev          # or: npm run dev
```

App runs at `http://localhost:5173`.

### Build for production

```bash
bun run build
bun run start
```

---

## 🗂️ Project Structure

```
src/
├── components/
│   ├── SmartKitchen.tsx       # main UI shell (tabs, header, dark mode)
│   └── ui/                    # shadcn primitives (Button, Card, Tabs, …)
├── hooks/
│   └── use-theme.tsx          # dark/light toggle with localStorage
├── lib/kitchen/
│   ├── core.ts                # matching, ranking, cooking, nutrition
│   ├── data.ts                # seeded recipes, substitutions, nutrition table
│   ├── storage.ts             # localStorage I/O
│   └── types.ts               # Recipe, Pantry, MatchResult
├── routes/
│   ├── __root.tsx             # root layout + meta tags
│   └── index.tsx              # home page (mounts SmartKitchen)
└── styles.css                 # design tokens (terracotta + sage), .glass utilities
supabase/functions/
├── ai-suggest-recipe/         # LLM endpoint for generating recipes
└── photo-pantry-scan/         # LLM vision endpoint for ingredient extraction
```

---

## 🎨 Design

- **Palette**: Terracotta & Sage — warm, earthy, kitchen-appropriate.
- **Typography**: Instrument Serif (headings) + Work Sans (body) — editorial modern.
- **Surfaces**: Frosted glass cards with subtle radial gradients for depth.
- **Motion**: Hover-only micro-interactions; no animation gimmicks.

---

## 📜 License

MIT — do whatever you want, no warranty.

---

## 🙏 Credits

Built as a learning project. Inspired by every "what's in my fridge?" moment.
