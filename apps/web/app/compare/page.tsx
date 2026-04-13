import {
  ActionLink,
  MetricCard,
  PageFrame,
  SectionEyebrow,
  ShellCard,
  StatusBadge,
} from "@/app/orbit-ui";
import {
  type PortfolioComparisonPayload,
  fetchOrbitJson,
  formatDate,
  formatScore,
  publicApiHref,
} from "@/lib/orbit-api";

type ComparePageProps = {
  searchParams?: Promise<{ portfolioId?: string | string[] }>;
};

function normalizePortfolioIds(value: string | string[] | undefined): string[] {
  if (value === undefined) {
    return [];
  }
  const candidates = Array.isArray(value) ? value : [value];
  return Array.from(new Set(candidates.map((item) => item.trim()).filter(Boolean)));
}

function recommendationTone(
  recommendation: string | null | undefined,
): "default" | "success" | "warning" | "danger" {
  if (!recommendation) {
    return "default";
  }
  if (recommendation === "Strong Proceed") {
    return "success";
  }
  if (recommendation === "Proceed with Conditions" || recommendation === "Pilot Only") {
    return "warning";
  }
  return "danger";
}

function comparisonPath(portfolioIds: string[]): string {
  return `/api/v1/portfolios/compare?${portfolioIds.map((portfolioId) => `portfolio_id=${encodeURIComponent(portfolioId)}`).join("&")}`;
}

export default async function ComparePage({ searchParams }: ComparePageProps) {
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const portfolioIds = normalizePortfolioIds(resolvedSearchParams.portfolioId);
  const comparison =
    portfolioIds.length > 0
      ? await fetchOrbitJson<PortfolioComparisonPayload>(comparisonPath(portfolioIds))
      : null;

  return (
    <PageFrame>
      <section className="rounded-[32px] border border-orbit-pine/10 bg-white/80 p-8 shadow-panel backdrop-blur md:p-10">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <StatusBadge label="Milestone 14" />
              <StatusBadge label={`${portfolioIds.length} selected`} tone="warning" />
            </div>
            <div className="space-y-3">
              <p className="text-sm uppercase tracking-[0.22em] text-orbit-pine/70">Portfolio Comparison</p>
              <h1 className="text-4xl font-semibold tracking-tight text-orbit-ink md:text-5xl">
                Compare ORBIT committee outcomes side by side.
              </h1>
              <p className="max-w-3xl text-base leading-7 text-orbit-ink/75">
                This page reads the latest active committee state for each selected portfolio and links back to the
                approved detail, history, artifact inspection APIs, and the hardened Committee Mode playback page.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <ActionLink href="/">Back to Workspace</ActionLink>
          </div>
        </div>
      </section>

      {!portfolioIds.length ? (
        <ShellCard>
          <SectionEyebrow>No Portfolios Selected</SectionEyebrow>
          <p className="mt-4 text-sm leading-6 text-orbit-ink/70">
            Select one or more portfolios from the Milestone 14 workspace to compare their latest committee outcomes.
          </p>
        </ShellCard>
      ) : null}

      {portfolioIds.length === 1 ? (
        <ShellCard className="border-orbit-gold/40 bg-orbit-gold/10">
          <SectionEyebrow>Comparison Note</SectionEyebrow>
          <p className="mt-4 text-sm leading-6 text-orbit-ink/75">
            Comparison is more useful with two or more portfolios, but the page still shows the latest active lineage
            for the selected item.
          </p>
        </ShellCard>
      ) : null}

      {comparison ? (
        <>
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Compared"
              value={String(comparison.items.length)}
              detail="Selected portfolios are shown in the requested order."
            />
            <MetricCard
              label="Highest Score"
              value={formatScore(
                comparison.items.reduce<number | null>(
                  (current, item) =>
                    current === null ||
                    (item.latest_weighted_composite_score ?? Number.NEGATIVE_INFINITY) > current
                      ? item.latest_weighted_composite_score
                      : current,
                  null,
                ),
              )}
              detail="Ranking remains derived only from persisted active artifacts."
            />
            <MetricCard
              label="Most Conflicts"
              value={String(
                comparison.items.reduce(
                  (current, item) => Math.max(current, item.conflict_count),
                  0,
                ),
              )}
              detail="Conflict count is sourced from the latest persisted review artifact bundle."
            />
            <MetricCard
              label="Recheck Requests"
              value={String(
                comparison.items.reduce(
                  (current, item) => current + item.score_change_required_count,
                  0,
                ),
              )}
              detail="Re-synthesis only appears when persisted resolutions require score change review."
            />
          </section>

          <section className="grid gap-4 xl:grid-cols-2" data-testid="portfolio-comparison-grid">
            {comparison.items.map((item) => (
              <ShellCard key={item.portfolio.portfolio_id} data-testid={`comparison-card-${item.portfolio.portfolio_id}`}>
                <div className="space-y-5">
                  <div className="space-y-3">
                    <div className="flex flex-wrap items-center gap-3">
                      <StatusBadge label={item.portfolio.portfolio_status} tone="warning" />
                      <StatusBadge
                        label={item.latest_final_recommendation ?? "Not reviewed"}
                        tone={recommendationTone(item.latest_final_recommendation)}
                      />
                      {item.active_artifact_source ? (
                        <StatusBadge label={`${item.active_artifact_source} artifacts`} />
                      ) : null}
                    </div>
                    <div>
                      <div className="text-2xl font-semibold text-orbit-ink">{item.portfolio.portfolio_name}</div>
                      <p className="mt-2 text-sm leading-6 text-orbit-ink/70">
                        {item.portfolio.owner} · submitted {formatDate(item.portfolio.submitted_at)} · updated{" "}
                        {formatDate(item.latest_updated_at)}
                      </p>
                    </div>
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <MetricCard
                      label="Weighted Score"
                      value={formatScore(item.latest_weighted_composite_score)}
                      detail={item.latest_review_status ?? "No review has been recorded yet."}
                    />
                    <MetricCard
                      label="Committee Footprint"
                      value={`${item.agent_review_count} agents`}
                      detail={`${item.conflict_count} conflicts, ${item.score_change_required_count} score recheck requests.`}
                    />
                    <MetricCard
                      label="Lifecycle Counts"
                      value={`${item.review_run_count}/${item.debate_count}/${item.resynthesis_count}`}
                      detail="reviews / debates / re-syntheses"
                    />
                    <MetricCard
                      label="Latest Artifact"
                      value={item.active_artifact_source ?? "No run yet"}
                      detail={`Recommendation rank ${item.recommendation_rank ?? 0}`}
                    />
                  </div>

                  <div className="rounded-[24px] border border-orbit-pine/10 bg-orbit-mist/50 p-4">
                    <div className="text-xs uppercase tracking-[0.2em] text-orbit-pine/70">Latest Lineage</div>
                    <p className="mt-3 font-mono text-xs leading-6 text-orbit-ink/75">
                      {item.latest_lineage
                        ? `${item.latest_lineage.review_run_id}${item.latest_lineage.debate_id ? ` -> ${item.latest_lineage.debate_id}` : ""}${item.latest_lineage.resynthesis_id ? ` -> ${item.latest_lineage.resynthesis_id}` : ""}`
                        : "No lineage exists yet for this portfolio."}
                    </p>
                  </div>

                  <div className="flex flex-wrap gap-3">
                    <ActionLink href={`/portfolios/${item.portfolio.portfolio_id}`}>Portfolio Detail</ActionLink>
                    <ActionLink href={`/portfolios/${item.portfolio.portfolio_id}/history`} tone="muted">
                      Review History
                    </ActionLink>
                    {item.latest_lineage?.review_run_id ? (
                      <ActionLink href={`/review-runs/${item.latest_lineage.review_run_id}/committee`} tone="muted">
                        Committee Mode
                      </ActionLink>
                    ) : null}
                    {item.latest_lineage?.review_run_id ? (
                      <a
                        className="inline-flex rounded-full border border-orbit-pine/10 px-4 py-2 text-sm font-medium text-orbit-ink/75 transition hover:border-orbit-pine/30 hover:text-orbit-ink"
                        href={publicApiHref(`/api/v1/review-runs/${item.latest_lineage.review_run_id}/artifacts`)}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Artifact API
                      </a>
                    ) : null}
                  </div>
                </div>
              </ShellCard>
            ))}
          </section>
        </>
      ) : null}
    </PageFrame>
  );
}
