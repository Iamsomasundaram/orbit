import { getRuntimeConfig } from "@/lib/config";

export type HealthPayload = {
  service: string;
  status: string;
  checks: Array<{ name: string; status: string; detail: string }>;
};

export type InfoPayload = {
  service: string;
  environment: string;
  milestone: string;
  runtime_mode: string;
  active_backend: string;
  reference_runtime: string;
  reference_runtime_stage: string;
  reference_runtime_archival_target_milestone: string;
  llm_provider: string;
  openai_model: string;
  llm_max_concurrency: number;
  persistence_schema_version: string;
  persistence_tables: number;
  runtime_direction: string;
};

export type PersistenceCatalogPayload = {
  schema_version: string;
  tables: Array<{ table_name: string; purpose: string; source_contract: string | null }>;
};

export type PortfolioSummary = {
  portfolio_id: string;
  portfolio_name: string;
  portfolio_type: string;
  owner: string;
  submitted_at: string;
  portfolio_status: string;
  source_document_count: number;
  canonical_schema_version: string;
  created_at: string;
  updated_at: string;
};

export type PortfolioListPayload = {
  items: PortfolioSummary[];
};

export type PortfolioRecord = {
  portfolio_id: string;
  portfolio_name: string;
  portfolio_type: string;
  owner: string;
  submitted_at: string;
  portfolio_status: string;
  latest_review_run_id: string | null;
  created_at: string;
  updated_at: string;
};

export type SourceDocumentRecord = {
  source_document_row_id: string;
  source_document_id: string;
  portfolio_id: string;
  kind: string;
  title: string;
  path: string;
  document_hash: string;
  content_available: boolean;
  created_at: string;
};

export type CanonicalPortfolioRecord = {
  canonical_portfolio_row_id: string;
  portfolio_id: string;
  schema_version: string;
  section_count: number;
  portfolio_payload_hash: string;
  created_at: string;
};

export type PortfolioDetailPayload = {
  portfolio: PortfolioRecord;
  source_documents: SourceDocumentRecord[];
  canonical_portfolio: CanonicalPortfolioRecord;
  audit_events: Array<{ event_id: string; action: string; created_at: string }>;
};

export type ReviewRunSummary = {
  run_id: string;
  portfolio_id: string;
  review_status: string;
  final_recommendation: string;
  weighted_composite_score: number;
  agent_review_count: number;
  conflict_count: number;
  created_at: string;
  completed_at: string | null;
};

export type DebateSummary = {
  debate_id: string;
  run_id: string;
  portfolio_id: string;
  debate_status: string;
  conflicts_considered: number;
  score_change_required_count: number;
  created_at: string;
};

export type ResynthesisSummary = {
  resynthesis_id: string;
  debate_id: string;
  run_id: string;
  portfolio_id: string;
  resynthesis_status: string;
  score_change_required_count: number;
  active_artifact_source: string;
  created_at: string;
};

export type ArtifactSelectionState = {
  active_artifact_source: "original" | "resynthesized";
  has_resynthesized_artifacts: boolean;
  score_change_required_count: number;
};

export type ReviewHistoryItem = {
  lineage: {
    portfolio_id: string;
    review_run_id: string;
    debate_id: string | null;
    resynthesis_id: string | null;
  };
  review_run: ReviewRunSummary;
  debate: DebateSummary | null;
  resynthesis: ResynthesisSummary | null;
  artifact_selection: ArtifactSelectionState;
  active_final_recommendation: string;
  active_weighted_composite_score: number;
};

export type PortfolioHistoryPayload = {
  portfolio: PortfolioRecord;
  canonical_portfolio: CanonicalPortfolioRecord;
  source_documents: SourceDocumentRecord[];
  latest_review_run_id: string | null;
  review_run_count: number;
  debate_count: number;
  resynthesis_count: number;
  items: ReviewHistoryItem[];
  audit_events: Array<{ event_id: string; action: string; created_at: string }>;
};

export type ArtifactInspectionPayload = {
  anchor_type: "review_run" | "debate" | "resynthesis";
  anchor_id: string;
  artifact_selection: ArtifactSelectionState;
  agent_review_count: number;
  conflict_count: number;
  active_scorecard: {
    final_recommendation: string;
    weighted_composite_score: number;
  };
  review_run: {
    run_id: string;
    review_status: string;
    completed_at: string | null;
  };
  debate_session: {
    debate_id: string;
    debate_status: string;
    conflicts_considered: number;
    score_change_required_count: number;
  } | null;
  resynthesis_session: {
    resynthesis_id: string;
    resynthesis_status: string;
    active_artifact_source: string;
    score_change_required_count: number;
  } | null;
};

export type PortfolioWorkspaceEntry = {
  portfolio: PortfolioRecord;
  latest_review_status: string | null;
  latest_final_recommendation: string | null;
  latest_weighted_composite_score: number | null;
  active_artifact_source: "original" | "resynthesized" | null;
  agent_review_count: number;
  conflict_count: number;
  score_change_required_count: number;
  review_run_count: number;
  debate_count: number;
  resynthesis_count: number;
  latest_updated_at: string;
  latest_lineage: {
    portfolio_id: string;
    review_run_id: string;
    debate_id: string | null;
    resynthesis_id: string | null;
  } | null;
  recommendation_rank: number | null;
};

export type PortfolioWorkspaceSummaryPayload = {
  sort_by: string;
  direction: "asc" | "desc";
  items: PortfolioWorkspaceEntry[];
};

export type PortfolioComparisonPayload = {
  requested_portfolio_ids: string[];
  items: PortfolioWorkspaceEntry[];
};

export type PortfolioRankingEntry = PortfolioWorkspaceEntry & {
  rank: number;
};

export type PortfolioRankingPayload = {
  sort_by: string;
  direction: "asc" | "desc";
  items: PortfolioRankingEntry[];
};

type ApiErrorPayload = {
  detail?: string;
};

export class OrbitApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "OrbitApiError";
    this.status = status;
  }
}

function buildUrl(baseUrl: string, path: string): string {
  return `${baseUrl.replace(/\/$/, "")}${path}`;
}

export async function fetchOrbitJson<T>(path: string): Promise<T | null> {
  const config = getRuntimeConfig();
  try {
    const response = await fetch(buildUrl(config.internalApiBaseUrl, path), { cache: "no-store" });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export async function postOrbitJson<T>(path: string, body: unknown): Promise<T> {
  const config = getRuntimeConfig();
  const response = await fetch(buildUrl(config.internalApiBaseUrl, path), {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `ORBIT API request failed with status ${response.status}.`;
    try {
      const payload = (await response.json()) as ApiErrorPayload;
      if (typeof payload.detail === "string" && payload.detail.trim()) {
        detail = payload.detail;
      }
    } catch {
      // Preserve the fallback message when the backend does not emit JSON.
    }
    throw new OrbitApiError(response.status, detail);
  }

  return (await response.json()) as T;
}

export function publicApiHref(path: string): string {
  const config = getRuntimeConfig();
  return buildUrl(config.publicApiBaseUrl, path);
}

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "Not available";
  }
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return new Intl.DateTimeFormat("en-IN", {
      dateStyle: "medium",
      timeZone: "UTC",
    }).format(new Date(`${value}T00:00:00Z`));
  }
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(new Date(value));
}

export function formatScore(value: number | null | undefined): string {
  return typeof value === "number" ? value.toFixed(2) : "Not available";
}

export function humanize(value: string): string {
  return value.replaceAll("_", " ").replaceAll("-", " ");
}

export function parseTags(value: string): string[] {
  return value
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);
}
