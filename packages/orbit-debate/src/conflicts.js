// @ts-check
'use strict';

const { getRecommendationDistance, SEVERITY_RANK } = require('../../orbit-core/src/domain');
const { validateConflictRecord } = require('../../orbit-core/src/schema');

function pairwise(items) {
  const pairs = [];
  for (let left = 0; left < items.length; left += 1) {
    for (let right = left + 1; right < items.length; right += 1) {
      pairs.push([items[left], items[right]]);
    }
  }
  return pairs;
}

function assumptionMap(review) {
  return Object.fromEntries(review.assumption_register.map((entry) => entry.split('=')));
}

function createConflict(conflictId, type, topic, participants, severity, triggerReason, routingReason) {
  return validateConflictRecord({
    conflict_id: conflictId,
    conflict_type: type,
    topic,
    participants: Array.from(new Set(participants)).sort(),
    severity,
    trigger_reason: triggerReason,
    supporting_artifacts: Array.from(new Set(participants)).sort().map((participant) => `agent_review.${participant}`),
    debate_required: severity === 'high',
    routing_reason: routingReason,
    status: 'open',
  });
}

function detectConflicts(reviews) {
  const recommendationParticipants = new Set();
  const assumptionClusters = new Map();
  const scoreClusters = new Map();
  const completenessClusters = new Map();
  const severityClusters = new Map();

  for (const [left, right] of pairwise(reviews)) {
    const recommendationDistance = getRecommendationDistance(left.recommendation, right.recommendation);
    if (recommendationDistance >= 2) {
      recommendationParticipants.add(left.agent_id);
      recommendationParticipants.add(right.agent_id);
    }

    const leftAssumptions = assumptionMap(left);
    const rightAssumptions = assumptionMap(right);
    for (const [topic, value] of Object.entries(leftAssumptions)) {
      if (rightAssumptions[topic] && rightAssumptions[topic] !== value) {
        const cluster = assumptionClusters.get(topic) || { participants: new Set(), examples: new Set() };
        cluster.participants.add(left.agent_id);
        cluster.participants.add(right.agent_id);
        cluster.examples.add(`${value} vs ${rightAssumptions[topic]}`);
        assumptionClusters.set(topic, cluster);
      }
    }

    for (const leftScore of left.dimension_scores) {
      const rightScore = right.dimension_scores.find((candidate) => candidate.dimension === leftScore.dimension);
      if (!rightScore) {
        continue;
      }
      const scoreDelta = Math.abs(leftScore.score - rightScore.score);
      if (scoreDelta >= 1.5) {
        const cluster = scoreClusters.get(leftScore.dimension) || { participants: new Set(), maxDelta: 0 };
        cluster.participants.add(left.agent_id);
        cluster.participants.add(right.agent_id);
        cluster.maxDelta = Math.max(cluster.maxDelta, scoreDelta);
        scoreClusters.set(leftScore.dimension, cluster);
      }
      const completenessDelta = Math.abs(leftScore.evidence_completeness - rightScore.evidence_completeness);
      if (completenessDelta >= 0.35) {
        const cluster = completenessClusters.get(leftScore.dimension) || { participants: new Set(), maxDelta: 0 };
        cluster.participants.add(left.agent_id);
        cluster.participants.add(right.agent_id);
        cluster.maxDelta = Math.max(cluster.maxDelta, completenessDelta);
        completenessClusters.set(leftScore.dimension, cluster);
      }
    }

    const leftCategories = Object.fromEntries(left.findings.map((finding) => [finding.category, finding]));
    for (const finding of right.findings) {
      const matching = leftCategories[finding.category];
      if (!matching) {
        continue;
      }
      const severityDelta = Math.abs(SEVERITY_RANK[matching.severity] - SEVERITY_RANK[finding.severity]);
      if (severityDelta >= 2) {
        const cluster = severityClusters.get(finding.category) || { participants: new Set(), maxDelta: 0 };
        cluster.participants.add(left.agent_id);
        cluster.participants.add(right.agent_id);
        cluster.maxDelta = Math.max(cluster.maxDelta, severityDelta);
        severityClusters.set(finding.category, cluster);
      }
    }
  }

  const conflicts = [];
  let index = 1;
  if (recommendationParticipants.size > 0) {
    conflicts.push(createConflict(
      `conflict-${String(index).padStart(3, '0')}`,
      'recommendation_conflict',
      'rollout_timing',
      recommendationParticipants,
      'high',
      `${recommendationParticipants.size} reviewers are separated by at least two recommendation tiers on rollout timing.`,
      'Recommendation polarity differs enough to alter rollout guidance.'
    ));
    index += 1;
  }

  for (const [topic, cluster] of assumptionClusters.entries()) {
    conflicts.push(createConflict(
      `conflict-${String(index).padStart(3, '0')}`,
      'assumption_mismatch',
      topic,
      cluster.participants,
      'medium',
      `Assumption topic ${topic} contains incompatible values including ${Array.from(cluster.examples).join('; ')}.`,
      'Different assumptions could distort committee synthesis.'
    ));
    index += 1;
  }

  for (const [dimension, cluster] of scoreClusters.entries()) {
    conflicts.push(createConflict(
      `conflict-${String(index).padStart(3, '0')}`,
      'score_divergence',
      dimension,
      cluster.participants,
      'high',
      `Maximum score delta ${cluster.maxDelta.toFixed(2)} exceeds the 1.50 threshold on ${dimension}.`,
      'Committee scoring could shift materially after reconciliation.'
    ));
    index += 1;
  }

  for (const [dimension, cluster] of completenessClusters.entries()) {
    conflicts.push(createConflict(
      `conflict-${String(index).padStart(3, '0')}`,
      'evidence_completeness_mismatch',
      dimension,
      cluster.participants,
      'high',
      `Maximum completeness delta ${cluster.maxDelta.toFixed(2)} exceeds the 0.35 threshold on ${dimension}.`,
      'Evidence sufficiency differs materially across reviewers.'
    ));
    index += 1;
  }

  for (const [category, cluster] of severityClusters.entries()) {
    conflicts.push(createConflict(
      `conflict-${String(index).padStart(3, '0')}`,
      'risk_severity_mismatch',
      category,
      cluster.participants,
      'medium',
      `Maximum severity delta ${cluster.maxDelta} exceeds the structured threshold on ${category}.`,
      'Risk handling guidance differs enough to require committee attention.'
    ));
    index += 1;
  }

  return conflicts.sort((left, right) => {
    const severityOrder = { high: 3, medium: 2, low: 1 };
    return severityOrder[right.severity] - severityOrder[left.severity] || left.conflict_id.localeCompare(right.conflict_id);
  });
}

module.exports = {
  detectConflicts,
};
