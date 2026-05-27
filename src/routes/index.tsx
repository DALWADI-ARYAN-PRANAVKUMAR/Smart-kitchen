import { createFileRoute } from "@tanstack/react-router";
import { SmartKitchen } from "@/components/SmartKitchen";
import { Toaster } from "@/components/ui/sonner";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Smart Kitchen — cook with what you have" },
      { name: "description", content: "A pantry-first cooking assistant: match recipes to what you have, plan your week, and waste nothing." },
      { property: "og:title", content: "Smart Kitchen" },
      { property: "og:description", content: "Cook with what you already have. AI-powered pantry assistant." },
    ],
  }),
  component: Index,
});

function Index() {
  return (
    <>
      <SmartKitchen />
      <Toaster richColors position="top-center" />
    </>
  );
}
