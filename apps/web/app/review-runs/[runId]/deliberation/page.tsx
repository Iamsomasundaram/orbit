import { notFound } from "next/navigation";

import {
  type ReviewRunDeliberationPayload,
  type ReviewRunDeliberationSummaryPayload,
  fetchOrbitJson,
  formatDate,
  formatScore,
  humanize,
  publicApiHref,
} from "@/lib/orbit-api";

import { ActionLink, MetricCard, PageFrame, SectionEyebrow, ShellCard, StatusBadge } from "@/app/orbit-ui";

type DeliberationPageProps = {
  params: Promise<{ runId: string }>;
};

function recommendationTone(recommendation: string): "default" | "success" | "warning" | "danger" {
  if (recommendation === "Strong Proceed") {
    return "success";
  }
  if (recommendation === "Proceed with Conditions" || recommendation === "Pilot Only") {
    return "warning";
  }
  if (recommendation === "High Risk" || recommendation === "Do Not Proceed") {
    return "danger";
  }
  return "default";
}

export default async function ReviewRunDeliberationPage({ params }: DeliberationPageProps) {
  const { runId } = await params;
  const [timeline, summary] = await Promise.all([
    fetchOrbitJson<ReviewRunDeliberationPayload>(`/api/v1/review-runs/${runId}/deliberation`),
    fetchOrbitJson<ReviewRunDeliberationSummaryPayload>(`/api/v1/review-runs/${runId}/deliberation/summary`),
  ]);

  if (!timeline || !summary) {
    notFound();
  }

  return (
    <PageFrame>
      <section className="rounded-[32px] border border-orbit-pine/10 bg-white/80 p-8 shadow-panel backdrop-blur md:p-10">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <StatusBadge label="Milestone 11" />
              <StatusBadge label={summary.active_artifact_source} tone="warning" />
              <StatusBadge label={summary.final_recommendation} tone={recommendationTone(summary.final_recommendation)} />
            </div>
            <div className="space-y-3">
              <p className="text-sm uppercase tracking-[0.22em] text-orbit-pine/70">Committee Deliberation</p>
              <h1 className="text-4xl font-semibold tracking-tight text-orbit-ink md:text-5xl">
                Review Timeline {timeline.review_run_id}
              </h1>
              <p className="max-w-3xl text-base leading-7 text-orbit-ink/75">
                This page reconstructs the ORBIT committee reasoning from persisted opening statements, conflict
                records, bounded debate artifacts, moderator synthesis, and the final verdict. No additional LLM calls
                are issued here.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <ActionLink href={`/portfolios/${timeline.portfolio_id}`}>Portfolio Detail</ActionLink>
            <ActionLink href={`/portfolios/${timeline.portfolio_id}/history?runId=${timeline.review_run_id}`} tone="muted">
              Review History
            </ActionLink>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Final Recommendation"
          value={summary.final_recommendation}
          detail={`Artifact source ${summary.active_artifact_source}`}
        />
        <MetricCard
          label="Weighted Score"
          value={formatScore(summary.weighted_composite_score)}
          detail={`Persisted sequence across ${timeline.entry_count} timeline entries.`}
        />
        <MetricCard
          label="Conflict Path"
          value={timeline.lineage.debate_id ? "debated" : "no debate"}
          detail={
            timeline.lineage.resynthesis_id
              ? `Re-synthesis ${timeline.lineage.resynthesis_id}`
              : "No re-synthesis session is attached to this review run."
          }
        />
        <MetricCard
          label="Lineage"
          value={timeline.portfolio_id}
          detail={timeline.lineage.review_run_id}
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        {summary.phase_summaries.map((phase) => (
          <ShellCard key={phase.phase}>
            <SectionEyebrow>{phase.label}</SectionEyebrow>
            <div className="mt-4 space-y-3">
              <div className="flex flex-wrap items-center gap-3">
                <StatusBadge label={`${phase.entry_count} entries`} />
                {phase.conflict_references.length ? (
                  <StatusBadge label={`${phase.conflict_references.length} conflict refs`} tone="warning" />
                ) : null}
              </div>
              <p className="text-sm leading-6 text-orbit-ink/75">{phase.representative_statement}</p>
            </div>
          </ShellCard>
        ))}
      </section>

      <ShellCard>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-3">
            <SectionEyebrow>Ordered Timeline</SectionEyebrow>
            <p className="max-w-3xl text-sm leading-6 text-orbit-ink/70">
              Statements are ordered by persisted sequence number, grouped into the five fixed committee phases, and
              linked back to conflict identifiers where applicable.
            </p>
          </div>
          <div className="flex flex-wrap gap-3 text-sm">
            <a className="underline decoration-orbit-pine/30 underline-offset-4" href={publicApiHref(`/api/v1/review-runs/${runId}/deliberation`)} target="_blank" rel="noreferrer">
              Timeline API
            </a>
            <a className="underline decoration-orbit-pine/30 underline-offset-4" href={publicApiHref(`/api/v1/review-runs/${runId}/deliberation/summary`)} target="_blank" rel="noreferrer">
              Summary API
            </a>
          </div>
        </div>

        <div className="mt-6 space-y-4">
          {timeline.entries.map((entry) => (
            <div key={entry.deliberation_entry_row_id} className="rounded-[24px] border border-orbit-pine/10 bg-white/75 p-5 shadow-panel backdrop-blur">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="space-y-3">
                  <div className="flex flex-wrap items-center gap-3">
                    <StatusBadge label={`#${entry.sequence_number}`} />
                    <StatusBadge label={humanize(entry.phase)} tone="warning" />
                    <StatusBadge label={humanize(entry.statement_type)} />
                    {entry.conflict_reference ? <StatusBadge label={entry.conflict_reference} tone="danger" /> : null}
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-orbit-ink">{entry.agent_role}</div>
                    <p className="mt-2 text-sm leading-6 text-orbit-ink/75">{entry.statement_text}</p>
                  </div>
                </div>
                <div className="text-sm leading-6 text-orbit-ink/65">
                  <div>Recorded {formatDate(entry.created_at)}</div>
                  {entry.agent_id ? <div>Agent ID {entry.agent_id}</div> : <div>System-generated phase entry</div>}
                </div>
              </div>
            </div>
          ))}
        </div>
      </ShellCard>
    </PageFrame>
  );
}
