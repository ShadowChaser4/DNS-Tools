import { QueryClient } from "@tanstack/react-query";

export const makeQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        // With SSR, we usually want to set some default staleTime
        // above 0 to avoid refetching immediately on the client
        staleTime: 60 * 5 * 1000,
        refetchOnWindowFocus: false,
        refetchOnMount: false,
      },
    },
  });
