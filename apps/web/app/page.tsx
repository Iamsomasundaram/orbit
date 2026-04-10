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

export default async function HomePage() {
  const config = getRuntimeConfig();
  const [apiReady, apiInfo, persistenceCatalog, portfolioList] = await Promise.all([
    fetchJson<HealthPayload>(`${config.internalApiBaseUrl}/health/ready`),
    fetchJson<InfoPayload>(`${config.internalApiBaseUrl}/api/v1/system/info`),
    fetchJson<PersistenceCatalogPayload>(`${config.internalApiBaseUrl}/api/v1/system/persistence/schema`),
    fetchJson<PortfolioListPayload>(`${config.internalApiBaseUrl}/api/v1/portfolios`),
  ]);

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
      label: "Ingestion API",
      value: `${portfolioList?.items.length ?? 0} stored`,
      detail: "The stored canonical portfolio base now feeds persisted review runs, debate sessions, and bounded committee re-synthesis through the Python backend path.",
    },
    {
      label: "Baseline",
      value: apiInfo?.reference_runtime_stage ?? "frozen-baseline",
      detail: `${apiInfo?.reference_runtime ?? "js-baseline-only"} stays frozen until the archival target of ${apiInfo?.reference_runtime_archival_target_milestone ?? "Milestone 7"}.`,
    },
  ];

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-10 px-6 py-10 md:px-10">
      <section className="rounded-[32px] border border-orbit-pine/10 bg-white/80 p-8 shadow-panel backdrop-blur md:p-10">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="max-w-3xl space-y-4">
            <div className="inline-flex w-fit items-center rounded-full border border-orbit-pine/15 bg-orbit-mist px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-orbit-pine">
              Milestone {config.milestone} Persistence and Migration Hardening
            </div>
            <h1 className="text-4xl font-semibold tracking-tight md:text-6xl">
              {config.appName} now runs on an explicit migration baseline and stronger DB-backed persistence guarantees without changing the approved committee behavior.
            </h1>
            <p className="max-w-2xl text-base leading-7 text-orbit-ink/75 md:text-lg">
              This milestone hardens schema evolution, duplicate enforcement, and local Docker workflow discipline around the existing portfolio, review, debate, and re-synthesis paths.
            </p>
          </div>
          <div className="rounded-3xl bg-orbit-ink px-5 py-4 text-orbit-mist">
            <div className="text-xs uppercase tracking-[0.24em] text-orbit-moss">Migration Discipline</div>
            <div className="mt-2 text-2xl font-semibold">Schema Before Runtime</div>
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
          <div className="text-xs uppercase tracking-[0.22em] text-orbit-pine/70">Milestone 6.1 Scope</div>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-orbit-ink/80">
            <li>Alembic now owns the baseline persistence schema, and API startup expects a migrated database instead of creating tables implicitly.</li>
            <li>Portfolio submission, debate creation, and re-synthesis creation now rely on stronger DB-backed uniqueness enforcement where practical.</li>
            <li>Docker Compose remains the primary workflow, with migrations applied before API and worker startup and the worker still exposed on port `5004` for debugging.</li>
            <li>Original review artifacts and optional re-synthesized artifacts keep the approved bounded behavior and storage semantics from Milestones 5 and 6.</li>
          </ul>
        </article>
        <article className="rounded-[28px] border border-orbit-pine/10 bg-orbit-pine p-6 text-orbit-mist shadow-panel">
          <div className="text-xs uppercase tracking-[0.22em] text-orbit-moss">Stored Portfolios</div>
          <p className="mt-4 text-lg leading-8">
            {portfolioList?.items.length ?? 0} canonical portfolio submissions are currently available to the hardened Milestone 6.1 review, debate, and re-synthesis API surface.
          </p>
        </article>
      </section>
    </main>
  );
}
