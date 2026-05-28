"""
Smart Kitchen — Tkinter desktop UI.

Run with:  python main.py
No external dependencies (uses Python's built-in tkinter).
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import date, timedelta

import core


# ---------- Theme ----------

COLORS = {
    "bg":         "#fbf7f0",   # cream
    "panel":      "#ffffff",
    "ink":        "#2b2620",
    "muted":      "#7a6f63",
    "primary":    "#c2552a",   # terracotta
    "primary_fg": "#ffffff",
    "sage":       "#7a9e6e",
    "sage_soft":  "#dfe9d8",
    "warn":       "#c97a2a",
    "danger":     "#b03a2e",
    "border":     "#e6dccc",
}


def style_app(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", background=COLORS["bg"], foreground=COLORS["ink"],
                    font=("Helvetica", 11))
    style.configure("TFrame", background=COLORS["bg"])
    style.configure("Card.TFrame", background=COLORS["panel"], relief="flat")
    style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["ink"])
    style.configure("Card.TLabel", background=COLORS["panel"], foreground=COLORS["ink"])
    style.configure("Muted.TLabel", background=COLORS["bg"], foreground=COLORS["muted"],
                    font=("Helvetica", 10))
    style.configure("CardMuted.TLabel", background=COLORS["panel"], foreground=COLORS["muted"],
                    font=("Helvetica", 10))
    style.configure("Title.TLabel", font=("Georgia", 22, "bold"),
                    foreground=COLORS["ink"], background=COLORS["bg"])
    style.configure("H2.TLabel", font=("Georgia", 14, "bold"),
                    foreground=COLORS["ink"], background=COLORS["panel"])

    style.configure("TButton", padding=(12, 6), background=COLORS["panel"],
                    foreground=COLORS["ink"], borderwidth=1, relief="flat")
    style.map("TButton", background=[("active", COLORS["sage_soft"])])

    style.configure("Primary.TButton", padding=(14, 8),
                    background=COLORS["primary"], foreground=COLORS["primary_fg"],
                    borderwidth=0)
    style.map("Primary.TButton",
              background=[("active", "#a8461f"), ("pressed", "#8e3b1a")])

    style.configure("Sage.TButton", padding=(12, 6),
                    background=COLORS["sage"], foreground="#ffffff", borderwidth=0)
    style.map("Sage.TButton", background=[("active", "#5f8a55")])

    style.configure("TEntry", fieldbackground=COLORS["panel"],
                    foreground=COLORS["ink"], bordercolor=COLORS["border"])
    style.configure("TCombobox", fieldbackground=COLORS["panel"],
                    foreground=COLORS["ink"])

    style.configure("TNotebook", background=COLORS["bg"], borderwidth=0)
    style.configure("TNotebook.Tab", padding=(18, 10),
                    background=COLORS["bg"], foreground=COLORS["muted"],
                    font=("Helvetica", 11, "bold"))
    style.map("TNotebook.Tab",
              background=[("selected", COLORS["panel"])],
              foreground=[("selected", COLORS["primary"])])

    style.configure("Treeview", background=COLORS["panel"],
                    fieldbackground=COLORS["panel"], foreground=COLORS["ink"],
                    rowheight=28, borderwidth=0)
    style.configure("Treeview.Heading",
                    background=COLORS["sage_soft"], foreground=COLORS["ink"],
                    font=("Helvetica", 10, "bold"))
    style.map("Treeview", background=[("selected", COLORS["sage_soft"])])


# ---------- App ----------

class SmartKitchenApp:
    def __init__(self, root):
        self.root = root
        root.title("Smart Kitchen — cook with what you have")
        root.geometry("1000x680")
        root.minsize(860, 600)
        root.configure(bg=COLORS["bg"])

        self.pantry = core.load_pantry()
        self.recipes = core.load_recipes()
        self.subs = core.load_subs()
        self.planner = []  # list of recipe names

        style_app(root)
        self._build_header()
        self._build_tabs()

    # ----- Header -----
    def _build_header(self):
        header = ttk.Frame(self.root, padding=(20, 16))
        header.pack(fill="x")

        title = ttk.Label(header, text="🍳  Smart Kitchen", style="Title.TLabel")
        title.pack(side="left")

        subtitle = ttk.Label(header,
                             text="Turn what you have into what you'll eat.",
                             style="Muted.TLabel")
        subtitle.pack(side="left", padx=(14, 0), pady=(10, 0))

        self.stat_var = tk.StringVar()
        stats = ttk.Label(header, textvariable=self.stat_var, style="Muted.TLabel")
        stats.pack(side="right")
        self._refresh_stats()

    def _refresh_stats(self):
        self.stat_var.set(f"{len(self.pantry)} in pantry  ·  {len(self.recipes)} recipes")

    # ----- Tabs -----
    def _build_tabs(self):
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        self.tab_pantry  = ttk.Frame(self.nb, style="Card.TFrame", padding=18)
        self.tab_cook    = ttk.Frame(self.nb, style="Card.TFrame", padding=18)
        self.tab_plan    = ttk.Frame(self.nb, style="Card.TFrame", padding=18)
        self.tab_book    = ttk.Frame(self.nb, style="Card.TFrame", padding=18)
        self.tab_surp    = ttk.Frame(self.nb, style="Card.TFrame", padding=18)

        self.nb.add(self.tab_pantry, text="  Pantry  ")
        self.nb.add(self.tab_cook,   text="  Cook  ")
        self.nb.add(self.tab_plan,   text="  Plan  ")
        self.nb.add(self.tab_book,   text="  Book  ")
        self.nb.add(self.tab_surp,   text="  Surprise  ")

        self._build_pantry_tab()
        self._build_cook_tab()
        self._build_plan_tab()
        self._build_book_tab()
        self._build_surprise_tab()

    # ----- Pantry -----
    def _build_pantry_tab(self):
        t = self.tab_pantry
        ttk.Label(t, text="Your Pantry", style="H2.TLabel").pack(anchor="w")
        ttk.Label(t, text="Add ingredients with quantity and optional expiry date.",
                  style="CardMuted.TLabel").pack(anchor="w", pady=(2, 14))

        form = ttk.Frame(t, style="Card.TFrame")
        form.pack(fill="x", pady=(0, 12))

        ttk.Label(form, text="Ingredient", style="Card.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(form, text="Qty",        style="Card.TLabel").grid(row=0, column=1, sticky="w", padx=(10, 0))
        ttk.Label(form, text="Expires (YYYY-MM-DD, optional)", style="Card.TLabel").grid(row=0, column=2, sticky="w", padx=(10, 0))

        self.p_name = ttk.Entry(form, width=24); self.p_name.grid(row=1, column=0, pady=4)
        self.p_qty  = ttk.Entry(form, width=8);  self.p_qty.grid(row=1, column=1, padx=(10, 0))
        self.p_qty.insert(0, "1")
        self.p_exp  = ttk.Entry(form, width=18); self.p_exp.grid(row=1, column=2, padx=(10, 0))

        ttk.Button(form, text="Add", style="Primary.TButton",
                   command=self._add_pantry_item).grid(row=1, column=3, padx=(12, 0))

        bulk = ttk.Frame(t, style="Card.TFrame")
        bulk.pack(fill="x", pady=(0, 12))
        ttk.Label(bulk, text="Or bulk add (e.g. \"eggs 4, milk 200, butter\"):",
                  style="CardMuted.TLabel").pack(anchor="w")
        bulk_row = ttk.Frame(bulk, style="Card.TFrame"); bulk_row.pack(fill="x", pady=4)
        self.bulk_entry = ttk.Entry(bulk_row); self.bulk_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(bulk_row, text="Bulk add", style="Sage.TButton",
                   command=self._bulk_add).pack(side="left", padx=(8, 0))

        cols = ("ingredient", "qty", "expires", "status")
        self.pantry_tree = ttk.Treeview(t, columns=cols, show="headings", height=12)
        for c, w in zip(cols, (260, 80, 140, 200)):
            self.pantry_tree.heading(c, text=c.title())
            self.pantry_tree.column(c, width=w, anchor="w")
        self.pantry_tree.pack(fill="both", expand=True, pady=(8, 8))

        actions = ttk.Frame(t, style="Card.TFrame"); actions.pack(fill="x")
        ttk.Button(actions, text="Remove selected", command=self._remove_pantry_item).pack(side="left")
        ttk.Button(actions, text="Clear pantry",
                   command=self._clear_pantry).pack(side="left", padx=(8, 0))

        self._refresh_pantry_tree()

    def _refresh_pantry_tree(self):
        self.pantry_tree.delete(*self.pantry_tree.get_children())
        for name, item in sorted(self.pantry.items()):
            d = core.days_until(item.expires)
            if d is None:
                status = "—"
            elif d < 0:
                status = f"Expired {abs(d)}d ago"
            elif d == 0:
                status = "Expires today"
            elif d <= 3:
                status = f"⚠ {d}d left"
            else:
                status = f"{d}d left"
            self.pantry_tree.insert("", "end",
                values=(name, item.qty, item.expires or "—", status))
        self._refresh_stats()

    def _add_pantry_item(self):
        name = self.p_name.get().strip()
        if not name:
            return
        try:
            qty = float(self.p_qty.get() or 1)
        except ValueError:
            messagebox.showerror("Invalid", "Quantity must be a number."); return
        exp = self.p_exp.get().strip() or None
        if exp:
            try: date.fromisoformat(exp)
            except ValueError:
                messagebox.showerror("Invalid", "Date must be YYYY-MM-DD"); return
        core.add_to_pantry(self.pantry, name, qty, exp)
        core.save_pantry(self.pantry)
        self.p_name.delete(0, "end"); self.p_qty.delete(0, "end"); self.p_qty.insert(0, "1")
        self.p_exp.delete(0, "end")
        self._refresh_pantry_tree()

    def _bulk_add(self):
        items = core.parse_ingredient_list(self.bulk_entry.get())
        for name, qty in items.items():
            core.add_to_pantry(self.pantry, name, qty)
        core.save_pantry(self.pantry)
        self.bulk_entry.delete(0, "end")
        self._refresh_pantry_tree()

    def _remove_pantry_item(self):
        sel = self.pantry_tree.selection()
        for s in sel:
            name = self.pantry_tree.item(s, "values")[0]
            self.pantry.pop(name, None)
        core.save_pantry(self.pantry)
        self._refresh_pantry_tree()

    def _clear_pantry(self):
        if messagebox.askyesno("Clear pantry", "Remove all pantry items?"):
            self.pantry.clear()
            core.save_pantry(self.pantry)
            self._refresh_pantry_tree()

    # ----- Cook -----
    def _build_cook_tab(self):
        t = self.tab_cook
        ttk.Label(t, text="What can I cook?", style="H2.TLabel").pack(anchor="w")
        ttk.Label(t, text="Recipes ranked by what you have. Items expiring soon get a boost.",
                  style="CardMuted.TLabel").pack(anchor="w", pady=(2, 12))

        filters = ttk.Frame(t, style="Card.TFrame"); filters.pack(fill="x", pady=(0, 10))
        ttk.Label(filters, text="Diet:", style="Card.TLabel").pack(side="left")
        self.diet_var = tk.StringVar(value="any")
        ttk.Combobox(filters, textvariable=self.diet_var,
                     values=["any", "vegetarian", "vegan", "quick", "breakfast", "high-protein"],
                     state="readonly", width=14).pack(side="left", padx=(6, 16))
        ttk.Label(filters, text="Max time (min):", style="Card.TLabel").pack(side="left")
        self.time_var = tk.StringVar(value="60")
        ttk.Entry(filters, textvariable=self.time_var, width=6).pack(side="left", padx=(6, 16))
        ttk.Button(filters, text="Find recipes", style="Primary.TButton",
                   command=self._refresh_cook).pack(side="left")

        body = ttk.Frame(t, style="Card.TFrame"); body.pack(fill="both", expand=True)
        left = ttk.Frame(body, style="Card.TFrame"); left.pack(side="left", fill="both", expand=True)
        right = ttk.Frame(body, style="Card.TFrame", padding=(14, 0)); right.pack(side="right", fill="both", expand=True)

        ttk.Label(left, text="Matches", style="Card.TLabel",
                  font=("Helvetica", 11, "bold")).pack(anchor="w")
        self.cook_list = tk.Listbox(left, height=18, bd=0, highlightthickness=1,
                                    highlightbackground=COLORS["border"],
                                    selectbackground=COLORS["sage_soft"],
                                    selectforeground=COLORS["ink"],
                                    font=("Helvetica", 11))
        self.cook_list.pack(fill="both", expand=True, pady=(6, 0))
        self.cook_list.bind("<<ListboxSelect>>", lambda e: self._show_cook_detail())

        ttk.Label(right, text="Details", style="Card.TLabel",
                  font=("Helvetica", 11, "bold")).pack(anchor="w")
        self.cook_detail = tk.Text(right, height=18, wrap="word", bd=0,
                                   highlightthickness=1, highlightbackground=COLORS["border"],
                                   bg=COLORS["panel"], fg=COLORS["ink"],
                                   font=("Helvetica", 11), padx=12, pady=10)
        self.cook_detail.pack(fill="both", expand=True, pady=(6, 8))
        self.cook_detail.config(state="disabled")
        ttk.Button(right, text="Cook this", style="Primary.TButton",
                   command=self._cook_selected).pack(anchor="e")

        self._cook_results = []
        self._refresh_cook()

    def _refresh_cook(self):
        try: max_t = int(self.time_var.get())
        except ValueError: max_t = None
        diet = [] if self.diet_var.get() == "any" else [self.diet_var.get()]
        self._cook_results = core.rank_recipes(self.recipes, self.pantry, self.subs,
                                                dietary=diet, max_time=max_t)
        self.cook_list.delete(0, "end")
        for m in self._cook_results:
            mark = "✓" if m.can_cook else f"missing {len(m.missing)}"
            star = "★ " if m.expiring_used else "  "
            self.cook_list.insert("end", f"{star}{m.recipe.name:30} {int(m.match_pct):3}%   [{mark}]")
        if self._cook_results:
            self.cook_list.selection_set(0)
            self._show_cook_detail()

    def _show_cook_detail(self):
        sel = self.cook_list.curselection()
        if not sel: return
        m = self._cook_results[sel[0]]
        r = m.recipe
        lines = [
            f"{r.name}",
            f"{r.time_minutes} min · {', '.join(r.tags) or 'no tags'}",
            "",
            "Ingredients:",
        ]
        for ing, qty in r.ingredients.items():
            tag = " (have)" if ing in m.have else \
                  f" (sub: {m.substituted[ing]})" if ing in m.substituted else \
                  " (MISSING)"
            lines.append(f"  • {ing} × {qty}{tag}")
        if m.expiring_used:
            lines.append(""); lines.append(f"⚠ Uses expiring: {', '.join(m.expiring_used)}")
        lines.append(""); lines.append("Steps:")
        for i, s in enumerate(r.steps, 1):
            lines.append(f"  {i}. {s}")
        self.cook_detail.config(state="normal")
        self.cook_detail.delete("1.0", "end")
        self.cook_detail.insert("1.0", "\n".join(lines))
        self.cook_detail.config(state="disabled")

    def _cook_selected(self):
        sel = self.cook_list.curselection()
        if not sel: return
        m = self._cook_results[sel[0]]
        ok, msg, self.pantry = core.cook(m.recipe, self.pantry, self.subs)
        core.save_pantry(self.pantry)
        (messagebox.showinfo if ok else messagebox.showwarning)("Cook", msg)
        self._refresh_pantry_tree(); self._refresh_cook()

    # ----- Plan -----
    def _build_plan_tab(self):
        t = self.tab_plan
        ttk.Label(t, text="Weekly Planner", style="H2.TLabel").pack(anchor="w")
        ttk.Label(t, text="Pick recipes for the week and export a combined shopping list.",
                  style="CardMuted.TLabel").pack(anchor="w", pady=(2, 12))

        body = ttk.Frame(t, style="Card.TFrame"); body.pack(fill="both", expand=True)
        left = ttk.Frame(body, style="Card.TFrame"); left.pack(side="left", fill="both", expand=True)
        right = ttk.Frame(body, style="Card.TFrame", padding=(14, 0)); right.pack(side="right", fill="both", expand=True)

        ttk.Label(left, text="All recipes", style="Card.TLabel",
                  font=("Helvetica", 11, "bold")).pack(anchor="w")
        self.plan_all = tk.Listbox(left, height=14, bd=0, highlightthickness=1,
                                   highlightbackground=COLORS["border"],
                                   selectbackground=COLORS["sage_soft"],
                                   font=("Helvetica", 11))
        self.plan_all.pack(fill="both", expand=True, pady=(6, 6))
        ttk.Button(left, text="Add → week", style="Sage.TButton",
                   command=self._plan_add).pack(anchor="e")

        ttk.Label(right, text="This week", style="Card.TLabel",
                  font=("Helvetica", 11, "bold")).pack(anchor="w")
        self.plan_week = tk.Listbox(right, height=10, bd=0, highlightthickness=1,
                                    highlightbackground=COLORS["border"],
                                    selectbackground=COLORS["sage_soft"],
                                    font=("Helvetica", 11))
        self.plan_week.pack(fill="x", pady=(6, 6))
        row = ttk.Frame(right, style="Card.TFrame"); row.pack(fill="x")
        ttk.Button(row, text="Remove", command=self._plan_remove).pack(side="left")
        ttk.Button(row, text="Clear",  command=self._plan_clear).pack(side="left", padx=(6, 0))
        ttk.Button(row, text="Build shopping list", style="Primary.TButton",
                   command=self._build_shopping_list).pack(side="right")

        ttk.Label(right, text="Shopping list", style="Card.TLabel",
                  font=("Helvetica", 11, "bold")).pack(anchor="w", pady=(12, 0))
        self.shop_text = tk.Text(right, height=10, wrap="word", bd=0,
                                 highlightthickness=1, highlightbackground=COLORS["border"],
                                 bg=COLORS["panel"], fg=COLORS["ink"],
                                 font=("Helvetica", 11), padx=10, pady=8)
        self.shop_text.pack(fill="both", expand=True, pady=(6, 6))
        ttk.Button(right, text="Save to file…",
                   command=self._save_shopping_list).pack(anchor="e")

        self._refresh_plan_lists()

    def _refresh_plan_lists(self):
        self.plan_all.delete(0, "end")
        for r in self.recipes:
            self.plan_all.insert("end", r.name)
        self.plan_week.delete(0, "end")
        for n in self.planner:
            self.plan_week.insert("end", n)

    def _plan_add(self):
        sel = self.plan_all.curselection()
        if sel:
            self.planner.append(self.plan_all.get(sel[0]))
            self._refresh_plan_lists()

    def _plan_remove(self):
        sel = self.plan_week.curselection()
        if sel:
            self.planner.pop(sel[0])
            self._refresh_plan_lists()

    def _plan_clear(self):
        self.planner.clear(); self._refresh_plan_lists()

    def _build_shopping_list(self):
        recipes_by_name = {r.name: r for r in self.recipes}
        matches = []
        for n in self.planner:
            r = recipes_by_name.get(n)
            if r:
                matches.append(core.match_recipe(r, self.pantry, self.subs))
        shop = core.shopping_list(matches)
        self.shop_text.delete("1.0", "end")
        if not shop:
            self.shop_text.insert("1.0", "You have everything for these recipes! 🎉")
        else:
            for ing, qty in shop.items():
                self.shop_text.insert("end", f"• {ing}  × {qty}\n")

    def _save_shopping_list(self):
        text = self.shop_text.get("1.0", "end").strip()
        if not text: return
        path = filedialog.asksaveasfilename(defaultextension=".txt",
            initialfile="shopping_list.txt",
            filetypes=[("Text", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            messagebox.showinfo("Saved", f"Saved to {path}")

    # ----- Book -----
    def _build_book_tab(self):
        t = self.tab_book
        ttk.Label(t, text="Recipe Book", style="H2.TLabel").pack(anchor="w")
        ttk.Label(t, text="Browse, add, or remove recipes.",
                  style="CardMuted.TLabel").pack(anchor="w", pady=(2, 12))

        body = ttk.Frame(t, style="Card.TFrame"); body.pack(fill="both", expand=True)
        left = ttk.Frame(body, style="Card.TFrame"); left.pack(side="left", fill="both", expand=True)
        right = ttk.Frame(body, style="Card.TFrame", padding=(14, 0)); right.pack(side="right", fill="both", expand=True)

        self.book_list = tk.Listbox(left, height=18, bd=0, highlightthickness=1,
                                    highlightbackground=COLORS["border"],
                                    selectbackground=COLORS["sage_soft"],
                                    font=("Helvetica", 11))
        self.book_list.pack(fill="both", expand=True)
        self.book_list.bind("<<ListboxSelect>>", lambda e: self._show_book_detail())

        actions = ttk.Frame(left, style="Card.TFrame"); actions.pack(fill="x", pady=(6, 0))
        ttk.Button(actions, text="Add new…", style="Primary.TButton",
                   command=self._add_recipe).pack(side="left")
        ttk.Button(actions, text="Delete", command=self._delete_recipe).pack(side="left", padx=(6, 0))

        self.book_detail = tk.Text(right, height=18, wrap="word", bd=0,
                                   highlightthickness=1, highlightbackground=COLORS["border"],
                                   bg=COLORS["panel"], fg=COLORS["ink"],
                                   font=("Helvetica", 11), padx=12, pady=10)
        self.book_detail.pack(fill="both", expand=True)
        self.book_detail.config(state="disabled")

        self._refresh_book()

    def _refresh_book(self):
        self.book_list.delete(0, "end")
        for r in self.recipes:
            self.book_list.insert("end", r.name)
        if self.recipes:
            self.book_list.selection_set(0)
            self._show_book_detail()
        self._refresh_stats()

    def _show_book_detail(self):
        sel = self.book_list.curselection()
        if not sel: return
        r = self.recipes[sel[0]]
        lines = [r.name, f"{r.time_minutes} min · {', '.join(r.tags) or 'no tags'}",
                 "", "Ingredients:"]
        for ing, qty in r.ingredients.items():
            lines.append(f"  • {ing} × {qty}")
        lines.append(""); lines.append("Steps:")
        for i, s in enumerate(r.steps, 1):
            lines.append(f"  {i}. {s}")
        self.book_detail.config(state="normal")
        self.book_detail.delete("1.0", "end")
        self.book_detail.insert("1.0", "\n".join(lines))
        self.book_detail.config(state="disabled")

    def _add_recipe(self):
        name = simpledialog.askstring("New recipe", "Recipe name:")
        if not name: return
        ing_str = simpledialog.askstring("New recipe",
            "Ingredients (e.g. 'eggs 2, milk 100, butter'):")
        if ing_str is None: return
        ingredients = core.parse_ingredient_list(ing_str)
        steps_str = simpledialog.askstring("New recipe",
            "Steps (separate with ' | '):") or ""
        steps = [s.strip() for s in steps_str.split("|") if s.strip()]
        tags_str = simpledialog.askstring("New recipe",
            "Tags (comma-separated, optional):") or ""
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        try:
            t = int(simpledialog.askstring("New recipe", "Time in minutes:") or 20)
        except ValueError:
            t = 20
        self.recipes.append(core.Recipe(name=name, ingredients=ingredients,
                                        steps=steps, tags=tags, time_minutes=t))
        core.save_recipes(self.recipes)
        self._refresh_book(); self._refresh_plan_lists()

    def _delete_recipe(self):
        sel = self.book_list.curselection()
        if not sel: return
        r = self.recipes[sel[0]]
        if messagebox.askyesno("Delete", f"Delete {r.name}?"):
            self.recipes.pop(sel[0])
            core.save_recipes(self.recipes)
            self._refresh_book(); self._refresh_plan_lists()

    # ----- Surprise -----
    def _build_surprise_tab(self):
        t = self.tab_surp
        ttk.Label(t, text="Surprise Me 🎲", style="H2.TLabel").pack(anchor="w")
        ttk.Label(t,
            text="Roll the dice for a random recipe you can cook right now.",
            style="CardMuted.TLabel").pack(anchor="w", pady=(2, 14))
        ttk.Button(t, text="Roll the dice", style="Primary.TButton",
                   command=self._roll).pack(anchor="w")
        self.surp_text = tk.Text(t, height=18, wrap="word", bd=0,
                                 highlightthickness=1, highlightbackground=COLORS["border"],
                                 bg=COLORS["panel"], fg=COLORS["ink"],
                                 font=("Helvetica", 11), padx=12, pady=10)
        self.surp_text.pack(fill="both", expand=True, pady=(14, 0))
        self.surp_text.insert("1.0", "Click \"Roll the dice\" to see what fate suggests.")
        self.surp_text.config(state="disabled")

    def _roll(self):
        m = core.surprise_me(self.recipes, self.pantry, self.subs)
        self.surp_text.config(state="normal")
        self.surp_text.delete("1.0", "end")
        if not m:
            self.surp_text.insert("1.0",
                "Nothing fully cookable right now.\nAdd a few staples to your pantry and try again.")
        else:
            r = m.recipe
            self.surp_text.insert("1.0",
                f"Tonight: {r.name}\n{r.time_minutes} min · {', '.join(r.tags)}\n\n"
                + "Ingredients:\n"
                + "\n".join(f"  • {i} × {q}" for i, q in r.ingredients.items())
                + "\n\nSteps:\n"
                + "\n".join(f"  {i}. {s}" for i, s in enumerate(r.steps, 1)))
        self.surp_text.config(state="disabled")


# ---------- Entry point ----------

def main():
    root = tk.Tk()
    SmartKitchenApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
