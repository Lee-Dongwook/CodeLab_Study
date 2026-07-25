import type { RiskItem } from "../types/research";

const labels: Record<RiskItem["category"], string> = {
  company: "기업",
  disclosure_news: "공시·뉴스",
  industry: "산업",
  check_point: "확인 항목",
};

export function RiskSection({ risks }: { risks: RiskItem[] }) {
  if (!risks.length)
    return <p>확인 가능한 공개자료 기반 리스크 항목이 없습니다.</p>;
  return (
    <ul>
      {risks.map((risk, index) => (
        <li key={`${risk.candidate_code}-${index}`}>
          <strong>{labels[risk.category]}</strong> · {risk.fact}
        </li>
      ))}
    </ul>
  );
}
