from __future__ import annotations

from datetime import datetime
from typing import Literal

from orbit_worker.persistence import PersistenceRepository, PortfolioRecord
from orbit_worker.schemas import OrbitModel

from .history import LineagePath, ReviewHistoryService

PortfolioWorkspaceSortField = Literal[
    "latest_updated_at",
    "portfolio_name",
    "weighted_composite_score",
    "recommendation_rank",
    "conflict_count",
    "score_change_required_count",
]
PortfolioWorkspaceRankingField = Literal[
    "weighted_composite_score",
    "recommendation_rank",
    "conflict_count",
    "score_change_required_count",
]
SortDirection = Literal["asc", "desc"]

RECOMMENDATION_RANKS = {
    "Strong Proceed": 5,
    "Proceed with Conditions": 4,
    "Pilot Only": 3,
    "High Risk": 2,
    "Do Not Proceed": 1,
}


class PortfolioWorkspaceEntry(OrbitModel):
    portfolio: PortfolioRecord
    latest_review_status: str | None = None
    latest_final_recommendation: str | None = None
    latest_weighted_composite_score: float | None = None
    active_artifact_source: Literal["original", "resynthesized"] | None = None
    agent_review_count: int = 0
    conflict_count: int = 0
    score_change_required_count: int = 0
    review_run_count: int = 0
    debate_count: int = 0
    resynthesis_count: int = 0
    latest_updated_at: datetime
    latest_lineage: LineagePath | None = None
    recommendation_rank: int | None = None


class PortfolioWorkspaceSummaryResponse(OrbitModel):
    sort_by: PortfolioWorkspaceSortField
    direction: SortDirection
    items: list[PortfolioWorkspaceEntry]


class PortfolioComparisonResponse(OrbitModel):
    requested_portfolio_ids: list[str]
    items: list[PortfolioWorkspaceEntry]


class PortfolioRankingEntry(PortfolioWorkspaceEntry):
    rank: int


class PortfolioRankingResponse(OrbitModel):
    sort_by: PortfolioWorkspaceRankingField
    direction: SortDirection
    items: list[PortfolioRankingEntry]


class PortfolioWorkspaceValidationError(ValueError):
    pass


class PortfolioWorkspaceNotFoundError(ValueError):
    pass


def _recommendation_rank(recommendation: str | None) -> int | None:
    if recommendation is None:
        return None
    return RECOMMENDATION_RANKS.get(recommendation)


def _latest_updated_at(entry: PortfolioWorkspaceEntry) -> datetime:
    return entry.latest_updated_at


def _sort_metric_value(
    entry: PortfolioWorkspaceEntry,
    sort_by: PortfolioWorkspaceSortField | PortfolioWorkspaceRankingField,
) -> float | int | datetime | str | None:
    if sort_by == "latest_updated_at":
        return entry.latest_updated_at
    if sort_by == "portfolio_name":
        return entry.portfolio.portfolio_name.lower()
    if sort_by == "weighted_composite_score":
        return entry.latest_weighted_composite_score
    if sort_by == "recommendation_rank":
        return entry.recommendation_rank
    if sort_by == "conflict_count":
        return entry.conflict_count if entry.latest_lineage is not None else None
    if sort_by == "score_change_required_count":
        return entry.score_change_required_count if entry.latest_lineage is not None else None
    return None


def _sorted_workspace_entries(
    entries: list[PortfolioWorkspaceEntry],
    *,
    sort_by: PortfolioWorkspaceSortField | PortfolioWorkspaceRankingField,
    direction: SortDirection,
) -> list[PortfolioWorkspaceEntry]:
    if sort_by == "portfolio_name":
        return sorted(
            entries,
            key=lambda entry: (entry.portfolio.portfolio_name.lower(), entry.portfolio.portfolio_id),
            reverse=direction == "desc",
        )

    present_entries = [
        entry for entry in entries if _sort_metric_value(entry, sort_by) is not None
    ]
    missing_entries = [
        entry for entry in entries if _sort_metric_value(entry, sort_by) is None
    ]

    def metric_number(entry: PortfolioWorkspaceEntry) -> float:
        metric = _sort_metric_value(entry, sort_by)
        if isinstance(metric, datetime):
            return metric.timestamp()
        return float(metric)  # type: ignore[arg-type]

    def sort_key(entry: PortfolioWorkspaceEntry) -> tuple[float, int, float, float, str]:
        primary_metric = metric_number(entry)
        if direction == "desc":
            primary_metric = -primary_metric
        latest_score = entry.latest_weighted_composite_score if entry.latest_weighted_composite_score is not None else -1.0
        return (
            primary_metric,
            -(_recommendation_rank(entry.latest_final_recommendation) or 0),
            -latest_score,
            -_latest_updated_at(entry).timestamp(),
            entry.portfolio.portfolio_id,
        )

    ordered_present_entries = sorted(present_entries, key=sort_key)
    ordered_missing_entries = sorted(
        missing_entries,
        key=lambda entry: (
            entry.portfolio.portfolio_name.lower(),
            entry.portfolio.portfolio_id,
        ),
    )
    return ordered_present_entries + ordered_missing_entries


class PortfolioWorkspaceService:
    def __init__(self, repository: PersistenceRepository) -> None:
        self._repository = repository
        self._history = ReviewHistoryService(repository=repository)

    def _build_entry(self, portfolio_id: str) -> PortfolioWorkspaceEntry:
        history = self._history.get_portfolio_history(portfolio_id)
        if history is None:
            raise PortfolioWorkspaceNotFoundError(f"Portfolio '{portfolio_id}' was not found.")

        latest_item = history.items[0] if history.items else None
        latest_artifacts = None
        if latest_item is not None:
            latest_artifacts = self._history.get_review_run_artifacts(latest_item.review_run.run_id)

        audit_timestamps = [event.created_at for event in history.audit_events]
        latest_updated_at = max([history.portfolio.updated_at, *audit_timestamps])

        return PortfolioWorkspaceEntry(
            portfolio=history.portfolio,
            latest_review_status=latest_item.review_run.review_status if latest_item is not None else None,
            latest_final_recommendation=(
                latest_item.active_final_recommendation if latest_item is not None else None
            ),
            latest_weighted_composite_score=(
                latest_item.active_weighted_composite_score if latest_item is not None else None
            ),
            active_artifact_source=(
                latest_item.artifact_selection.active_artifact_source if latest_item is not None else None
            ),
            agent_review_count=latest_artifacts.agent_review_count if latest_artifacts is not None else 0,
            conflict_count=latest_artifacts.conflict_count if latest_artifacts is not None else 0,
            score_change_required_count=(
                latest_item.artifact_selection.score_change_required_count if latest_item is not None else 0
            ),
            review_run_count=history.review_run_count,
            debate_count=history.debate_count,
            resynthesis_count=history.resynthesis_count,
            latest_updated_at=latest_updated_at,
            latest_lineage=latest_item.lineage if latest_item is not None else None,
            recommendation_rank=_recommendation_rank(
                latest_item.active_final_recommendation if latest_item is not None else None
            ),
        )

    def _all_entries(self) -> list[PortfolioWorkspaceEntry]:
        return [
            self._build_entry(bundle.portfolio.portfolio_id)
            for bundle in self._repository.list_portfolio_bundles()
        ]

    def list_summary(
        self,
        *,
        sort_by: PortfolioWorkspaceSortField = "latest_updated_at",
        direction: SortDirection = "desc",
    ) -> PortfolioWorkspaceSummaryResponse:
        return PortfolioWorkspaceSummaryResponse(
            sort_by=sort_by,
            direction=direction,
            items=_sorted_workspace_entries(self._all_entries(), sort_by=sort_by, direction=direction),
        )

    def compare(self, portfolio_ids: list[str]) -> PortfolioComparisonResponse:
        normalized_portfolio_ids: list[str] = []
        seen_ids: set[str] = set()
        for portfolio_id in portfolio_ids:
            candidate = portfolio_id.strip()
            if not candidate or candidate in seen_ids:
                continue
            normalized_portfolio_ids.append(candidate)
            seen_ids.add(candidate)

        if not normalized_portfolio_ids:
            raise PortfolioWorkspaceValidationError("At least one portfolio_id is required for comparison.")

        missing_portfolio_ids = [
            portfolio_id
            for portfolio_id in normalized_portfolio_ids
            if self._repository.get_portfolio_bundle(portfolio_id) is None
        ]
        if missing_portfolio_ids:
            quoted = ", ".join(f"'{portfolio_id}'" for portfolio_id in missing_portfolio_ids)
            raise PortfolioWorkspaceNotFoundError(f"Portfolio IDs were not found: {quoted}.")

        return PortfolioComparisonResponse(
            requested_portfolio_ids=normalized_portfolio_ids,
            items=[self._build_entry(portfolio_id) for portfolio_id in normalized_portfolio_ids],
        )

    def rank(
        self,
        *,
        sort_by: PortfolioWorkspaceRankingField = "weighted_composite_score",
        direction: SortDirection = "desc",
    ) -> PortfolioRankingResponse:
        ordered_entries = _sorted_workspace_entries(
            self._all_entries(),
            sort_by=sort_by,
            direction=direction,
        )
        return PortfolioRankingResponse(
            sort_by=sort_by,
            direction=direction,
            items=[
                PortfolioRankingEntry(rank=index + 1, **entry.model_dump(mode="python"))
                for index, entry in enumerate(ordered_entries)
            ],
        )
