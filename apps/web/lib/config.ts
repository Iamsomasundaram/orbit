export type RuntimeConfig = {
  appName: string;
  milestone: string;
  internalApiBaseUrl: string;
  publicApiBaseUrl: string;
};

export type ServiceCard = {
  label: string;
  value: string;
  detail: string;
};

export function getRuntimeConfig(): RuntimeConfig {
  return {
    appName: process.env.NEXT_PUBLIC_APP_NAME || "ORBIT",
    milestone: process.env.NEXT_PUBLIC_PLATFORM_MILESTONE || "10",
    internalApiBaseUrl: process.env.INTERNAL_API_BASE_URL || "http://api:8001",
    publicApiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5001",
  };
}

export async function fetchJson<T>(url: string): Promise<T | null> {
  try {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as T;
  } catch {
    return null;
  }
}
