import { notFound } from "next/navigation";

import {
  type ReviewRunDeliberationPayload,
  type ReviewRunDeliberationSummaryPayload,
  fetchOrbitJson,
} from "@/lib/orbit-api";

import { CommitteeMode } from "./committee-mode";

type CommitteePageProps = {
  params: Promise<{ runId: string }>;
};

export default async function ReviewRunCommitteePage({ params }: CommitteePageProps) {
  const { runId } = await params;
  const [timeline, summary] = await Promise.all([
    fetchOrbitJson<ReviewRunDeliberationPayload>(`/api/v1/review-runs/${runId}/deliberation`),
    fetchOrbitJson<ReviewRunDeliberationSummaryPayload>(`/api/v1/review-runs/${runId}/deliberation/summary`),
  ]);

  if (!timeline || !summary) {
    notFound();
  }

  return <CommitteeMode timeline={timeline} summary={summary} />;
}
