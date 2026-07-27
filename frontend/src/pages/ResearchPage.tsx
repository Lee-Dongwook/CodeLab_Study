import { useState } from "react";

import { requestResearch } from "../api/research";
import { CandidateTable } from "../components/CandidateTable";
import { MetricsTable } from "../components/MetricsTable";
import { NewsDisclosureSection } from "../components/NewsDisclosureSection";
import { ResearchForm } from "../components/ResearchForm";
import { RiskSection } from "../components/RiskSection";
import { SourceList } from "../components/SourceList";
import type { ResearchReport } from "../types/research";

export function ResearchPage() {
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleResearch(theme: string, topN: number) {
    setIsLoading(true);
    setError(null);
    try {
      const response = await requestResearch(theme, topN);
      setReport(response.report);
    } catch (caughtError) {
      setReport(null);
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "리서치 요청을 처리하지 못했습니다.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="page">
      <header>
        <p className="eyebrow">KRX THEME RESEARCH</p>
        <h1>테마 주식 리서치 에이전트</h1>
        <p>국내 KRX 상장 보통주를 공개자료 기반으로 정리합니다.</p>
      </header>
      <ResearchForm disabled={isLoading} onSubmit={handleResearch} />
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {report && (
        <article className="report">
          <section>
            <h2>1. 빠른 요약</h2>
            <p>
              {report.theme_definition.name} 테마에서 확인된 국내 후보는{" "}
              {report.candidates.length}개입니다.
            </p>
            <p className="caption">
              KRX 상장 보통주만 대상으로 하며 ETF·ETN·우선주·SPAC는 제외합니다.
              {report.candidates.length < report.request.top_n
                ? ` 적격 후보가 ${report.request.top_n}개보다 적어 확인된 ${report.candidates.length}개만 표시합니다.`
                : ""}
            </p>
          </section>
          <section>
            <h2>2. 국내 테마 정의</h2>
            <p>{report.theme_definition.description}</p>
            <p>
              <strong>포함 기준:</strong>{" "}
              {report.theme_definition.inclusion_criteria}
            </p>
            <p>
              <strong>제외 기준:</strong>{" "}
              {report.theme_definition.exclusion_criteria}
            </p>
          </section>
          <section>
            <h2>3. 국내 후보 종목 및 선정 근거</h2>
            <CandidateTable candidates={report.candidates} />
          </section>
          <section>
            <h2>4. 국내 정량 비교</h2>
            <MetricsTable
              metrics={report.metrics}
              priceVolumeMetrics={report.price_volume_metrics}
            />
          </section>
          <section>
            <h2>5. 상세 리스크 분석</h2>
            <RiskSection risks={report.risks} />
          </section>
          <section>
            <h2>6. 최근 뉴스 및 공시</h2>
            <NewsDisclosureSection items={report.news_disclosures} />
          </section>
          <section>
            <h2>7. 미국 시장 선행 동향 (참고)</h2>
            {report.us_market_reference ? (
              <div>
                <p><strong>기준일:</strong> {report.us_market_reference.as_of ?? "확인 불가"}</p>
                <p><strong>동향:</strong> {report.us_market_reference.trend}</p>
                <p><strong>배경:</strong> {report.us_market_reference.background}</p>
                <p><strong>대표 종목:</strong> {report.us_market_reference.representative_companies.join(", ") || "확인 가능한 자료 없음"}</p>
                <p><strong>대표 ETF:</strong> {report.us_market_reference.representative_etfs.join(", ") || "확인 가능한 자료 없음"}</p>
                <p><strong>뉴스 요약:</strong> {report.us_market_reference.news_summary}</p>
              </div>
            ) : <p>확인 가능한 공개 참고자료가 없습니다.</p>}
          </section>
          <section>
            <h2>8. 관련 미국 Peer Company (참고)</h2>
            {report.us_peer_companies.length ? <ul>{report.us_peer_companies.map((peer) => <li key={peer.ticker}><strong>{peer.name} ({peer.ticker})</strong>: {peer.related_business} — {peer.connection} ({peer.relevance === "direct" ? "직접 관련" : "간접 관련"})</li>)}</ul> : <p>확인 가능한 공개 참고자료가 없습니다.</p>}
          </section>
          <section>
            <h2>9. 글로벌 운용사 동향 (참고)</h2>
            {report.asset_manager_references.length ? <ul>{report.asset_manager_references.map((manager) => <li key={manager.manager}><strong>{manager.manager}</strong>: {manager.etf_or_holding} / {manager.public_view} / {manager.recent_activity} ({manager.as_of ?? "기준일 미확인"})</li>)}</ul> : <p>확인 가능한 공개 참고자료가 없습니다.</p>}
          </section>
          <section>
            <h2>10. 참고자료 및 출처</h2>
            <SourceList sources={report.sources} />
          </section>
          <footer>
            <h2>안내 문구</h2>
            <p>{report.disclaimer}</p>
          </footer>
        </article>
      )}
    </main>
  );
}
