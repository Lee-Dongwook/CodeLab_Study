import type { DartDisclosure } from "../types/research";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

interface DartDisclosureResponse {
  items: DartDisclosure[];
  count: number;
  bgn_de: string;
  end_de: string;
}

export async function requestRecentDartDisclosures(): Promise<DartDisclosureResponse> {
  const response = await fetch(`${apiBaseUrl}/dart/disclosures?page_count=10`);
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? "DART 공시 목록을 조회하지 못했습니다.");
  }
  return (await response.json()) as DartDisclosureResponse;
}
