import type { SourceRecord } from "../types/research";

export function SourceList({ sources }: { sources: SourceRecord[] }) {
  return (
    <ul className="source-list">
      {sources.map((source) => (
        <li key={source.source_id}>
          <a href={source.url} target="_blank" rel="noreferrer">
            {source.title}
          </a>
          <small>
            {source.publisher} · {source.published_at ?? "발행일 미확인"}
          </small>
        </li>
      ))}
    </ul>
  );
}
