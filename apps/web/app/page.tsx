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
  llm_provider: string;
};

export default async function HomePage() {
  const config = getRuntimeConfig();
  const [apiReady, apiInfo] = await Promise.all([
    fetchJson<HealthPayload>(`${config.internalApiBaseUrl}/health/ready`),
    fetchJson<InfoPayload>(`${config.internalApiBaseUrl}/api/v1/system/info`),
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
      label: "Worker",
      value: "python-primary",
      detail: "Milestone 0.5a Python runtime remains the active backend execution path.",
    },
    {
      label: "Baseline",
      value: apiInfo?.reference_runtime ?? "js-baseline-only",
      detail: "The JS thin-slice remains reference-only and is not the active backend direction.",
    },
    {
      label: "Environment",
      value: apiInfo?.environment ?? "local",
      detail: `Public API URL ${config.publicApiBaseUrl}`,
    },
  ];

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-10 px-6 py-10 md:px-10">
      <section className="rounded-[32px] border border-orbit-pine/10 bg-white/80 p-8 shadow-panel backdrop-blur md:p-10">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="max-w-3xl space-y-4">
            <div className="inline-flex w-fit items-center rounded-full border border-orbit-pine/15 bg-orbit-mist px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-orbit-pine">
              Milestone {config.milestone} Platform Foundation
            </div>
            <h1 className="text-4xl font-semibold tracking-tight md:text-6xl">
              {config.appName} local platform is now anchored around the Python backend path.
            </h1>
            <p className="max-w-2xl text-base leading-7 text-orbit-ink/75 md:text-lg">
              This foundation stage adds the web shell, FastAPI control plane, Python worker service, and local dockerized dependencies without altering the approved committee behavior from Milestones 0.5 and 0.5a.
            </p>
          </div>
          <div className="rounded-3xl bg-orbit-ink px-5 py-4 text-orbit-mist">
            <div className="text-xs uppercase tracking-[0.24em] text-orbit-moss">Runtime</div>
            <div className="mt-2 text-2xl font-semibold">{apiInfo?.active_backend ?? "python"}</div>
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
          <div className="text-xs uppercase tracking-[0.22em] text-orbit-pine/70">Foundation Scope</div>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-orbit-ink/80">
            <li>Compose-managed `web`, `api`, `worker`, `postgres`, and `redis` services.</li>
            <li>Typed Python config and health endpoints for the control plane and worker runtime.</li>
            <li>Active backend direction fixed on Python, with JS preserved as baseline-only reference.</li>
            <li>Carry-forward planning captured for parity coverage, JS archival, and CI regression strategy.</li>
          </ul>
        </article>
        <article className="rounded-[28px] border border-orbit-pine/10 bg-orbit-pine p-6 text-orbit-mist shadow-panel">
          <div className="text-xs uppercase tracking-[0.22em] text-orbit-moss">Next Gate</div>
          <p className="mt-4 text-lg leading-8">
            Milestone 2 stays blocked until this foundation layer is reviewed and accepted through the Ralph review pack.
          </p>
        </article>
      </section>
    </main>
  );
}
