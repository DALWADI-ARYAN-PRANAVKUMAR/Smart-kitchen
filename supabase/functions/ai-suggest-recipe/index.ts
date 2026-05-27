// AI recipe suggestions based on pantry contents.
// POST { pantry: string[], hint?: string }  -> { recipes: Recipe[] }

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: corsHeaders });

  try {
    const { pantry = [], hint = "" } = await req.json();
    const apiKey = Deno.env.get("LOVABLE_API_KEY");
    if (!apiKey) throw new Error("LOVABLE_API_KEY missing");

    const system = `You are a creative home cook. Suggest 3 realistic recipes a person can mostly cook with the listed pantry ingredients. Keep ingredient names short and singular (e.g. "egg", "tomato"). Return ONLY via the suggest_recipes function call.`;
    const user = `Pantry: ${pantry.length ? pantry.join(", ") : "(empty — propose pantry staples)"}
Hint: ${hint || "(none)"}
Each recipe needs: name, time_minutes (5-60), 3-5 tags, ingredients object {name: quantity}, 3-6 step strings, cuisine.`;

    const resp = await fetch("https://ai.gateway.lovable.dev/v1/chat/completions", {
      method: "POST",
      headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        model: "google/gemini-2.5-flash",
        messages: [{ role: "system", content: system }, { role: "user", content: user }],
        tools: [{
          type: "function",
          function: {
            name: "suggest_recipes",
            description: "Return three recipes.",
            parameters: {
              type: "object",
              properties: {
                recipes: {
                  type: "array",
                  items: {
                    type: "object",
                    properties: {
                      name: { type: "string" },
                      time_minutes: { type: "number" },
                      tags: { type: "array", items: { type: "string" } },
                      cuisine: { type: "string" },
                      ingredients: { type: "object", additionalProperties: { type: "number" } },
                      steps: { type: "array", items: { type: "string" } },
                    },
                    required: ["name", "time_minutes", "tags", "ingredients", "steps"],
                  },
                },
              },
              required: ["recipes"],
            },
          },
        }],
        tool_choice: { type: "function", function: { name: "suggest_recipes" } },
      }),
    });

    if (resp.status === 429) return new Response(JSON.stringify({ error: "Rate limited — try again in a moment." }), { status: 429, headers: { ...corsHeaders, "Content-Type": "application/json" } });
    if (resp.status === 402) return new Response(JSON.stringify({ error: "AI credits exhausted. Add funds in Settings." }), { status: 402, headers: { ...corsHeaders, "Content-Type": "application/json" } });
    if (!resp.ok) {
      const t = await resp.text();
      console.error("ai-suggest gateway error", resp.status, t);
      return new Response(JSON.stringify({ error: "AI gateway error" }), { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } });
    }

    const json = await resp.json();
    const call = json.choices?.[0]?.message?.tool_calls?.[0];
    const args = call?.function?.arguments ? JSON.parse(call.function.arguments) : { recipes: [] };
    return new Response(JSON.stringify({ recipes: args.recipes ?? [] }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (e) {
    console.error(e);
    return new Response(JSON.stringify({ error: e instanceof Error ? e.message : "Unknown error" }), {
      status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
