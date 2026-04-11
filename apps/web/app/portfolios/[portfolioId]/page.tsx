import { notFound } from "next/navigation";

import {
  type ArtifactInspectionPayload,
  type PortfolioDetailPayload,
  type PortfolioHistoryPayload,
  fetchOrbitJson,
  formatScore,
  humanize,
  publicApiHref,
} from "@/lib/orbit-api";

import { ActionLink, MetricCard, PageFrame, SectionEyebrow, ShellCard, StatusBadge, SubmitButton } from "@/app/orbit-ui";

type DetailPageProps = {
  params: Promise<{ portfolioId: string }>;
  searchParams?: Promise<{ reviewError?: string }>;
};

function formatSubmittedAt(value: string | null | undefined): string {
  if (!value) {
    return "Not available";
  }
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return new Intl.DateTimeFormat("en-IN", {
      dateStyle: "medium",
      timeZone: "UTC",
    }).format(new Date(`${value}T00:00:00Z`));
  }
  return value;
}

function toneForRecommendation(recommendation: string | null): "default" | "success" | "warning" | "danger" {
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

export default async function PortfolioDetailPage({ params, searchParams }: DetailPageProps) {
  const { portfolioId } = await params;
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const [portfolio, history] = await Promise.all([
    fetchOrbitJson<PortfolioDetailPayload>(`/api/v1/portfolios/${portfolioId}`),
    fetchOrbitJson<PortfolioHistoryPayload>(`/api/v1/portfolios/${portfolioId}/history`),
  ]);

  if (!portfolio || !history) {
    notFound();
  }

  const latestArtifacts =
    history.latest_review_run_id != null
      ? await fetchOrbitJson<ArtifactInspectionPayload>(`/api/v1/review-runs/${history.latest_review_run_id}/artifacts`)
      : null;

  return (
    <PageFrame>
      <section className="rounded-[32px] border border-orbit-pine/10 bg-white/80 p-8 shadow-panel backdrop-blur md:p-10">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <StatusBadge label="Milestone 10" />
              <StatusBadge label={humanize(portfolio.portfolio.portfolio_status)} tone="warning" />
            </div>
            <div className="space-y-3">
              <p className="text-sm uppercase tracking-[0.22em] text-orbit-pine/70">Portfolio Detail</p>
              <h1 className="text-4xl font-semibold tracking-tight text-orbit-ink md:text-5xl">
                {portfolio.portfolio.portfolio_name}
              </h1>
              <p className="max-w-2xl text-base leading-7 text-orbit-ink/75">
                Submitted by {portfolio.portfolio.owner} on {formatSubmittedAt(portfolio.portfolio.submitted_at)} as a{" "}
                {humanize(portfolio.portfolio.portfolio_type)}. This page is the operational launch point for the ORBIT
                committee workflow.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <form action={`/api/portfolios/${portfolioId}/review-runs`} method="post">
              <SubmitButton>Run ORBIT Review</SubmitButton>
            </form>
            <ActionLink href={`/portfolios/${portfolioId}/history`} tone="muted">
              View Review History
            </ActionLink>
          </div>
        </div>
      </section>

      {resolvedSearchParams.reviewError ? (
        <ShellCard className="border-rose-200 bg-rose-50/90">
          <SectionEyebrow>Review Error</SectionEyebrow>
          <p className="mt-3 text-sm leading-6 text-rose-800">{resolvedSearchParams.reviewError}</p>
        </ShellCard>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Owner"
          value={portfolio.portfolio.owner}
          detail={`Portfolio ID ${portfolio.portfolio.portfolio_id}`}
        />
        <MetricCard
          label="Canonical Sections"
          value={String(portfolio.canonical_portfolio.section_count)}
          detail={`Schema ${portfolio.canonical_portfolio.schema_version}`}
        />
        <MetricCard
          label="Source Documents"
          value={String(portfolio.source_documents.length)}
          detail={`${portfolio.audit_events.length} ingestion and lifecycle audit events are currently recorded.`}
        />
        <MetricCard
          label="Review History"
          value={`${history.review_run_count} runs`}
          detail={`${history.debate_count} debates and ${history.resynthesis_count} re-syntheses are linked through lineage.`}
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <ShellCard>
          <SectionEyebrow>Latest Committee Result</SectionEyebrow>
          {latestArtifacts ? (
            <div className="mt-4 space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <StatusBadge
                  label={latestArtifacts.active_scorecard.final_recommendation}
                  tone={toneForRecommendation(latestArtifacts.active_scorecard.final_recommendation)}
                />
                <StatusBadge label={`${latestArtifacts.artifact_selection.active_artifact_source} artifacts`} />
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <MetricCard
                  label="Weighted Score"
                  value={formatScore(latestArtifacts.active_scorecard.weighted_composite_score)}
                  detail={`Review run ${latestArtifacts.review_run.run_id}`}
                />
                <MetricCard
                  label="Structured Evidence"
                  value={`${latestArtifacts.agent_review_count} agents`}
                  detail={`${latestArtifacts.conflict_count} conflicts were detected in the committee pass.`}
                />
              </div>
              <p className="text-sm leading-6 text-orbit-ink/70">
                Debate state: {latestArtifacts.debate_session?.debate_status ?? "not started"}. Re-synthesis state:{" "}
                {latestArtifacts.resynthesis_session?.resynthesis_status ?? "not needed"}.
              </p>
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-orbit-ink/70">
              No review run has been recorded yet. Use the review action above to execute the existing deterministic
              ORBIT committee pipeline for this portfolio.
            </p>
          )}
        </ShellCard>

        <ShellCard className="bg-orbit-pine text-orbit-mist">
          <SectionEyebrow>Inspection Links</SectionEyebrow>
          <div className="mt-4 space-y-3 text-sm leading-6">
            <a className="block underline decoration-orbit-moss underline-offset-4" href={publicApiHref(`/api/v1/portfolios/${portfolioId}`)} target="_blank" rel="noreferrer">
              Open portfolio detail API
            </a>
            <a className="block underline decoration-orbit-moss underline-offset-4" href={publicApiHref(`/api/v1/portfolios/${portfolioId}/history`)} target="_blank" rel="noreferrer">
              Open portfolio history API
            </a>
            {history.latest_review_run_id ? (
              <a className="block underline decoration-orbit-moss underline-offset-4" href={publicApiHref(`/api/v1/review-runs/${history.latest_review_run_id}/artifacts`)} target="_blank" rel="noreferrer">
                Open latest artifact inspection API
              </a>
            ) : null}
          </div>
          <p className="mt-5 text-sm leading-6 text-orbit-mist/80">
            The active result shown here always comes from the persisted artifact-selection state, so original and
            re-synthesized committee outputs remain distinguishable.
          </p>
        </ShellCard>
      </section>
    </PageFrame>
  );
}
