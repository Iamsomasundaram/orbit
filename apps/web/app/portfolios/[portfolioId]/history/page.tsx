import { notFound } from "next/navigation";

import {
  type ArtifactInspectionPayload,
  type PortfolioHistoryPayload,
  fetchOrbitJson,
  formatDate,
  formatScore,
  publicApiHref,
} from "@/lib/orbit-api";

import { ActionLink, MetricCard, PageFrame, SectionEyebrow, ShellCard, StatusBadge, SubmitButton } from "@/app/orbit-ui";

type HistoryPageProps = {
  params: Promise<{ portfolioId: string }>;
  searchParams?: Promise<{ created?: string; runId?: string }>;
};

function artifactTone(source: string): "default" | "success" | "warning" {
  return source === "resynthesized" ? "warning" : "success";
}

export default async function PortfolioHistoryPage({ params, searchParams }: HistoryPageProps) {
  const { portfolioId } = await params;
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const history = await fetchOrbitJson<PortfolioHistoryPayload>(`/api/v1/portfolios/${portfolioId}/history`);

  if (!history) {
    notFound();
  }

  const highlightedRunId = resolvedSearchParams.runId ?? history.latest_review_run_id ?? undefined;
  const latestArtifacts =
    history.latest_review_run_id != null
      ? await fetchOrbitJson<ArtifactInspectionPayload>(`/api/v1/review-runs/${history.latest_review_run_id}/artifacts`)
      : null;

  return (
    <PageFrame>
      <section className="rounded-[32px] border border-orbit-pine/10 bg-white/80 p-8 shadow-panel backdrop-blur md:p-10">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <StatusBadge label="Milestone 12" />
              <StatusBadge label={`${history.review_run_count} review ${history.review_run_count === 1 ? "run" : "runs"}`} tone="warning" />
            </div>
            <div className="space-y-3">
              <p className="text-sm uppercase tracking-[0.22em] text-orbit-pine/70">Portfolio History</p>
              <h1 className="text-4xl font-semibold tracking-tight text-orbit-ink md:text-5xl">
                {history.portfolio.portfolio_name}
              </h1>
              <p className="max-w-3xl text-base leading-7 text-orbit-ink/75">
                Review lineage is persisted across the portfolio, review run, debate session, and re-synthesis session.
                The active artifact state remains explicit for every cycle.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <form action={`/api/portfolios/${portfolioId}/review-runs`} method="post">
              <SubmitButton>Run ORBIT Review</SubmitButton>
            </form>
            <ActionLink href={`/portfolios/${portfolioId}`} tone="muted">
              Portfolio Detail
            </ActionLink>
            {history.latest_review_run_id ? (
              <ActionLink href={`/review-runs/${history.latest_review_run_id}/committee`} tone="muted">
                Committee Mode
              </ActionLink>
            ) : null}
          </div>
        </div>
      </section>

      {resolvedSearchParams.created ? (
        <ShellCard className="border-emerald-200 bg-emerald-50/90">
          <SectionEyebrow>Submission Recorded</SectionEyebrow>
          <p className="mt-3 text-sm leading-6 text-emerald-800">
            The portfolio has been canonicalized and persisted. Run the ORBIT review when you are ready to generate the
            first committee result.
          </p>
        </ShellCard>
      ) : null}

      {resolvedSearchParams.runId ? (
        <ShellCard className="border-orbit-gold/40 bg-orbit-gold/10">
          <SectionEyebrow>Review Completed</SectionEyebrow>
          <p className="mt-3 text-sm leading-6 text-orbit-ink/80">
            Review run <span className="font-mono text-xs">{resolvedSearchParams.runId}</span> completed synchronously.
            Debate and re-synthesis were executed automatically where the persisted committee rules required them.
          </p>
        </ShellCard>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Latest Recommendation"
          value={latestArtifacts?.active_scorecard.final_recommendation ?? "No runs yet"}
          detail={
            latestArtifacts
              ? `Artifact source ${latestArtifacts.artifact_selection.active_artifact_source}`
              : "The first review run has not been created yet."
          }
        />
        <MetricCard
          label="Weighted Score"
          value={formatScore(latestArtifacts?.active_scorecard.weighted_composite_score)}
          detail={
            latestArtifacts
              ? `${latestArtifacts.agent_review_count} agents, ${latestArtifacts.conflict_count} conflicts`
              : "Committee metrics appear after the first review run."
          }
        />
        <MetricCard
          label="Debates"
          value={String(history.debate_count)}
          detail={`${history.resynthesis_count} re-syntheses are currently attached to this portfolio.`}
        />
        <MetricCard
          label="Canonical Shape"
          value={`${history.canonical_portfolio.section_count} sections`}
          detail={`${history.source_documents.length} stored source documents back the current portfolio record.`}
        />
      </section>

      {history.items.length === 0 ? (
        <ShellCard>
          <SectionEyebrow>No Review Lineage Yet</SectionEyebrow>
          <p className="mt-4 text-sm leading-6 text-orbit-ink/70">
            The portfolio exists in the persistence layer, but no review run has been executed. Use the ORBIT review
            action above to generate the first review, debate, and optional re-synthesis cycle.
          </p>
        </ShellCard>
      ) : (
        <section className="space-y-4">
          {history.items.map((item) => {
            const isHighlighted = highlightedRunId === item.review_run.run_id;
            return (
              <ShellCard key={item.review_run.run_id} className={isHighlighted ? "border-orbit-gold/50 bg-orbit-gold/10" : ""}>
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="space-y-3">
                    <div className="flex flex-wrap items-center gap-3">
                      <StatusBadge label={item.review_run.review_status} tone="success" />
                      <StatusBadge label={`${item.artifact_selection.active_artifact_source} artifacts`} tone={artifactTone(item.artifact_selection.active_artifact_source)} />
                      {item.debate ? <StatusBadge label={item.debate.debate_status} tone="warning" /> : null}
                      {item.resynthesis ? <StatusBadge label={item.resynthesis.resynthesis_status} tone="warning" /> : null}
                    </div>
                    <div>
                      <div className="text-sm uppercase tracking-[0.2em] text-orbit-pine/70">Lineage</div>
                      <div className="mt-2 font-mono text-xs leading-6 text-orbit-ink/80">
                        {item.lineage.review_run_id}
                        {item.lineage.debate_id ? ` -> ${item.lineage.debate_id}` : ""}
                        {item.lineage.resynthesis_id ? ` -> ${item.lineage.resynthesis_id}` : ""}
                      </div>
                    </div>
                    <p className="text-sm leading-6 text-orbit-ink/75">
                      Completed {formatDate(item.review_run.created_at)} with recommendation {item.active_final_recommendation} at a weighted composite score of {formatScore(item.active_weighted_composite_score)}.
                    </p>
                  </div>
                  <div className="grid gap-3 text-sm text-orbit-ink/75 md:grid-cols-2">
                    <a className="rounded-2xl border border-orbit-pine/10 px-4 py-3 hover:border-orbit-pine/30" href={publicApiHref(`/api/v1/review-runs/${item.review_run.run_id}/artifacts`)} target="_blank" rel="noreferrer">
                      Review artifacts
                    </a>
                    <ActionLink href={`/review-runs/${item.review_run.run_id}/committee`} tone="muted">
                      Committee Mode
                    </ActionLink>
                    {item.debate ? (
                      <a className="rounded-2xl border border-orbit-pine/10 px-4 py-3 hover:border-orbit-pine/30" href={publicApiHref(`/api/v1/debates/${item.debate.debate_id}/artifacts`)} target="_blank" rel="noreferrer">
                        Debate artifacts
                      </a>
                    ) : null}
                    {item.resynthesis ? (
                      <a className="rounded-2xl border border-orbit-pine/10 px-4 py-3 hover:border-orbit-pine/30" href={publicApiHref(`/api/v1/re-syntheses/${item.resynthesis.resynthesis_id}/artifacts`)} target="_blank" rel="noreferrer">
                        Re-synthesis artifacts
                      </a>
                    ) : null}
                    <div className="rounded-2xl border border-orbit-pine/10 px-4 py-3">
                      Score recheck required count: {item.artifact_selection.score_change_required_count}
                    </div>
                  </div>
                </div>
              </ShellCard>
            );
          })}
        </section>
      )}
    </PageFrame>
  );
}
