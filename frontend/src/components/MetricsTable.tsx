import type { DomesticMetrics, PriceVolumeMetrics } from "../types/research";

const display = (value: number | string | null | undefined) =>
  value ?? "확인 불가";

const formatMarketCap = (value: number | null) => {
  if (value == null) return "확인 불가";

  // 원 단위 시가총액을 10억 원 단위로 내림 처리한다.
  const tenBillionWon = Math.floor(value / 1_000_000_000) * 10;
  return `${tenBillionWon.toLocaleString("ko-KR")}억원`;
};

const formatClosePrice = (value: number | null) =>
  value == null ? "확인 불가" : `${value.toLocaleString("ko-KR")}원`;

export function MetricsTable({
  metrics,
  priceVolumeMetrics,
}: {
  metrics: DomesticMetrics[];
  priceVolumeMetrics: PriceVolumeMetrics[];
}) {
  const priceVolumeByCode = new Map(
    priceVolumeMetrics.map((metric) => [metric.candidate_code, metric]),
  );
  if (!metrics.length) return <p>확인 가능한 기본 정량 데이터가 없습니다.</p>;

  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>종목코드</th>
            <th>최근 종가</th>
            <th>시가총액</th>
            <th>PER</th>
            <th>PBR</th>
            <th>매출 성장률</th>
            <th>영업이익률</th>
            <th>시장 기준일</th>
            <th>재무 기준 기간</th>
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
                <td>{metric.candidate_code}</td>
                <td>{formatClosePrice(metric.close_price)}</td>
                <td>{formatMarketCap(metric.market_cap)}</td>
                <td>{display(metric.per?.toFixed(2))}</td>
                <td>{display(metric.pbr?.toFixed(2))}</td>
                <td>{display(metric.revenue_growth?.toFixed(2))}</td>
                <td>{display(metric.operating_margin?.toFixed(2))}</td>
                <td>{metric.market_data_as_of ?? "확인 불가"}</td>
                <td>{metric.financial_period ?? "확인 불가"}</td>
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
  );
}
