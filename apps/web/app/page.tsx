import { fetchJson, getRuntimeConfig, type ServiceCard } from "@/lib/config";

type HealthPayload = {
  service: string;
  status: string;
  checks: Array<{ name: string; status: string; detail: string }>;
};

type InfoPayload = {
  service: string;
  environment: string;
  active_backend: string;
  reference_runtime: string;
  reference_runtime_stage: string;
  reference_runtime_archival_target_milestone: string;
  llm_provider: string;
  persistence_schema_version: string;
  persistence_tables: number;
};

type PersistenceCatalogPayload = {
  schema_version: string;
  tables: Array<{ table_name: string; purpose: string; source_contract: string | null }>;
};

type PortfolioListPayload = {
  items: Array<{ portfolio_id: string }>;
};

type PortfolioHistoryPayload = {
  review_run_count: number;
  debate_count: number;
  resynthesis_count: number;
};

export default async function HomePage() {
  const config = getRuntimeConfig();
  const [apiReady, apiInfo, persistenceCatalog, portfolioList] = await Promise.all([
    fetchJson<HealthPayload>(`${config.internalApiBaseUrl}/health/ready`),
    fetchJson<InfoPayload>(`${config.internalApiBaseUrl}/api/v1/system/info`),
    fetchJson<PersistenceCatalogPayload>(`${config.internalApiBaseUrl}/api/v1/system/persistence/schema`),
    fetchJson<PortfolioListPayload>(`${config.internalApiBaseUrl}/api/v1/portfolios`),
  ]);
  const history =
    portfolioList?.items?.[0] != null
      ? await fetchJson<PortfolioHistoryPayload>(
          `${config.internalApiBaseUrl}/api/v1/portfolios/${portfolioList.items[0].portfolio_id}/history`,
        )
      : null;

  const cards: ServiceCard[] = [
    {
      label: "API",
      value: apiReady?.status ?? "unreachable",
      detail: apiReady
        ? `postgres=${apiReady.checks.find((item) => item.name === "postgres")?.status ?? "unknown"}, redis=${apiReady.checks.find((item) => item.name === "redis")?.status ?? "unknown"}`
        : "FastAPI readiness has not responded yet.",
    },
    {
      label: "Persistence",
      value: persistenceCatalog?.schema_version ?? apiInfo?.persistence_schema_version ?? "unknown",
      detail: `${persistenceCatalog?.tables.length ?? apiInfo?.persistence_tables ?? 0} durable tables defined from the Python worker contracts.`,
    },
    {
      label: "History",
      value: `${history?.review_run_count ?? 0} runs`,
      detail:
        history != null
          ? `${history.debate_count} debates and ${history.resynthesis_count} re-syntheses are now inspectable through lineage-aware API responses.`
          : "Review history endpoints become active as soon as the first portfolio is stored.",
    },
    {
      label: "Baseline",
      value: apiInfo?.reference_runtime_stage ?? "frozen-baseline",
      detail: `${apiInfo?.reference_runtime ?? "js-baseline-only"} stays frozen until the archival target of ${apiInfo?.reference_runtime_archival_target_milestone ?? "Milestone 7.1"}.`,
    },
  ];

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-10 px-6 py-10 md:px-10">
      <section className="rounded-[32px] border border-orbit-pine/10 bg-white/80 p-8 shadow-panel backdrop-blur md:p-10">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="max-w-3xl space-y-4">
            <div className="inline-flex w-fit items-center rounded-full border border-orbit-pine/15 bg-orbit-mist px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-orbit-pine">
              Milestone {config.milestone} Review History and Artifact Inspection
            </div>
            <h1 className="text-4xl font-semibold tracking-tight md:text-6xl">
              {config.appName} now exposes lineage-aware review history and artifact inspection across portfolios, review runs, debates, and re-syntheses.
            </h1>
            <p className="max-w-2xl text-base leading-7 text-orbit-ink/75 md:text-lg">
              This milestone adds auditable history retrieval and explicit original-versus-active artifact visibility while keeping the approved committee behavior and Docker-first workflow unchanged.
            </p>
          </div>
          <div className="rounded-3xl bg-orbit-ink px-5 py-4 text-orbit-mist">
            <div className="text-xs uppercase tracking-[0.24em] text-orbit-moss">Artifact Lineage</div>
            <div className="mt-2 text-2xl font-semibold">Original and Active State</div>
            <div className="mt-1 text-sm text-orbit-mist/70">Provider: {apiInfo?.llm_provider ?? "openai"}</div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <article key={card.label} className="rounded-[28px] border border-orbit-pine/10 bg-white/75 p-6 shadow-panel backdrop-blur">
            <div className="text-xs uppercase tracking-[0.22em] text-orbit-pine/70">{card.label}</div>
            <div className="mt-3 text-2xl font-semibold capitalize">{card.value.replaceAll("-", " ")}</div>
            <p className="mt-3 text-sm leading-6 text-orbit-ink/70">{card.detail}</p>
          </article>
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.3fr_0.9fr]">
        <article className="rounded-[28px] border border-orbit-pine/10 bg-white/75 p-6 shadow-panel backdrop-blur">
          <div className="text-xs uppercase tracking-[0.22em] text-orbit-pine/70">Milestone 7 Scope</div>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-orbit-ink/80">
            <li>Portfolio history endpoints now expose lineage across canonical portfolio state, review runs, debates, and optional re-syntheses.</li>
            <li>Artifact inspection endpoints now show original versus active scorecard and committee report state without mutating approved committee outcomes.</li>
            <li>Docker Compose remains the primary workflow, with migrated persistence, live API inspection, and worker validation staying on the Python backend path.</li>
            <li>The JS baseline remains frozen reference-only while the active runtime continues to expose auditable lineage through Python-owned contracts.</li>
          </ul>
        </article>
        <article className="rounded-[28px] border border-orbit-pine/10 bg-orbit-pine p-6 text-orbit-mist shadow-panel">
          <div className="text-xs uppercase tracking-[0.22em] text-orbit-moss">Inspectable History</div>
          <p className="mt-4 text-lg leading-8">
            {portfolioList?.items.length ?? 0} canonical portfolio submissions are currently available to the Milestone 7 history and artifact inspection API surface.
          </p>
        </article>
      </section>
    </main>
  );
}
