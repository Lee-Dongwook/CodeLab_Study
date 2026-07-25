import type { DartDisclosure } from "../types/research";

interface DartDisclosureListProps {
  items: DartDisclosure[];
  bgnDe: string;
  endDe: string;
}

export function DartDisclosureList({ items, bgnDe, endDe }: DartDisclosureListProps) {
  if (!items.length) return <p>{bgnDe}~{endDe} 기간의 공시가 없습니다.</p>;

  return <div className="table-scroll"><p className="caption">조회 기간: {bgnDe} ~ {endDe}</p><table><thead><tr><th>회사명</th><th>종목코드</th><th>공시명</th><th>접수일</th><th>제출인</th></tr></thead><tbody>
    {items.map((item) => <tr key={item.rcept_no}><td>{item.corp_name}</td><td>{item.stock_code || "확인 불가"}</td><td><a href={`https://dart.fss.or.kr/dsaf001/main.do?rcpNo=${item.rcept_no}`} target="_blank" rel="noreferrer">{item.report_nm}</a></td><td>{item.rcept_dt}</td><td>{item.flr_nm}</td></tr>)}
  </tbody></table></div>;
}
