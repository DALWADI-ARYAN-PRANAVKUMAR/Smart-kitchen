# 🥘 Smart Kitchen

A Python + Streamlit app that turns your random pantry into actual meals.

## Features

- **Pantry tracker** with quantities and expiry dates (color-coded warnings)
- **Smart recipe matching** — what you can cook now, and what's almost there
- **Substitutions** — butter ↔ oil, milk ↔ yogurt, etc.
- **Expiry-aware ranking** — prioritizes recipes that use ingredients about to go bad
- **Dietary & time filters** — vegetarian, vegan, gluten-free, quick, etc.
- **Meal planner** — pick recipes for the week → one consolidated shopping list (downloadable)
- **Cook button** — auto-deducts ingredients from pantry
- **Surprise me** — random pick from what's fully cookable
- **Recipe book** — 12 starter recipes + add your own
- **JSON persistence** — your pantry and recipes survive restarts

## Run

```bash
cd smart_kitchen
pip install -r requirements.txt
streamlit run app.py
```

Opens at http://localhost:8501

## Project structure

```
smart_kitchen/
├── app.py              # Streamlit UI
├── core.py             # Pure logic: matching, ranking, planner
├── requirements.txt
└── data/
    ├── recipes.json        # Recipe library (editable)
    ├── pantry.json         # Your pantry (auto-managed)
    └── substitutions.json  # Ingredient swaps
```

## How matching works

Each recipe is scored against your pantry:
1. Direct match — you have the ingredient
2. Substitute match — you have something equivalent (from `substitutions.json`)
3. Missing — goes to the shopping list

Recipes are sorted by: cookable first → uses expiring items → fewest missing → highest % match.
