import {
  ActionLink,
  FieldLabel,
  Input,
  MetricCard,
  PageFrame,
  SectionEyebrow,
  ShellCard,
  StatusBadge,
  SubmitButton,
  TextArea,
} from "@/app/orbit-ui";
import { getRuntimeConfig } from "@/lib/config";
import {
  type HealthPayload,
  type InfoPayload,
  type PersistenceCatalogPayload,
  type PortfolioRankingPayload,
  type PortfolioWorkspaceSummaryPayload,
  fetchOrbitJson,
  formatDate,
  formatScore,
  humanize,
} from "@/lib/orbit-api";

type HomePageProps = {
  searchParams?: Promise<{
    submissionError?: string;
    sortBy?: string;
    direction?: string;
  }>;
};

const SORT_OPTIONS = [
  { label: "Recently Updated", sortBy: "latest_updated_at", direction: "desc" },
  { label: "Strongest Score", sortBy: "weighted_composite_score", direction: "desc" },
  { label: "Best Recommendation", sortBy: "recommendation_rank", direction: "desc" },
  { label: "Highest Conflict", sortBy: "conflict_count", direction: "desc" },
  { label: "Needs Recheck", sortBy: "score_change_required_count", direction: "desc" },
] as const;

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

function normalizeSortBy(value: string | undefined): string {
  const match = SORT_OPTIONS.find((option) => option.sortBy === value);
  return match?.sortBy ?? "latest_updated_at";
}

function normalizeDirection(value: string | undefined): "asc" | "desc" {
  return value === "asc" ? "asc" : "desc";
}

function workspaceSummaryPath(sortBy: string, direction: "asc" | "desc"): string {
  return `/api/v1/portfolios/summary?sort_by=${encodeURIComponent(sortBy)}&direction=${encodeURIComponent(direction)}`;
}

export default async function HomePage({ searchParams }: HomePageProps) {
  const config = getRuntimeConfig();
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const sortBy = normalizeSortBy(resolvedSearchParams.sortBy);
  const direction = normalizeDirection(resolvedSearchParams.direction);
  const [apiReady, apiInfo, persistenceCatalog, workspaceSummary, portfolioRanking] = await Promise.all([
    fetchOrbitJson<HealthPayload>("/health/ready"),
    fetchOrbitJson<InfoPayload>("/api/v1/system/info"),
    fetchOrbitJson<PersistenceCatalogPayload>("/api/v1/system/persistence/schema"),
    fetchOrbitJson<PortfolioWorkspaceSummaryPayload>(workspaceSummaryPath(sortBy, direction)),
    fetchOrbitJson<PortfolioRankingPayload>("/api/v1/portfolios/ranking?sort_by=weighted_composite_score&direction=desc"),
  ]);

  return (
    <PageFrame>
      <section className="rounded-[32px] border border-orbit-pine/10 bg-white/80 p-8 shadow-panel backdrop-blur md:p-10">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="max-w-3xl space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <StatusBadge label={`Milestone ${config.milestone}`} />
              <StatusBadge label={apiInfo?.reference_runtime_stage ?? "archived-baseline"} tone="success" />
            </div>
            <h1 className="text-4xl font-semibold tracking-tight md:text-6xl">
              Run a parallel llm-backed ORBIT committee, compare portfolio outcomes, and replay the boardroom
              discussion from one workspace.
            </h1>
            <p className="max-w-2xl text-base leading-7 text-orbit-ink/75 md:text-lg">
              Milestone 12.1 sharpens Committee Mode with agent identity cards, conflict stance visualization,
              playback speed control, and token telemetry, while preserving the approved deterministic fallback,
              governance flow, and multi-portfolio workspace.
            </p>
          </div>
          <div className="rounded-3xl bg-orbit-ink px-5 py-4 text-orbit-mist">
            <div className="text-xs uppercase tracking-[0.24em] text-orbit-moss">Runtime Direction</div>
            <div className="mt-2 text-2xl font-semibold">Parallel LLM Committee</div>
            <div className="mt-1 text-sm text-orbit-mist/70">
              {apiInfo?.runtime_direction ?? "llm-backed-parallel-committee-engine-with-observable-boardroom-playback"}
            </div>
          </div>
        </div>
      </section>

      {resolvedSearchParams.submissionError ? (
        <ShellCard className="border-rose-200 bg-rose-50/90">
          <SectionEyebrow>Submission Error</SectionEyebrow>
          <p className="mt-3 text-sm leading-6 text-rose-800">{resolvedSearchParams.submissionError}</p>
        </ShellCard>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="API"
          value={apiReady?.status ?? "unreachable"}
          detail={
            apiReady
              ? `postgres=${apiReady.checks.find((item) => item.name === "postgres")?.status ?? "unknown"}, redis=${apiReady.checks.find((item) => item.name === "redis")?.status ?? "unknown"}`
              : "FastAPI readiness has not responded yet."
          }
        />
        <MetricCard
          label="Persistence"
          value={persistenceCatalog?.schema_version ?? apiInfo?.persistence_schema_version ?? "unknown"}
          detail={`${persistenceCatalog?.tables.length ?? apiInfo?.persistence_tables ?? 0} durable tables remain aligned to the Python contracts.`}
        />
        <MetricCard
          label="Workspace"
          value={String(workspaceSummary?.items.length ?? 0)}
          detail="All submitted portfolios can now be ranked, compared, and linked back to history and artifacts."
        />
        <MetricCard
          label="Parity"
          value={apiInfo?.reference_runtime_stage ?? "archived-baseline"}
          detail={`The Docker Compose baseline profile still validates deterministic Python output against the archived artifact set from ${apiInfo?.reference_runtime_archival_target_milestone ?? "Milestone 7.1"}.`}
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
        <ShellCard>
          <SectionEyebrow>Submit a New Idea</SectionEyebrow>
          <form action="/api/portfolios" method="post" className="mt-5 space-y-5">
            <div>
              <FieldLabel htmlFor="portfolio_name">Idea name</FieldLabel>
              <Input id="portfolio_name" name="portfolio_name" placeholder="ProcurePilot" required />
            </div>
            <div>
              <FieldLabel htmlFor="owner">Owner</FieldLabel>
              <Input id="owner" name="owner" placeholder="Somasundaram P" required />
            </div>
            <div>
              <FieldLabel htmlFor="description">Idea description</FieldLabel>
              <TextArea
                id="description"
                name="description"
                required
                rows={8}
                placeholder="Describe the user problem, proposed workflow, and why ORBIT should review this idea now."
              />
            </div>
            <div>
              <FieldLabel htmlFor="tags">Optional tags</FieldLabel>
              <Input id="tags" name="tags" placeholder="ai-saas, procurement, workflow" />
            </div>
            <div className="flex flex-col gap-3 border-t border-orbit-pine/10 pt-4 text-sm text-orbit-ink/70 md:flex-row md:items-center md:justify-between">
              <span>
                New idea submissions use a bounded portfolio identity strategy while preserving the approved
                canonicalization path.
              </span>
              <SubmitButton>Create Portfolio</SubmitButton>
            </div>
          </form>
        </ShellCard>

        <ShellCard className="bg-orbit-pine text-orbit-mist">
          <SectionEyebrow>Priority Snapshot</SectionEyebrow>
          <div className="mt-5 space-y-4">
            {portfolioRanking?.items.length ? (
              portfolioRanking.items.slice(0, 3).map((item) => (
                <div key={item.portfolio.portfolio_id} className="rounded-[24px] border border-white/10 bg-white/6 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <StatusBadge label={`Rank ${item.rank}`} />
                    <StatusBadge
                      label={item.latest_final_recommendation ?? "Not reviewed"}
                      tone={recommendationTone(item.latest_final_recommendation)}
                    />
                  </div>
                  <div className="mt-3 text-lg font-semibold">{item.portfolio.portfolio_name}</div>
                  <p className="mt-2 text-sm leading-6 text-orbit-mist/75">
                    {item.portfolio.owner} · updated {formatDate(item.latest_updated_at)}
                  </p>
                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    <div className="rounded-2xl border border-white/10 px-4 py-3">
                      <div className="text-xs uppercase tracking-[0.18em] text-orbit-moss">Weighted Score</div>
                      <div className="mt-2 text-xl font-semibold">{formatScore(item.latest_weighted_composite_score)}</div>
                    </div>
                    <div className="rounded-2xl border border-white/10 px-4 py-3">
                      <div className="text-xs uppercase tracking-[0.18em] text-orbit-moss">Lineage State</div>
                      <div className="mt-2 text-xl font-semibold">{item.active_artifact_source ?? "No run yet"}</div>
                    </div>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-3">
                    <a
                      className="inline-flex rounded-full border border-white/15 px-4 py-2 text-sm font-medium text-orbit-mist transition hover:border-white/35"
                      href={`/portfolios/${item.portfolio.portfolio_id}`}
                    >
                      Portfolio Detail
                    </a>
                    <a
                      className="inline-flex rounded-full border border-white/15 px-4 py-2 text-sm font-medium text-orbit-mist transition hover:border-white/35"
                      href={`/portfolios/${item.portfolio.portfolio_id}/history`}
                    >
                      Review History
                    </a>
                    {item.latest_lineage?.review_run_id ? (
                      <a
                        className="inline-flex rounded-full border border-white/15 px-4 py-2 text-sm font-medium text-orbit-mist transition hover:border-white/35"
                        href={`/review-runs/${item.latest_lineage.review_run_id}/committee`}
                      >
                        Committee Mode
                      </a>
                    ) : null}
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm leading-6 text-orbit-mist/78">
                Ranking appears here once portfolios have been reviewed through the approved committee path.
              </p>
            )}
          </div>
        </ShellCard>
      </section>

      <ShellCard>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-3">
            <SectionEyebrow>Portfolio Workspace</SectionEyebrow>
            <p className="max-w-3xl text-sm leading-6 text-orbit-ink/70">
              Sort all submitted portfolios by committee outcome, select multiple ideas for side-by-side comparison,
              and jump directly into the persisted history and artifact surfaces for each one.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {SORT_OPTIONS.map((option) => {
              const isActive = option.sortBy === sortBy && option.direction === direction;
              return (
                <a
                  key={`${option.sortBy}:${option.direction}`}
                  href={`/?sortBy=${encodeURIComponent(option.sortBy)}&direction=${encodeURIComponent(option.direction)}`}
                  className={
                    isActive
                      ? "inline-flex rounded-full bg-orbit-pine px-4 py-2 text-sm font-medium text-orbit-mist"
                      : "inline-flex rounded-full border border-orbit-pine/10 px-4 py-2 text-sm font-medium text-orbit-ink/75 transition hover:border-orbit-pine/30 hover:text-orbit-ink"
                  }
                >
                  {option.label}
                </a>
              );
            })}
          </div>
        </div>

        <form action="/compare" method="get" className="mt-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm leading-6 text-orbit-ink/70">
              Current sort: <span className="font-medium text-orbit-ink">{humanize(sortBy)}</span> ({direction}).
            </p>
            <SubmitButton>Compare Selected Portfolios</SubmitButton>
          </div>

          {workspaceSummary?.items.length ? (
            <div className="space-y-4">
              {workspaceSummary.items.map((item) => (
                <div
                  key={item.portfolio.portfolio_id}
                  className="rounded-[24px] border border-orbit-pine/10 bg-white/75 p-5 shadow-panel backdrop-blur"
                >
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div className="space-y-3">
                      <div className="flex flex-wrap items-center gap-3">
                        <input
                          type="checkbox"
                          name="portfolioId"
                          value={item.portfolio.portfolio_id}
                          className="h-4 w-4 rounded border-orbit-pine/30 text-orbit-pine focus:ring-orbit-gold/35"
                        />
                        <StatusBadge label={humanize(item.portfolio.portfolio_status)} tone="warning" />
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
                      <p className="font-mono text-xs leading-6 text-orbit-ink/65">
                        {item.latest_lineage
                          ? `${item.latest_lineage.review_run_id}${item.latest_lineage.debate_id ? ` -> ${item.latest_lineage.debate_id}` : ""}${item.latest_lineage.resynthesis_id ? ` -> ${item.latest_lineage.resynthesis_id}` : ""}`
                          : "No review lineage has been created yet."}
                      </p>
                    </div>
                    <div className="grid gap-3 text-sm text-orbit-ink/75 md:grid-cols-2 xl:grid-cols-3">
                      <div className="rounded-2xl border border-orbit-pine/10 px-4 py-3">
                        <div className="text-xs uppercase tracking-[0.18em] text-orbit-pine/70">Weighted Score</div>
                        <div className="mt-2 text-xl font-semibold text-orbit-ink">
                          {formatScore(item.latest_weighted_composite_score)}
                        </div>
                      </div>
                      <div className="rounded-2xl border border-orbit-pine/10 px-4 py-3">
                        <div className="text-xs uppercase tracking-[0.18em] text-orbit-pine/70">Structured Evidence</div>
                        <div className="mt-2 text-xl font-semibold text-orbit-ink">
                          {item.agent_review_count} agents
                        </div>
                      </div>
                      <div className="rounded-2xl border border-orbit-pine/10 px-4 py-3">
                        <div className="text-xs uppercase tracking-[0.18em] text-orbit-pine/70">Conflict State</div>
                        <div className="mt-2 text-xl font-semibold text-orbit-ink">
                          {item.conflict_count} conflicts
                        </div>
                      </div>
                      <div className="rounded-2xl border border-orbit-pine/10 px-4 py-3">
                        <div className="text-xs uppercase tracking-[0.18em] text-orbit-pine/70">Recheck Requests</div>
                        <div className="mt-2 text-xl font-semibold text-orbit-ink">
                          {item.score_change_required_count}
                        </div>
                      </div>
                      <div className="rounded-2xl border border-orbit-pine/10 px-4 py-3">
                        <div className="text-xs uppercase tracking-[0.18em] text-orbit-pine/70">Review Cycles</div>
                        <div className="mt-2 text-xl font-semibold text-orbit-ink">
                          {item.review_run_count}/{item.debate_count}/{item.resynthesis_count}
                        </div>
                        <p className="mt-2 text-xs leading-5 text-orbit-ink/60">reviews / debates / re-syntheses</p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <ActionLink href={`/portfolios/${item.portfolio.portfolio_id}`}>Portfolio Detail</ActionLink>
                        <ActionLink href={`/portfolios/${item.portfolio.portfolio_id}/history`} tone="muted">
                          Review History
                        </ActionLink>
                        {item.latest_lineage?.review_run_id ? (
                          <ActionLink href={`/review-runs/${item.latest_lineage.review_run_id}/committee`} tone="muted">
                            Committee Mode
                          </ActionLink>
                        ) : null}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm leading-6 text-orbit-ink/70">
              No portfolios are stored yet. Submit an idea above to create the first entry in the Milestone 12.1
              comparison and boardroom playback workspace.
            </p>
          )}
        </form>
      </ShellCard>
    </PageFrame>
  );
}
