export default function Loading() {
  return (
    <>
      <main className="flex min-h-[60vh] items-center justify-center p-6">
        <div className="flex flex-col items-center gap-4">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-t-primary border-gray-200" />
          <p className="text-sm text-muted-foreground">Loading…</p>
        </div>
      </main>
    </>
  );
}
