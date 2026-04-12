import { notFound } from "next/navigation";

import {
  type ArtifactInspectionPayload,
  type ReviewRunDeliberationPayload,
  type ReviewRunDetailPayload,
  fetchOrbitJson,
  formatCostUsd,
  formatDate,
  formatInteger,
  formatScore,
  publicApiHref,
} from "@/lib/orbit-api";

import { ActionLink, MetricCard, PageFrame, SectionEyebrow, ShellCard, StatusBadge } from "@/app/orbit-ui";

type ReviewRunPageProps = {
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

export default async function ReviewRunPage({ params }: ReviewRunPageProps) {
  const { runId } = await params;
  const [detail, artifacts, timeline] = await Promise.all([
    fetchOrbitJson<ReviewRunDetailPayload>(`/api/v1/review-runs/${runId}`),
    fetchOrbitJson<ArtifactInspectionPayload>(`/api/v1/review-runs/${runId}/artifacts`),
    fetchOrbitJson<ReviewRunDeliberationPayload>(`/api/v1/review-runs/${runId}/deliberation`),
  ]);

  if (!detail || !artifacts || !timeline) {
    notFound();
  }

  return (
    <PageFrame>
      <section className="rounded-[32px] border border-orbit-pine/10 bg-white/80 p-8 shadow-panel backdrop-blur md:p-10">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <StatusBadge label="Milestone 13" />
              <StatusBadge label={detail.review_run.review_status} tone="warning" />
              <StatusBadge
                label={artifacts.active_scorecard.final_recommendation}
                tone={recommendationTone(artifacts.active_scorecard.final_recommendation)}
              />
              <StatusBadge label={`${artifacts.artifact_selection.active_artifact_source} artifacts`} />
            </div>
            <div className="space-y-3">
              <p className="text-sm uppercase tracking-[0.22em] text-orbit-pine/70">Review Run Detail</p>
              <h1 className="text-4xl font-semibold tracking-tight text-orbit-ink md:text-5xl">
                {detail.review_run.run_id}
              </h1>
              <p className="max-w-3xl text-base leading-7 text-orbit-ink/75">
                This page surfaces the active committee result, persisted runtime telemetry, fallback state, conflict
                metadata, and audit events for a single review cycle without recomputing any committee reasoning.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <ActionLink href={`/review-runs/${runId}/committee`}>Committee Mode</ActionLink>
            <ActionLink href={`/review-runs/${runId}/deliberation`} tone="muted">
              Static Timeline
            </ActionLink>
            <ActionLink href={`/portfolios/${detail.portfolio.portfolio_id}/history?runId=${runId}`} tone="muted">
              Review History
            </ActionLink>
          </div>
        </div>
      </section>

      {timeline.runtime_metadata.fallback_applied ? (
        <ShellCard className="border-amber-200 bg-amber-50/90">
          <SectionEyebrow>Deterministic Fallback</SectionEyebrow>
          <p className="mt-3 text-sm leading-6 text-amber-900">
            Requested runtime {timeline.runtime_metadata.requested_runtime_mode} via{" "}
            {timeline.runtime_metadata.requested_provider}/{timeline.runtime_metadata.requested_model_name} fell back
            to deterministic execution because of {timeline.runtime_metadata.fallback_category ?? "an llm runtime error"}
            .
          </p>
          {timeline.runtime_metadata.fallback_reason ? (
            <p className="mt-2 text-sm leading-6 text-amber-800">{timeline.runtime_metadata.fallback_reason}</p>
          ) : null}
        </ShellCard>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Weighted Score"
          value={formatScore(artifacts.active_scorecard.weighted_composite_score)}
          detail={`Recommendation ${artifacts.active_scorecard.final_recommendation}`}
        />
        <MetricCard
          label="Conflicts"
          value={String(artifacts.conflict_count)}
          detail={`${artifacts.agent_review_count} agent reviews were persisted for this run.`}
        />
        <MetricCard
          label="Runtime Mode"
          value={timeline.runtime_metadata.effective_runtime_mode}
          detail={`Requested ${timeline.runtime_metadata.requested_runtime_mode} via ${timeline.runtime_metadata.requested_provider}`}
        />
        <MetricCard
          label="Tokens"
          value={formatInteger(timeline.runtime_metadata.total_tokens)}
          detail={`Core ${timeline.runtime_metadata.core_executed_count} / specialists ${timeline.runtime_metadata.activated_specialist_count} / passive ${timeline.runtime_metadata.passive_observer_count}`}
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
        <ShellCard className="bg-orbit-pine text-orbit-mist">
          <SectionEyebrow>Committee Runtime Telemetry</SectionEyebrow>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <div className="rounded-[24px] border border-white/10 bg-white/6 px-4 py-4">
              <div className="text-xs uppercase tracking-[0.2em] text-orbit-moss">Effective Runtime</div>
              <div className="mt-2 text-xl font-semibold">{timeline.runtime_metadata.effective_runtime_mode}</div>
              <div className="mt-2 text-sm text-orbit-mist/72">
                {timeline.runtime_metadata.model_provider} / {timeline.runtime_metadata.model_name}
              </div>
            </div>
            <div className="rounded-[24px] border border-white/10 bg-white/6 px-4 py-4">
              <div className="text-xs uppercase tracking-[0.2em] text-orbit-moss">Requested Runtime</div>
              <div className="mt-2 text-xl font-semibold">{timeline.runtime_metadata.requested_runtime_mode}</div>
              <div className="mt-2 text-sm text-orbit-mist/72">
                {timeline.runtime_metadata.requested_provider} / {timeline.runtime_metadata.requested_model_name}
              </div>
            </div>
            <div className="rounded-[24px] border border-white/10 bg-white/6 px-4 py-4">
              <div className="text-xs uppercase tracking-[0.2em] text-orbit-moss">Committee Runtime</div>
              <div className="mt-2 text-xl font-semibold">
                {formatInteger(timeline.runtime_metadata.total_duration_ms)} ms
              </div>
              <div className="mt-2 text-sm text-orbit-mist/72">
                {timeline.runtime_metadata.agent_count} persisted agents
              </div>
            </div>
            <div className="rounded-[24px] border border-white/10 bg-white/6 px-4 py-4">
              <div className="text-xs uppercase tracking-[0.2em] text-orbit-moss">Token Footprint</div>
              <div className="mt-2 text-xl font-semibold">
                {formatInteger(timeline.runtime_metadata.total_tokens)}
              </div>
              <div className="mt-2 text-sm text-orbit-mist/72">
                in {formatInteger(timeline.runtime_metadata.total_input_tokens)} / out{" "}
                {formatInteger(timeline.runtime_metadata.total_output_tokens)}
              </div>
            </div>
            <div className="rounded-[24px] border border-white/10 bg-white/6 px-4 py-4 md:col-span-2">
              <div className="text-xs uppercase tracking-[0.2em] text-orbit-moss">Adaptive Routing</div>
              <div className="mt-2 text-xl font-semibold">
                {timeline.runtime_metadata.routing_strategy_version ?? "legacy routing"}
              </div>
              <div className="mt-2 text-sm text-orbit-mist/72">
                Core {timeline.runtime_metadata.core_executed_count}, specialists {timeline.runtime_metadata.activated_specialist_count}, passive observers {timeline.runtime_metadata.passive_observer_count}, estimated cost {formatCostUsd(timeline.runtime_metadata.estimated_cost_usd)}
              </div>
              {timeline.runtime_metadata.routing_signals.length ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {timeline.runtime_metadata.routing_signals.map((signal) => (
                    <StatusBadge key={signal} label={signal.replaceAll("_", " ")} tone="warning" />
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        </ShellCard>

        <ShellCard>
          <SectionEyebrow>Inspection Links</SectionEyebrow>
          <div className="mt-5 space-y-3 text-sm leading-6">
            <a className="block underline decoration-orbit-pine/30 underline-offset-4" href={publicApiHref(`/api/v1/review-runs/${runId}`)} target="_blank" rel="noreferrer">
              Open review run detail API
            </a>
            <a className="block underline decoration-orbit-pine/30 underline-offset-4" href={publicApiHref(`/api/v1/review-runs/${runId}/artifacts`)} target="_blank" rel="noreferrer">
              Open artifact inspection API
            </a>
            <a className="block underline decoration-orbit-pine/30 underline-offset-4" href={publicApiHref(`/api/v1/review-runs/${runId}/deliberation`)} target="_blank" rel="noreferrer">
              Open deliberation API
            </a>
          </div>
          <p className="mt-5 text-sm leading-6 text-orbit-ink/72">
            Started {formatDate(detail.review_run.started_at)} and completed{" "}
            {formatDate(detail.review_run.completed_at ?? detail.review_run.created_at)}.
          </p>
        </ShellCard>
      </section>

      <ShellCard data-testid="review-run-conflicts">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-3">
            <SectionEyebrow>Conflict Metadata</SectionEyebrow>
            <p className="max-w-3xl text-sm leading-6 text-orbit-ink/70">
              Conflict cards show the persisted structured metadata used by Committee Mode and artifact inspection.
            </p>
          </div>
          <StatusBadge label={`${timeline.conflicts.length} conflicts`} tone="warning" />
        </div>
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          {timeline.conflicts.map((conflict) => (
            <div key={conflict.conflict_id} className="rounded-[24px] border border-orbit-pine/10 bg-white/75 p-5 shadow-panel">
              <div className="flex flex-wrap items-center gap-3">
                <StatusBadge label={conflict.conflict_payload.conflict_category ?? "uncategorized"} tone="warning" />
                <StatusBadge label={conflict.severity} tone={conflict.severity === "high" ? "danger" : "warning"} />
              </div>
              <div className="mt-4 text-lg font-semibold text-orbit-ink">{conflict.topic}</div>
              <p className="mt-2 text-sm leading-6 text-orbit-ink/75">
                {conflict.conflict_payload.conflict_reason ?? conflict.conflict_payload.trigger_reason}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {conflict.conflict_payload.conflicting_agents.map((agentId) => (
                  <StatusBadge key={agentId} label={agentId} />
                ))}
              </div>
            </div>
          ))}
        </div>
      </ShellCard>

      <ShellCard>
        <SectionEyebrow>Review Audit Scope</SectionEyebrow>
        <div className="mt-5 space-y-3">
          {artifacts.review_audit_events.map((event) => (
            <div key={event.event_id} className="rounded-[20px] border border-orbit-pine/10 bg-white/75 px-4 py-4 text-sm leading-6 text-orbit-ink/75">
              <div className="flex flex-wrap items-center gap-3">
                <StatusBadge label={event.action} />
                <span>{formatDate(event.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      </ShellCard>
    </PageFrame>
  );
}
