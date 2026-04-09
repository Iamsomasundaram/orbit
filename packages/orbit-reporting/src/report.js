// @ts-check
'use strict';

const { validateCommitteeReport } = require('../../orbit-core/src/schema');

function severityRank(value) {
  return { critical: 5, major: 4, moderate: 3, minor: 2, informational: 1 }[value] || 0;
}

function buildMarkdown(portfolio, scorecard, report) {
  const scoreRows = scorecard.dimension_scores.map((entry) => `| ${entry.dimension} | ${entry.score.toFixed(2)} | ${entry.confidence.toFixed(2)} | ${entry.evidence_completeness.toFixed(2)} |`).join('\n');
  const findings = report.top_findings.map((finding) => `- ${finding.title} (${finding.severity}): ${finding.claim}`).join('\n');
  const conflicts = report.top_conflicts.map((conflict) => `- ${conflict.conflict_type} on ${conflict.topic}: ${conflict.trigger_reason}`).join('\n');
  const conditions = report.conditions.map((condition) => `- ${condition}`).join('\n');
  const auditNotes = report.audit_notes.map((note) => `- ${note}`).join('\n');

  return [
    `# ORBIT Committee Report: ${portfolio.portfolio_name}`,
    '',
    `Final recommendation: **${scorecard.final_recommendation}**`,
    `Weighted composite score: **${scorecard.weighted_composite_score.toFixed(2)} / 5.00**`,
    `Average confidence: **${scorecard.average_confidence.toFixed(2)}**`,
    `Average evidence completeness: **${scorecard.average_evidence_completeness.toFixed(2)}**`,
    '',
    '## Executive Summary',
    report.executive_summary,
    '',
    '## Scorecard',
    '| Dimension | Score | Confidence | Evidence Completeness |',
    '| --- | ---: | ---: | ---: |',
    scoreRows,
    '',
    '## Top Findings',
    findings,
    '',
    '## Top Conflicts',
    conflicts || '- No conflicts detected.',
    '',
    '## Conditions',
    conditions || '- No additional conditions.',
    '',
    '## Audit Notes',
    auditNotes,
    '',
  ].join('\n');
}

function buildCommitteeReport(portfolio, runId, reviews, conflicts, scorecard) {
  const topFindings = reviews
    .flatMap((review) => review.findings.map((finding) => ({ ...finding, agent_id: review.agent_id })))
    .sort((left, right) => severityRank(right.severity) - severityRank(left.severity) || left.title.localeCompare(right.title))
    .slice(0, 8);
  const topConflicts = conflicts.slice(0, 5);
  const executiveSummary = `${portfolio.portfolio_name} completes the Milestone 0.5 thin-slice review with ${reviews.length} specialist reviews, ${conflicts.length} structured conflicts, and a final recommendation of ${scorecard.final_recommendation}. The committee sees strong business and product potential, but it still requires explicit integration, resilience, and governance conditions before broader rollout.`;
  const report = {
    portfolio_id: portfolio.portfolio_id,
    run_id: runId,
    executive_summary: executiveSummary,
    top_findings: topFindings,
    top_conflicts: topConflicts,
    conditions: scorecard.conditions,
    audit_notes: [
      'Thin slice executed with deterministic structured reviewer logic for all 15 agents.',
      `Conflict detector v1 evaluated ${conflicts.length} structured conflict records.`,
      'Scorecard recommendation follows the Milestone 0 override rules for governance blockers.',
    ],
    markdown: '',
  };
  report.markdown = buildMarkdown(portfolio, scorecard, report);
  return validateCommitteeReport(report);
}

module.exports = {
  buildCommitteeReport,
};
