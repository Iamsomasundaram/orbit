// @ts-check
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { runReviewPipeline } = require('../../apps/worker/src/review-runner');
const {
  validateAgentReview,
  validateCanonicalPortfolio,
  validateCommitteeReport,
  validateConflictRecord,
  validateScorecard,
} = require('../../packages/orbit-core/src/schema');

const inputPath = path.resolve('tests/fixtures/source-documents/procurepilot-thin-slice.md');

test('milestone 0.5 thin slice produces structured committee artifacts', () => {
  const outputDir = fs.mkdtempSync(path.join(os.tmpdir(), 'orbit-thin-slice-'));
  const result = runReviewPipeline(inputPath, outputDir);

  validateCanonicalPortfolio(result.canonicalPortfolio);
  assert.equal(result.agentReviews.length, 15);
  result.agentReviews.forEach(validateAgentReview);
  result.conflicts.forEach(validateConflictRecord);
  validateScorecard(result.scorecard);
  validateCommitteeReport(result.committeeReport);

  assert.equal(result.scorecard.final_recommendation, 'Proceed with Conditions');
  assert.ok(result.scorecard.weighted_composite_score >= 3.5 && result.scorecard.weighted_composite_score <= 4.2);
  assert.ok(result.conflicts.some((conflict) => conflict.conflict_type === 'recommendation_conflict'));
  assert.ok(result.conflicts.some((conflict) => conflict.conflict_type === 'assumption_mismatch'));
  assert.ok(result.conflicts.some((conflict) => conflict.conflict_type === 'risk_severity_mismatch'));
  assert.ok(fs.existsSync(path.join(outputDir, 'committee-report.md')));
  assert.ok(fs.existsSync(path.join(outputDir, 'scorecard.json')));
});
