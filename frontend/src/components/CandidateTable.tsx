import type { DomesticCandidate } from "../types/research";

export function CandidateTable({
  candidates,
}: {
  candidates: DomesticCandidate[];
}) {
  if (!candidates.length) return <p>확인된 적격 국내 후보가 없습니다.</p>;

  return (
    <div className="table-scroll">
    <table>
      <thead>
        <tr>
          <th>종목</th>
          <th>종목코드</th>
          <th>상장 적격성</th>
          <th>테마 관련 사업</th>
          <th>관련 여부</th>
          <th>선정 근거</th>
          <th>공식 근거</th>
        </tr>
      </thead>
      <tbody>
        {candidates.map((candidate) => (
          <tr key={candidate.code}>
            <td>{candidate.name}</td>
            <td>{candidate.code}</td>
            <td>
              <span className="tag eligible-tag">KRX {candidate.security_type === "COMMON_STOCK" ? "보통주" : candidate.security_type}</span>
            </td>
            <td>{candidate.related_business}</td>
            <td>
              {candidate.relevance === "direct" ? "직접 관련" : "간접 관련"}
            </td>
            <td>{candidate.selection_reason}</td>
            <td>
              <ul className="candidate-sources">
                {candidate.sources.map((source) => (
                  <li key={source.source_id}>
                    <a href={source.url} target="_blank" rel="noreferrer">
                      {source.title}
                    </a>
                    <small>{source.publisher}</small>
                  </li>
                ))}
              </ul>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
    </div>
  );
}
