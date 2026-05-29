"""
Smart Kitchen — text/console interface.

This runs in ANY Python environment (online IDEs, terminals, notebooks)
because it needs no graphical display. It shares the exact same logic as
the Tkinter GUI via core.py, so behaviour is identical on every platform.

Run with:  python cli.py
"""

import core


def _line(char="-", n=52):
    print(char * n)


def show_menu():
    print()
    _line("=")
    print("  SMART KITCHEN  —  cook with what you already have")
    _line("=")
    print("  1. View pantry")
    print("  2. Add ingredients to pantry")
    print("  3. What can I cook?")
    print("  4. Shopping list (for almost-there recipes)")
    print("  5. Surprise me")
    print("  6. Browse recipe book")
    print("  7. Cook a recipe (uses up pantry items)")
    print("  0. Quit")
    _line()


def view_pantry(pantry):
    if not pantry:
        print("\nYour pantry is empty. Choose option 2 to add ingredients.")
        return
    print("\nPantry:")
    for name, item in sorted(pantry.items()):
        d = core.days_until(item.expires)
        flag = ""
        if d is not None:
            if d < 0:
                flag = "  (EXPIRED)"
            elif d <= 3:
                flag = f"  (expires in {d}d)"
        print(f"  • {name} × {item.qty}{flag}")


def add_ingredients(pantry):
    print("\nType ingredients like:  eggs 4, milk 200, butter")
    text = input("Add > ").strip()
    if not text:
        return pantry
    parsed = core.parse_ingredient_list(text)
    for name, qty in parsed.items():
        pantry = core.add_to_pantry(pantry, name, qty)
    core.save_pantry(pantry)
    print(f"Added {len(parsed)} item(s).")
    return pantry


def what_can_i_cook(recipes, pantry, subs):
    results = core.rank_recipes(recipes, pantry, subs)
    cookable = [m for m in results if m.can_cook]
    almost = [m for m in results if not m.can_cook][:5]

    print("\n— Cookable now —")
    if not cookable:
        print("  (nothing yet — add a few staples)")
    for m in cookable:
        extra = f"  ↻ {', '.join(m.substituted)}" if m.substituted else ""
        warn = f"  ⏳ uses expiring: {', '.join(m.expiring_used)}" if m.expiring_used else ""
        print(f"  ✓ {m.recipe.name} ({m.recipe.time_minutes} min){extra}{warn}")

    print("\n— Almost there —")
    for m in almost:
        print(f"  ◦ {m.recipe.name} — missing: {', '.join(m.missing)} ({m.match_pct:.0f}% match)")


def shopping_list(recipes, pantry, subs):
    almost = [m for m in core.rank_recipes(recipes, pantry, subs) if not m.can_cook][:5]
    items = core.shopping_list(almost)
    if not items:
        print("\nNothing to buy — you can cook everything!")
        return
    print("\nShopping list:")
    for name, qty in items.items():
        print(f"  ☐ {name} × {qty}")
    if input("\nSave to shopping_list.txt? (y/n) ").strip().lower() == "y":
        with open("shopping_list.txt", "w", encoding="utf-8") as f:
            for name, qty in items.items():
                f.write(f"[ ] {name} x {qty}\n")
        print("Saved shopping_list.txt")


def surprise(recipes, pantry, subs):
    m = core.surprise_me(recipes, pantry, subs)
    if not m:
        print("\nNothing fully cookable right now. Add a few staples and try again.")
        return
    r = m.recipe
    print(f"\nTonight: {r.name}  ({r.time_minutes} min · {', '.join(r.tags)})")
    print("Ingredients:")
    for i, q in r.ingredients.items():
        print(f"  • {i} × {q}")
    print("Steps:")
    for i, s in enumerate(r.steps, 1):
        print(f"  {i}. {s}")


def browse(recipes):
    print("\nRecipe book:")
    for i, r in enumerate(recipes, 1):
        print(f"  {i:>2}. {r.name}  ({r.time_minutes} min · {', '.join(r.tags)})")
    choice = input("\nView a recipe number (or Enter to skip) > ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(recipes):
        r = recipes[int(choice) - 1]
        print(f"\n{r.name}")
        _line()
        for i, q in r.ingredients.items():
            print(f"  • {i} × {q}")
        print()
        for i, s in enumerate(r.steps, 1):
            print(f"  {i}. {s}")


def cook(recipes, pantry, subs):
    cookable = [m.recipe for m in core.rank_recipes(recipes, pantry, subs) if m.can_cook]
    if not cookable:
        print("\nNothing cookable right now.")
        return pantry
    print("\nCookable recipes:")
    for i, r in enumerate(cookable, 1):
        print(f"  {i}. {r.name}")
    choice = input("Cook which number? > ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(cookable):
        ok, msg, pantry = core.cook(cookable[int(choice) - 1], pantry, subs)
        core.save_pantry(pantry)
        print(msg)
    return pantry


def main():
    pantry = core.load_pantry()
    recipes = core.load_recipes()
    subs = core.load_subs()

    while True:
        show_menu()
        choice = input("Choose > ").strip()
        if choice == "0":
            print("Happy cooking! 👋")
            break
        elif choice == "1":
            view_pantry(pantry)
        elif choice == "2":
            pantry = add_ingredients(pantry)
        elif choice == "3":
            what_can_i_cook(recipes, pantry, subs)
        elif choice == "4":
            shopping_list(recipes, pantry, subs)
        elif choice == "5":
            surprise(recipes, pantry, subs)
        elif choice == "6":
            browse(recipes)
        elif choice == "7":
            pantry = cook(recipes, pantry, subs)
        else:
            print("Please choose a number from the menu.")


if __name__ == "__main__":
    main()
