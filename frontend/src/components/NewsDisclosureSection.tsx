import type {
  DomesticCandidate,
  NewsDisclosureItem,
} from "../types/research";

export function NewsDisclosureSection({
  candidates,
  items,
}: {
  candidates: DomesticCandidate[];
  items: NewsDisclosureItem[];
}) {
  if (!items.length) return <p>확인 가능한 최근 뉴스 또는 공시가 없습니다.</p>;

  const candidateNameByCode = new Map(
    candidates.map((candidate) => [candidate.code, candidate.name]),
  );
  const itemsByCandidate = new Map<string, NewsDisclosureItem[]>();
  for (const item of items) {
    const candidateItems = itemsByCandidate.get(item.candidate_code) ?? [];
    candidateItems.push(item);
    itemsByCandidate.set(item.candidate_code, candidateItems);
  }

  return (
    <div className="news-disclosure-groups">
      {[...itemsByCandidate].map(([candidateCode, candidateItems]) => {
        const disclosureCount = candidateItems.filter(
          (item) => item.category === "disclosure",
        ).length;
        const newsCount = candidateItems.length - disclosureCount;
        const candidateName =
          candidateNameByCode.get(candidateCode) ?? candidateCode;

        return (
          <section className="news-disclosure-group" key={candidateCode}>
            <h3>{candidateName}</h3>
            <p className="caption">
              최근 항목 {candidateItems.length}건 · 공시 {disclosureCount}건 · 뉴스 {newsCount}건
            </p>
            <ul className="source-list">
              {candidateItems.map((item) => (
                <li key={`${item.candidate_code}-${item.url}`}>
                  <span className="tag">
                    {item.category === "disclosure" ? "공시" : "뉴스"}
                  </span>
                  <a href={item.url} target="_blank" rel="noreferrer">
                    {item.title}
                  </a>
                  <p>{item.summary}</p>
                  <small>{item.published_at ?? "발행일 미확인"}</small>
                </li>
              ))}
            </ul>
          </section>
        );
      })}
    </div>
  );
}
