import type { DomesticCandidate } from "../types/research";

export function CandidateTable({
  candidates,
}: {
  candidates: DomesticCandidate[];
}) {
  if (!candidates.length) return <p>확인된 적격 국내 후보가 없습니다.</p>;

  return (
    <table>
      <thead>
        <tr>
          <th>종목</th>
          <th>종목코드</th>
          <th>테마 관련 사업</th>
          <th>관련 여부</th>
          <th>선정 근거</th>
        </tr>
      </thead>
      <tbody>
        {candidates.map((candidate) => (
          <tr key={candidate.code}>
            <td>{candidate.name}</td>
            <td>{candidate.code}</td>
            <td>{candidate.related_business}</td>
            <td>
              {candidate.relevance === "direct" ? "직접 관련" : "간접 관련"}
            </td>
            <td>{candidate.selection_reason}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
