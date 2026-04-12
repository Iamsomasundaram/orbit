"use client";

import { startTransition, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { FieldLabel, SectionEyebrow, ShellCard } from "@/app/orbit-ui";

const FIELD_CLASS =
  "mt-2 w-full rounded-2xl border border-orbit-pine/10 bg-white px-4 py-3 text-sm text-orbit-ink shadow-sm outline-none transition focus:border-orbit-pine/40 focus:ring-2 focus:ring-orbit-gold/25 disabled:cursor-not-allowed disabled:bg-orbit-mist/40";

const TEXTAREA_CLASS =
  "mt-2 w-full rounded-3xl border border-orbit-pine/10 bg-white px-4 py-3 text-sm leading-6 text-orbit-ink shadow-sm outline-none transition focus:border-orbit-pine/40 focus:ring-2 focus:ring-orbit-gold/25 disabled:cursor-not-allowed disabled:bg-orbit-mist/40";

export function HomeSubmissionCard() {
  const router = useRouter();
  const [portfolioName, setPortfolioName] = useState("");
  const [owner, setOwner] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const formData = new FormData();
    formData.set("portfolio_name", portfolioName);
    formData.set("owner", owner);
    formData.set("description", description);
    formData.set("tags", tags);

    try {
      const response = await fetch("/api/portfolios", {
        method: "POST",
        headers: {
          accept: "application/json",
        },
        body: formData,
      });
      const payload = (await response.json().catch(() => null)) as
        | { detail?: string; redirect_to?: string }
        | null;

      if (!response.ok) {
        throw new Error(payload?.detail?.trim() || "Unable to submit the portfolio idea.");
      }

      const redirectTo = payload?.redirect_to?.trim();
      startTransition(() => {
        router.push(redirectTo || "/");
      });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to submit the portfolio idea.");
      setIsSubmitting(false);
    }
  }

  return (
    <ShellCard>
      <SectionEyebrow>Submit a New Idea</SectionEyebrow>
      <form data-testid="portfolio-create-form" onSubmit={handleSubmit} className="mt-5 space-y-5">
        <div>
          <FieldLabel htmlFor="portfolio_name">Idea name</FieldLabel>
          <input
            id="portfolio_name"
            name="portfolio_name"
            placeholder="ProcurePilot"
            required
            value={portfolioName}
            onChange={(event) => setPortfolioName(event.target.value)}
            disabled={isSubmitting}
            className={FIELD_CLASS}
            data-testid="portfolio-name-input"
          />
        </div>
        <div>
          <FieldLabel htmlFor="owner">Owner</FieldLabel>
          <input
            id="owner"
            name="owner"
            placeholder="Somasundaram P"
            required
            value={owner}
            onChange={(event) => setOwner(event.target.value)}
            disabled={isSubmitting}
            className={FIELD_CLASS}
            data-testid="portfolio-owner-input"
          />
        </div>
        <div>
          <FieldLabel htmlFor="description">Idea description</FieldLabel>
          <textarea
            id="description"
            name="description"
            required
            rows={8}
            placeholder="Describe the user problem, proposed workflow, and why ORBIT should review this idea now."
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            disabled={isSubmitting}
            className={TEXTAREA_CLASS}
            data-testid="portfolio-description-input"
          />
        </div>
        <div>
          <FieldLabel htmlFor="tags">Optional tags</FieldLabel>
          <input
            id="tags"
            name="tags"
            placeholder="ai-saas, procurement, workflow"
            value={tags}
            onChange={(event) => setTags(event.target.value)}
            disabled={isSubmitting}
            className={FIELD_CLASS}
            data-testid="portfolio-tags-input"
          />
        </div>
        <div className="flex flex-col gap-3 border-t border-orbit-pine/10 pt-4 text-sm text-orbit-ink/70 md:flex-row md:items-center md:justify-between">
          <span>
            New idea submissions use a bounded portfolio identity strategy while preserving the approved
            canonicalization path.
          </span>
          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex rounded-full bg-orbit-ink px-5 py-3 text-sm font-semibold text-orbit-mist transition hover:bg-orbit-pine disabled:cursor-not-allowed disabled:bg-orbit-ink/55"
            data-testid="portfolio-create-submit"
          >
            {isSubmitting ? "Creating Portfolio..." : "Create Portfolio"}
          </button>
        </div>
        {error ? (
          <div
            className="rounded-[20px] border border-rose-200 bg-rose-50 px-4 py-3 text-sm leading-6 text-rose-800"
            data-testid="portfolio-create-error"
          >
            {error}
          </div>
        ) : null}
      </form>
    </ShellCard>
  );
}
