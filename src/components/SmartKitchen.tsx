"use client";

import { useEffect, useMemo, useState } from "react";
import { ChefHat, Sparkles, Calendar, BookOpen, Dice5, Soup, Trash2, Plus, Download, Camera, Wand2, Clock, AlertTriangle, Check, X, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";

import type { MatchResult, Pantry, Recipe } from "@/lib/kitchen/types";
import {
  cookRecipe,
  daysUntil,
  estimateNutrition,
  matchRecipe,
  rankRecipes,
  shoppingList,
  surpriseMe,
} from "@/lib/kitchen/core";
import {
  loadPantry,
  loadRecipes,
  loadSubs,
  resetAll,
  savePantry,
  saveRecipes,
} from "@/lib/kitchen/storage";
import { supabase } from "@/integrations/supabase/client";

export function SmartKitchen() {
  const [mounted, setMounted] = useState(false);
  const [pantry, setPantry] = useState<Pantry>({});
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [subs, setSubs] = useState<Record<string, string[]>>({});

  useEffect(() => {
    setPantry(loadPantry());
    setRecipes(loadRecipes());
    setSubs(loadSubs());
    setMounted(true);
  }, []);

  useEffect(() => { if (mounted) savePantry(pantry); }, [pantry, mounted]);
  useEffect(() => { if (mounted) saveRecipes(recipes); }, [recipes, mounted]);

  if (!mounted) {
    return <div className="min-h-screen paper" />;
  }

  return (
    <div className="min-h-screen paper">
      <Header
        pantrySize={Object.keys(pantry).length}
        recipeCount={recipes.length}
        onReset={() => { resetAll(); setPantry({}); setRecipes(loadRecipes()); toast.success("Reset complete"); }}
      />

      <main className="mx-auto max-w-6xl px-4 pb-24 pt-6 sm:px-6">
        <Tabs defaultValue="pantry" className="w-full">
          <TabsList className="mx-auto mb-8 grid h-auto w-full max-w-3xl grid-cols-5 gap-1 rounded-full bg-card/70 p-1.5 shadow-sm backdrop-blur">
            <TabTrigger value="pantry" icon={<Soup className="h-4 w-4" />} label="Pantry" />
            <TabTrigger value="cook" icon={<ChefHat className="h-4 w-4" />} label="Cook" />
            <TabTrigger value="plan" icon={<Calendar className="h-4 w-4" />} label="Plan" />
            <TabTrigger value="book" icon={<BookOpen className="h-4 w-4" />} label="Book" />
            <TabTrigger value="surprise" icon={<Dice5 className="h-4 w-4" />} label="Surprise" />
          </TabsList>

          <TabsContent value="pantry"><PantryTab pantry={pantry} setPantry={setPantry} /></TabsContent>
          <TabsContent value="cook"><CookTab pantry={pantry} setPantry={setPantry} recipes={recipes} subs={subs} /></TabsContent>
          <TabsContent value="plan"><PlanTab pantry={pantry} recipes={recipes} subs={subs} /></TabsContent>
          <TabsContent value="book"><BookTab recipes={recipes} setRecipes={setRecipes} pantry={pantry} subs={subs} /></TabsContent>
          <TabsContent value="surprise"><SurpriseTab pantry={pantry} setPantry={setPantry} recipes={recipes} subs={subs} /></TabsContent>
        </Tabs>
      </main>
      <Footer />
    </div>
  );
}

function TabTrigger({ value, icon, label }: { value: string; icon: React.ReactNode; label: string }) {
  return (
    <TabsTrigger
      value={value}
      className="flex items-center justify-center gap-2 rounded-full px-3 py-2 text-sm font-medium text-muted-foreground transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow"
    >
      {icon}
      <span className="hidden sm:inline">{label}</span>
    </TabsTrigger>
  );
}

function Header({ pantrySize, recipeCount, onReset }: { pantrySize: number; recipeCount: number; onReset: () => void }) {
  return (
    <header className="border-b border-border/60 bg-gradient-to-b from-cream/80 to-transparent backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-6 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-2xl bg-primary text-primary-foreground shadow-sm">
            <ChefHat className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl leading-none">Smart Kitchen</h1>
            <p className="mt-1 text-xs text-muted-foreground">
              Turn what you have into what you'll eat.
            </p>
          </div>
        </div>
        <div className="hidden items-center gap-3 text-sm text-muted-foreground sm:flex">
          <Badge variant="secondary" className="rounded-full bg-secondary/70 px-3 py-1 font-normal">
            {pantrySize} in pantry
          </Badge>
          <Badge variant="secondary" className="rounded-full bg-secondary/70 px-3 py-1 font-normal">
            {recipeCount} recipes
          </Badge>
          <Button variant="ghost" size="sm" onClick={onReset} className="text-muted-foreground hover:text-foreground">
            Reset
          </Button>
        </div>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="border-t border-border/60 py-8 text-center text-xs text-muted-foreground">
      Made with care · pantry-first cooking · runs entirely in your browser
    </footer>
  );
}

/* ---------------- PANTRY ---------------- */

function PantryTab({ pantry, setPantry }: { pantry: Pantry; setPantry: (p: Pantry) => void }) {
  const [name, setName] = useState("");
  const [qty, setQty] = useState("1");
  const [exp, setExp] = useState("");
  const [bulk, setBulk] = useState("");
  const [scanning, setScanning] = useState(false);

  const sorted = useMemo(() => Object.entries(pantry).sort(([a], [b]) => a.localeCompare(b)), [pantry]);

  const add = (n: string, q: number, e?: string | null) => {
    const key = n.trim();
    if (!key) return;
    const next = { ...pantry };
    if (next[key]) {
      next[key] = { qty: next[key].qty + q, expires: e ?? next[key].expires ?? null };
    } else {
      next[key] = { qty: q, expires: e ?? null };
    }
    setPantry(next);
  };

  const remove = (k: string) => {
    const next = { ...pantry };
    delete next[k];
    setPantry(next);
  };

  const handleAdd = () => {
    if (!name.trim()) return;
    add(name, Number(qty) || 1, exp || null);
    setName(""); setQty("1"); setExp("");
    toast.success(`Added ${name}`);
  };

  const handleBulk = () => {
    const items = bulk.split(/[,\n]/).map((s) => s.trim()).filter(Boolean);
    if (!items.length) return;
    let next = { ...pantry };
    for (const it of items) {
      next = { ...next, [it]: { qty: (next[it]?.qty ?? 0) + 1, expires: next[it]?.expires ?? null } };
    }
    setPantry(next);
    setBulk("");
    toast.success(`Added ${items.length} items`);
  };

  const handlePhoto = async (file: File) => {
    setScanning(true);
    try {
      const b64 = await fileToBase64(file);
      const { data, error } = await supabase.functions.invoke("photo-pantry-scan", {
        body: { imageBase64: b64 },
      });
      if (error) throw error;
      const items: string[] = data?.items ?? [];
      if (!items.length) { toast.error("No ingredients detected"); return; }
      let next = { ...pantry };
      for (const it of items) {
        const k = it.toLowerCase();
        next = { ...next, [k]: { qty: (next[k]?.qty ?? 0) + 1, expires: next[k]?.expires ?? null } };
      }
      setPantry(next);
      toast.success(`Added ${items.length} from photo: ${items.slice(0, 4).join(", ")}${items.length > 4 ? "…" : ""}`);
    } catch (e: any) {
      toast.error(e?.message ?? "Photo scan failed");
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
      <Card className="border-border/60 bg-card/80 backdrop-blur">
        <CardHeader>
          <CardTitle className="text-2xl">Add to pantry</CardTitle>
          <CardDescription>Track what you have so we can match it to recipes.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="ing">Ingredient</Label>
              <Input id="ing" value={name} placeholder="e.g. eggs" onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAdd()} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="qty">Quantity</Label>
                <Input id="qty" type="number" min="0" step="1" value={qty} onChange={(e) => setQty(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="exp">Expires</Label>
                <Input id="exp" type="date" value={exp} onChange={(e) => setExp(e.target.value)} />
              </div>
            </div>
            <Button onClick={handleAdd} className="w-full gap-2"><Plus className="h-4 w-4" /> Add</Button>
          </div>

          <Separator />

          <div className="space-y-3">
            <Label>Bulk add</Label>
            <Textarea value={bulk} onChange={(e) => setBulk(e.target.value)}
              placeholder="rice, onion, garlic&#10;tomato&#10;basil" rows={3} />
            <Button onClick={handleBulk} variant="secondary" className="w-full">Add list</Button>
          </div>

          <Separator />

          <div className="space-y-3">
            <Label>Scan a photo</Label>
            <p className="text-xs text-muted-foreground">Snap your fridge or pantry — AI detects ingredients and adds them.</p>
            <label className="flex cursor-pointer items-center justify-center gap-2 rounded-md border border-dashed border-border bg-muted/30 px-4 py-3 text-sm transition hover:bg-muted/60">
              <Camera className="h-4 w-4" />
              <span>{scanning ? "Scanning…" : "Upload photo"}</span>
              <input type="file" accept="image/*" className="hidden"
                disabled={scanning}
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handlePhoto(f);
                  e.target.value = "";
                }} />
            </label>
          </div>
        </CardContent>
      </Card>

      <Card className="border-border/60 bg-card/80 backdrop-blur">
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle className="text-2xl">Your pantry</CardTitle>
            <CardDescription>{sorted.length === 0 ? "Empty — add some ingredients." : `${sorted.length} ingredients`}</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          {sorted.length === 0 ? (
            <div className="rounded-lg border border-dashed border-border bg-muted/20 px-6 py-10 text-center text-sm text-muted-foreground">
              Once you add items, you'll see them here with expiry warnings.
            </div>
          ) : (
            <ul className="divide-y divide-border/60">
              {sorted.map(([k, v]) => {
                const d = daysUntil(v.expires);
                let tone = "text-muted-foreground";
                let pill: React.ReactNode = null;
                if (d !== null) {
                  if (d < 0) { tone = "text-destructive"; pill = <Badge variant="destructive" className="font-normal">expired</Badge>; }
                  else if (d <= 3) { tone = "text-primary"; pill = <Badge className="bg-primary/15 text-primary hover:bg-primary/15 font-normal"><AlertTriangle className="mr-1 h-3 w-3" />{d}d left</Badge>; }
                  else pill = <Badge variant="outline" className="font-normal">{d}d left</Badge>;
                }
                return (
                  <li key={k} className="flex items-center justify-between gap-3 py-3">
                    <div className="min-w-0">
                      <div className="truncate font-medium capitalize">{k}</div>
                      <div className={`text-xs ${tone}`}>qty {v.qty}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      {pill}
                      <Button size="icon" variant="ghost" className="h-8 w-8 text-muted-foreground hover:text-destructive" onClick={() => remove(k)}>
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

/* ---------------- COOK ---------------- */

function CookTab({ pantry, setPantry, recipes, subs }: { pantry: Pantry; setPantry: (p: Pantry) => void; recipes: Recipe[]; subs: Record<string, string[]> }) {
  const [dietary, setDietary] = useState<string[]>([]);
  const [maxTime, setMaxTime] = useState(60);
  const [prio, setPrio] = useState(true);
  const [q, setQ] = useState("");

  const allTags = useMemo(() => Array.from(new Set(recipes.flatMap((r) => r.tags))).sort(), [recipes]);

  const matches = useMemo(() => {
    let res = rankRecipes(recipes, pantry, subs, { dietary, maxTime, prioritizeExpiring: prio });
    if (q.trim()) {
      const ql = q.toLowerCase();
      res = res.filter((m) => m.recipe.name.toLowerCase().includes(ql) || m.recipe.tags.some((t) => t.includes(ql)));
    }
    return res;
  }, [recipes, pantry, subs, dietary, maxTime, prio, q]);

  const cookable = matches.filter((m) => m.canCook);
  const almost = matches.filter((m) => !m.canCook).slice(0, 12);

  return (
    <div className="space-y-6">
      <Card className="border-border/60 bg-card/80 backdrop-blur">
        <CardContent className="pt-6">
          <div className="grid gap-5 md:grid-cols-[1fr_1fr_auto]">
            <div className="space-y-2">
              <Label className="text-xs uppercase tracking-wide text-muted-foreground">Search</Label>
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="pasta, breakfast…" className="pl-9" />
              </div>
            </div>
            <div className="space-y-2">
              <Label className="text-xs uppercase tracking-wide text-muted-foreground">Max time · {maxTime} min</Label>
              <Slider value={[maxTime]} min={5} max={90} step={5} onValueChange={(v) => setMaxTime(v[0])} />
            </div>
            <div className="flex items-end">
              <Button variant={prio ? "default" : "outline"} onClick={() => setPrio((p) => !p)} className="gap-2">
                <Clock className="h-4 w-4" /> Prioritize expiring
              </Button>
            </div>
          </div>

          {allTags.length > 0 && (
            <div className="mt-5">
              <Label className="mb-2 block text-xs uppercase tracking-wide text-muted-foreground">Tags</Label>
              <ToggleGroup type="multiple" value={dietary} onValueChange={setDietary} className="flex flex-wrap justify-start gap-1.5">
                {allTags.map((t) => (
                  <ToggleGroupItem key={t} value={t} className="rounded-full border border-border bg-background px-3 py-1 text-xs capitalize data-[state=on]:border-primary data-[state=on]:bg-primary data-[state=on]:text-primary-foreground">
                    {t}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </div>
          )}
        </CardContent>
      </Card>

      <div>
        <SectionHeader title="Cookable now" count={cookable.length} accent="sage" />
        {cookable.length === 0 ? (
          <EmptyState text="Nothing fully cookable yet. Try adding a few staples or relax the filters." />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {cookable.map((m) => <RecipeCard key={m.recipe.name} m={m} pantry={pantry} setPantry={setPantry} subs={subs} />)}
          </div>
        )}
      </div>

      {almost.length > 0 && (
        <div>
          <SectionHeader title="Almost there" count={almost.length} accent="terracotta" />
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {almost.map((m) => <RecipeCard key={m.recipe.name} m={m} pantry={pantry} setPantry={setPantry} subs={subs} />)}
          </div>
        </div>
      )}
    </div>
  );
}

function SectionHeader({ title, count, accent }: { title: string; count: number; accent: "sage" | "terracotta" }) {
  const c = accent === "sage" ? "bg-accent" : "bg-primary";
  return (
    <div className="mb-4 flex items-baseline gap-3">
      <span className={`h-2.5 w-2.5 rounded-full ${c}`} />
      <h2 className="text-2xl">{title}</h2>
      <span className="text-sm text-muted-foreground">{count}</span>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return <div className="rounded-lg border border-dashed border-border bg-muted/20 px-6 py-10 text-center text-sm text-muted-foreground">{text}</div>;
}

function RecipeCard({ m, pantry, setPantry, subs }: { m: MatchResult; pantry: Pantry; setPantry: (p: Pantry) => void; subs: Record<string, string[]> }) {
  const r = m.recipe;
  const nut = useMemo(() => estimateNutrition(r), [r]);
  return (
    <Dialog>
      <Card className="group flex h-full flex-col border-border/60 bg-card/90 transition-all hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-xl leading-tight">{r.name}</CardTitle>
            {m.canCook ? <Badge className="bg-accent/15 text-[color:var(--sage-deep)] hover:bg-accent/15 font-normal"><Check className="mr-1 h-3 w-3" /> ready</Badge> : <Badge variant="outline" className="font-normal">{m.missing.length} missing</Badge>}
          </div>
          <CardDescription className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {r.time_minutes} min</span>
            {r.cuisine && <span>· {r.cuisine}</span>}
            <span>· {Math.round(m.matchPct)}% match</span>
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-1 flex-col gap-3">
          <Progress value={m.matchPct} className="h-1.5" />
          <div className="flex flex-wrap gap-1">
            {r.tags.slice(0, 4).map((t) => (
              <span key={t} className="rounded-full bg-secondary/70 px-2 py-0.5 text-[10px] uppercase tracking-wide text-secondary-foreground">{t}</span>
            ))}
          </div>
          {m.expiringUsed.length > 0 && (
            <p className="text-xs text-primary">⏰ uses expiring: {m.expiringUsed.join(", ")}</p>
          )}
          {m.missing.length > 0 && (
            <p className="text-xs text-muted-foreground"><span className="font-medium text-foreground">Missing:</span> {m.missing.join(", ")}</p>
          )}
          {Object.keys(m.substituted).length > 0 && (
            <p className="text-xs text-muted-foreground"><span className="font-medium text-foreground">Substitutes:</span> {Object.entries(m.substituted).map(([k, v]) => `${k}→${v}`).join(", ")}</p>
          )}
          <div className="mt-auto flex items-center justify-between gap-2 pt-2">
            <div className="text-xs text-muted-foreground">
              ~{nut.kcal} kcal · {nut.protein}g P
            </div>
            <DialogTrigger asChild>
              <Button size="sm" variant="ghost">View</Button>
            </DialogTrigger>
          </div>
        </CardContent>
      </Card>
      <RecipeDialog m={m} pantry={pantry} setPantry={setPantry} subs={subs} />
    </Dialog>
  );
}

function RecipeDialog({ m, pantry, setPantry, subs }: { m: MatchResult; pantry: Pantry; setPantry: (p: Pantry) => void; subs: Record<string, string[]> }) {
  const r = m.recipe;
  const nut = useMemo(() => estimateNutrition(r), [r]);
  const onCook = () => {
    const res = cookRecipe(r, pantry, subs);
    if (!res.ok) { toast.error(res.msg); return; }
    setPantry(res.pantry);
    toast.success(res.msg);
  };
  return (
    <DialogContent className="max-w-2xl">
      <DialogHeader>
        <DialogTitle className="text-3xl">{r.name}</DialogTitle>
        <DialogDescription className="flex flex-wrap items-center gap-2 text-xs">
          <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{r.time_minutes} min</span>
          {r.cuisine && <span>· {r.cuisine}</span>}
          {r.tags.map((t) => <span key={t} className="rounded-full bg-secondary/70 px-2 py-0.5 capitalize">{t}</span>)}
        </DialogDescription>
      </DialogHeader>

      <div className="grid gap-6 md:grid-cols-[1fr_1fr]">
        <div>
          <h3 className="mb-2 text-sm font-medium uppercase tracking-wide text-muted-foreground">Ingredients</h3>
          <ul className="space-y-1.5 text-sm">
            {Object.entries(r.ingredients).map(([ing, qty]) => {
              const have = m.have.includes(ing);
              const sub = m.substituted[ing];
              return (
                <li key={ing} className="flex items-baseline justify-between gap-3">
                  <span className={have || sub ? "" : "text-muted-foreground line-through"}>
                    {ing} <span className="text-muted-foreground">× {qty}</span>
                    {sub && <span className="ml-1 text-xs text-accent-foreground/80">(use {sub})</span>}
                  </span>
                  {have ? <Check className="h-3.5 w-3.5 text-accent" /> : sub ? <span className="text-xs text-accent">sub</span> : <X className="h-3.5 w-3.5 text-destructive" />}
                </li>
              );
            })}
          </ul>
        </div>
        <div className="space-y-4">
          <div>
            <h3 className="mb-2 text-sm font-medium uppercase tracking-wide text-muted-foreground">Steps</h3>
            <ol className="space-y-2 text-sm">
              {r.steps.map((s, i) => (
                <li key={i} className="flex gap-3">
                  <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-primary/15 text-[10px] font-medium text-primary">{i + 1}</span>
                  <span>{s}</span>
                </li>
              ))}
            </ol>
          </div>
          <div className="rounded-lg border border-border/60 bg-muted/30 p-3 text-xs">
            <div className="mb-1 font-medium uppercase tracking-wide text-muted-foreground">Estimated nutrition</div>
            <div className="grid grid-cols-4 gap-2 text-center">
              <Stat label="kcal" value={nut.kcal} />
              <Stat label="protein" value={`${nut.protein}g`} />
              <Stat label="carbs" value={`${nut.carbs}g`} />
              <Stat label="fat" value={`${nut.fat}g`} />
            </div>
            <p className="mt-2 text-[10px] text-muted-foreground">Heuristic from {nut.covered}/{nut.total} ingredients.</p>
          </div>
        </div>
      </div>

      <div className="flex justify-end pt-2">
        <Button onClick={onCook} disabled={!m.canCook} className="gap-2"><ChefHat className="h-4 w-4" /> Cook & deduct from pantry</Button>
      </div>
    </DialogContent>
  );
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div className="text-base font-medium">{value}</div>
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
    </div>
  );
}

/* ---------------- PLAN ---------------- */

function PlanTab({ pantry, recipes, subs }: { pantry: Pantry; recipes: Recipe[]; subs: Record<string, string[]> }) {
  const [picks, setPicks] = useState<string[]>([]);

  const selected = recipes.filter((r) => picks.includes(r.name));
  const matchObjs = selected.map((r) => matchRecipe(r, pantry, subs));
  const list = shoppingList(matchObjs);

  const toggle = (n: string) => setPicks((p) => p.includes(n) ? p.filter((x) => x !== n) : [...p, n]);

  const download = () => {
    const txt = "Smart Kitchen — Shopping list\n\n" + Object.entries(list).map(([i, q]) => `- ${i} × ${q}`).join("\n");
    const blob = new Blob([txt], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "shopping_list.txt"; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
      <Card className="border-border/60 bg-card/80 backdrop-blur">
        <CardHeader>
          <CardTitle className="text-2xl">Plan your week</CardTitle>
          <CardDescription>Pick recipes — we'll merge their missing items into one list.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 sm:grid-cols-2">
            {recipes.map((r) => {
              const on = picks.includes(r.name);
              return (
                <button key={r.name} onClick={() => toggle(r.name)}
                  className={`group flex items-center justify-between rounded-lg border px-3 py-2.5 text-left transition ${on ? "border-primary bg-primary/10" : "border-border bg-background hover:border-primary/40"}`}>
                  <div className="min-w-0">
                    <div className="truncate font-medium">{r.name}</div>
                    <div className="text-xs text-muted-foreground">{r.time_minutes} min · {r.cuisine ?? r.tags[0]}</div>
                  </div>
                  <div className={`grid h-5 w-5 place-items-center rounded-full border ${on ? "border-primary bg-primary text-primary-foreground" : "border-border"}`}>
                    {on && <Check className="h-3 w-3" />}
                  </div>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <Card className="border-border/60 bg-card/80 backdrop-blur">
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle className="text-2xl">Shopping list</CardTitle>
            <CardDescription>{Object.keys(list).length === 0 ? "Pick some recipes to begin." : `${Object.keys(list).length} items to buy`}</CardDescription>
          </div>
          {Object.keys(list).length > 0 && (
            <Button size="sm" variant="outline" onClick={download} className="gap-2"><Download className="h-4 w-4" /> Export</Button>
          )}
        </CardHeader>
        <CardContent>
          {selected.length === 0 ? (
            <EmptyState text="No recipes selected." />
          ) : Object.keys(list).length === 0 ? (
            <div className="rounded-lg border border-accent/40 bg-accent/10 px-4 py-6 text-center text-sm text-accent-foreground">
              You already have everything for these recipes!
            </div>
          ) : (
            <ul className="divide-y divide-border/60">
              {Object.entries(list).map(([i, q]) => (
                <li key={i} className="flex items-center justify-between py-2.5">
                  <span className="capitalize">{i}</span>
                  <span className="text-sm text-muted-foreground">× {q}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

/* ---------------- BOOK ---------------- */

function BookTab({ recipes, setRecipes, pantry, subs }: { recipes: Recipe[]; setRecipes: (r: Recipe[]) => void; pantry: Pantry; subs: Record<string, string[]> }) {
  const [open, setOpen] = useState(false);
  const [aiOpen, setAiOpen] = useState(false);
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl">Recipe book</h2>
          <p className="text-sm text-muted-foreground">{recipes.length} recipes</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="gap-2" onClick={() => setAiOpen(true)}><Sparkles className="h-4 w-4" /> AI suggest</Button>
          <Button className="gap-2" onClick={() => setOpen(true)}><Plus className="h-4 w-4" /> Add recipe</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {recipes.map((r) => {
          const m = matchRecipe(r, pantry, subs);
          return (
            <Dialog key={r.name}>
              <Card className="flex h-full flex-col border-border/60 bg-card/90 transition hover:-translate-y-0.5 hover:shadow-md">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-xl leading-tight">{r.name}</CardTitle>
                    <Button size="icon" variant="ghost" className="h-7 w-7 text-muted-foreground hover:text-destructive"
                      onClick={() => { setRecipes(recipes.filter((x) => x.name !== r.name)); toast.success(`Removed ${r.name}`); }}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                  <CardDescription className="text-xs">{r.time_minutes} min · {r.cuisine ?? r.tags[0]}</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-1 flex-col gap-2 pt-0">
                  <div className="flex flex-wrap gap-1">
                    {r.tags.slice(0, 3).map((t) => <span key={t} className="rounded-full bg-secondary/70 px-2 py-0.5 text-[10px] uppercase tracking-wide text-secondary-foreground">{t}</span>)}
                  </div>
                  <p className="text-xs text-muted-foreground">{Object.keys(r.ingredients).length} ingredients</p>
                  <div className="mt-auto pt-2">
                    <DialogTrigger asChild>
                      <Button size="sm" variant="ghost" className="w-full">View</Button>
                    </DialogTrigger>
                  </div>
                </CardContent>
              </Card>
              <RecipeDialog m={m} pantry={pantry} setPantry={() => {}} subs={subs} />
            </Dialog>
          );
        })}
      </div>

      <AddRecipeDialog open={open} onOpenChange={setOpen} onAdd={(r) => setRecipes([...recipes, r])} />
      <AiSuggestDialog open={aiOpen} onOpenChange={setAiOpen} pantry={pantry} onAdd={(r) => setRecipes([...recipes, r])} />
    </div>
  );
}

function AddRecipeDialog({ open, onOpenChange, onAdd }: { open: boolean; onOpenChange: (b: boolean) => void; onAdd: (r: Recipe) => void }) {
  const [name, setName] = useState("");
  const [time, setTime] = useState("20");
  const [tags, setTags] = useState("");
  const [ings, setIngs] = useState("");
  const [steps, setSteps] = useState("");
  const reset = () => { setName(""); setTime("20"); setTags(""); setIngs(""); setSteps(""); };
  const submit = () => {
    if (!name.trim() || !ings.trim()) return;
    const ingredients: Record<string, number> = {};
    for (const line of ings.split("\n")) {
      const [n, q] = line.split(":");
      if (n && q && !isNaN(Number(q))) ingredients[n.trim()] = Number(q);
    }
    onAdd({
      name: name.trim(),
      time_minutes: Number(time) || 20,
      tags: tags.split(",").map((s) => s.trim()).filter(Boolean),
      ingredients,
      steps: steps.split("\n").map((s) => s.trim()).filter(Boolean),
    });
    toast.success(`Added ${name}`);
    reset(); onOpenChange(false);
  };
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader><DialogTitle>Add a recipe</DialogTitle></DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1.5"><Label>Name</Label><Input value={name} onChange={(e) => setName(e.target.value)} /></div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5"><Label>Time (min)</Label><Input type="number" value={time} onChange={(e) => setTime(e.target.value)} /></div>
            <div className="space-y-1.5"><Label>Tags (comma)</Label><Input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="vegetarian, quick" /></div>
          </div>
          <div className="space-y-1.5"><Label>Ingredients (one per line: name : qty)</Label>
            <Textarea rows={5} value={ings} onChange={(e) => setIngs(e.target.value)} placeholder={"eggs : 2\nbutter : 1"} /></div>
          <div className="space-y-1.5"><Label>Steps (one per line)</Label><Textarea rows={4} value={steps} onChange={(e) => setSteps(e.target.value)} /></div>
          <Button onClick={submit} className="w-full">Save recipe</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function AiSuggestDialog({ open, onOpenChange, pantry, onAdd }: { open: boolean; onOpenChange: (b: boolean) => void; pantry: Pantry; onAdd: (r: Recipe) => void }) {
  const [loading, setLoading] = useState(false);
  const [hint, setHint] = useState("");
  const [results, setResults] = useState<Recipe[]>([]);

  const run = async () => {
    setLoading(true); setResults([]);
    try {
      const { data, error } = await supabase.functions.invoke("ai-suggest-recipe", {
        body: { pantry: Object.keys(pantry), hint },
      });
      if (error) throw error;
      const recipes: Recipe[] = data?.recipes ?? [];
      if (!recipes.length) toast.error("No suggestions returned");
      setResults(recipes);
    } catch (e: any) {
      toast.error(e?.message ?? "AI suggest failed");
    } finally { setLoading(false); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-2xl">AI recipe suggestions</DialogTitle>
          <DialogDescription>We'll propose 3 recipes based on your pantry. Add the ones you like.</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label>Optional hint</Label>
            <Input value={hint} onChange={(e) => setHint(e.target.value)} placeholder="something Italian, under 25 minutes…" />
          </div>
          <Button onClick={run} disabled={loading} className="w-full gap-2"><Wand2 className="h-4 w-4" /> {loading ? "Cooking up ideas…" : "Generate"}</Button>
          {results.length > 0 && (
            <div className="space-y-3 pt-2">
              {results.map((r) => (
                <div key={r.name} className="rounded-lg border border-border bg-muted/30 p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="font-medium">{r.name}</div>
                      <div className="text-xs text-muted-foreground">{r.time_minutes} min · {r.tags.join(", ")}</div>
                    </div>
                    <Button size="sm" onClick={() => { onAdd(r); toast.success(`Added ${r.name}`); }}>Add</Button>
                  </div>
                  <div className="mt-2 text-xs text-muted-foreground">
                    {Object.entries(r.ingredients).map(([i, q]) => `${i} × ${q}`).join(" · ")}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

/* ---------------- SURPRISE ---------------- */

function SurpriseTab({ pantry, setPantry, recipes, subs }: { pantry: Pantry; setPantry: (p: Pantry) => void; recipes: Recipe[]; subs: Record<string, string[]> }) {
  const [pick, setPick] = useState<MatchResult | null>(null);
  const roll = () => {
    const r = surpriseMe(recipes, pantry, subs);
    if (!r) { toast.error("Nothing cookable yet. Add more pantry items."); return; }
    setPick(r);
  };
  return (
    <div className="mx-auto max-w-2xl">
      <Card className="border-border/60 bg-card/80 text-center backdrop-blur">
        <CardHeader>
          <CardTitle className="text-3xl">Feeling lucky?</CardTitle>
          <CardDescription>We'll pick something you can cook right now.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6 pb-8">
          <Button size="lg" onClick={roll} className="gap-2 rounded-full px-8">
            <Dice5 className="h-5 w-5" /> Roll the dice
          </Button>
          {pick && (
            <div className="rounded-xl border border-border bg-background/70 p-6 text-left">
              <div className="mb-1 text-xs uppercase tracking-widest text-muted-foreground">Tonight</div>
              <h3 className="text-3xl">{pick.recipe.name}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{pick.recipe.time_minutes} min · {pick.recipe.cuisine ?? pick.recipe.tags[0]}</p>
              <ol className="mt-4 space-y-2 text-sm">
                {pick.recipe.steps.map((s, i) => (
                  <li key={i} className="flex gap-3">
                    <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-primary/15 text-[10px] font-medium text-primary">{i + 1}</span>
                    <span>{s}</span>
                  </li>
                ))}
              </ol>
              <Button className="mt-5 gap-2" onClick={() => {
                const res = cookRecipe(pick.recipe, pantry, subs);
                if (!res.ok) { toast.error(res.msg); return; }
                setPantry(res.pantry); toast.success(res.msg);
              }}><ChefHat className="h-4 w-4" /> Cook this</Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

/* ---------------- utils ---------------- */

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result));
    r.onerror = reject;
    r.readAsDataURL(file);
  });
}
