// @ts-check
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { PORTFOLIO_SECTIONS, SECTION_TITLE_TO_KEY } = require('../../orbit-core/src/domain');
const { validateCanonicalPortfolio } = require('../../orbit-core/src/schema');

function slugify(value) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

function parseMetadata(lines) {
  const metadata = {};
  for (const line of lines) {
    const match = line.match(/^([A-Za-z ]+):\s*(.+)$/);
    if (!match) {
      continue;
    }
    const key = match[1].trim().toLowerCase().replace(/\s+/g, '_');
    metadata[key] = match[2].trim();
  }
  return metadata;
}

function buildSectionPayload(title, body) {
  const lines = body.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const keyPoints = lines.filter((line) => line.startsWith('- ')).map((line) => line.slice(2).trim());
  const summary = lines.find((line) => !line.startsWith('- ')) || 'Summary not provided.';
  return {
    title,
    summary,
    key_points: keyPoints,
    raw_text: body.trim(),
    evidence_ref: `portfolio.${SECTION_TITLE_TO_KEY[title.toLowerCase()]}`,
  };
}

function parseMarkdown(markdown, sourcePath) {
  const normalized = markdown.replace(/\r\n/g, '\n');
  const titleMatch = normalized.match(/^#\s+(.+)$/m);
  const portfolioTitle = titleMatch ? titleMatch[1].trim() : path.basename(sourcePath, path.extname(sourcePath));
  const firstSectionIndex = normalized.search(/^##\s+/m);
  const preamble = firstSectionIndex >= 0 ? normalized.slice(0, firstSectionIndex) : normalized;
  const metadata = parseMetadata(preamble.split('\n'));
  const sectionRegex = /^##\s+(.+)$/gm;
  const matches = Array.from(normalized.matchAll(sectionRegex));
  const sections = {};

  for (let index = 0; index < matches.length; index += 1) {
    const current = matches[index];
    const next = matches[index + 1];
    const title = current[1].trim();
    const key = SECTION_TITLE_TO_KEY[title.toLowerCase()];
    if (!key) {
      continue;
    }
    const start = current.index + current[0].length;
    const end = next ? next.index : normalized.length;
    sections[key] = buildSectionPayload(title, normalized.slice(start, end));
  }

  const canonical = {
    portfolio_id: metadata.portfolio_id || slugify(portfolioTitle),
    portfolio_name: metadata.portfolio_name || portfolioTitle.replace(/\s+Portfolio$/i, ''),
    portfolio_type: metadata.portfolio_type || 'product',
    owner: metadata.owner || 'Unknown Owner',
    submitted_at: metadata.submitted_at || '2026-04-09',
    source_documents: [
      { id: 'source-markdown-001', kind: 'markdown', title: path.basename(sourcePath), path: sourcePath },
    ],
    sections,
  };

  for (const section of PORTFOLIO_SECTIONS) {
    if (!canonical.sections[section.key]) {
      canonical.sections[section.key] = {
        title: section.title,
        summary: 'Missing section in source document.',
        key_points: [],
        raw_text: '',
        evidence_ref: `portfolio.${section.key}`,
      };
    }
  }

  return validateCanonicalPortfolio(canonical);
}

function ingestPortfolioDocument(sourcePath) {
  const absolutePath = path.resolve(sourcePath);
  const markdown = fs.readFileSync(absolutePath, 'utf8');
  return parseMarkdown(markdown, absolutePath);
}

module.exports = {
  ingestPortfolioDocument,
  parseMarkdown,
};
