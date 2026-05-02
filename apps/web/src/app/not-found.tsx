import Link from "next/link";
import { Button } from "@/components/ui/button";
export default function NotFound() {
  return (
    <>
      <main className="flex min-h-[60vh] flex-col items-center justify-center text-center p-6">
        <h1 className="text-2xl font-bold">Page not found</h1>
        <p className="text-sm text-muted-foreground mt-2">
          We couldn't find the page you're looking for.
        </p>
        <div className="mt-4">
          <Button asChild>
            <Link href="/">Go home</Link>
          </Button>
        </div>
      </main>
    </>
  );
}
