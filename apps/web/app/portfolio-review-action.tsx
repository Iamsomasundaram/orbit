"use client";

import { startTransition, useState } from "react";
import { useRouter } from "next/navigation";

type PortfolioReviewActionProps = {
  portfolioId: string;
  redirectTo: string;
  buttonLabel?: string;
  className?: string;
  testId?: string;
};

export function PortfolioReviewAction({
  portfolioId,
  redirectTo,
  buttonLabel = "Run ORBIT Review",
  className,
  testId = "run-review-button",
}: PortfolioReviewActionProps) {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleReview() {
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`/api/portfolios/${portfolioId}/review-runs`, {
        method: "POST",
        headers: {
          accept: "application/json",
        },
      });
      const payload = (await response.json().catch(() => null)) as
        | { detail?: string; redirect_to?: string; review_run?: { run_id: string } }
        | null;

      if (!response.ok) {
        throw new Error(payload?.detail?.trim() || "Unable to run the ORBIT review.");
      }

      const redirectTarget = payload?.redirect_to?.trim() || redirectTo;
      startTransition(() => {
        router.push(redirectTarget);
      });
    } catch (reviewError) {
      setError(reviewError instanceof Error ? reviewError.message : "Unable to run the ORBIT review.");
      setIsSubmitting(false);
    }
  }

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={handleReview}
        disabled={isSubmitting}
        className={
          className ??
          "inline-flex rounded-full bg-orbit-ink px-5 py-3 text-sm font-semibold text-orbit-mist transition hover:bg-orbit-pine disabled:cursor-not-allowed disabled:bg-orbit-ink/55"
        }
        data-testid={testId}
      >
        {isSubmitting ? "Running ORBIT Review..." : buttonLabel}
      </button>
      {error ? (
        <div
          className="rounded-[20px] border border-rose-200 bg-rose-50 px-4 py-3 text-sm leading-6 text-rose-800"
          data-testid={`${testId}-error`}
        >
          {error}
        </div>
      ) : null}
    </div>
  );
}
