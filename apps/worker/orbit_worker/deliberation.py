from __future__ import annotations

from datetime import datetime, timedelta

from .persistence import DebatePersistenceBundle, ReviewPersistenceBundle, ResynthesisPersistenceBundle
from .schemas import DeliberationEntry, validate_deliberation_entry

CONFLICT_DETECTOR_ROLE = "Conflict Detector"
DEBATE_MODERATOR_ROLE = "Debate Moderator"
COMMITTEE_SYNTHESIS_ROLE = "Committee Synthesizer"
FINAL_VERDICT_ROLE = "ORBIT Committee"
PHASE_ORDER = (
    "opening_statements",
    "conflict_identification",
    "conflict_discussion",
    "moderator_synthesis",
    "final_verdict",
)


def _normalize_text(value: str, fallback: str, *, max_length: int = 360) -> str:
    candidate = " ".join((value or "").split())
    if not candidate:
        candidate = fallback
    return candidate[:max_length]


def _display_topic(value: str) -> str:
    return value.replace("_", " ")


def _entry_timestamp(base_time: datetime, sequence_number: int) -> datetime:
    return base_time + timedelta(milliseconds=sequence_number)


def _make_entry(
    *,
    run_id: str,
    portfolio_id: str,
    sequence_number: int,
    phase: str,
    agent_role: str,
    statement_type: str,
    statement_text: str,
    created_at: datetime,
    agent_id: str | None = None,
    conflict_reference: str | None = None,
) -> DeliberationEntry:
    return validate_deliberation_entry(
        {
            "run_id": run_id,
            "portfolio_id": portfolio_id,
            "sequence_number": sequence_number,
            "phase": phase,
            "agent_id": agent_id,
            "agent_role": agent_role,
            "statement_type": statement_type,
            "statement_text": statement_text,
            "conflict_reference": conflict_reference,
            "created_at": created_at,
        }
    )


def _active_verdict(
    review_bundle: ReviewPersistenceBundle,
    resynthesis_bundle: ResynthesisPersistenceBundle | None = None,
) -> tuple[str, str, float, str]:
    if (
        resynthesis_bundle is not None
        and resynthesis_bundle.resynthesis_session.active_artifact_source == "resynthesized"
        and resynthesis_bundle.resynthesized_scorecard is not None
        and resynthesis_bundle.resynthesized_committee_report is not None
    ):
        return (
            "resynthesized",
            resynthesis_bundle.resynthesized_scorecard.final_recommendation,
            resynthesis_bundle.resynthesized_scorecard.weighted_composite_score,
            resynthesis_bundle.resynthesized_committee_report.report_payload.executive_summary,
        )
    return (
        "original",
        review_bundle.scorecard.final_recommendation,
        review_bundle.scorecard.weighted_composite_score,
        review_bundle.committee_report.report_payload.executive_summary,
    )


def _discussion_round_by_conflict(
    review_bundle: ReviewPersistenceBundle,
    debate_bundle: DebatePersistenceBundle | None,
) -> dict[str, object]:
    if debate_bundle is None:
        return {}
    rounds = debate_bundle.debate_session.debate_payload.rounds
    mapping: dict[str, object] = {}
    for conflict in review_bundle.conflicts:
        expected_focus = f"{conflict.conflict_type}:{conflict.topic}"
        matching_round = next(
            (
                round_record
                for round_record in rounds
                if round_record.round_index == 1 and round_record.focus == expected_focus
            ),
            None,
        )
        if matching_round is not None:
            mapping[conflict.conflict_id] = matching_round
    return mapping


def build_deliberation_entries(
    review_bundle: ReviewPersistenceBundle,
    *,
    debate_bundle: DebatePersistenceBundle | None = None,
    resynthesis_bundle: ResynthesisPersistenceBundle | None = None,
) -> list[DeliberationEntry]:
    run_id = review_bundle.review_run.run_id
    portfolio_id = review_bundle.portfolio.portfolio_id
    review_time = review_bundle.review_run.completed_at or review_bundle.review_run.created_at
    debate_time = debate_bundle.debate_session.created_at if debate_bundle is not None else review_time
    verdict_time = (
        resynthesis_bundle.resynthesis_session.created_at
        if resynthesis_bundle is not None
        else debate_time
    )
    discussion_rounds = _discussion_round_by_conflict(review_bundle, debate_bundle)

    entries: list[DeliberationEntry] = []

    for review_record in review_bundle.agent_reviews:
        review = review_record.review_payload
        sequence_number = len(entries) + 1
        entries.append(
            _make_entry(
                run_id=run_id,
                portfolio_id=portfolio_id,
                sequence_number=sequence_number,
                phase="opening_statements",
                agent_id=review.agent_id,
                agent_role=review.agent_name,
                statement_type="opening_statement",
                statement_text=_normalize_text(
                    f"{review.recommendation}. {review.review_summary}",
                    f"{review.agent_name} issued a {review.recommendation} opening statement.",
                ),
                created_at=_entry_timestamp(review_time, sequence_number),
            )
        )

    if review_bundle.conflicts:
        for conflict in review_bundle.conflicts:
            sequence_number = len(entries) + 1
            entries.append(
                _make_entry(
                    run_id=run_id,
                    portfolio_id=portfolio_id,
                    sequence_number=sequence_number,
                    phase="conflict_identification",
                    agent_role=CONFLICT_DETECTOR_ROLE,
                    statement_type="conflict_identified",
                    statement_text=_normalize_text(
                        (
                            f"{conflict.conflict_type} was identified on {_display_topic(conflict.topic)} "
                            f"at {conflict.severity} severity. {conflict.conflict_payload.trigger_reason}"
                        ),
                        f"Conflict detector flagged {_display_topic(conflict.topic)} for committee review.",
                    ),
                    conflict_reference=conflict.conflict_id,
                    created_at=_entry_timestamp(review_time, sequence_number),
                )
            )
    else:
        sequence_number = len(entries) + 1
        entries.append(
            _make_entry(
                run_id=run_id,
                portfolio_id=portfolio_id,
                sequence_number=sequence_number,
                phase="conflict_identification",
                agent_role=CONFLICT_DETECTOR_ROLE,
                statement_type="phase_note",
                statement_text="Conflict detector found no material committee disagreements in the persisted review artifacts.",
                created_at=_entry_timestamp(review_time, sequence_number),
            )
        )

    if review_bundle.conflicts and debate_bundle is not None:
        for conflict in review_bundle.conflicts:
            discussion_round = discussion_rounds.get(conflict.conflict_id)
            if discussion_round is None:
                continue
            for position in discussion_round.participant_positions:
                sequence_number = len(entries) + 1
                entries.append(
                    _make_entry(
                        run_id=run_id,
                        portfolio_id=portfolio_id,
                        sequence_number=sequence_number,
                        phase="conflict_discussion",
                        agent_id=position.agent_id,
                        agent_role=position.agent_name,
                        statement_type="conflict_argument",
                        statement_text=_normalize_text(
                            position.conflict_view,
                            f"{position.agent_name} presented a bounded committee argument for {_display_topic(conflict.topic)}.",
                        ),
                        conflict_reference=conflict.conflict_id,
                        created_at=_entry_timestamp(debate_time, sequence_number),
                    )
                )
    elif review_bundle.conflicts:
        sequence_number = len(entries) + 1
        entries.append(
            _make_entry(
                run_id=run_id,
                portfolio_id=portfolio_id,
                sequence_number=sequence_number,
                phase="conflict_discussion",
                agent_role=DEBATE_MODERATOR_ROLE,
                statement_type="phase_note",
                statement_text="Persisted conflicts exist for this run, but no debate session has been materialized yet.",
                created_at=_entry_timestamp(debate_time, sequence_number),
            )
        )
    else:
        sequence_number = len(entries) + 1
        entries.append(
            _make_entry(
                run_id=run_id,
                portfolio_id=portfolio_id,
                sequence_number=sequence_number,
                phase="conflict_discussion",
                agent_role=DEBATE_MODERATOR_ROLE,
                statement_type="phase_note",
                statement_text="No focused conflict discussion was required because the review run produced no persisted conflicts.",
                created_at=_entry_timestamp(debate_time, sequence_number),
            )
        )

    if debate_bundle is not None and debate_bundle.conflict_resolutions:
        for resolution_record in debate_bundle.conflict_resolutions:
            resolution = resolution_record.resolution_payload
            summary_suffix = (
                " Score recheck was requested."
                if resolution.score_change_required
                else " Existing committee scoring was retained."
            )
            sequence_number = len(entries) + 1
            entries.append(
                _make_entry(
                    run_id=run_id,
                    portfolio_id=portfolio_id,
                    sequence_number=sequence_number,
                    phase="moderator_synthesis",
                    agent_role=DEBATE_MODERATOR_ROLE,
                    statement_type="moderator_synthesis",
                    statement_text=_normalize_text(
                        f"{resolution.resolution_summary}{summary_suffix}",
                        f"Debate moderator issued a bounded synthesis for {_display_topic(resolution.topic)}.",
                    ),
                    conflict_reference=resolution.conflict_id,
                    created_at=_entry_timestamp(debate_time, sequence_number),
                )
            )
    elif review_bundle.conflicts:
        sequence_number = len(entries) + 1
        entries.append(
            _make_entry(
                run_id=run_id,
                portfolio_id=portfolio_id,
                sequence_number=sequence_number,
                phase="moderator_synthesis",
                agent_role=DEBATE_MODERATOR_ROLE,
                statement_type="phase_note",
                statement_text="Moderator synthesis is pending because the conflict debate has not been materialized for this run.",
                created_at=_entry_timestamp(debate_time, sequence_number),
            )
        )
    else:
        sequence_number = len(entries) + 1
        entries.append(
            _make_entry(
                run_id=run_id,
                portfolio_id=portfolio_id,
                sequence_number=sequence_number,
                phase="moderator_synthesis",
                agent_role=DEBATE_MODERATOR_ROLE,
                statement_type="phase_note",
                statement_text="Moderator synthesis was not required because no persisted conflicts needed committee resolution.",
                created_at=_entry_timestamp(debate_time, sequence_number),
            )
        )

    artifact_source, final_recommendation, weighted_score, executive_summary = _active_verdict(
        review_bundle,
        resynthesis_bundle=resynthesis_bundle,
    )
    sequence_number = len(entries) + 1
    entries.append(
        _make_entry(
            run_id=run_id,
            portfolio_id=portfolio_id,
            sequence_number=sequence_number,
            phase="final_verdict",
            agent_role=FINAL_VERDICT_ROLE,
            statement_type="final_verdict",
            statement_text=_normalize_text(
                (
                    f"Final verdict: {final_recommendation} at weighted composite score {weighted_score:.2f} "
                    f"using {artifact_source} artifacts. {executive_summary}"
                ),
                f"ORBIT issued a final verdict of {final_recommendation} at score {weighted_score:.2f}.",
            ),
            created_at=_entry_timestamp(verdict_time, sequence_number),
        )
    )

    return entries
