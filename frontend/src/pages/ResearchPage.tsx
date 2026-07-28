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
              candidates={report.candidates}
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
            <NewsDisclosureSection
              candidates={report.candidates}
              items={report.news_disclosures}
            />
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
                {report.us_market_reference.macro_indicators.length > 0 && (
                  <>
                    <h3>미국 대표 지표: 수치 기반 사실·의미 해석·당일 국내시장 대응 기준</h3>
                    <p className="caption">아래 대응 기준은 매수·매도 지시가 아닌, 국내 장중 함께 확인할 공개 수치와 조건부 점검 항목입니다.</p>
                    <div className="table-scroll">
                      <table>
                        <thead>
                          <tr><th>지표</th><th>수치 기반 사실</th><th>의미 해석</th><th>당일 국내시장 대응 기준</th></tr>
                        </thead>
                        <tbody>
                          {report.us_market_reference.macro_indicators.map((indicator) => {
                            const snapshot = indicator.snapshot;
                            return (
                              <tr key={indicator.ticker}>
                                <td>{indicator.label} ({indicator.ticker})</td>
                                <td>최근 값 {snapshot.close_price?.toLocaleString("en-US") ?? "확인 불가"}<br />일간 등락률 {snapshot.daily_change_percent == null ? "확인 불가" : `${snapshot.daily_change_percent.toFixed(2)}%`}<br />거래량 변화 {snapshot.volume_change_percent == null ? "확인 불가" : `${snapshot.volume_change_percent.toFixed(2)}%`}</td>
                                <td>{indicator.interpretation}</td>
                                <td>{indicator.domestic_check_point}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
                {report.us_market_reference.market_snapshots.length > 0 && (
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>Yahoo Finance 참고 지표</th><th>최근 종가</th><th>일간 등락률</th><th>거래량</th><th>기준일</th>
                        </tr>
                      </thead>
                      <tbody>
                        {report.us_market_reference.market_snapshots.map((snapshot) => (
                          <tr key={snapshot.ticker}>
                            <td>{snapshot.name} ({snapshot.ticker})</td>
                            <td>{snapshot.close_price?.toLocaleString("en-US") ?? "확인 불가"}</td>
                            <td>{snapshot.daily_change_percent == null ? "확인 불가" : `${snapshot.daily_change_percent.toFixed(2)}%`}</td>
                            <td>{snapshot.volume?.toLocaleString("en-US") ?? "확인 불가"}</td>
                            <td>{snapshot.as_of ?? "확인 불가"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ) : <p>확인 가능한 공개 참고자료가 없습니다.</p>}
          </section>
          <section>
            <h2>8. 관련 미국 Peer Company (참고)</h2>
            {report.us_peer_companies.length ? (
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr><th>Peer Company</th><th>관련 사업·연결 근거</th><th>관련 여부</th><th>최근 종가</th><th>일간 등락률</th><th>거래량 변화</th><th>종가 마감 영향 공시·뉴스</th></tr>
                  </thead>
                  <tbody>
                    {report.us_peer_companies.map((peer) => {
                      const snapshot = peer.market_snapshot;
                      return (
                        <tr key={peer.ticker}>
                          <td>{peer.name} ({peer.ticker})</td>
                          <td>{peer.related_business} — {peer.connection}</td>
                          <td>{peer.relevance === "direct" ? "직접 관련" : "간접 관련"}</td>
                          <td>{snapshot?.close_price?.toLocaleString("en-US") ?? "확인 불가"}</td>
                          <td>{snapshot?.daily_change_percent == null ? "확인 불가" : `${snapshot.daily_change_percent.toFixed(2)}%`}</td>
                          <td>{snapshot?.volume_change_percent == null ? "확인 불가" : `${snapshot.volume_change_percent.toFixed(2)}%`}</td>
                          <td>
                            {peer.closing_news_summary}
                            {peer.closing_news_url && (
                              <>
                                <br />
                                <a href={peer.closing_news_url} target="_blank" rel="noreferrer">
                                  원문 보기
                                </a>
                              </>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : <p>확인 가능한 공개 참고자료가 없습니다.</p>}
          </section>
          <section>
            <h2>9. 글로벌 운용사 동향 (참고)</h2>
            {report.asset_manager_references.length ? (
              <>
                <AssetManagerList
                  title="글로벌 운용사"
                  managers={report.asset_manager_references.filter(
                    (manager) => manager.market === "GLOBAL",
                  )}
                />
                <AssetManagerList
                  title="대한민국 운용사 ETF"
                  managers={report.asset_manager_references.filter(
                    (manager) => manager.market === "KR",
                  )}
                />
              </>
            ) : <p>확인 가능한 공개 참고자료가 없습니다.</p>}
          </section>
          <section>
            <h2>10. 참고자료 및 출처</h2>
            <SourceList
              candidates={report.candidates}
              metrics={report.metrics}
              newsDisclosures={report.news_disclosures}
              sources={report.sources}
            />
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

function AssetManagerList({
  title,
  managers,
}: {
  title: string;
  managers: ResearchReport["asset_manager_references"];
}) {
  if (!managers.length) return null;

  return (
    <div className="asset-manager-group">
      <h3>{title}</h3>
      <ul>
        {managers.map((manager) => (
          <li key={`${manager.market}-${manager.manager}-${manager.etf_or_holding}`}>
            <strong>{manager.manager}</strong>: {manager.etf_or_holding} / {manager.public_view} / {manager.recent_activity} ({manager.as_of ?? "기준일 미확인"})
            {manager.source_url && (
              <> · <a href={manager.source_url} target="_blank" rel="noreferrer">공식 ETF 자료</a></>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
