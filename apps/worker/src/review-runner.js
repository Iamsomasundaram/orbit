// @ts-check
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { ingestPortfolioDocument } = require('../../../packages/orbit-ingestion/src/markdown-intake');
const { runSpecialistReviews } = require('../../../packages/orbit-agents/src/reviewer');
const { detectConflicts } = require('../../../packages/orbit-debate/src/conflicts');
const { buildCommitteeScorecard } = require('../../../packages/orbit-scoring/src/scorecard');
const { buildCommitteeReport } = require('../../../packages/orbit-reporting/src/report');

function writeJson(filePath, value) {
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function runReviewPipeline(inputPath, outputDir) {
  const canonicalPortfolio = ingestPortfolioDocument(inputPath);
  const runId = `thin-slice-${canonicalPortfolio.portfolio_id}`;
  const agentReviews = runSpecialistReviews(canonicalPortfolio);
  const conflicts = detectConflicts(agentReviews);
  const scorecard = buildCommitteeScorecard(canonicalPortfolio, runId, agentReviews, conflicts);
  const committeeReport = buildCommitteeReport(canonicalPortfolio, runId, agentReviews, conflicts, scorecard);

  if (outputDir) {
    const resolvedOutputDir = path.resolve(outputDir);
    fs.mkdirSync(resolvedOutputDir, { recursive: true });
    writeJson(path.join(resolvedOutputDir, 'canonical-portfolio.json'), canonicalPortfolio);
    writeJson(path.join(resolvedOutputDir, 'agent-reviews.json'), agentReviews);
    writeJson(path.join(resolvedOutputDir, 'conflicts.json'), conflicts);
    writeJson(path.join(resolvedOutputDir, 'scorecard.json'), scorecard);
    writeJson(path.join(resolvedOutputDir, 'committee-report.json'), committeeReport);
    fs.writeFileSync(path.join(resolvedOutputDir, 'committee-report.md'), committeeReport.markdown, 'utf8');
  }

  return {
    runId,
    canonicalPortfolio,
    agentReviews,
    conflicts,
    scorecard,
    committeeReport,
  };
}

module.exports = {
  runReviewPipeline,
};
