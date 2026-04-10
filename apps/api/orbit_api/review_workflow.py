from __future__ import annotations

from orbit_worker.schemas import OrbitModel

from .debates import DebateSummary, DebateService
from .review_runs import ReviewRunService, ReviewRunSummary
from .resyntheses import ResynthesisSummary, ResynthesisService


class ReviewWorkflowSummary(OrbitModel):
    review_run: ReviewRunSummary
    debate: DebateSummary | None = None
    resynthesis: ResynthesisSummary | None = None


class ReviewWorkflowService:
    def __init__(
        self,
        review_runs: ReviewRunService,
        debates: DebateService,
        resyntheses: ResynthesisService,
    ) -> None:
        self._review_runs = review_runs
        self._debates = debates
        self._resyntheses = resyntheses

    def start_review(self, portfolio_id: str) -> ReviewWorkflowSummary:
        review_run = self._review_runs.start_review(portfolio_id)
        debate = None
        resynthesis = None

        if review_run.conflict_count > 0:
            debate = self._debates.start_debate(review_run.run_id)
            if debate.score_change_required_count > 0:
                resynthesis = self._resyntheses.start_resynthesis(debate.debate_id)

        return ReviewWorkflowSummary(
            review_run=review_run,
            debate=debate,
            resynthesis=resynthesis,
        )
