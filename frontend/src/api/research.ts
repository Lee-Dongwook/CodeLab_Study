import type { ResearchReport } from "../types/research";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

interface ResearchResponse {
  report: ResearchReport;
  markdown: string;
}

export async function requestResearch(
  theme: string,
  topN: number,
): Promise<ResearchResponse> {
  const response = await fetch(`${apiBaseUrl}/research`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ theme, top_n: topN }),
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(payload?.detail ?? "리서치 요청을 처리하지 못했습니다.");
  }

  return (await response.json()) as ResearchResponse;
}
