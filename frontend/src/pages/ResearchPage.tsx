import { useState } from "react";

import { requestRecentDartDisclosures } from "../api/dart";
import { requestResearch } from "../api/research";
import { CandidateTable } from "../components/CandidateTable";
import { DartDisclosureList } from "../components/DartDisclosureList";
import { MetricsTable } from "../components/MetricsTable";
import { NewsDisclosureSection } from "../components/NewsDisclosureSection";
import { ResearchForm } from "../components/ResearchForm";
import { RiskSection } from "../components/RiskSection";
import { SourceList } from "../components/SourceList";
import type { DartDisclosure, ResearchReport } from "../types/research";

export function ResearchPage() {
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [dartItems, setDartItems] = useState<DartDisclosure[] | null>(null);
  const [dartRange, setDartRange] = useState<{ bgnDe: string; endDe: string } | null>(null);
  const [dartError, setDartError] = useState<string | null>(null);
  const [isDartLoading, setIsDartLoading] = useState(false);

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

  async function handleDartDisclosures() {
    setIsDartLoading(true);
    setDartError(null);
    try {
      const response = await requestRecentDartDisclosures();
      setDartItems(response.items);
      setDartRange({ bgnDe: response.bgn_de, endDe: response.end_de });
    } catch (caughtError) {
      setDartItems(null);
      setDartRange(null);
      setDartError(caughtError instanceof Error ? caughtError.message : "DART 공시 목록을 조회하지 못했습니다.");
    } finally {
      setIsDartLoading(false);
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
      <section className="dart-panel">
        <div>
          <p className="eyebrow">PUBLIC DISCLOSURES</p>
          <h2>최근 DART 공시 목록</h2>
          <p>국내 후보 선정 전, OpenDART에서 제공하는 최근 공시를 확인할 수 있습니다.</p>
        </div>
        <button type="button" onClick={handleDartDisclosures} disabled={isDartLoading}>
          {isDartLoading ? "공시 조회 중..." : "최근 공시 보기"}
        </button>
      </section>
      {dartError && <p className="error" role="alert">{dartError}</p>}
      {dartItems && dartRange && (
        <section className="dart-results">
          <DartDisclosureList items={dartItems} bgnDe={dartRange.bgnDe} endDe={dartRange.endDe} />
        </section>
      )}
      {report && (
        <article className="report">
          <section>
            <h2>1. 빠른 요약</h2>
            <p>
              {report.theme_definition.name} 테마에서 확인된 국내 후보는{" "}
              {report.candidates.length}개입니다.
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
            <h2>7. 참고자료 및 출처</h2>
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
