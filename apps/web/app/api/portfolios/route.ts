import { NextResponse } from "next/server";

import { OrbitApiError, type PortfolioDetailPayload, parseTags, postOrbitJson } from "@/lib/orbit-api";

export async function POST(request: Request) {
  const formData = await request.formData();
  const portfolioName = String(formData.get("portfolio_name") ?? "").trim();
  const owner = String(formData.get("owner") ?? "").trim();
  const description = String(formData.get("description") ?? "").trim();
  const tags = parseTags(String(formData.get("tags") ?? ""));

  try {
    const created = await postOrbitJson<PortfolioDetailPayload>("/api/v1/portfolios", {
      portfolio_name: portfolioName,
      portfolio_type: "product_idea",
      owner,
      description,
      tags,
      metadata: {},
    });
    return NextResponse.redirect(new URL(`/portfolios/${created.portfolio.portfolio_id}/history?created=1`, request.url), 303);
  } catch (error) {
    const message = error instanceof OrbitApiError ? error.message : "Unable to submit the portfolio idea.";
    return NextResponse.redirect(new URL(`/?submissionError=${encodeURIComponent(message)}`, request.url), 303);
  }
}
