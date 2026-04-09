// @ts-check
'use strict';

const { AGENT_REGISTRY, RECOMMENDATION_ORDER, RECOMMENDATION_RANK, SCORE_DIMENSIONS, clampScore } = require('../../orbit-core/src/domain');
const { validateAgentReview } = require('../../orbit-core/src/schema');

const POSITIVE_SIGNAL_META = {
  problem_strength: { title: 'Problem is concrete and tied to measurable pain', category: 'problem_validity', severity: 'minor', action: 'Carry the quantified business pain into pilot framing and scorecard rationale.' },
  buyer_clarity: { title: 'Initial buyer and adoption path are clearly identifiable', category: 'market_fit', severity: 'minor', action: 'Use the named buyer profile to constrain first-wave customer selection.' },
  monetization_clarity: { title: 'Commercial model shows early economic discipline', category: 'economic_viability', severity: 'minor', action: 'Translate margin and pricing assumptions into explicit launch conditions.' },
  market_story_strength: { title: 'Positioning is differentiated enough for a first GTM story', category: 'market_fit', severity: 'minor', action: 'Anchor the launch narrative on workflow acceleration and auditability.' },
  mvp_focus: { title: 'The MVP scope is focused enough for a thin-slice launch', category: 'product_quality', severity: 'minor', action: 'Protect the bounded workflow scope during the first release.' },
  workflow_traceability: { title: 'Traceability supports a defensible user workflow', category: 'product_quality', severity: 'minor', action: 'Retain traceability and approval export as non-negotiable product requirements.' },
  customer_value_clarity: { title: 'Customer value is easy to explain in operational terms', category: 'product_quality', severity: 'minor', action: 'Turn the value story into measurable onboarding outcomes.' },
  architecture_strength: { title: 'System design is coherent for an initial production slice', category: 'technical_feasibility', severity: 'minor', action: 'Preserve the current service separation and make deployment topology explicit.' },
  ai_controls: { title: 'Human approval and audit visibility improve AI control', category: 'ai_reliability', severity: 'minor', action: 'Keep human approval and output logging as hard launch constraints.' },
  ops_controls: { title: 'Operational controls are named early enough to shape launch criteria', category: 'operational_resilience', severity: 'minor', action: 'Convert the named controls into concrete runbooks and ownership assignments.' },
  security_controls: { title: 'Baseline governance controls are at least acknowledged', category: 'security_and_compliance', severity: 'minor', action: 'Carry redaction, auditability, and access control language into the first security review.' },
};

const RISK_SIGNAL_META = {
  integration_risk: { title: 'Integration complexity remains a first-wave risk', category: 'technical_feasibility', severity: 'moderate', action: 'Scope integration commitments explicitly and treat them as launch conditions.' },
  resilience_gap: { title: 'Recovery and release posture is not yet strong enough', category: 'operational_resilience', severity: 'major', action: 'Define recovery objectives, rollback rules, and validation steps before broader rollout.' },
  ai_evaluation_gap: { title: 'AI evaluation evidence is still incomplete', category: 'ai_reliability', severity: 'major', action: 'Define offline evaluation benchmarks and acceptance thresholds before scale.' },
  support_gap: { title: 'Support and sustainment readiness lag the product ambition', category: 'operational_resilience', severity: 'major', action: 'Assign ownership for onboarding, support, and maintenance before expanding pilots.' },
  compliance_gap: { title: 'Compliance posture is directionally positive but incomplete', category: 'security_and_compliance', severity: 'major', action: 'Add retention, identity, incident, and jurisdiction controls before broad rollout.' },
};

function clampUnit(value) {
  return Math.max(0, Math.min(1, Number(value.toFixed(2))));
}

function mean(values) {
  return values.length === 0 ? 0 : values.reduce((sum, value) => sum + value, 0) / values.length;
}

function collectText(portfolio, keys) {
  return keys.map((key) => {
    const section = portfolio.sections[key];
    return `${section.summary}\n${section.key_points.join('\n')}`;
  }).join('\n').toLowerCase();
}

function hasAny(text, patterns) {
  return patterns.some((pattern) => text.includes(pattern));
}

function analyzePortfolio(portfolio) {
  const problemText = collectText(portfolio, ['problem_discovery']);
  const visionText = collectText(portfolio, ['product_vision']);
  const competitiveText = collectText(portfolio, ['competitive_landscape']);
  const businessText = collectText(portfolio, ['business_requirements']);
  const productText = collectText(portfolio, ['product_requirements']);
  const architectureText = collectText(portfolio, ['architecture_system_design']);
  const aiText = collectText(portfolio, ['ai_agents_ethical_framework']);
  const opsText = collectText(portfolio, ['operational_resilience']);
  const roadmapText = collectText(portfolio, ['mvp_roadmap']);
  const metricsText = collectText(portfolio, ['success_metrics']);
  const postLaunchText = collectText(portfolio, ['post_launch_strategy']);
  const allText = [problemText, visionText, competitiveText, businessText, productText, architectureText, aiText, opsText, roadmapText, metricsText, postLaunchText].join('\n');
  const metricCount = (allText.match(/\b\d+(?:\.\d+)?\b/g) || []).length;

  const signals = {
    problem_strength: hasAny(problemText, ['cycle-time', 'hours', 'manual', 'auditability', 'workflow']),
    buyer_clarity: hasAny(`${problemText}\n${visionText}\n${businessText}`, ['vp procurement', 'cfo', 'buyer', 'procurement leadership', 'mid-market']),
    monetization_clarity: hasAny(`${businessText}\n${metricsText}`, ['gross margin', 'enterprise pricing', 'roi', 'pricing']),
    market_story_strength: hasAny(`${competitiveText}\n${visionText}`, ['workflow acceleration', 'differentiation', 'incumbents', 'time to value']),
    mvp_focus: hasAny(`${productText}\n${roadmapText}`, ['mvp', 'phase 1', 'approval packet', 'workflow', 'pilot customers']),
    workflow_traceability: hasAny(productText, ['traceability', 'audit trail', 'approval packet', 'comment threads']),
    customer_value_clarity: hasAny(`${problemText}\n${metricsText}`, ['cycle-time', 'throughput', 'adoption', 'retention', 'roi']),
    architecture_strength: hasAny(architectureText, ['web app', 'api', 'worker', 'event-driven', 'tenant isolation', 'data store']),
    ai_controls: hasAny(aiText, ['human approval', 'logged', 'redaction', 'access policy', 'visible to users']),
    ops_controls: hasAny(opsText, ['backup', 'monitoring', 'availability', 'recovery', 'staged rollout']),
    security_controls: hasAny(`${aiText}\n${opsText}`, ['redaction', 'access policy', 'audit', 'logged']),
    integration_risk: hasAny(`${architectureText}\n${postLaunchText}`, ['integration', 'connector', 'erp']),
    resilience_gap: hasAny(opsText, ['future enhancement', 'regional failover']) || !hasAny(opsText, ['rollback', 'drill', 'tested recovery']),
    ai_evaluation_gap: !hasAny(`${aiText}\n${metricsText}`, ['evaluation', 'benchmark', 'dataset', 'threshold']),
    support_gap: !hasAny(`${opsText}\n${postLaunchText}`, ['customer success', 'support', 'onboarding ownership']),
    compliance_gap: !hasAny(`${aiText}\n${opsText}\n${postLaunchText}`, ['retention', 'jurisdiction', 'incident response', 'identity', 'key management', 'regulatory']),
    metric_depth: metricCount >= 6,
  };

  const baseScores = {
    'Problem Validity': clampScore(3.2 + (signals.problem_strength ? 0.6 : 0) + (signals.buyer_clarity ? 0.3 : 0) + (signals.metric_depth ? 0.15 : 0)),
    'Market Fit': clampScore(3.0 + (signals.buyer_clarity ? 0.4 : 0) + (signals.market_story_strength ? 0.35 : 0) - (signals.integration_risk ? 0.1 : 0)),
    'Product Quality': clampScore(3.0 + (signals.mvp_focus ? 0.35 : 0) + (signals.workflow_traceability ? 0.3 : 0) + (signals.customer_value_clarity ? 0.15 : 0) - (signals.ai_evaluation_gap ? 0.1 : 0)),
    'Technical Feasibility': clampScore(3.0 + (signals.architecture_strength ? 0.55 : 0) + (signals.mvp_focus ? 0.15 : 0) - (signals.integration_risk ? 0.1 : 0)),
    'AI Reliability': clampScore(3.1 + (signals.ai_controls ? 0.4 : 0) - (signals.ai_evaluation_gap ? 0.2 : 0)),
    'Economic Viability': clampScore(3.0 + (signals.monetization_clarity ? 0.45 : 0) + (signals.customer_value_clarity ? 0.2 : 0) - (signals.integration_risk ? 0.15 : 0)),
    'Operational Resilience': clampScore(3.0 + (signals.ops_controls ? 0.3 : 0) + (signals.architecture_strength ? 0.2 : 0) - (signals.resilience_gap ? 0.25 : 0) - (signals.support_gap ? 0.12 : 0)),
    'Security & Compliance': clampScore(3.15 + (signals.security_controls ? 0.25 : 0) + (signals.ai_controls ? 0.15 : 0) - (signals.compliance_gap ? 0.15 : 0) - (signals.resilience_gap ? 0.05 : 0)),
  };

  const baseCompleteness = {
    'Problem Validity': clampUnit(0.7 + (signals.problem_strength ? 0.1 : 0) + (signals.metric_depth ? 0.08 : 0)),
    'Market Fit': clampUnit(0.66 + (signals.buyer_clarity ? 0.08 : 0) + (signals.market_story_strength ? 0.06 : 0)),
    'Product Quality': clampUnit(0.64 + (signals.mvp_focus ? 0.08 : 0) + (signals.workflow_traceability ? 0.08 : 0)),
    'Technical Feasibility': clampUnit(0.62 + (signals.architecture_strength ? 0.12 : 0) - (signals.integration_risk ? 0.04 : 0)),
    'AI Reliability': clampUnit(0.56 + (signals.ai_controls ? 0.14 : 0) - (signals.ai_evaluation_gap ? 0.04 : 0)),
    'Economic Viability': clampUnit(0.6 + (signals.monetization_clarity ? 0.12 : 0) - (signals.integration_risk ? 0.03 : 0)),
    'Operational Resilience': clampUnit(0.6 + (signals.ops_controls ? 0.12 : 0) - (signals.resilience_gap ? 0.05 : 0) - (signals.support_gap ? 0.03 : 0)),
    'Security & Compliance': clampUnit(0.58 + (signals.security_controls ? 0.08 : 0) + (signals.ai_controls ? 0.08 : 0) - (signals.compliance_gap ? 0.04 : 0)),
  };

  return { signals, baseScores, baseCompleteness };
}

function buildFinding(agent, portfolio, signalKey, kind, dimensionScores) {
  const meta = kind === 'positive' ? POSITIVE_SIGNAL_META[signalKey] : RISK_SIGNAL_META[signalKey];
  const scoreImpacts = dimensionScores.map((score) => ({
    dimension: score.dimension,
    delta: kind === 'positive' ? 0.15 : -0.25,
    rationale: `${agent.name} adjusts ${score.dimension} through ${signalKey}.`,
  }));
  return {
    finding_id: `${agent.id}-${kind}-${signalKey}`,
    title: meta.title,
    category: meta.category,
    severity: meta.severity,
    claim: `${agent.name} notes that ${meta.title.toLowerCase()} for this portfolio based on the available source material.`,
    evidence_refs: kind === 'positive' ? agent.positiveRefs : agent.riskRefs,
    assumptions: kind === 'risk' ? [agent.assumption] : [],
    recommended_action: meta.action,
    score_impacts: scoreImpacts,
  };
}

function scoreRecommendation(scoreAverage, completenessAverage, bias) {
  const weighted = scoreAverage + bias;
  if (weighted >= 4.15 && completenessAverage >= 0.72) {
    return 'Strong Proceed';
  }
  if (weighted >= 3.3) {
    return 'Proceed with Conditions';
  }
  if (weighted >= 2.55) {
    return 'Pilot Only';
  }
  if (weighted >= 1.8) {
    return 'High Risk';
  }
  return 'Do Not Proceed';
}

function downgradeRecommendation(recommendation, steps) {
  const current = RECOMMENDATION_RANK[recommendation];
  const nextIndex = Math.max(0, current - steps);
  return RECOMMENDATION_ORDER[nextIndex];
}

function buildAgentReview(agent, portfolio, analysis) {
  const positiveActive = analysis.signals[agent.positiveSignal];
  const riskActive = analysis.signals[agent.riskSignal];
  const dimensionScores = agent.dimensions.map((dimension) => {
    let score = analysis.baseScores[dimension] + (agent.dimensionBiases[dimension] || 0);
    if (riskActive) {
      score -= agent.strictness * 0.2;
    }
    if (positiveActive) {
      score += 0.05;
    }
    let completeness = analysis.baseCompleteness[dimension] + (positiveActive ? 0.03 : 0) - (riskActive ? agent.strictness * 0.12 : 0);
    const confidence = clampUnit(0.55 + (positiveActive ? 0.12 : 0) - (riskActive ? 0.08 : 0) + (completeness - 0.6) * 0.5 - agent.strictness * 0.05);
    completeness = clampUnit(completeness);
    const severityFlags = [];
    if (riskActive) {
      severityFlags.push(`${agent.riskSignal}_${dimension.toLowerCase().replace(/[^a-z0-9]+/g, '_')}`);
    }
    return {
      dimension,
      score: clampScore(score),
      confidence,
      evidence_completeness: completeness,
      severity_flags: severityFlags,
      rationale: `${agent.name} adjusts ${dimension} using deterministic thin-slice heuristics for ${agent.positiveSignal} and ${agent.riskSignal}.`,
      evidence_refs: Array.from(new Set([...agent.positiveRefs, ...agent.riskRefs])),
    };
  });

  const scoreAverage = mean(dimensionScores.map((score) => score.score));
  const completenessAverage = mean(dimensionScores.map((score) => score.evidence_completeness));
  let recommendation = scoreRecommendation(scoreAverage, completenessAverage, agent.recommendationBias);
  if (riskActive && agent.strictness >= 0.35 && scoreAverage < 3.2) {
    recommendation = downgradeRecommendation(recommendation, 1);
  }
  if (agent.id === 'legal_compliance_reviewer' && analysis.signals.compliance_gap && scoreAverage < 3.2) {
    recommendation = downgradeRecommendation(recommendation, 1);
  }

  const findings = [];
  if (positiveActive) {
    findings.push(buildFinding(agent, portfolio, agent.positiveSignal, 'positive', dimensionScores));
  }
  if (riskActive) {
    findings.push(buildFinding(agent, portfolio, agent.riskSignal, 'risk', dimensionScores));
  }

  const review = {
    agent_id: agent.id,
    agent_name: agent.name,
    portfolio_id: portfolio.portfolio_id,
    review_summary: `${agent.name} recommends ${recommendation} with strongest support in ${dimensionScores[0].dimension} and primary concern in ${agent.riskSignal}.`,
    findings,
    dimension_scores: dimensionScores,
    recommendation,
    open_questions: [agent.openQuestion],
    evidence_gaps: riskActive ? [agent.evidenceGap] : [],
    assumption_register: [agent.assumption],
    review_metadata: {
      prompt_contract_version: 'm0.5-deterministic-v1',
      model_provider: 'deterministic-thin-slice',
      model_name: 'heuristic-reviewer',
      duration_ms: 0,
    },
  };

  return validateAgentReview(review);
}

function runSpecialistReviews(portfolio) {
  const analysis = analyzePortfolio(portfolio);
  return AGENT_REGISTRY.map((agent) => buildAgentReview(agent, portfolio, analysis));
}

module.exports = {
  analyzePortfolio,
  runSpecialistReviews,
};

