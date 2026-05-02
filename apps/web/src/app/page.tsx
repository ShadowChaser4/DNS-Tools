import WorldMap from "@/app/_components/world-map";
import { fetchDnsServers, keys } from "@/lib/api/dns";
import { makeQueryClient } from "@/lib/react-query-client";
import { dehydrate, HydrationBoundary } from "@tanstack/react-query";

export default async function Home() {
  const queryClient = makeQueryClient();
  await queryClient.prefetchQuery({
    queryKey: keys.fetchDnsServers(),
    queryFn: fetchDnsServers,
  });

  const dehydratedState = dehydrate(queryClient);

  return (
    <main className="min-h-screen">
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row md:items-start md:gap-8">
          <section className="w-full md:flex-1">
            <div className="flex h-full items-center">
              <h1 className="text-4xl font-bold">Welcome to DNS Tools</h1>
            </div>
            {/* other content / tool panels can go here */}
          </section>

          <aside className="w-full md:w-[80%] mt-8 md:mt-0">
            <HydrationBoundary state={dehydratedState}>
              <WorldMap />
            </HydrationBoundary>
          </aside>
        </div>
      </div>
    </main>
  );
}
