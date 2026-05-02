import { fetchDnsServers } from "@/lib/api/dns";
import { useQuery } from "@tanstack/react-query";

export const useDnsServers = () => {
  const query = useQuery({
    queryKey: ["dnsServers"],
    queryFn: fetchDnsServers,
  });

  return query;
};
