# Smart Kitchen — Stanford Code in Place Final Project

A pantry-first cooking assistant written in **pure Python** with **Tkinter**.
You type the ingredients you have, the program matches them against a recipe
database, and tells you what you can cook tonight — or builds a shopping list
for what's missing.

## Why this project

For my Code in Place final project I wanted something I'd actually use. Every
week I open my fridge, see random ingredients, and have no idea what to make.
This app solves that with a smart matching algorithm built around the core
data structures we learned: **lists, dictionaries, functions, classes, and
file I/O**.

## How to run

```bash
cd smart_kitchen
python run.py
```

`run.py` works **everywhere**:

- On a desktop with a screen → opens the full **Tkinter GUI**.
- In a headless / online Python IDE (no display) → automatically opens an
  identical **console version** (`cli.py`).

Both share the same logic in `core.py`, so behaviour is the same on every
platform. **No `pip install` needed.** Tested on Python 3.10+.

> The web version (React, in the project root) is what you publish online;
> this Python app is the standalone, IDE-friendly version of the same project.


## What it does

- **Pantry** — Add ingredients with quantity + optional expiry date. Items
  expiring within 3 days are flagged.
- **Cook** — Ranks every recipe by what you can make. Cookable recipes first,
  then recipes that use your soon-to-expire items (reduces waste), then
  fewest missing ingredients.
- **Substitutions** — Knows that butter↔oil, milk↔yogurt, soy sauce↔tamari,
  rice↔quinoa, etc. A missing ingredient doesn't kill a recipe if you have
  a known substitute.
- **Plan** — Pick recipes for the week, get a combined shopping list you can
  save to a `.txt` file.
- **Book** — Browse the 12 seeded recipes or add your own.
- **Surprise me** — Roll the dice for a random cookable recipe.

All data persists in `data/*.json` files so your pantry survives between runs.

## The matching algorithm (the interesting part)

```
for each recipe:
    have       = ingredients found in pantry
    missing    = ingredients with no match and no substitute
    swapped    = ingredients matched via the substitutions dictionary
    expiring   = ingredients in `have` whose pantry item expires in ≤ 3 days
    match_pct  = (have + swapped) / total

rank by:
    1. fully cookable first (missing == 0)
    2. uses the most expiring items   ← reduces food waste
    3. fewest missing ingredients
    4. highest match %
```

## Project structure

```
smart_kitchen/
├── main.py                  # Tkinter UI
├── core.py                  # matching, ranking, cooking, file I/O
├── data/
│   ├── recipes.json         # 12 seeded recipes
│   ├── substitutions.json   # 24 swap groups
│   └── pantry.json          # your saved pantry (starts empty)
└── README.md
```

## Python concepts used (CIP rubric)

- Variables, control flow, functions
- Lists, dictionaries, sets
- Dataclasses (`PantryItem`, `Recipe`, `MatchResult`)
- File I/O with the `json` module
- Date arithmetic with the `datetime` module
- The `random` module
- GUI programming with `tkinter` and `ttk`
- Sorting with custom keys
- Comprehensions
