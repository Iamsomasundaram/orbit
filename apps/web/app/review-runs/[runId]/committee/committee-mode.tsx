"use client";

import { startTransition, useDeferredValue, useEffect, useState } from "react";

import {
  type AgentRuntimeTelemetryPayload,
  type AgentReasoningPayload,
  type ConflictPersistencePayload,
  type DeliberationEntryPayload,
  type ReviewRunDeliberationPayload,
  type ReviewRunDeliberationSummaryPayload,
  type ReviewRunValidationPayload,
  formatCostUsd,
  formatDate,
  formatInteger,
  formatScore,
  humanize,
  publicApiHref,
} from "@/lib/orbit-api";

import { ActionLink, MetricCard, PageFrame, SectionEyebrow, ShellCard, StatusBadge } from "@/app/orbit-ui";

type CommitteeModeProps = {
  timeline: ReviewRunDeliberationPayload;
  summary: ReviewRunDeliberationSummaryPayload;
  validation: ReviewRunValidationPayload | null;
};

type Tone = "default" | "success" | "warning" | "danger";
type PlaybackSpeed = "0.5x" | "1x" | "2x" | "5x" | "instant";
type CommitteeStance = "support" | "neutral" | "oppose";

const PHASE_ORDER = [
  "opening_statements",
  "conflict_identification",
  "conflict_discussion",
  "moderator_synthesis",
  "final_verdict",
] as const;

const PLAYBACK_SPEEDS: Array<{ value: PlaybackSpeed; label: string; detail: string }> = [
  { value: "0.5x", label: "0.5x", detail: "Deliberate playback" },
  { value: "1x", label: "1x", detail: "Default pacing" },
  { value: "2x", label: "2x", detail: "Faster reveal" },
  { value: "5x", label: "5x", detail: "Rapid playback" },
  { value: "instant", label: "Instant", detail: "Minimal delay" },
];

const ROLE_ALIAS: Record<string, string> = {
  "Business Owner": "Product Strategy Agent",
  "Finance Lead": "Finance Agent",
  "Sales Strategist": "Growth / GTM Agent",
  "Marketing Strategist": "Market Opportunity Agent",
  "Product Manager": "Customer Value Agent",
  "UX/UI Reviewer": "Customer Value Agent",
  "Customer Success Lead": "Business Model Agent",
  "System Architect": "Architecture Agent",
  "AI/Data Scientist": "AI Systems Agent",
  Developer: "Implementation Feasibility Agent",
  "DevOps Architect": "Operations / Reliability Agent",
  "System Maintenance Lead": "Operations / Reliability Agent",
  "QA/SDET": "Data Strategy Agent",
  "InfoSec Architect": "Security & Compliance Agent",
  "Legal & Compliance Reviewer": "Risk & Governance Agent",
  "Conflict Detector": "Conflict Detector",
  "Debate Moderator": "Moderator",
  "ORBIT Committee": "Investment Committee Agent",
};

type SpeakerProfile = {
  displayRole: string;
  sourceRole: string | null;
  avatar: string;
  avatarClass: string;
  panelClass: string;
};

type ConflictSpotlight = {
  conflictReference: string;
  identification: DeliberationEntryPayload | null;
  discussion: DeliberationEntryPayload[];
  moderator: DeliberationEntryPayload | null;
};

function recommendationTone(recommendation: string | null | undefined): Tone {
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

function parseStance(statementText: string): string | null {
  const recommendations = [
    "Strong Proceed",
    "Proceed with Conditions",
    "Pilot Only",
    "High Risk",
    "Do Not Proceed",
  ];
  for (const recommendation of recommendations) {
    if (statementText.includes(recommendation)) {
      return recommendation;
    }
  }
  return null;
}

function committeeStance(recommendation: string | null | undefined): CommitteeStance | null {
  if (!recommendation) {
    return null;
  }
  if (recommendation === "Strong Proceed" || recommendation === "Proceed with Conditions") {
    return "support";
  }
  if (recommendation === "Pilot Only") {
    return "neutral";
  }
  return "oppose";
}

function stanceTone(stance: CommitteeStance): Tone {
  if (stance === "support") {
    return "success";
  }
  if (stance === "neutral") {
    return "warning";
  }
  return "danger";
}

function activationTone(status: string): Tone {
  if (status === "passive_observer") {
    return "default";
  }
  return "warning";
}

function agreementTone(score: number | null | undefined): Tone {
  if (typeof score !== "number") {
    return "default";
  }
  if (score >= 0.8) {
    return "success";
  }
  if (score >= 0.6) {
    return "warning";
  }
  return "danger";
}

function avatarLabel(role: string): string {
  const words = role.split(/[^A-Za-z]+/).filter(Boolean);
  if (words.length === 0) {
    return "OR";
  }
  return words
    .slice(0, 3)
    .map((word) => word[0])
    .join("")
    .toUpperCase();
}

function speakerProfile(agentRole: string): SpeakerProfile {
  const displayRole = ROLE_ALIAS[agentRole] ?? agentRole;
  const sourceRole = displayRole === agentRole ? null : agentRole;

  if (displayRole.includes("Security") || displayRole.includes("Risk")) {
    return {
      displayRole,
      sourceRole,
      avatar: avatarLabel(displayRole),
      avatarClass: "border-rose-200 bg-rose-50 text-rose-700",
      panelClass: "border-rose-200/60 bg-rose-50/70",
    };
  }
  if (displayRole.includes("AI") || displayRole.includes("Architecture") || displayRole.includes("Implementation") || displayRole.includes("Operations") || displayRole.includes("Data")) {
    return {
      displayRole,
      sourceRole,
      avatar: avatarLabel(displayRole),
      avatarClass: "border-sky-200 bg-sky-50 text-sky-700",
      panelClass: "border-sky-200/60 bg-sky-50/70",
    };
  }
  if (displayRole.includes("Finance") || displayRole.includes("Growth") || displayRole.includes("Market") || displayRole.includes("Business") || displayRole.includes("Investment")) {
    return {
      displayRole,
      sourceRole,
      avatar: avatarLabel(displayRole),
      avatarClass: "border-amber-200 bg-amber-50 text-amber-700",
      panelClass: "border-amber-200/60 bg-amber-50/70",
    };
  }
  if (displayRole.includes("Moderator") || displayRole.includes("Conflict")) {
    return {
      displayRole,
      sourceRole,
      avatar: avatarLabel(displayRole),
      avatarClass: "border-slate-200 bg-slate-100 text-slate-700",
      panelClass: "border-slate-200/60 bg-slate-100/75",
    };
  }
  return {
    displayRole,
    sourceRole,
    avatar: avatarLabel(displayRole),
    avatarClass: "border-emerald-200 bg-emerald-50 text-emerald-700",
    panelClass: "border-emerald-200/60 bg-emerald-50/70",
  };
}

function playbackDelay(entry: DeliberationEntryPayload, playbackSpeed: PlaybackSpeed): number {
  if (playbackSpeed === "instant") {
    return 45;
  }

  let baseDelay = 700;
  if (entry.phase === "final_verdict") {
    baseDelay = 1500;
  } else if (entry.phase === "moderator_synthesis") {
    baseDelay = 1200;
  } else if (entry.phase === "conflict_identification") {
    baseDelay = 900;
  } else if (entry.phase === "conflict_discussion") {
    baseDelay = 850;
  }

  if (playbackSpeed === "0.5x") {
    return Math.max(baseDelay * 2, 240);
  }
  const divisor = playbackSpeed === "2x" ? 2 : playbackSpeed === "5x" ? 5 : 1;
  return Math.max(Math.round(baseDelay / divisor), 120);
}

function phaseVisibleCount(entries: DeliberationEntryPayload[], phase: string): number {
  return entries.filter((entry) => entry.phase === phase).length;
}

function phaseTotalCount(timeline: ReviewRunDeliberationPayload, phase: string): number {
  return timeline.entries.filter((entry) => entry.phase === phase).length;
}

function phaseStatus(
  visibleEntries: DeliberationEntryPayload[],
  timeline: ReviewRunDeliberationPayload,
  phase: string,
): "locked" | "live" | "complete" {
  const visible = phaseVisibleCount(visibleEntries, phase);
  const total = phaseTotalCount(timeline, phase);
  if (visible === 0) {
    return "locked";
  }
  if (visible < total) {
    return "live";
  }
  return "complete";
}

function nextPhaseRevealCount(timeline: ReviewRunDeliberationPayload, visibleCount: number): number {
  if (visibleCount >= timeline.entries.length) {
    return timeline.entries.length;
  }
  const currentPhase = visibleCount === 0 ? timeline.entries[0].phase : timeline.entries[Math.max(visibleCount - 1, 0)].phase;
  const phaseIndex = PHASE_ORDER.indexOf(currentPhase as (typeof PHASE_ORDER)[number]);
  const currentPhaseEnd = timeline.entries.findLastIndex((entry) => entry.phase === currentPhase) + 1;
  if (visibleCount < currentPhaseEnd) {
    return currentPhaseEnd;
  }
  const nextPhase = PHASE_ORDER[Math.min(phaseIndex + 1, PHASE_ORDER.length - 1)];
  return timeline.entries.findLastIndex((entry) => entry.phase === nextPhase) + 1;
}

function buildConflictSpotlights(entries: DeliberationEntryPayload[]): ConflictSpotlight[] {
  const conflictReferences = Array.from(
    new Set(entries.map((entry) => entry.conflict_reference).filter((value): value is string => Boolean(value))),
  );

  return conflictReferences.map((conflictReference) => {
    const relatedEntries = entries.filter((entry) => entry.conflict_reference === conflictReference);
    return {
      conflictReference,
      identification: relatedEntries.find((entry) => entry.statement_type === "conflict_identified") ?? null,
      discussion: relatedEntries.filter((entry) => entry.statement_type === "conflict_argument"),
      moderator: relatedEntries.find((entry) => entry.statement_type === "moderator_synthesis") ?? null,
    };
  });
}

function formatDurationMs(durationMs: number): string {
  return `${formatInteger(durationMs)} ms`;
}

function agentTelemetryForEntry(
  agents: AgentRuntimeTelemetryPayload[],
  entry: DeliberationEntryPayload | null,
): AgentRuntimeTelemetryPayload | null {
  if (!entry) {
    return null;
  }
  return agents.find((agent) => agent.agent_id === entry.agent_id) ?? agents.find((agent) => agent.agent_role === entry.agent_role) ?? null;
}

function agentReasoningForEntry(
  reasoning: AgentReasoningPayload[],
  entry: DeliberationEntryPayload | null,
): AgentReasoningPayload | null {
  if (!entry) {
    return null;
  }
  return reasoning.find((agent) => agent.agent_id === entry.agent_id) ?? reasoning.find((agent) => agent.agent_role === entry.agent_role) ?? null;
}

function conflictMetadataForReference(
  conflicts: ConflictPersistencePayload[],
  conflictReference: string | null | undefined,
): ConflictPersistencePayload | null {
  if (!conflictReference) {
    return null;
  }
  return conflicts.find((conflict) => conflict.conflict_id === conflictReference) ?? null;
}

export function CommitteeMode({ timeline, summary, validation }: CommitteeModeProps) {
  const [visibleCount, setVisibleCount] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<PlaybackSpeed>("1x");
  const deferredVisibleCount = useDeferredValue(visibleCount);
  const revealedEntries = timeline.entries.slice(0, deferredVisibleCount);
  const currentEntry = revealedEntries.length ? revealedEntries[revealedEntries.length - 1] : null;
  const currentAgentTelemetry = agentTelemetryForEntry(timeline.runtime_metadata.agents, currentEntry);
  const currentAgentReasoning = agentReasoningForEntry(timeline.agent_reasoning, currentEntry);
  const visibleConflictSpotlights = buildConflictSpotlights(revealedEntries);
  const activeSpotlight =
    currentEntry?.conflict_reference != null
      ? visibleConflictSpotlights.find((spotlight) => spotlight.conflictReference === currentEntry.conflict_reference) ?? null
      : visibleConflictSpotlights[0] ?? null;
  const activeConflictMetadata = conflictMetadataForReference(
    timeline.conflicts,
    activeSpotlight?.conflictReference,
  );
  const latestValidation = validation?.validations?.[0] ?? null;
  const latestHumanReview =
    (latestValidation
      ? validation?.human_reviews?.find(
          (review) => review.human_review_id === latestValidation.human_review_id,
        )
      : null) ??
    validation?.human_reviews?.[0] ??
    null;

  const openingStatementByRole: Record<string, DeliberationEntryPayload> = {};
  const stanceByRole: Record<string, string> = {};
  for (const entry of timeline.entries) {
    if (entry.statement_type === "opening_statement" && openingStatementByRole[entry.agent_role] == null) {
      openingStatementByRole[entry.agent_role] = entry;
    }
    if (entry.statement_type === "opening_statement") {
      const stance = parseStance(entry.statement_text);
      if (stance) {
        stanceByRole[entry.agent_role] = stance;
      }
    }
  }

  useEffect(() => {
    if (!isPlaying) {
      return;
    }
    if (visibleCount >= timeline.entries.length) {
      setIsPlaying(false);
      return;
    }
    const scheduledEntry = timeline.entries[visibleCount];
    const timer = window.setTimeout(
      () =>
        setVisibleCount((current) => {
          if (current >= timeline.entries.length) {
            return current;
          }
          return current + 1;
        }),
      playbackDelay(scheduledEntry, playbackSpeed),
    );
    return () => window.clearTimeout(timer);
  }, [isPlaying, playbackSpeed, timeline.entries, visibleCount]);

  const playbackLabel =
    visibleCount === 0
      ? "Start Playback"
      : visibleCount >= timeline.entries.length
        ? "Replay Committee"
        : isPlaying
          ? "Pause Playback"
          : "Resume Playback";

  function handleTogglePlayback() {
    if (visibleCount >= timeline.entries.length) {
      startTransition(() => {
        setVisibleCount(1);
        setIsPlaying(true);
      });
      return;
    }
    if (visibleCount === 0) {
      startTransition(() => {
        setVisibleCount(1);
        setIsPlaying(true);
      });
      return;
    }
    startTransition(() => {
      setIsPlaying((current) => !current);
    });
  }

  function handleSkipPhase() {
    startTransition(() => {
      setIsPlaying(false);
      setVisibleCount(nextPhaseRevealCount(timeline, visibleCount));
    });
  }

  function handleJumpToVerdict() {
    startTransition(() => {
      setIsPlaying(false);
      setVisibleCount(timeline.entries.length);
    });
  }

  function handleReset() {
    startTransition(() => {
      setIsPlaying(false);
      setVisibleCount(0);
    });
  }

  const verdictVisible = revealedEntries.some((entry) => entry.phase === "final_verdict");
  const currentPhase = currentEntry?.phase ?? summary.phase_summaries[0]?.phase ?? "opening_statements";

  return (
    <PageFrame>
      <section className="rounded-[36px] border border-orbit-pine/10 bg-orbit-ink px-8 py-9 text-orbit-mist shadow-panel md:px-10" data-testid="committee-mode-page">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <StatusBadge label="Milestone 15" />
              <StatusBadge label="Committee Mode" tone="warning" />
              <StatusBadge label={summary.active_artifact_source} />
              <StatusBadge label={summary.final_recommendation} tone={recommendationTone(summary.final_recommendation)} />
            </div>
            <div className="space-y-3">
              <p className="text-sm uppercase tracking-[0.24em] text-orbit-moss">Boardroom Experience</p>
              <h1 className="max-w-4xl text-4xl font-semibold tracking-tight md:text-5xl">
                Watch the ORBIT committee unfold like a live investment boardroom.
              </h1>
              <p className="max-w-3xl text-base leading-7 text-orbit-mist/78">
                Committee Mode replays the persisted deliberation timeline with evidence-based claim chains, adaptive
                routing telemetry, human decision validation overlays, consistent agent identities, and controllable
                playback speed, while preserving the same bounded committee record underneath.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <ActionLink href={`/review-runs/${timeline.review_run_id}/deliberation`} tone="muted">
              Static Timeline
            </ActionLink>
            <ActionLink href={`/portfolios/${timeline.portfolio_id}/history?runId=${timeline.review_run_id}`} tone="muted">
              Review History
            </ActionLink>
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <ShellCard className="bg-orbit-pine text-orbit-mist">
          <SectionEyebrow>Committee Runtime Metadata</SectionEyebrow>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <div className="rounded-[24px] border border-white/10 bg-white/6 px-4 py-4">
              <div className="text-xs uppercase tracking-[0.2em] text-orbit-moss">Runtime Mode</div>
              <div className="mt-2 text-xl font-semibold">{timeline.runtime_metadata.effective_runtime_mode}</div>
              <div className="mt-2 text-sm text-orbit-mist/72">
                {timeline.runtime_metadata.prompt_contract_version}
                {timeline.runtime_metadata.routing_strategy_version
                  ? ` / ${timeline.runtime_metadata.routing_strategy_version}`
                  : ""}
              </div>
            </div>
            <div className="rounded-[24px] border border-white/10 bg-white/6 px-4 py-4">
              <div className="text-xs uppercase tracking-[0.2em] text-orbit-moss">Provider / Model</div>
              <div className="mt-2 text-xl font-semibold">{timeline.runtime_metadata.model_provider}</div>
              <div className="mt-2 text-sm text-orbit-mist/72">{timeline.runtime_metadata.model_name}</div>
            </div>
            <div className="rounded-[24px] border border-white/10 bg-white/6 px-4 py-4">
              <div className="text-xs uppercase tracking-[0.2em] text-orbit-moss">Requested Runtime</div>
              <div className="mt-2 text-xl font-semibold">{timeline.runtime_metadata.requested_runtime_mode}</div>
              <div className="mt-2 text-sm text-orbit-mist/72">
                {timeline.runtime_metadata.requested_provider} / {timeline.runtime_metadata.requested_model_name}
              </div>
            </div>
            <div className="rounded-[24px] border border-white/10 bg-white/6 px-4 py-4">
              <div className="text-xs uppercase tracking-[0.2em] text-orbit-moss">Agents Executed</div>
              <div className="mt-2 text-xl font-semibold">{timeline.runtime_metadata.agent_count}</div>
              <div className="mt-2 text-sm text-orbit-mist/72">
                Core {timeline.runtime_metadata.core_executed_count} / specialists{" "}
                {timeline.runtime_metadata.activated_specialist_count} / passive{" "}
                {timeline.runtime_metadata.passive_observer_count}
              </div>
            </div>
            <div className="rounded-[24px] border border-white/10 bg-white/6 px-4 py-4">
              <div className="text-xs uppercase tracking-[0.2em] text-orbit-moss">Total Tokens</div>
              <div className="mt-2 text-xl font-semibold">{formatInteger(timeline.runtime_metadata.total_tokens)}</div>
              <div className="mt-2 text-sm text-orbit-mist/72">
                in {formatInteger(timeline.runtime_metadata.total_input_tokens)} / out{" "}
                {formatInteger(timeline.runtime_metadata.total_output_tokens)}
              </div>
            </div>
            <div className="rounded-[24px] border border-white/10 bg-white/6 px-4 py-4 md:col-span-2">
              <div className="text-xs uppercase tracking-[0.2em] text-orbit-moss">Estimated Cost</div>
              <div className="mt-2 text-2xl font-semibold">{formatCostUsd(timeline.runtime_metadata.estimated_cost_usd)}</div>
              <div className="mt-2 text-sm text-orbit-mist/72">
                Deterministic runs remain zero-token and zero-cost. Playback itself does not trigger new model usage.
              </div>
            </div>
            {timeline.runtime_metadata.routing_signals.length ? (
              <div className="rounded-[24px] border border-white/10 bg-white/6 px-4 py-4 md:col-span-2">
                <div className="text-xs uppercase tracking-[0.2em] text-orbit-moss">Adaptive Routing Signals</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {timeline.runtime_metadata.routing_signals.map((signal) => (
                    <StatusBadge key={signal} label={humanize(signal)} tone="warning" />
                  ))}
                </div>
                <div className="mt-3 text-sm text-orbit-mist/72">
                  Aggregate duration {formatDurationMs(timeline.runtime_metadata.total_duration_ms)}
                </div>
              </div>
            ) : null}
            {timeline.runtime_metadata.fallback_applied ? (
              <div className="rounded-[24px] border border-amber-200 bg-amber-100/20 px-4 py-4 md:col-span-2">
                <div className="text-xs uppercase tracking-[0.2em] text-orbit-moss">Fallback Safety</div>
                <div className="mt-2 text-xl font-semibold">Deterministic fallback applied</div>
                <div className="mt-2 text-sm text-orbit-mist/80">
                  {timeline.runtime_metadata.fallback_category ?? "llm failure"}:{" "}
                  {timeline.runtime_metadata.fallback_reason ?? "The review completed in deterministic mode after an llm runtime failure."}
                </div>
              </div>
            ) : null}
          </div>
        </ShellCard>

        <ShellCard>
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-3">
              <SectionEyebrow>Agent Identity Lineup</SectionEyebrow>
              <p className="max-w-3xl text-sm leading-6 text-orbit-ink/72">
                The same 15 committee agents remain visible throughout playback. Each card keeps the agent identity,
                stance, reasoning snapshot, and token footprint in one place.
              </p>
            </div>
            <StatusBadge label={`${timeline.runtime_metadata.agents.length} agents`} />
          </div>
          <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {timeline.runtime_metadata.agents.map((agent) => {
              const profile = speakerProfile(agent.agent_role);
              const recommendation = stanceByRole[agent.agent_role] ?? agent.recommendation;
              const stance = committeeStance(recommendation);
              const openingStatement = openingStatementByRole[agent.agent_role]?.statement_text ?? "No opening statement was persisted.";
              const isCurrentSpeaker =
                currentEntry != null && (currentEntry.agent_id === agent.agent_id || currentEntry.agent_role === agent.agent_role);

              return (
                <div
                  key={agent.agent_id}
                  className={
                    isCurrentSpeaker
                      ? `rounded-[24px] border-2 px-4 py-4 shadow-panel ${profile.panelClass}`
                      : `rounded-[24px] border px-4 py-4 ${profile.panelClass}`
                  }
                >
                  <div className="flex items-start gap-3">
                    <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border text-sm font-semibold ${profile.avatarClass}`}>
                      {profile.avatar}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <div className="text-sm font-semibold text-orbit-ink">{profile.displayRole}</div>
                        {stance ? <StatusBadge label={stance} tone={stanceTone(stance)} /> : null}
                      </div>
                      {profile.sourceRole ? (
                        <div className="mt-1 text-[11px] uppercase tracking-[0.18em] text-orbit-ink/55">{profile.sourceRole}</div>
                      ) : null}
                    </div>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <StatusBadge label={recommendation} tone={recommendationTone(recommendation)} />
                    <StatusBadge label={agent.activation_tier} tone="warning" />
                    <StatusBadge label={humanize(agent.activation_status)} tone={activationTone(agent.activation_status)} />
                    <StatusBadge label={`${formatInteger(agent.total_tokens)} tokens`} />
                  </div>
                  <p className="mt-3 text-sm leading-6 text-orbit-ink/78">{openingStatement}</p>
                  <p className="mt-3 text-xs leading-5 text-orbit-ink/58">{agent.activation_reason || "No adaptive routing note was persisted for this agent."}</p>
                </div>
              );
            })}
          </div>
        </ShellCard>
      </section>

      <ShellCard data-testid="committee-human-review">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-3">
            <SectionEyebrow>Human Review Overlay</SectionEyebrow>
            <p className="max-w-3xl text-sm leading-6 text-orbit-ink/70">
              Decision validation compares the latest human expert verdict with the ORBIT committee outcome using
              recommendation alignment, score proximity, and risk overlap.
            </p>
          </div>
          <a
            className="inline-flex rounded-full border border-orbit-pine/10 px-4 py-2 text-sm font-medium text-orbit-ink/75 transition hover:border-orbit-pine/30 hover:text-orbit-ink"
            href={publicApiHref(`/api/v1/validation/review-runs/${timeline.review_run_id}`)}
            target="_blank"
            rel="noreferrer"
          >
            Validation API
          </a>
        </div>

        {latestHumanReview ? (
          <div className="mt-6 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="rounded-[24px] border border-orbit-pine/10 bg-white/70 p-4 shadow-panel">
              <div className="flex flex-wrap items-center gap-3">
                <StatusBadge label={latestHumanReview.reviewer_name} />
                <StatusBadge
                  label={latestHumanReview.final_recommendation}
                  tone={recommendationTone(latestHumanReview.final_recommendation)}
                />
                <StatusBadge label={`Confidence: ${latestHumanReview.confidence}`} />
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <MetricCard
                  label="Human Score"
                  value={formatScore(latestHumanReview.score)}
                  detail={`Submitted ${formatDate(latestHumanReview.created_at)}`}
                />
                <MetricCard
                  label="Human Risks"
                  value={formatInteger(latestHumanReview.review_payload.identified_risks.length)}
                  detail="Risks supplied by the human reviewer."
                />
              </div>
              {latestHumanReview.review_payload.review_notes ? (
                <p className="mt-4 text-sm leading-6 text-orbit-ink/75">
                  {latestHumanReview.review_payload.review_notes}
                </p>
              ) : null}
            </div>

            <div className="space-y-4 rounded-[24px] border border-orbit-gold/30 bg-orbit-gold/10 p-4">
              {latestValidation ? (
                <>
                  <div className="flex flex-wrap items-center gap-3">
                    <StatusBadge label="Agreement Score" tone={agreementTone(latestValidation.agreement_score)} />
                    <StatusBadge label={`Match: ${latestValidation.recommendation_match}`} />
                    <StatusBadge label={`Risk overlap ${latestValidation.risk_overlap}`} />
                  </div>
                  <div className="grid gap-3 md:grid-cols-2">
                    <MetricCard
                      label="Agreement"
                      value={latestValidation.agreement_score.toFixed(2)}
                      detail={`Score diff ${latestValidation.score_difference.toFixed(2)}`}
                    />
                    <MetricCard
                      label="Confidence Alignment"
                      value={latestValidation.confidence_alignment.toFixed(2)}
                      detail={`Risk recall ${latestValidation.risk_recall.toFixed(2)}`}
                    />
                  </div>
                  <p className="text-sm leading-6 text-orbit-ink/70">
                    ORBIT recommendation: {latestValidation.validation_payload.orbit_recommendation} · Human
                    recommendation: {latestValidation.validation_payload.human_recommendation}
                  </p>
                </>
              ) : (
                <p className="text-sm leading-6 text-orbit-ink/70">
                  A human review is stored, but no decision validation has been computed yet for this review run.
                </p>
              )}
            </div>
          </div>
        ) : (
          <div className="mt-5 rounded-[24px] border border-dashed border-orbit-pine/15 bg-orbit-mist/35 px-5 py-6 text-sm leading-6 text-orbit-ink/65">
            No human review has been submitted for this portfolio yet. Submit a human review to compare the committee
            outcome against an expert baseline.
          </div>
        )}
      </ShellCard>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Playback Progress"
          value={`${deferredVisibleCount}/${timeline.entry_count}`}
          detail="Statements are revealed locally in browser order using the persisted sequence numbers."
        />
        <MetricCard
          label="Current Phase"
          value={humanize(currentPhase)}
          detail={currentEntry ? `Latest visible statement recorded ${formatDate(currentEntry.created_at)}.` : "Playback has not started yet."}
        />
        <MetricCard
          label="Final Recommendation"
          value={summary.final_recommendation}
          detail={`Weighted composite ${formatScore(summary.weighted_composite_score)}`}
        />
        <MetricCard
          label="Lineage"
          value={timeline.lineage.review_run_id}
          detail={timeline.lineage.debate_id ?? "No debate session attached to this run."}
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <ShellCard data-testid="committee-playback-controls">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
              <div className="space-y-3">
                <SectionEyebrow>Playback Controls</SectionEyebrow>
                <p className="max-w-2xl text-sm leading-6 text-orbit-ink/72">
                  Start, pause, resume, skip by phase, or jump straight to the verdict. Committee Mode runs entirely
                  on the persisted deliberation dataset already attached to this review run.
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={handleTogglePlayback}
                  className="inline-flex rounded-full bg-orbit-ink px-5 py-3 text-sm font-semibold text-orbit-mist transition hover:bg-orbit-pine"
                  data-testid="committee-playback-toggle"
                >
                  {playbackLabel}
                </button>
                <button
                  type="button"
                  onClick={handleSkipPhase}
                  className="inline-flex rounded-full border border-orbit-pine/15 px-5 py-3 text-sm font-semibold text-orbit-ink transition hover:border-orbit-pine/35"
                  data-testid="committee-skip-phase"
                >
                  Skip to Next Phase
                </button>
                <button
                  type="button"
                  onClick={handleJumpToVerdict}
                  className="inline-flex rounded-full border border-orbit-pine/15 px-5 py-3 text-sm font-semibold text-orbit-ink transition hover:border-orbit-pine/35"
                  data-testid="committee-jump-verdict"
                >
                  Jump to Final Verdict
                </button>
                <button
                  type="button"
                  onClick={handleReset}
                  className="inline-flex rounded-full border border-orbit-pine/15 px-5 py-3 text-sm font-semibold text-orbit-ink transition hover:border-orbit-pine/35"
                  data-testid="committee-reset"
                >
                  Reset
                </button>
              </div>
            </div>
            <div className="mt-5 flex flex-col gap-3 border-t border-orbit-pine/10 pt-4 text-sm lg:flex-row lg:items-center lg:justify-between">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium text-orbit-ink/75">Playback speed</span>
                {PLAYBACK_SPEEDS.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => startTransition(() => setPlaybackSpeed(option.value))}
                    className={
                      playbackSpeed === option.value
                        ? "inline-flex rounded-full border border-orbit-gold/50 bg-orbit-gold/10 px-4 py-2 font-medium text-orbit-ink"
                        : "inline-flex rounded-full border border-orbit-pine/10 px-4 py-2 font-medium text-orbit-ink/75 transition hover:border-orbit-pine/30 hover:text-orbit-ink"
                    }
                    data-testid={`committee-speed-${option.value}`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
              <span className="text-orbit-ink/60" data-testid="committee-speed-current">
                Selected speed: {PLAYBACK_SPEEDS.find((option) => option.value === playbackSpeed)?.detail}
              </span>
            </div>
          </ShellCard>

          <ShellCard className="bg-orbit-pine text-orbit-mist">
            <SectionEyebrow>Current Speaker</SectionEyebrow>
            {currentEntry ? (
              (() => {
                const profile = speakerProfile(currentEntry.agent_role);
                const recommendation = stanceByRole[currentEntry.agent_role] ?? parseStance(currentEntry.statement_text);
                const stance = committeeStance(recommendation);
                return (
                  <div className="mt-5 space-y-4">
                    <div className="flex flex-wrap items-center gap-4">
                      <div className={`flex h-16 w-16 items-center justify-center rounded-2xl border text-lg font-semibold ${profile.avatarClass}`}>
                        {profile.avatar}
                      </div>
                      <div>
                        <div className="text-xs uppercase tracking-[0.22em] text-orbit-moss">Now speaking</div>
                        <div className="mt-1 text-2xl font-semibold">{profile.displayRole}</div>
                        {profile.sourceRole ? (
                          <div className="mt-1 text-sm text-orbit-mist/70">Source persona: {profile.sourceRole}</div>
                        ) : null}
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-3">
                      <StatusBadge label={humanize(currentEntry.statement_type)} />
                      <StatusBadge label={humanize(currentEntry.phase)} tone="warning" />
                      {recommendation ? (
                        <StatusBadge label={recommendation} tone={recommendationTone(recommendation)} />
                      ) : null}
                      {stance ? <StatusBadge label={stance} tone={stanceTone(stance)} /> : null}
                      {currentEntry.conflict_reference ? (
                        <StatusBadge label={currentEntry.conflict_reference} tone="danger" />
                      ) : null}
                    </div>
              {currentAgentTelemetry ? (
                <div className="grid gap-3 md:grid-cols-3">
                        <div className="rounded-[20px] border border-white/10 bg-white/7 px-4 py-3 text-sm">
                          <div className="text-xs uppercase tracking-[0.18em] text-orbit-moss">Runtime</div>
                          <div className="mt-2 font-semibold">{formatDurationMs(currentAgentTelemetry.duration_ms)}</div>
                        </div>
                        <div className="rounded-[20px] border border-white/10 bg-white/7 px-4 py-3 text-sm">
                          <div className="text-xs uppercase tracking-[0.18em] text-orbit-moss">Tokens</div>
                          <div className="mt-2 font-semibold">{formatInteger(currentAgentTelemetry.total_tokens)}</div>
                        </div>
                        <div className="rounded-[20px] border border-white/10 bg-white/7 px-4 py-3 text-sm">
                          <div className="text-xs uppercase tracking-[0.18em] text-orbit-moss">Estimated Cost</div>
                          <div className="mt-2 font-semibold">
                            {formatCostUsd(currentAgentTelemetry.estimated_cost_usd)}
                          </div>
                        </div>
                </div>
              ) : null}
              {currentAgentReasoning ? (
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <div className="rounded-[20px] border border-white/10 bg-white/7 px-4 py-3 text-sm">
                    <div className="text-xs uppercase tracking-[0.18em] text-orbit-moss">Claim</div>
                    <div className="mt-2 font-semibold">{currentAgentReasoning.claim}</div>
                  </div>
                  <div className="rounded-[20px] border border-white/10 bg-white/7 px-4 py-3 text-sm">
                    <div className="text-xs uppercase tracking-[0.18em] text-orbit-moss">Implication</div>
                    <div className="mt-2 font-semibold">{currentAgentReasoning.implication}</div>
                  </div>
                  <div className="rounded-[20px] border border-white/10 bg-white/7 px-4 py-3 text-sm">
                    <div className="text-xs uppercase tracking-[0.18em] text-orbit-moss">Evidence</div>
                    <ul className="mt-2 list-disc pl-5">
                      {currentAgentReasoning.evidence.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="rounded-[20px] border border-white/10 bg-white/7 px-4 py-3 text-sm">
                    <div className="text-xs uppercase tracking-[0.18em] text-orbit-moss">Risks</div>
                    <ul className="mt-2 list-disc pl-5">
                      {currentAgentReasoning.risk.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="rounded-[20px] border border-white/10 bg-white/7 px-4 py-3 text-sm">
                    <div className="text-xs uppercase tracking-[0.18em] text-orbit-moss">Score</div>
                    <div className="mt-2 font-semibold">{formatScore(currentAgentReasoning.score)}</div>
                  </div>
                  <div className="rounded-[20px] border border-white/10 bg-white/7 px-4 py-3 text-sm">
                    <div className="text-xs uppercase tracking-[0.18em] text-orbit-moss">Confidence</div>
                    <div className="mt-2 font-semibold">{currentAgentReasoning.confidence}</div>
                  </div>
                </div>
              ) : null}
              {currentAgentTelemetry ? (
                <div className="flex flex-wrap gap-2">
                        <StatusBadge label={currentAgentTelemetry.activation_tier} tone="warning" />
                        <StatusBadge
                          label={humanize(currentAgentTelemetry.activation_status)}
                          tone={activationTone(currentAgentTelemetry.activation_status)}
                        />
                      </div>
                    ) : null}
                    <p className="text-base leading-7 text-orbit-mist/88">{currentEntry.statement_text}</p>
                    {currentAgentTelemetry?.activation_reason ? (
                      <p className="text-sm leading-6 text-orbit-mist/72">{currentAgentTelemetry.activation_reason}</p>
                    ) : null}
                  </div>
                );
              })()
            ) : (
              <p className="mt-5 text-sm leading-6 text-orbit-mist/76">
                Start playback to reveal the opening statements and move into the conflict spotlight sequence.
              </p>
            )}
          </ShellCard>

          <ShellCard data-testid="committee-transcript">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div className="space-y-3">
                <SectionEyebrow>Revealed Transcript</SectionEyebrow>
                <p className="max-w-3xl text-sm leading-6 text-orbit-ink/70">
                  Entries appear only after playback reveals them. The transcript remains grouped by the five
                  deliberation phases so you can replay or inspect the committee flow without losing chronology.
                </p>
              </div>
              <a
                className="inline-flex rounded-full border border-orbit-pine/10 px-4 py-2 text-sm font-medium text-orbit-ink/75 transition hover:border-orbit-pine/30 hover:text-orbit-ink"
                href={publicApiHref(`/api/v1/review-runs/${timeline.review_run_id}/deliberation`)}
                target="_blank"
                rel="noreferrer"
              >
                Timeline API
              </a>
            </div>

            {revealedEntries.length === 0 ? (
              <div className="mt-6 rounded-[24px] border border-dashed border-orbit-pine/15 bg-orbit-mist/35 px-5 py-6 text-sm leading-6 text-orbit-ink/65">
                No entries are visible yet. Use the controls above to begin the replay.
              </div>
            ) : (
              <div className="mt-6 space-y-6">
                {summary.phase_summaries.map((phase) => {
                  const phaseEntries = revealedEntries.filter((entry) => entry.phase === phase.phase);
                  if (phaseEntries.length === 0) {
                    return null;
                  }
                  return (
                    <div key={phase.phase} className="space-y-4">
                      <div className="flex flex-wrap items-center gap-3">
                        <StatusBadge label={phase.label} tone="warning" />
                        <StatusBadge label={`${phaseEntries.length} revealed`} />
                      </div>
                      <div className="space-y-3">
                        {phaseEntries.map((entry) => {
                          const profile = speakerProfile(entry.agent_role);
                          const recommendation = stanceByRole[entry.agent_role] ?? parseStance(entry.statement_text);
                          const stance = committeeStance(recommendation);
                          const telemetry = agentTelemetryForEntry(timeline.runtime_metadata.agents, entry);
                          const reasoning = agentReasoningForEntry(timeline.agent_reasoning, entry);
                          return (
                            <div key={entry.deliberation_entry_row_id} className={`committee-entry-reveal rounded-[24px] border px-4 py-4 shadow-panel ${profile.panelClass}`}>
                              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                                <div className="space-y-3">
                                  <div className="flex flex-wrap items-center gap-3">
                                    <div className={`flex h-11 w-11 items-center justify-center rounded-2xl border text-sm font-semibold ${profile.avatarClass}`}>
                                      {profile.avatar}
                                    </div>
                                    <div>
                                      <div className="text-base font-semibold text-orbit-ink">{profile.displayRole}</div>
                                      {profile.sourceRole ? <div className="text-xs uppercase tracking-[0.18em] text-orbit-ink/55">{profile.sourceRole}</div> : null}
                                    </div>
                                  </div>
                                  <div className="flex flex-wrap items-center gap-3">
                                    <StatusBadge label={`#${entry.sequence_number}`} />
                                    <StatusBadge label={humanize(entry.statement_type)} />
                                    {recommendation ? <StatusBadge label={recommendation} tone={recommendationTone(recommendation)} /> : null}
                                    {stance ? <StatusBadge label={stance} tone={stanceTone(stance)} /> : null}
                                    {entry.conflict_reference ? <StatusBadge label={entry.conflict_reference} tone="danger" /> : null}
                                  </div>
                                  <p className="text-sm leading-6 text-orbit-ink/80">{entry.statement_text}</p>
                                  {reasoning ? (
                                    <div className="mt-3 space-y-2 text-sm text-orbit-ink/75">
                                      <div><span className="font-semibold">Claim:</span> {reasoning.claim}</div>
                                      <div><span className="font-semibold">Implication:</span> {reasoning.implication}</div>
                                      <div>
                                        <span className="font-semibold">Evidence:</span>
                                        <ul className="list-disc pl-5">
                                          {reasoning.evidence.map((item) => (
                                            <li key={item}>{item}</li>
                                          ))}
                                        </ul>
                                      </div>
                                      <div>
                                        <span className="font-semibold">Risks:</span>
                                        <ul className="list-disc pl-5">
                                          {reasoning.risk.map((item) => (
                                            <li key={item}>{item}</li>
                                          ))}
                                        </ul>
                                      </div>
                                      <div className="flex flex-wrap gap-3">
                                        <span><span className="font-semibold">Score:</span> {formatScore(reasoning.score)}</span>
                                        <span><span className="font-semibold">Confidence:</span> {reasoning.confidence}</span>
                                      </div>
                                    </div>
                                  ) : null}
                                </div>
                                <div className="text-sm leading-6 text-orbit-ink/60">
                                  <div>Recorded {formatDate(entry.created_at)}</div>
                                  <div>{entry.agent_id ? `Agent ${entry.agent_id}` : "System-generated"}</div>
                                  {telemetry ? <div>{formatInteger(telemetry.total_tokens)} tokens</div> : null}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </ShellCard>
        </div>

        <div className="space-y-6">
          <ShellCard data-testid="committee-phase-rail">
            <SectionEyebrow>Phase Rail</SectionEyebrow>
            <div className="mt-5 space-y-3">
              {summary.phase_summaries.map((phase) => {
                const status = phaseStatus(revealedEntries, timeline, phase.phase);
                const visible = phaseVisibleCount(revealedEntries, phase.phase);
                return (
                  <div
                    key={phase.phase}
                    className={
                      status === "live"
                        ? "rounded-[24px] border border-orbit-gold/50 bg-orbit-gold/10 px-4 py-4"
                        : status === "complete"
                          ? "rounded-[24px] border border-emerald-200 bg-emerald-50/70 px-4 py-4"
                          : "rounded-[24px] border border-orbit-pine/10 bg-white/70 px-4 py-4"
                    }
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-orbit-ink">{phase.label}</div>
                        <div className="mt-1 text-xs uppercase tracking-[0.18em] text-orbit-ink/55">
                          {status === "live" ? "in focus" : status === "complete" ? "completed" : "locked"}
                        </div>
                      </div>
                      <StatusBadge label={`${visible}/${phase.entry_count}`} tone={status === "complete" ? "success" : status === "live" ? "warning" : "default"} />
                    </div>
                    <p className="mt-3 text-sm leading-6 text-orbit-ink/70">{phase.representative_statement}</p>
                  </div>
                );
              })}
            </div>
          </ShellCard>

          <ShellCard className={activeSpotlight ? "committee-spotlight-ring" : ""} data-testid="committee-conflict-spotlight">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div className="space-y-3">
                <SectionEyebrow>Conflict Spotlight</SectionEyebrow>
                <p className="max-w-2xl text-sm leading-6 text-orbit-ink/70">
                  Conflicts become visible as the boardroom reaches them. Each spotlight shows the disagreement topic,
                  the agents involved, the side each agent is taking, and the moderator interpretation.
                </p>
              </div>
              {activeSpotlight ? <StatusBadge label={activeSpotlight.conflictReference} tone="danger" /> : null}
            </div>

            {activeSpotlight ? (
              <div className="mt-5 space-y-4">
                <div className="rounded-[24px] border border-orbit-gold/35 bg-orbit-gold/10 px-4 py-4">
                  <div className="text-xs uppercase tracking-[0.2em] text-orbit-pine/70">Conflict Topic</div>
                  <p className="mt-3 text-sm leading-6 text-orbit-ink/80">
                    {activeSpotlight.identification?.statement_text ?? "Conflict identification has not been revealed yet."}
                  </p>
                  {activeConflictMetadata ? (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {activeConflictMetadata.conflict_payload.conflict_category ? (
                        <StatusBadge label={activeConflictMetadata.conflict_payload.conflict_category} tone="warning" />
                      ) : null}
                      {activeConflictMetadata.conflict_payload.conflict_reason ? (
                        <StatusBadge label={activeConflictMetadata.conflict_payload.conflict_reason} />
                      ) : null}
                    </div>
                  ) : null}
                  {activeConflictMetadata?.conflict_payload.conflicting_claims?.length ? (
                    <div className="mt-4 text-sm text-orbit-ink/75">
                      <div className="text-xs uppercase tracking-[0.18em] text-orbit-pine/70">Conflicting Claims</div>
                      <ul className="mt-2 list-disc pl-5">
                        {activeConflictMetadata.conflict_payload.conflicting_claims.map((claim) => (
                          <li key={claim}>{claim}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {activeConflictMetadata?.conflict_payload.conflicting_evidence?.length ? (
                    <div className="mt-4 text-sm text-orbit-ink/75">
                      <div className="text-xs uppercase tracking-[0.18em] text-orbit-pine/70">Conflicting Evidence</div>
                      <ul className="mt-2 list-disc pl-5">
                        {activeConflictMetadata.conflict_payload.conflicting_evidence.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  <div className="mt-4 flex flex-wrap gap-2">
                    {(activeConflictMetadata?.conflict_payload.conflicting_agents.length
                      ? activeConflictMetadata.conflict_payload.conflicting_agents
                      : Array.from(new Set(activeSpotlight.discussion.map((entry) => speakerProfile(entry.agent_role).displayRole)))).map((role) => (
                        <StatusBadge key={role} label={role} />
                      ))}
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="text-xs uppercase tracking-[0.2em] text-orbit-pine/70">Agent Positions</div>
                  {activeSpotlight.discussion.length ? (
                    <div className="grid gap-3 md:grid-cols-2">
                      {activeSpotlight.discussion.map((entry) => {
                        const profile = speakerProfile(entry.agent_role);
                        const recommendation = stanceByRole[entry.agent_role] ?? parseStance(entry.statement_text);
                        const stance = committeeStance(recommendation);
                        return (
                          <div key={entry.deliberation_entry_row_id} className={`rounded-[24px] border px-4 py-4 ${profile.panelClass}`}>
                            <div className="flex flex-wrap items-center gap-3">
                              <div className={`flex h-10 w-10 items-center justify-center rounded-2xl border text-sm font-semibold ${profile.avatarClass}`}>
                                {profile.avatar}
                              </div>
                              <div className="text-sm font-semibold text-orbit-ink">{profile.displayRole}</div>
                            </div>
                            <div className="mt-3 flex flex-wrap gap-2">
                              {stance ? <StatusBadge label={stance} tone={stanceTone(stance)} /> : null}
                              {recommendation ? <StatusBadge label={recommendation} tone={recommendationTone(recommendation)} /> : null}
                            </div>
                            <p className="mt-3 text-sm leading-6 text-orbit-ink/80">{entry.statement_text}</p>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="rounded-[24px] border border-dashed border-orbit-pine/15 bg-orbit-mist/35 px-4 py-4 text-sm leading-6 text-orbit-ink/65">
                      Participant arguments for this conflict will appear once playback reaches the conflict discussion phase.
                    </div>
                  )}
                </div>
                <div className="rounded-[24px] border border-slate-200 bg-slate-100/70 px-4 py-4">
                  <div className="text-xs uppercase tracking-[0.2em] text-slate-600">Moderator Interpretation</div>
                  <p className="mt-3 text-sm leading-6 text-orbit-ink/80">
                    {activeSpotlight.moderator?.statement_text ?? "Moderator synthesis has not been revealed yet."}
                  </p>
                </div>
              </div>
            ) : (
              <div className="mt-5 rounded-[24px] border border-dashed border-orbit-pine/15 bg-orbit-mist/35 px-5 py-6 text-sm leading-6 text-orbit-ink/65">
                No conflict spotlight is active yet. The panel will light up automatically once conflict entries appear.
              </div>
            )}
          </ShellCard>

          <ShellCard className={verdictVisible ? "border-emerald-200 bg-emerald-50/80" : "bg-white/82"} data-testid="committee-final-verdict">
            <SectionEyebrow>Final Verdict Reveal</SectionEyebrow>
            {verdictVisible ? (
              <div className="mt-5 space-y-4">
                <div className="flex flex-wrap items-center gap-3">
                  <StatusBadge label={summary.final_recommendation} tone={recommendationTone(summary.final_recommendation)} />
                  <StatusBadge label={summary.active_artifact_source} />
                </div>
                <MetricCard
                  label="Weighted Composite"
                  value={formatScore(summary.weighted_composite_score)}
                  detail={`The verdict was revealed after ${timeline.entry_count} persisted statements.`}
                />
              </div>
            ) : (
              <div className="mt-5 rounded-[24px] border border-dashed border-orbit-pine/15 bg-orbit-mist/35 px-5 py-6 text-sm leading-6 text-orbit-ink/65">
                The final verdict remains hidden until the last phase is revealed or you jump to the end.
              </div>
            )}
          </ShellCard>
        </div>
      </section>
    </PageFrame>
  );
}
