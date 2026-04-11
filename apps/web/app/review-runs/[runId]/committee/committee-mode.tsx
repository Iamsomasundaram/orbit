"use client";

import { startTransition, useDeferredValue, useEffect, useState } from "react";

import {
  type DeliberationEntryPayload,
  type ReviewRunDeliberationPayload,
  type ReviewRunDeliberationSummaryPayload,
  formatDate,
  formatScore,
  humanize,
  publicApiHref,
} from "@/lib/orbit-api";

import { ActionLink, MetricCard, PageFrame, SectionEyebrow, ShellCard, StatusBadge } from "@/app/orbit-ui";

type CommitteeModeProps = {
  timeline: ReviewRunDeliberationPayload;
  summary: ReviewRunDeliberationSummaryPayload;
};

type Tone = "default" | "success" | "warning" | "danger";

const PHASE_ORDER = [
  "opening_statements",
  "conflict_identification",
  "conflict_discussion",
  "moderator_synthesis",
  "final_verdict",
] as const;

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

function playbackDelay(entry: DeliberationEntryPayload, skipDelays: boolean): number {
  if (skipDelays) {
    return 65;
  }
  if (entry.phase === "final_verdict") {
    return 1500;
  }
  if (entry.phase === "moderator_synthesis") {
    return 1200;
  }
  if (entry.phase === "conflict_identification") {
    return 900;
  }
  if (entry.phase === "conflict_discussion") {
    return 850;
  }
  return 700;
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

export function CommitteeMode({ timeline, summary }: CommitteeModeProps) {
  const [visibleCount, setVisibleCount] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [skipDelays, setSkipDelays] = useState(false);
  const deferredVisibleCount = useDeferredValue(visibleCount);
  const revealedEntries = timeline.entries.slice(0, deferredVisibleCount);
  const currentEntry = revealedEntries.length ? revealedEntries[revealedEntries.length - 1] : null;
  const visibleConflictSpotlights = buildConflictSpotlights(revealedEntries);
  const activeSpotlight =
    currentEntry?.conflict_reference != null
      ? visibleConflictSpotlights.find((spotlight) => spotlight.conflictReference === currentEntry.conflict_reference) ?? null
      : visibleConflictSpotlights[0] ?? null;

  const stanceByRole: Record<string, string> = {};
  for (const entry of timeline.entries) {
    if (entry.statement_type !== "opening_statement") {
      continue;
    }
    const stance = parseStance(entry.statement_text);
    if (stance) {
      stanceByRole[entry.agent_role] = stance;
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
      playbackDelay(scheduledEntry, skipDelays),
    );
    return () => window.clearTimeout(timer);
  }, [isPlaying, skipDelays, timeline.entries, visibleCount]);

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

  return (
    <PageFrame>
      <section className="rounded-[36px] border border-orbit-pine/10 bg-orbit-ink px-8 py-9 text-orbit-mist shadow-panel md:px-10">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <StatusBadge label="Milestone 12" />
              <StatusBadge label="Committee Mode" tone="warning" />
              <StatusBadge label={summary.active_artifact_source} />
              <StatusBadge label={summary.final_recommendation} tone={recommendationTone(summary.final_recommendation)} />
            </div>
            <div className="space-y-3">
              <p className="text-sm uppercase tracking-[0.24em] text-orbit-moss">Boardroom Experience</p>
              <h1 className="max-w-4xl text-4xl font-semibold tracking-tight md:text-5xl">
                Replay the ORBIT committee like a live boardroom session.
              </h1>
              <p className="max-w-3xl text-base leading-7 text-orbit-mist/78">
                Committee Mode stages the persisted deliberation timeline entry by entry, reveals conflict spotlights
                as they occur, and holds back the final verdict until the boardroom sequence reaches its last phase.
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

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Playback Progress"
          value={`${deferredVisibleCount}/${timeline.entry_count}`}
          detail="Statements are revealed locally in browser order using the persisted sequence numbers."
        />
        <MetricCard
          label="Current Phase"
          value={humanize((currentEntry?.phase ?? summary.phase_summaries[0].phase) || "opening_statements")}
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
          <ShellCard>
            <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
              <div className="space-y-3">
                <SectionEyebrow>Playback Controls</SectionEyebrow>
                <p className="max-w-2xl text-sm leading-6 text-orbit-ink/72">
                  Start, pause, resume, skip by phase, or jump straight to the verdict. Committee Mode uses only the
                  already persisted deliberation entries.
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={handleTogglePlayback}
                  className="inline-flex rounded-full bg-orbit-ink px-5 py-3 text-sm font-semibold text-orbit-mist transition hover:bg-orbit-pine"
                >
                  {playbackLabel}
                </button>
                <button
                  type="button"
                  onClick={handleSkipPhase}
                  className="inline-flex rounded-full border border-orbit-pine/15 px-5 py-3 text-sm font-semibold text-orbit-ink transition hover:border-orbit-pine/35"
                >
                  Skip to Next Phase
                </button>
                <button
                  type="button"
                  onClick={handleJumpToVerdict}
                  className="inline-flex rounded-full border border-orbit-pine/15 px-5 py-3 text-sm font-semibold text-orbit-ink transition hover:border-orbit-pine/35"
                >
                  Jump to Final Verdict
                </button>
                <button
                  type="button"
                  onClick={handleReset}
                  className="inline-flex rounded-full border border-orbit-pine/15 px-5 py-3 text-sm font-semibold text-orbit-ink transition hover:border-orbit-pine/35"
                >
                  Reset
                </button>
              </div>
            </div>
            <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-orbit-pine/10 pt-4 text-sm">
              <button
                type="button"
                onClick={() => setSkipDelays((current) => !current)}
                className={
                  skipDelays
                    ? "inline-flex rounded-full border border-orbit-gold/50 bg-orbit-gold/10 px-4 py-2 font-medium text-orbit-ink"
                    : "inline-flex rounded-full border border-orbit-pine/10 px-4 py-2 font-medium text-orbit-ink/75"
                }
              >
                {skipDelays ? "Skip Delays On" : "Skip Delays Off"}
              </button>
              <span className="text-orbit-ink/60">No new LLM calls are made during playback.</span>
            </div>
          </ShellCard>

          <ShellCard className="bg-orbit-pine text-orbit-mist">
            <SectionEyebrow>Current Speaker</SectionEyebrow>
            {currentEntry ? (
              (() => {
                const profile = speakerProfile(currentEntry.agent_role);
                const stance = stanceByRole[currentEntry.agent_role] ?? parseStance(currentEntry.statement_text);
                return (
                  <div className="mt-5 space-y-4">
                    <div className="flex flex-wrap items-center gap-4">
                      <div className={`flex h-16 w-16 items-center justify-center rounded-2xl border text-lg font-semibold ${profile.avatarClass}`}>
                        {profile.avatar}
                      </div>
                      <div>
                        <div className="text-xs uppercase tracking-[0.22em] text-orbit-moss">Now speaking</div>
                        <div className="mt-1 text-2xl font-semibold">{profile.displayRole}</div>
                        {profile.sourceRole ? <div className="mt-1 text-sm text-orbit-mist/70">Source persona: {profile.sourceRole}</div> : null}
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-3">
                      <StatusBadge label={humanize(currentEntry.statement_type)} />
                      <StatusBadge label={humanize(currentEntry.phase)} tone="warning" />
                      {stance ? <StatusBadge label={stance} tone={recommendationTone(stance)} /> : null}
                      {currentEntry.conflict_reference ? <StatusBadge label={currentEntry.conflict_reference} tone="danger" /> : null}
                    </div>
                    <p className="text-base leading-7 text-orbit-mist/88">{currentEntry.statement_text}</p>
                  </div>
                );
              })()
            ) : (
              <p className="mt-5 text-sm leading-6 text-orbit-mist/76">
                Start playback to reveal the opening statements and move into the conflict spotlight sequence.
              </p>
            )}
          </ShellCard>

          <ShellCard>
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
                          const stance = stanceByRole[entry.agent_role] ?? parseStance(entry.statement_text);
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
                                    {stance ? <StatusBadge label={stance} tone={recommendationTone(stance)} /> : null}
                                    {entry.conflict_reference ? <StatusBadge label={entry.conflict_reference} tone="danger" /> : null}
                                  </div>
                                  <p className="text-sm leading-6 text-orbit-ink/80">{entry.statement_text}</p>
                                </div>
                                <div className="text-sm leading-6 text-orbit-ink/60">
                                  <div>Recorded {formatDate(entry.created_at)}</div>
                                  <div>{entry.agent_id ? `Agent ${entry.agent_id}` : "System-generated"}</div>
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
          <ShellCard>
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

          <ShellCard className={activeSpotlight ? "committee-spotlight-ring" : ""}>
            <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div className="space-y-3">
                <SectionEyebrow>Conflict Spotlight</SectionEyebrow>
                <p className="max-w-2xl text-sm leading-6 text-orbit-ink/70">
                  Conflicts become visible as the boardroom reaches them. Each spotlight links the disagreement,
                  participant arguments, and moderator resolution into one inspection panel.
                </p>
              </div>
              {activeSpotlight ? <StatusBadge label={activeSpotlight.conflictReference} tone="danger" /> : null}
            </div>

            {activeSpotlight ? (
              <div className="mt-5 space-y-4">
                <div className="rounded-[24px] border border-orbit-gold/35 bg-orbit-gold/10 px-4 py-4">
                  <div className="text-xs uppercase tracking-[0.2em] text-orbit-pine/70">Conflict topic</div>
                  <p className="mt-3 text-sm leading-6 text-orbit-ink/80">
                    {activeSpotlight.identification?.statement_text ?? "Conflict identification has not been revealed yet."}
                  </p>
                </div>
                <div className="space-y-3">
                  {activeSpotlight.discussion.length ? (
                    activeSpotlight.discussion.map((entry) => {
                      const profile = speakerProfile(entry.agent_role);
                      const stance = stanceByRole[entry.agent_role] ?? parseStance(entry.statement_text);
                      return (
                        <div key={entry.deliberation_entry_row_id} className={`rounded-[24px] border px-4 py-4 ${profile.panelClass}`}>
                          <div className="flex flex-wrap items-center gap-3">
                            <div className={`flex h-10 w-10 items-center justify-center rounded-2xl border text-sm font-semibold ${profile.avatarClass}`}>
                              {profile.avatar}
                            </div>
                            <div className="text-sm font-semibold text-orbit-ink">{profile.displayRole}</div>
                            {stance ? <StatusBadge label={stance} tone={recommendationTone(stance)} /> : null}
                          </div>
                          <p className="mt-3 text-sm leading-6 text-orbit-ink/80">{entry.statement_text}</p>
                        </div>
                      );
                    })
                  ) : (
                    <div className="rounded-[24px] border border-dashed border-orbit-pine/15 bg-orbit-mist/35 px-4 py-4 text-sm leading-6 text-orbit-ink/65">
                      Participant arguments for this conflict will appear once playback reaches the conflict discussion phase.
                    </div>
                  )}
                </div>
                <div className="rounded-[24px] border border-slate-200 bg-slate-100/70 px-4 py-4">
                  <div className="text-xs uppercase tracking-[0.2em] text-slate-600">Moderator synthesis</div>
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

          <ShellCard className={verdictVisible ? "border-emerald-200 bg-emerald-50/80" : "bg-white/82"}>
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
