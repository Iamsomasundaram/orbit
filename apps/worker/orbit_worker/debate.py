from __future__ import annotations

from .domain import dedupe_preserve_order
from .schemas import AgentReview, ConflictRecord, DebateSession, validate_debate_session

MODERATOR_ID = "debate_moderator"
MODERATOR_NAME = "ORBIT Debate Moderator"
MAX_DEBATE_ROUNDS = 2
CRITICAL_REVIEW_TOPICS = {"Security & Compliance", "AI Reliability", "security_and_compliance", "ai_reliability"}


def find_reviews(agent_reviews: list[AgentReview], participants: list[str]) -> list[AgentReview]:
    review_index = {review.agent_id: review for review in agent_reviews}
    return [review_index[participant] for participant in participants if participant in review_index]


def dimension_focus(review: AgentReview, topic: str) -> list[str]:
    matching = [score.dimension for score in review.dimension_scores if score.dimension == topic]
    if matching:
        return matching
    return [score.dimension for score in review.dimension_scores[:2]]


def position_view(review: AgentReview, conflict: ConflictRecord) -> str:
    dimension_names = ", ".join(dimension_focus(review, conflict.topic))
    return (
        f"{review.agent_name} maintains {review.recommendation} with emphasis on {dimension_names} "
        f"while responding to {conflict.conflict_type} on {conflict.topic}."
    )


def participant_positions(reviews: list[AgentReview], conflict: ConflictRecord) -> list[dict[str, object]]:
    return [
        {
            "agent_id": review.agent_id,
            "agent_name": review.agent_name,
            "recommendation": review.recommendation,
            "conflict_view": position_view(review, conflict),
            "cited_evidence_refs": dedupe_preserve_order(
                ref
                for score in review.dimension_scores
                for ref in score.evidence_refs
            )[:6],
            "dimension_focus": dimension_focus(review, conflict.topic),
        }
        for review in reviews
    ]


def moderator_prompt(conflict: ConflictRecord) -> str:
    return (
        f"Resolve {conflict.conflict_type} on {conflict.topic} using persisted structured reviewer outputs only. "
        "Keep the decision bounded, favor explicit conditions over ungrounded score changes, and mark score change "
        "requirements only when the conflict directly affects critical governance dimensions."
    )


def moderator_observation(conflict: ConflictRecord, reviews: list[AgentReview]) -> str:
    return (
        f"The moderator reviewed {len(reviews)} participant positions for {conflict.conflict_type} on {conflict.topic} "
        f"and found that the persisted evidence is sufficient to issue a bounded resolution at severity {conflict.severity}."
    )


def conflict_resolution(conflict: ConflictRecord) -> dict[str, object]:
    if conflict.conflict_type == "recommendation_conflict":
        return {
            "outcome": "accepted_with_condition",
            "resolution_summary": "Retain the existing committee recommendation and convert rollout disagreement into an explicit rollout gate.",
            "moderator_rationale": "The conflict affects rollout timing rather than the underlying committee evidence model, so the bounded resolution is to keep the current scorecard and tighten launch conditions.",
            "applied_conditions": [f"Resolve {conflict.topic} through a moderator-owned launch gate before broad rollout."],
            "score_change_required": False,
            "score_change_rationale": None,
            "follow_up_action": "Document the gating criteria in the committee recommendation pack.",
            "status": "completed",
        }
    if conflict.conflict_type == "assumption_mismatch":
        return {
            "outcome": "accepted_with_condition",
            "resolution_summary": "Adopt the more conservative interpretation until the assumption is validated with real evidence.",
            "moderator_rationale": "Assumption mismatches are best handled by freezing the more conservative operating assumption rather than changing committee scores without new evidence.",
            "applied_conditions": [f"Validate assumption topic {conflict.topic} and keep the conservative interpretation until evidence closes the gap."],
            "score_change_required": False,
            "score_change_rationale": None,
            "follow_up_action": f"Add explicit validation criteria for assumption topic {conflict.topic}.",
            "status": "completed",
        }
    if conflict.conflict_type == "score_divergence":
        score_change_required = conflict.severity == "high" and conflict.topic in CRITICAL_REVIEW_TOPICS
        return {
            "outcome": "needs_score_revisit" if score_change_required else "deferred",
            "resolution_summary": "Reconcile the divergent structured scores before any committee score change is applied.",
            "moderator_rationale": "Score divergence alone does not justify score mutation unless it lands on a critical governance dimension at high severity.",
            "applied_conditions": [f"Reconcile structured score evidence for {conflict.topic} before any broader rollout decision changes."],
            "score_change_required": score_change_required,
            "score_change_rationale": f"Critical structured score divergence on {conflict.topic} requires committee recheck." if score_change_required else None,
            "follow_up_action": f"Review the participant evidence chain for {conflict.topic}.",
            "status": "needs_review" if score_change_required else "completed",
        }
    if conflict.conflict_type == "evidence_completeness_mismatch":
        return {
            "outcome": "deferred",
            "resolution_summary": "Keep the current committee result and require evidence completeness reconciliation.",
            "moderator_rationale": "Evidence sufficiency mismatches should add a follow-up requirement rather than modify the scorecard without new material.",
            "applied_conditions": [f"Close the evidence completeness gap on {conflict.topic} before expanding scope."],
            "score_change_required": False,
            "score_change_rationale": None,
            "follow_up_action": f"Collect missing evidence for {conflict.topic}.",
            "status": "completed",
        }

    score_change_required = conflict.severity == "high" and conflict.topic in CRITICAL_REVIEW_TOPICS
    return {
        "outcome": "needs_score_revisit" if score_change_required else "accepted_with_condition",
        "resolution_summary": "Retain the current committee result while normalizing risk treatment through explicit conditions.",
        "moderator_rationale": "Severity disagreements are resolved conservatively by tightening conditions unless the disagreement affects a critical governance topic at high severity.",
        "applied_conditions": [f"Normalize risk handling expectations for {conflict.topic} before broader rollout."],
        "score_change_required": score_change_required,
        "score_change_rationale": f"High-severity governance disagreement on {conflict.topic} requires committee recheck." if score_change_required else None,
        "follow_up_action": f"Record the normalized risk handling standard for {conflict.topic}.",
        "status": "needs_review" if score_change_required else "completed",
    }


def rounds_for_conflict(conflict: ConflictRecord, reviews: list[AgentReview]) -> list[dict[str, object]]:
    positions = participant_positions(reviews, conflict)
    first_round = {
        "round_index": 1,
        "focus": f"{conflict.conflict_type}:{conflict.topic}",
        "moderator_prompt": moderator_prompt(conflict),
        "participant_positions": positions,
        "moderator_observation": moderator_observation(conflict, reviews),
        "exit_criteria_met": not conflict.debate_required,
    }
    if not conflict.debate_required:
        return [first_round]

    return [
        first_round,
        {
            "round_index": 2,
            "focus": f"resolution:{conflict.topic}",
            "moderator_prompt": "Issue the bounded conflict resolution and decide whether a score change is required.",
            "participant_positions": positions,
            "moderator_observation": f"The moderator completed the bounded debate for {conflict.topic} within {MAX_DEBATE_ROUNDS} rounds.",
            "exit_criteria_met": True,
        },
    ]


def resolution_record(conflict: ConflictRecord) -> dict[str, object]:
    resolution = conflict_resolution(conflict)
    return {
        "resolution_id": f"resolution-{conflict.conflict_id}",
        "conflict_id": conflict.conflict_id,
        "conflict_type": conflict.conflict_type,
        "topic": conflict.topic,
        **resolution,
    }


def run_bounded_debate(
    run_id: str,
    portfolio_id: str,
    conflicts: list[ConflictRecord],
    agent_reviews: list[AgentReview],
    debate_id: str,
) -> DebateSession:
    ordered_conflicts = sorted(conflicts, key=lambda conflict: (conflict.severity, conflict.conflict_id), reverse=True)
    rounds: list[dict[str, object]] = []
    resolutions = []
    for conflict in ordered_conflicts:
        reviews = find_reviews(agent_reviews, conflict.participants)
        rounds.extend(rounds_for_conflict(conflict, reviews))
        resolutions.append(resolution_record(conflict))

    score_change_count = len([resolution for resolution in resolutions if resolution["score_change_required"]])
    debate_status = "completed_with_escalations" if score_change_count else "completed"
    executive_summary = (
        f"Moderator-controlled debate completed for {len(conflicts)} persisted conflicts on run {run_id}. "
        f"{len(resolutions) - score_change_count} conflicts were resolved without score changes and "
        f"{score_change_count} conflict(s) were flagged for possible committee recheck."
    )
    return validate_debate_session(
        {
            "debate_id": debate_id,
            "run_id": run_id,
            "portfolio_id": portfolio_id,
            "moderator_id": MODERATOR_ID,
            "moderator_name": MODERATOR_NAME,
            "debate_status": debate_status,
            "max_rounds": MAX_DEBATE_ROUNDS,
            "rounds": rounds,
            "resolutions": resolutions,
            "executive_summary": executive_summary,
            "audit_notes": [
                "Debate used persisted structured conflict records and reviewer artifacts only.",
                f"Moderator rounds were bounded to {MAX_DEBATE_ROUNDS} per debate item.",
                "Scorecard state is unchanged unless a conflict resolution explicitly marks score_change_required.",
            ],
        }
    )
