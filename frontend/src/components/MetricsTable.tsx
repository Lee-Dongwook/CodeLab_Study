import type { DomesticMetrics, PriceVolumeMetrics } from "../types/research";

const display = (value: number | null) => value ?? "확인 불가";

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
            <th>기간 수익률</th>
            <th>변동성</th>
            <th>거래량 변화</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map((metric) => {
            const priceVolume = priceVolumeByCode.get(metric.candidate_code);
            return (
              <tr key={metric.candidate_code}>
                <td>{metric.candidate_code}</td>
                <td>{display(metric.close_price)}</td>
                <td>{display(metric.market_cap)}</td>
                <td>{display(metric.per)}</td>
                <td>{display(metric.pbr)}</td>
                <td>{display(metric.revenue_growth)}</td>
                <td>{display(metric.operating_margin)}</td>
                <td>{display(priceVolume?.period_return ?? null)}</td>
                <td>{display(priceVolume?.volatility ?? null)}</td>
                <td>{display(priceVolume?.volume_change ?? null)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
