#!/usr/bin/env node
// @ts-check
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { runReviewPipeline } = require('../review-runner');

const repoRoot = process.cwd();
const casesPath = path.join(repoRoot, 'tests', 'fixtures', 'parity-cases.json');
const portfolioCases = JSON.parse(fs.readFileSync(casesPath, 'utf8'));

for (const portfolioCase of portfolioCases) {
  const inputPath = path.resolve(repoRoot, portfolioCase.input_path);
  const outputDir = path.resolve(repoRoot, portfolioCase.baseline_dir);
  const result = runReviewPipeline(inputPath, outputDir);

  console.log(`[${portfolioCase.case_id}] ${result.canonicalPortfolio.portfolio_name}`);
  console.log(`  Agents executed: ${result.agentReviews.length}`);
  console.log(`  Conflicts detected: ${result.conflicts.length}`);
  console.log(`  Final recommendation: ${result.scorecard.final_recommendation}`);
  console.log(`  Weighted composite score: ${result.scorecard.weighted_composite_score.toFixed(2)}`);
  console.log(`  Artifacts written to: ${outputDir}`);
}
