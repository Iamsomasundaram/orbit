#!/usr/bin/env node
// @ts-check
'use strict';

const path = require('node:path');
const { runReviewPipeline } = require('../review-runner');

function parseArgs(argv) {
  const args = { inputPath: '', outputDir: '' };
  const positional = [];
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === '--output-dir') {
      args.outputDir = argv[index + 1];
      index += 1;
      continue;
    }
    positional.push(value);
  }
  args.inputPath = positional[0] || '';
  return args;
}

const args = parseArgs(process.argv.slice(2));
if (!args.inputPath) {
  console.error('Usage: node apps/worker/src/cli/review-portfolio.js <markdown-file> [--output-dir <dir>]');
  process.exit(1);
}

const result = runReviewPipeline(args.inputPath, args.outputDir);
console.log(`Run ID: ${result.runId}`);
console.log(`Portfolio: ${result.canonicalPortfolio.portfolio_name}`);
console.log(`Agents executed: ${result.agentReviews.length}`);
console.log(`Conflicts detected: ${result.conflicts.length}`);
console.log(`Final recommendation: ${result.scorecard.final_recommendation}`);
console.log(`Weighted composite score: ${result.scorecard.weighted_composite_score.toFixed(2)}`);
if (args.outputDir) {
  console.log(`Artifacts written to: ${path.resolve(args.outputDir)}`);
}
