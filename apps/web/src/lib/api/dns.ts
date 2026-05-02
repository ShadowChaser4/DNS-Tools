import { unstable_cache } from "next/cache";

import { apiClient } from "./client";

export const keys = {
  fetchDnsServers: () => ["dnsServers"] as const,
};

const _fetchDnsServers = async () => {
  const { data, error } = await apiClient.GET("/dns/servers");
  if (error) throw error;
  return data;
};

export const fetchDnsServers = unstable_cache(
  _fetchDnsServers,
  Array.from(keys.fetchDnsServers()),
  { revalidate: 3600 },
);
