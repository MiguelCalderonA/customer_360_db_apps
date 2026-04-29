import type { CustomerProfile, CustomerSummary, Stats } from "./types";

const BASE = "/api";

async function jsonFetch<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${detail}`);
  }
  return res.json();
}

export const api = {
  stats: () => jsonFetch<Stats>(`${BASE}/stats`),
  search: (q: string) =>
    jsonFetch<CustomerSummary[]>(
      `${BASE}/customers?q=${encodeURIComponent(q)}&limit=50`
    ),
  topCustomers: () => jsonFetch<CustomerSummary[]>(`${BASE}/customers?limit=50`),
  profile: (email: string) =>
    jsonFetch<CustomerProfile>(`${BASE}/customers/${encodeURIComponent(email)}`),
};
