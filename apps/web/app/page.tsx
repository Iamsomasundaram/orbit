import {
  FieldLabel,
  Input,
  MetricCard,
  PageFrame,
  SectionEyebrow,
  ShellCard,
  StatusBadge,
  SubmitButton,
  TextArea,
} from "@/app/orbit-ui";
import { getRuntimeConfig } from "@/lib/config";
import {
  type HealthPayload,
  type InfoPayload,
  type PersistenceCatalogPayload,
  type PortfolioListPayload,
  fetchOrbitJson,
  formatDate,
  humanize,
} from "@/lib/orbit-api";

type HomePageProps = {
  searchParams?: Promise<{ submissionError?: string }>;
};

export default async function HomePage({ searchParams }: HomePageProps) {
  const config = getRuntimeConfig();
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const [apiReady, apiInfo, persistenceCatalog, portfolioList] = await Promise.all([
    fetchOrbitJson<HealthPayload>("/health/ready"),
    fetchOrbitJson<InfoPayload>("/api/v1/system/info"),
    fetchOrbitJson<PersistenceCatalogPayload>("/api/v1/system/persistence/schema"),
    fetchOrbitJson<PortfolioListPayload>("/api/v1/portfolios"),
  ]);

  return (
    <PageFrame>
      <section className="rounded-[32px] border border-orbit-pine/10 bg-white/80 p-8 shadow-panel backdrop-blur md:p-10">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="max-w-3xl space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <StatusBadge label={`Milestone ${config.milestone}`} />
              <StatusBadge label={apiInfo?.reference_runtime_stage ?? "archived-baseline"} tone="success" />
            </div>
            <h1 className="text-4xl font-semibold tracking-tight md:text-6xl">
              Submit a new product idea, run the ORBIT committee, and inspect the full lineage without leaving the
              current platform shell.
            </h1>
            <p className="max-w-2xl text-base leading-7 text-orbit-ink/75 md:text-lg">
              Milestone 8 turns the approved deterministic backend into a first practical workflow: JSON idea
              submission, persisted canonicalization, review execution, automatic bounded debate and re-synthesis, and
              auditable result inspection.
            </p>
          </div>
          <div className="rounded-3xl bg-orbit-ink px-5 py-4 text-orbit-mist">
            <div className="text-xs uppercase tracking-[0.24em] text-orbit-moss">Runtime Direction</div>
            <div className="mt-2 text-2xl font-semibold">Interactive ORBIT Workflow</div>
            <div className="mt-1 text-sm text-orbit-mist/70">
              {apiInfo?.runtime_direction ?? "submission-review-history"}
            </div>
          </div>
        </div>
      </section>

      {resolvedSearchParams.submissionError ? (
        <ShellCard className="border-rose-200 bg-rose-50/90">
          <SectionEyebrow>Submission Error</SectionEyebrow>
          <p className="mt-3 text-sm leading-6 text-rose-800">{resolvedSearchParams.submissionError}</p>
        </ShellCard>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="API"
          value={apiReady?.status ?? "unreachable"}
          detail={
            apiReady
              ? `postgres=${apiReady.checks.find((item) => item.name === "postgres")?.status ?? "unknown"}, redis=${apiReady.checks.find((item) => item.name === "redis")?.status ?? "unknown"}`
              : "FastAPI readiness has not responded yet."
          }
        />
        <MetricCard
          label="Persistence"
          value={persistenceCatalog?.schema_version ?? apiInfo?.persistence_schema_version ?? "unknown"}
          detail={`${persistenceCatalog?.tables.length ?? apiInfo?.persistence_tables ?? 0} durable tables remain aligned to the Python contracts.`}
        />
        <MetricCard
          label="Portfolios"
          value={String(portfolioList?.items.length ?? 0)}
          detail="New ideas are accepted through the JSON submission path and persisted as canonical ORBIT portfolios."
        />
        <MetricCard
          label="Parity"
          value={apiInfo?.reference_runtime_stage ?? "archived-baseline"}
          detail={`The Docker Compose baseline profile still validates Python output against the archived artifact set from ${apiInfo?.reference_runtime_archival_target_milestone ?? "Milestone 7.1"}.`}
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <ShellCard>
          <SectionEyebrow>Submit a New Idea</SectionEyebrow>
          <form action="/api/portfolios" method="post" className="mt-5 space-y-5">
            <div>
              <FieldLabel htmlFor="portfolio_name">Idea name</FieldLabel>
              <Input id="portfolio_name" name="portfolio_name" placeholder="ProcurePilot" required />
            </div>
            <div>
              <FieldLabel htmlFor="owner">Owner</FieldLabel>
              <Input id="owner" name="owner" placeholder="Somasundaram P" required />
            </div>
            <div>
              <FieldLabel htmlFor="description">Idea description</FieldLabel>
              <TextArea
                id="description"
                name="description"
                required
                rows={8}
                placeholder="Describe the user problem, proposed workflow, and why ORBIT should review this idea now."
              />
            </div>
            <div>
              <FieldLabel htmlFor="tags">Optional tags</FieldLabel>
              <Input id="tags" name="tags" placeholder="ai-saas, procurement, workflow" />
            </div>
            <div className="flex flex-col gap-3 border-t border-orbit-pine/10 pt-4 text-sm text-orbit-ink/70 md:flex-row md:items-center md:justify-between">
              <span>
                Submission type is stored as <span className="font-mono text-xs">product_idea</span> in Milestone 8.
              </span>
              <SubmitButton>Create Portfolio</SubmitButton>
            </div>
          </form>
        </ShellCard>

        <ShellCard className="bg-orbit-pine text-orbit-mist">
          <SectionEyebrow>Recent Portfolios</SectionEyebrow>
          <div className="mt-5 space-y-4">
            {portfolioList?.items.length ? (
              portfolioList.items.slice(0, 5).map((portfolio) => (
                <div key={portfolio.portfolio_id} className="rounded-[24px] border border-white/10 bg-white/6 p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge label={humanize(portfolio.portfolio_status)} tone="warning" />
                    <span className="text-xs uppercase tracking-[0.2em] text-orbit-moss">
                      {humanize(portfolio.portfolio_type)}
                    </span>
                  </div>
                  <div className="mt-3 text-lg font-semibold">{portfolio.portfolio_name}</div>
                  <p className="mt-2 text-sm leading-6 text-orbit-mist/75">
                    {portfolio.owner} · submitted {formatDate(portfolio.submitted_at)}
                  </p>
                  <div className="mt-4 flex flex-wrap gap-3">
                    <a
                      className="inline-flex rounded-full border border-white/15 px-4 py-2 text-sm font-medium text-orbit-mist transition hover:border-white/35"
                      href={`/portfolios/${portfolio.portfolio_id}`}
                    >
                      Portfolio Detail
                    </a>
                    <a
                      className="inline-flex rounded-full border border-white/15 px-4 py-2 text-sm font-medium text-orbit-mist transition hover:border-white/35"
                      href={`/portfolios/${portfolio.portfolio_id}/history`}
                    >
                      Review History
                    </a>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm leading-6 text-orbit-mist/78">
                No user-submitted ideas are stored yet. The first submission through the form will create a canonical
                portfolio and open its history page.
              </p>
            )}
          </div>
        </ShellCard>
      </section>

      <ShellCard>
        <SectionEyebrow>Workflow Shape</SectionEyebrow>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <MetricCard
            label="Submission"
            value="JSON idea intake"
            detail="The web shell posts minimal idea fields and the API persists both source document and canonical portfolio artifacts."
          />
          <MetricCard
            label="Execution"
            value="Review + bounded follow-ons"
            detail="The review trigger reuses the existing deterministic worker path, then starts debate and optional re-synthesis automatically."
          />
          <MetricCard
            label="Inspection"
            value="History + artifacts"
            detail="Portfolio history and artifact APIs remain the source of truth for original versus active committee outputs."
          />
        </div>
      </ShellCard>
    </PageFrame>
  );
}
