# Worker App

The worker now contains the Milestone 0.5 thin-slice proof path.

Current capability:

- ingest one markdown portfolio document
- canonicalize it into the ORBIT section model
- run all 15 specialist reviewers with structured outputs
- detect structured conflicts
- build a committee scorecard
- generate a committee report in JSON and Markdown

Entry points:

- `apps/worker/src/review-runner.js`
- `apps/worker/src/cli/review-portfolio.js`
