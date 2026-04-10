import { NextResponse } from "next/server";

import { OrbitApiError, type ReviewRunSummary, postOrbitJson } from "@/lib/orbit-api";

type RouteContext = {
  params: Promise<{ portfolioId: string }>;
};

export async function POST(request: Request, context: RouteContext) {
  const { portfolioId } = await context.params;

  try {
    const run = await postOrbitJson<ReviewRunSummary>(`/api/v1/portfolios/${portfolioId}/review-runs`, {});
    return NextResponse.redirect(new URL(`/portfolios/${portfolioId}/history?runId=${run.run_id}`, request.url), 303);
  } catch (error) {
    const message = error instanceof OrbitApiError ? error.message : "Unable to run the ORBIT review.";
    return NextResponse.redirect(new URL(`/portfolios/${portfolioId}?reviewError=${encodeURIComponent(message)}`, request.url), 303);
  }
}
