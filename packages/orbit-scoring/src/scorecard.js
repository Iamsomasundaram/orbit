// @ts-check
'use strict';

const { DIMENSION_WEIGHTS, RECOMMENDATION_ORDER, RECOMMENDATION_RANK, SCORE_DIMENSIONS, clampScore } = require('../../orbit-core/src/domain');
const { validateScorecard } = require('../../orbit-core/src/schema');

function mean(values) {
  return values.length === 0 ? 0 : values.reduce((sum, value) => sum + value, 0) / values.length;
}

function downgradeRecommendation(recommendation) {
  const index = Math.max(0, RECOMMENDATION_RANK[recommendation] - 1);
  return RECOMMENDATION_ORDER[index];
}

function buildCommitteeScorecard(portfolio, runId, reviews, conflicts) {
  const dimensionScores = SCORE_DIMENSIONS.map((dimension) => {
    const entries = reviews.flatMap((review) => review.dimension_scores.filter((score) => score.dimension === dimension));
    const score = clampScore(mean(entries.map((entry) => entry.score)));
    const confidence = Number(mean(entries.map((entry) => entry.confidence)).toFixed(2));
    const evidenceCompleteness = Number(mean(entries.map((entry) => entry.evidence_completeness)).toFixed(2));
    const severityFlags = Array.from(new Set(entries.flatMap((entry) => entry.severity_flags))).sort();
    return {
      dimension,
      score,
      confidence,
      evidence_completeness: evidenceCompleteness,
      severity_flags: severityFlags,
      rationale: `Committee score derived from ${entries.length} structured reviewer dimension entries.`,
      evidence_refs: Array.from(new Set(entries.flatMap((entry) => entry.evidence_refs))),
    };
  });

  const weightedCompositeScore = Number((dimensionScores.reduce((sum, entry) => sum + (entry.score * DIMENSION_WEIGHTS[entry.dimension]), 0) / 100).toFixed(2));
  const averageConfidence = Number(mean(dimensionScores.map((entry) => entry.confidence)).toFixed(2));
  const averageEvidenceCompleteness = Number(mean(dimensionScores.map((entry) => entry.evidence_completeness)).toFixed(2));
  const severityFlags = Array.from(new Set(reviews.flatMap((review) => review.dimension_scores.flatMap((entry) => entry.severity_flags)))).sort();
  const findings = reviews.flatMap((review) => review.findings);
  const criticalGovernanceFinding = findings.find((finding) => finding.severity === 'critical' && ['security_and_compliance', 'ai_reliability'].includes(finding.category));

  let finalRecommendation;
  if (weightedCompositeScore >= 4.2 && averageConfidence >= 0.7 && averageEvidenceCompleteness >= 0.8 && !criticalGovernanceFinding) {
    finalRecommendation = 'Strong Proceed';
  } else if (weightedCompositeScore >= 3.5 && !criticalGovernanceFinding) {
    finalRecommendation = 'Proceed with Conditions';
  } else if (weightedCompositeScore >= 2.8) {
    finalRecommendation = 'Pilot Only';
  } else if (weightedCompositeScore >= 2.0) {
    finalRecommendation = 'High Risk';
  } else {
    finalRecommendation = 'Do Not Proceed';
  }

  const highConflicts = conflicts.filter((conflict) => conflict.severity === 'high').length;
  if (highConflicts >= 4 && RECOMMENDATION_RANK[finalRecommendation] > RECOMMENDATION_RANK['Pilot Only']) {
    finalRecommendation = downgradeRecommendation(finalRecommendation);
  }
  if (criticalGovernanceFinding && RECOMMENDATION_RANK[finalRecommendation] > RECOMMENDATION_RANK['High Risk']) {
    finalRecommendation = 'High Risk';
  }

  const conditions = Array.from(new Set([
    ...findings.filter((finding) => ['major', 'critical'].includes(finding.severity)).slice(0, 6).map((finding) => finding.recommended_action),
    ...conflicts.filter((conflict) => conflict.severity === 'high').slice(0, 3).map((conflict) => `Resolve ${conflict.conflict_type} on ${conflict.topic} before broad rollout.`),
  ])).slice(0, 8);

  return validateScorecard({
    portfolio_id: portfolio.portfolio_id,
    run_id: runId,
    dimension_scores: dimensionScores,
    weighted_composite_score: weightedCompositeScore,
    average_confidence: averageConfidence,
    average_evidence_completeness: averageEvidenceCompleteness,
    severity_flags: severityFlags,
    final_recommendation: finalRecommendation,
    override_applied: Boolean(criticalGovernanceFinding),
    conditions,
  });
}

module.exports = {
  buildCommitteeScorecard,
};
