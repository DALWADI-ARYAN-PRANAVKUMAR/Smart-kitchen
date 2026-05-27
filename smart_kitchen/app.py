"""Smart Kitchen — Streamlit UI.

Run with:
    streamlit run app.py
"""
from __future__ import annotations

from datetime import date

import streamlit as st

from core import (
    add_to_pantry,
    cook,
    days_until_expiry,
    load_pantry,
    load_recipes,
    load_substitutions,
    parse_ingredient_list,
    rank_recipes,
    remove_from_pantry,
    save_pantry,
    save_recipes,
    shopping_list,
    surprise_me,
)

st.set_page_config(page_title="Smart Kitchen", page_icon="🥘", layout="wide")

# Cache loaded data in session
if "pantry" not in st.session_state:
    st.session_state.pantry = load_pantry()
if "recipes" not in st.session_state:
    st.session_state.recipes = load_recipes()
if "subs" not in st.session_state:
    st.session_state.subs = load_substitutions()

pantry = st.session_state.pantry
recipes = st.session_state.recipes
subs = st.session_state.subs

st.title("🥘 Smart Kitchen")
st.caption("Track your pantry, find what you can cook, and never waste food again.")

tabs = st.tabs(["🥫 Pantry", "🍳 Find Recipes", "📅 Meal Planner", "📖 Recipe Book", "🎲 Surprise Me"])

# --------------- PANTRY ---------------
with tabs[0]:
    left, right = st.columns([1, 1])

    with left:
        st.subheader("Add ingredients")
        with st.form("add_one", clear_on_submit=True):
            name = st.text_input("Ingredient", placeholder="eggs")
            c1, c2 = st.columns(2)
            qty = c1.number_input("Quantity", min_value=0.0, value=1.0, step=1.0)
            exp = c2.date_input("Expires (optional)", value=None, format="YYYY-MM-DD")
            if st.form_submit_button("Add", use_container_width=True) and name:
                add_to_pantry(pantry, name, qty, exp.isoformat() if exp else None)
                st.success(f"Added {name}")
                st.rerun()

        st.divider()
        st.subheader("Bulk add")
        bulk = st.text_area("Comma or newline separated", placeholder="rice, onion, garlic, tomato")
        if st.button("Add all (qty 1, no expiry)") and bulk.strip():
            for n in parse_ingredient_list(bulk):
                add_to_pantry(pantry, n, 1, None)
            st.success("Added.")
            st.rerun()

    with right:
        st.subheader(f"Your pantry ({len(pantry)} items)")
        if not pantry:
            st.info("Pantry is empty. Add something on the left.")
        else:
            today = date.today()
            for name, info in sorted(pantry.items()):
                d = days_until_expiry(info.get("expires"))
                badge = ""
                if d is not None:
                    if d < 0:
                        badge = f" 🔴 expired {-d}d ago"
                    elif d <= 3:
                        badge = f" 🟡 expires in {d}d"
                    else:
                        badge = f" 🟢 {d}d left"
                col1, col2, col3 = st.columns([4, 2, 1])
                col1.write(f"**{name}**{badge}")
                col2.write(f"qty: {info['qty']:g}")
                if col3.button("✕", key=f"rm_{name}"):
                    remove_from_pantry(pantry, name)
                    st.rerun()

# --------------- FIND RECIPES ---------------
with tabs[1]:
    st.subheader("What can I cook?")
    c1, c2, c3 = st.columns([2, 2, 1])
    diet_options = sorted({t for r in recipes for t in r.get("tags", [])})
    dietary = c1.multiselect("Dietary / tags filter", diet_options)
    max_time = c2.slider("Max time (minutes)", 5, 90, 60, 5)
    prio = c3.toggle("Prioritize expiring", value=True)

    matches = rank_recipes(recipes, pantry, subs, dietary, max_time, prio)

    cookable = [m for m in matches if m.can_cook]
    almost = [m for m in matches if not m.can_cook]

    st.markdown(f"### ✅ You can cook now ({len(cookable)})")
    if not cookable:
        st.info("Nothing fully cookable yet — see 'almost there' below.")
    for m in cookable:
        with st.expander(f"**{m.recipe['name']}** — {m.recipe['time_minutes']} min · {int(m.match_pct)}% match"):
            st.write("**Tags:** " + ", ".join(m.recipe.get("tags", [])))
            st.write("**Ingredients:**")
            for ing, qty in m.recipe["ingredients"].items():
                tag = ""
                if ing in m.substituted:
                    tag = f" _(using {m.substituted[ing]} as substitute)_"
                if ing in m.expiring_used:
                    tag += " ⏰"
                st.write(f"- {ing} × {qty}{tag}")
            st.write("**Steps:**")
            for i, s in enumerate(m.recipe.get("steps", []), 1):
                st.write(f"{i}. {s}")
            if st.button(f"🍳 Cook {m.recipe['name']}", key=f"cook_{m.recipe['name']}"):
                ok, msg = cook(m.recipe, pantry, subs)
                (st.success if ok else st.error)(msg)
                st.rerun()

    st.markdown(f"### 🛒 Almost there ({len(almost)})")
    for m in almost[:10]:
        with st.expander(f"{m.recipe['name']} — missing {len(m.missing)} item(s), {int(m.match_pct)}% match"):
            st.write("**Missing:** " + ", ".join(m.missing))
            st.write("**Have:** " + (", ".join(m.have) or "—"))
            if m.substituted:
                st.write("**Substitutes possible:** " + ", ".join(f"{k}→{v}" for k, v in m.substituted.items()))

# --------------- MEAL PLANNER ---------------
with tabs[2]:
    st.subheader("Plan your week")
    names = [r["name"] for r in recipes]
    picks = st.multiselect("Choose recipes for the week", names)
    selected = [r for r in recipes if r["name"] in picks]
    if selected:
        from core import match_recipe
        match_objs = [match_recipe(r, pantry, subs) for r in selected]
        sl = shopping_list(match_objs)
        st.markdown("### 🛒 Consolidated shopping list")
        if not sl:
            st.success("You already have everything!")
        else:
            for ing, qty in sl.items():
                st.write(f"- {ing} × {qty:g}")
            export = "\n".join(f"- {i} × {q:g}" for i, q in sl.items())
            st.download_button("Download list (.txt)", export, file_name="shopping_list.txt")
    else:
        st.info("Pick a few recipes above to generate one shopping list.")

# --------------- RECIPE BOOK ---------------
with tabs[3]:
    st.subheader(f"All recipes ({len(recipes)})")
    for r in recipes:
        with st.expander(f"{r['name']} — {r['time_minutes']} min"):
            st.write("**Tags:** " + ", ".join(r.get("tags", [])))
            st.json({"ingredients": r["ingredients"]}, expanded=False)
            if st.button(f"Delete {r['name']}", key=f"del_{r['name']}"):
                st.session_state.recipes = [x for x in recipes if x["name"] != r["name"]]
                save_recipes(st.session_state.recipes)
                st.rerun()

    st.divider()
    st.subheader("Add your own recipe")
    with st.form("new_recipe", clear_on_submit=True):
        nm = st.text_input("Recipe name")
        tm = st.number_input("Time (minutes)", min_value=1, value=20)
        tg = st.text_input("Tags (comma separated)", placeholder="vegetarian, quick")
        ing_text = st.text_area(
            "Ingredients (one per line, format: name : quantity)",
            placeholder="eggs : 2\nrice : 1\nsoy sauce : 1",
        )
        steps_text = st.text_area("Steps (one per line)")
        if st.form_submit_button("Save recipe") and nm and ing_text:
            ingredients = {}
            for line in ing_text.splitlines():
                if ":" in line:
                    n, q = line.split(":", 1)
                    try:
                        ingredients[n.strip()] = float(q.strip())
                    except ValueError:
                        pass
            new = {
                "name": nm.strip(),
                "time_minutes": int(tm),
                "tags": [t.strip() for t in tg.split(",") if t.strip()],
                "ingredients": ingredients,
                "steps": [s.strip() for s in steps_text.splitlines() if s.strip()],
            }
            st.session_state.recipes.append(new)
            save_recipes(st.session_state.recipes)
            st.success(f"Added {nm}")
            st.rerun()

# --------------- SURPRISE ---------------
with tabs[4]:
    st.subheader("Feeling lucky?")
    if st.button("🎲 Surprise me with what I can cook"):
        pick = surprise_me(recipes, pantry, subs)
        if not pick:
            st.warning("Nothing fully cookable. Add more pantry items!")
        else:
            st.success(f"Tonight: **{pick.recipe['name']}** ({pick.recipe['time_minutes']} min)")
            st.write("**Steps:**")
            for i, s in enumerate(pick.recipe.get("steps", []), 1):
                st.write(f"{i}. {s}")
