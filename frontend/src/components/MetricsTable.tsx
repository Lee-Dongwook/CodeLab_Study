import type {
  DomesticCandidate,
  DomesticMetrics,
  PriceVolumeMetrics,
} from "../types/research";

const display = (value: number | string | null | undefined) =>
  value ?? "확인 불가";

const formatMarketCap = (value: number | null) => {
  if (value == null) return "확인 불가";

  // 원 단위 시가총액을 십억 원 단위로 내림 처리한다.
  const billionWon = Math.floor(value / 1_000_000_000);
  return `${billionWon.toLocaleString("ko-KR")}십억원`;
};

const formatClosePrice = (value: number | null) =>
  value == null ? "확인 불가" : `${value.toLocaleString("ko-KR")}원`;

const formatPercent = (value: number | null) =>
  value == null ? "확인 불가" : `${value.toFixed(2)}%`;

interface IMetricsTable {
  candidates: DomesticCandidate[];
  metrics: DomesticMetrics[];
  priceVolumeMetrics: PriceVolumeMetrics[];
}

export function MetricsTable({
  candidates,
  metrics,
  priceVolumeMetrics,
}: IMetricsTable) {
  const candidateNameByCode = new Map(
    candidates.map((candidate) => [candidate.code, candidate.name]),
  );
  const priceVolumeByCode = new Map(
    priceVolumeMetrics.map((metric) => [metric.candidate_code, metric]),
  );

  if (!metrics.length) return <p>확인 가능한 기본 정량 데이터가 없습니다.</p>;

  return (
    <>
      <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>종목명</th>
            <th>최근 종가</th>
            <th>
              전일 주가 등락률<br />(전 거래일)
            </th>
            <th>
              당일 주가 등락률<br />(최근 거래일)
            </th>
            <th>주간 등락률<br />(5거래일)</th>
            <th>월간 등락률<br />(20거래일)</th>
            <th>기간 수익률</th>
            <th>변동성</th>
            <th>거래량 변화</th>
            <th>거래량 급증</th>
            <th>분석 기간</th>
            <th>분석 기준일</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map((metric) => {
            const priceVolume = priceVolumeByCode.get(metric.candidate_code);
            return (
              <tr key={metric.candidate_code}>
                <td>
                  {candidateNameByCode.get(metric.candidate_code) ??
                    metric.candidate_code}
                </td>
                <td>{formatClosePrice(metric.close_price)}</td>
                <td>{formatPercent(metric.previous_day_price_change_percent)}</td>
                <td>{formatPercent(metric.current_day_price_change_percent)}</td>
                <td>{formatPercent(metric.weekly_price_change_percent)}</td>
                <td>{formatPercent(metric.monthly_price_change_percent)}</td>
                <td>
                  {display(priceVolume?.period_return?.toFixed(2) ?? null)}
                </td>
                <td>{display(priceVolume?.volatility?.toFixed(2) ?? null)}</td>
                <td>
                  {display(priceVolume?.volume_change?.toFixed(2) ?? null)}
                </td>
                <td>
                  {priceVolume?.volume_surge == null
                    ? "확인 불가"
                    : priceVolume.volume_surge
                      ? "예"
                      : "아니오"}
                </td>
                <td>{priceVolume?.analysis_period ?? "확인 불가"}</td>
                <td>{priceVolume?.data_as_of ?? "확인 불가"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      </div>
      <details className="metrics-details">
        <summary>추가 시장·재무 정보 보기</summary>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>종목명</th>
                <th>시가총액</th>
                <th>PER</th>
                <th>PBR</th>
                <th>매출 성장률</th>
                <th>영업이익률</th>
                <th>시장 기준일</th>
                <th>재무 기준 기간</th>
              </tr>
            </thead>
            <tbody>
              {metrics.map((metric) => (
                <tr key={metric.candidate_code}>
                  <td>
                    {candidateNameByCode.get(metric.candidate_code) ??
                      metric.candidate_code}
                  </td>
                  <td>{formatMarketCap(metric.market_cap)}</td>
                  <td>{display(metric.per?.toFixed(2))}</td>
                  <td>{display(metric.pbr?.toFixed(2))}</td>
                  <td>{formatPercent(metric.revenue_growth)}</td>
                  <td>{formatPercent(metric.operating_margin)}</td>
                  <td>{metric.market_data_as_of ?? "확인 불가"}</td>
                  <td>{metric.financial_period ?? "확인 불가"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </>
  );
}
