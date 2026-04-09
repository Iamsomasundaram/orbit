import { NextResponse } from "next/server";

import { fetchJson, getRuntimeConfig } from "@/lib/config";

type ApiReady = {
  service: string;
  status: string;
  checks: Array<{ name: string; status: string; detail: string }>;
};

export async function GET() {
  const config = getRuntimeConfig();
  const payload = await fetchJson<ApiReady>(`${config.internalApiBaseUrl}/health/ready`);

  if (!payload || payload.status !== "ok") {
    return NextResponse.json(
      {
        service: "orbit-web",
        status: "degraded",
        dependency: "api",
        detail: "The web shell could not confirm API readiness.",
      },
      { status: 503 },
    );
  }

  return NextResponse.json({
    service: "orbit-web",
    status: "ok",
    dependency: payload.service,
    detail: "The web shell can reach the API readiness endpoint.",
  });
}
