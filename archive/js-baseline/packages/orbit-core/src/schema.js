// @ts-check
'use strict';

const { AGENT_REGISTRY, PORTFOLIO_SECTIONS, RECOMMENDATION_RANK, SCORE_DIMENSIONS, SEVERITY_RANK } = require('./domain');

function invariant(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function assertString(value, message) {
  invariant(typeof value === 'string' && value.trim().length > 0, message);
}

function assertNumber(value, message) {
  invariant(typeof value === 'number' && Number.isFinite(value), message);
}

function assertArray(value, message) {
  invariant(Array.isArray(value), message);
}

function assertObject(value, message) {
  invariant(Boolean(value) && typeof value === 'object' && !Array.isArray(value), message);
}

function validateCanonicalPortfolio(portfolio) {
  assertObject(portfolio, 'Canonical portfolio must be an object.');
  assertString(portfolio.portfolio_id, 'Canonical portfolio requires portfolio_id.');
  assertString(portfolio.portfolio_name, 'Canonical portfolio requires portfolio_name.');
  assertString(portfolio.portfolio_type, 'Canonical portfolio requires portfolio_type.');
  assertString(portfolio.owner, 'Canonical portfolio requires owner.');
  assertString(portfolio.submitted_at, 'Canonical portfolio requires submitted_at.');
  assertObject(portfolio.sections, 'Canonical portfolio requires sections.');
  for (const section of PORTFOLIO_SECTIONS) {
    const value = portfolio.sections[section.key];
    assertObject(value, `Missing section ${section.key}.`);
    assertString(value.title, `Section ${section.key} requires title.`);
    assertString(value.summary, `Section ${section.key} requires summary.`);
    assertArray(value.key_points, `Section ${section.key} requires key_points.`);
  }
  return portfolio;
}

function validateFinding(finding) {
  assertObject(finding, 'Finding must be an object.');
  assertString(finding.finding_id, 'Finding requires finding_id.');
  assertString(finding.title, 'Finding requires title.');
  assertString(finding.category, 'Finding requires category.');
  assertString(finding.severity, 'Finding requires severity.');
  invariant(Object.hasOwn(SEVERITY_RANK, finding.severity), `Unsupported severity ${finding.severity}.`);
  assertString(finding.claim, 'Finding requires claim.');
  assertArray(finding.evidence_refs, 'Finding requires evidence_refs.');
  assertString(finding.recommended_action, 'Finding requires recommended_action.');
  assertArray(finding.assumptions, 'Finding requires assumptions.');
  assertArray(finding.score_impacts, 'Finding requires score_impacts.');
  return finding;
}

function validateDimensionScore(score) {
  assertObject(score, 'Dimension score must be an object.');
  assertString(score.dimension, 'Dimension score requires dimension.');
  invariant(SCORE_DIMENSIONS.includes(score.dimension), `Unsupported dimension ${score.dimension}.`);
  assertNumber(score.score, `Dimension score ${score.dimension} requires score.`);
  assertNumber(score.confidence, `Dimension score ${score.dimension} requires confidence.`);
  assertNumber(score.evidence_completeness, `Dimension score ${score.dimension} requires evidence_completeness.`);
  assertArray(score.severity_flags, `Dimension score ${score.dimension} requires severity_flags.`);
  assertString(score.rationale, `Dimension score ${score.dimension} requires rationale.`);
  assertArray(score.evidence_refs, `Dimension score ${score.dimension} requires evidence_refs.`);
  return score;
}

function validateAgentReview(review) {
  assertObject(review, 'Agent review must be an object.');
  assertString(review.agent_id, 'Agent review requires agent_id.');
  const agent = AGENT_REGISTRY.find((candidate) => candidate.id === review.agent_id);
  invariant(Boolean(agent), `Unknown agent_id ${review.agent_id}.`);
  assertString(review.agent_name, 'Agent review requires agent_name.');
  assertString(review.portfolio_id, 'Agent review requires portfolio_id.');
  assertString(review.review_summary, 'Agent review requires review_summary.');
  assertArray(review.findings, 'Agent review requires findings.');
  review.findings.forEach(validateFinding);
  assertArray(review.dimension_scores, 'Agent review requires dimension_scores.');
  review.dimension_scores.forEach(validateDimensionScore);
  assertString(review.recommendation, 'Agent review requires recommendation.');
  invariant(Object.hasOwn(RECOMMENDATION_RANK, review.recommendation), `Unsupported recommendation ${review.recommendation}.`);
  assertArray(review.open_questions, 'Agent review requires open_questions.');
  assertArray(review.evidence_gaps, 'Agent review requires evidence_gaps.');
  assertArray(review.assumption_register, 'Agent review requires assumption_register.');
  assertObject(review.review_metadata, 'Agent review requires review_metadata.');
  return review;
}

function validateConflictRecord(conflict) {
  assertObject(conflict, 'Conflict must be an object.');
  assertString(conflict.conflict_id, 'Conflict requires conflict_id.');
  assertString(conflict.conflict_type, 'Conflict requires conflict_type.');
  assertString(conflict.topic, 'Conflict requires topic.');
  assertArray(conflict.participants, 'Conflict requires participants.');
  assertString(conflict.severity, 'Conflict requires severity.');
  assertString(conflict.trigger_reason, 'Conflict requires trigger_reason.');
  assertArray(conflict.supporting_artifacts, 'Conflict requires supporting_artifacts.');
  invariant(typeof conflict.debate_required === 'boolean', 'Conflict requires debate_required boolean.');
  assertString(conflict.routing_reason, 'Conflict requires routing_reason.');
  assertString(conflict.status, 'Conflict requires status.');
  return conflict;
}

function validateScorecard(scorecard) {
  assertObject(scorecard, 'Scorecard must be an object.');
  assertString(scorecard.portfolio_id, 'Scorecard requires portfolio_id.');
  assertString(scorecard.run_id, 'Scorecard requires run_id.');
  assertArray(scorecard.dimension_scores, 'Scorecard requires dimension_scores.');
  scorecard.dimension_scores.forEach(validateDimensionScore);
  assertNumber(scorecard.weighted_composite_score, 'Scorecard requires weighted_composite_score.');
  assertNumber(scorecard.average_confidence, 'Scorecard requires average_confidence.');
  assertNumber(scorecard.average_evidence_completeness, 'Scorecard requires average_evidence_completeness.');
  assertArray(scorecard.severity_flags, 'Scorecard requires severity_flags.');
  assertString(scorecard.final_recommendation, 'Scorecard requires final_recommendation.');
  invariant(Object.hasOwn(RECOMMENDATION_RANK, scorecard.final_recommendation), `Unsupported final recommendation ${scorecard.final_recommendation}.`);
  invariant(typeof scorecard.override_applied === 'boolean', 'Scorecard requires override_applied boolean.');
  assertArray(scorecard.conditions, 'Scorecard requires conditions.');
  return scorecard;
}

function validateCommitteeReport(report) {
  assertObject(report, 'Committee report must be an object.');
  assertString(report.portfolio_id, 'Committee report requires portfolio_id.');
  assertString(report.run_id, 'Committee report requires run_id.');
  assertString(report.executive_summary, 'Committee report requires executive_summary.');
  assertArray(report.top_findings, 'Committee report requires top_findings.');
  report.top_findings.forEach(validateFinding);
  assertArray(report.top_conflicts, 'Committee report requires top_conflicts.');
  report.top_conflicts.forEach(validateConflictRecord);
  assertArray(report.conditions, 'Committee report requires conditions.');
  assertArray(report.audit_notes, 'Committee report requires audit_notes.');
  assertString(report.markdown, 'Committee report requires markdown.');
  return report;
}

module.exports = {
  validateAgentReview,
  validateCanonicalPortfolio,
  validateCommitteeReport,
  validateConflictRecord,
  validateScorecard,
};
