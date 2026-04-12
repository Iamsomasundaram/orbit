import { expect, test, type Page } from "@playwright/test";

const apiBaseUrl = process.env.PLAYWRIGHT_API_BASE_URL || "http://api:8001";

function uniqueIdeaName(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
}

async function createPortfolioThroughUi(page: Page, portfolioName: string) {
  await page.goto("/");
  await page.getByTestId("portfolio-name-input").fill(portfolioName);
  await page.getByTestId("portfolio-owner-input").fill("Automation Owner");
  await page
    .getByTestId("portfolio-description-input")
    .fill("Automation-created portfolio for Milestone 13 browser validation.");
  await page.getByTestId("portfolio-tags-input").fill("automation, browser");
  await page.getByTestId("portfolio-create-submit").click();

  await page.waitForURL(/\/portfolios\/.+\/history\?created=1/, { timeout: 60_000 });
  await expect(page.getByText("Submission Recorded")).toBeVisible();
  const match = page.url().match(/\/portfolios\/([^/]+)\/history/);
  expect(match?.[1]).toBeTruthy();
  return match![1];
}

async function runReviewFromHistory(page: Page) {
  await page.getByTestId("run-review-button").click();
  await page.waitForURL(/runId=/, { timeout: 90_000 });
  await expect(page.getByText("Review Completed")).toBeVisible();
  const runId = new URL(page.url()).searchParams.get("runId");
  expect(runId).toBeTruthy();
  return runId!;
}

test.describe.configure({ mode: "serial" });

test("portfolio creation, review, telemetry, committee playback, and deliberation timeline work end to end", async ({
  page,
}) => {
  const portfolioId = await createPortfolioThroughUi(page, uniqueIdeaName("boardroom-e2e"));
  const runId = await runReviewFromHistory(page);

  await expect(page.getByText(/Latest Recommendation/)).toBeVisible();
  await page.getByRole("link", { name: "Review Run Detail" }).first().click();
  await page.waitForURL(new RegExp(`/review-runs/${runId}$`), { timeout: 30_000 });
  await expect(page.getByText("Committee Runtime Telemetry")).toBeVisible();
  await expect(page.getByTestId("review-run-conflicts")).toBeVisible();

  await page.getByRole("link", { name: "Committee Mode" }).first().click();
  await page.waitForURL(new RegExp(`/review-runs/${runId}/committee$`), { timeout: 30_000 });
  await expect(page.getByTestId("committee-mode-page")).toBeVisible();
  await expect(page.getByText("Committee Runtime Metadata")).toBeVisible();

  await page.getByTestId("committee-speed-0.5x").click();
  await expect(page.getByTestId("committee-speed-current")).toContainText("Deliberate playback");
  await page.getByTestId("committee-speed-5x").click();
  await expect(page.getByTestId("committee-speed-current")).toContainText("Rapid playback");

  await page.getByTestId("committee-playback-toggle").click();
  await page.waitForTimeout(2000);
  await expect(page.getByTestId("committee-transcript")).not.toContainText("No entries are visible yet.");

  await page.getByTestId("committee-skip-phase").click();
  await expect(page.getByTestId("committee-conflict-spotlight")).toBeVisible();

  await page.getByTestId("committee-jump-verdict").click();
  await expect(page.getByTestId("committee-final-verdict")).toContainText("Weighted Composite");

  await page.goto(`/review-runs/${runId}/deliberation`);
  await expect(page.getByText("Ordered Timeline")).toBeVisible();
  await expect(page.getByText("Committee Deliberation")).toBeVisible();
  await expect(page.getByText("#1", { exact: true })).toBeVisible();

  await page.goto(`/portfolios/${portfolioId}`);
  await expect(page.getByText("Portfolio Detail", { exact: true })).toBeVisible();
});

test("workspace comparison flow supports multiple portfolios side by side", async ({ page, request }) => {
  const primaryPortfolioId = await createPortfolioThroughUi(page, uniqueIdeaName("compare-ui"));
  await runReviewFromHistory(page);

  const secondaryPortfolioName = uniqueIdeaName("compare-api");
  const createResponse = await request.post(`${apiBaseUrl}/api/v1/portfolios`, {
    data: {
      portfolio_name: secondaryPortfolioName,
      portfolio_type: "product_idea",
      owner: "Automation Owner",
      description: "Second automation-created portfolio for comparison validation.",
      tags: ["automation", "comparison"],
      metadata: {},
    },
  });
  expect(createResponse.ok()).toBeTruthy();
  const created = (await createResponse.json()) as { portfolio: { portfolio_id: string } };
  const secondaryPortfolioId = created.portfolio.portfolio_id;

  const reviewResponse = await request.post(`${apiBaseUrl}/api/v1/portfolios/${secondaryPortfolioId}/review-runs`, {
    data: {},
  });
  expect(reviewResponse.ok()).toBeTruthy();

  await page.goto("/");
  await expect(page.getByTestId(`workspace-card-${primaryPortfolioId}`)).toBeVisible();
  await expect(page.getByTestId(`workspace-card-${secondaryPortfolioId}`)).toBeVisible();
  await page.getByTestId(`compare-checkbox-${primaryPortfolioId}`).check();
  await page.getByTestId(`compare-checkbox-${secondaryPortfolioId}`).check();
  await page.getByTestId("compare-selected-submit").click();

  await page.waitForURL(/\/compare\?/, { timeout: 30_000 });
  await expect(page.getByTestId("portfolio-comparison-grid")).toBeVisible();
  await expect(page.getByTestId(`comparison-card-${primaryPortfolioId}`)).toBeVisible();
  await expect(page.getByTestId(`comparison-card-${secondaryPortfolioId}`)).toBeVisible();
});
