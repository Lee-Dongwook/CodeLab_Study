import type { NewsDisclosureItem } from "../types/research";

export function NewsDisclosureSection({
  items,
}: {
  items: NewsDisclosureItem[];
}) {
  if (!items.length) return <p>확인 가능한 최근 뉴스 또는 공시가 없습니다.</p>;
  return (
    <ul className="source-list">
      {items.map((item) => (
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
  );
}
