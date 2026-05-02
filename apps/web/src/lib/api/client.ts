import createClient from "openapi-fetch";
import type { paths } from "@/lib/api/api-types";

const getApiBaseUrl = (): string => {
  return process.env.NEXT_PUBLIC_API_BASE_URL as string;
};

export const apiClient = createClient<paths>({
  baseUrl: getApiBaseUrl(),
});
