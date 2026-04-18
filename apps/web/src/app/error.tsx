"use client";

import { Button } from "@/components/ui/button";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <>
      <main className="flex min-h-[60vh] flex-col items-center justify-center text-center p-6">
        <h1 className="text-2xl font-bold">Something went wrong</h1>
        <p className="text-sm text-muted-foreground mt-2">
          {error?.message || "An unexpected error occurred."}
        </p>
        <div className="mt-4">
          <Button onClick={() => reset()}>Try again</Button>
        </div>
      </main>
    </>
  );
}
