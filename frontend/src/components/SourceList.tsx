import type {
  DomesticCandidate,
  DomesticMetrics,
  NewsDisclosureItem,
  SourceRecord,
} from "../types/research";

interface SourceListProps {
  candidates: DomesticCandidate[];
  metrics: DomesticMetrics[];
  newsDisclosures: NewsDisclosureItem[];
  sources: SourceRecord[];
}

export function SourceList({
  candidates,
  metrics,
  newsDisclosures,
  sources,
}: SourceListProps) {
  const sourceOwners = new Map<string, Set<string>>();
  const sourceById = new Map(sources.map((source) => [source.source_id, source]));

  function connectSources(candidateCode: string, records: SourceRecord[]) {
    for (const record of records) {
      if (!sourceById.has(record.source_id)) continue;
      const owners = sourceOwners.get(record.source_id) ?? new Set<string>();
      owners.add(candidateCode);
      sourceOwners.set(record.source_id, owners);
    }
  }

  for (const candidate of candidates) {
    connectSources(candidate.code, candidate.sources);
  }
  for (const metric of metrics) {
    connectSources(metric.candidate_code, metric.sources);
  }
  for (const item of newsDisclosures) {
    connectSources(item.candidate_code, [item.source]);
  }

  const sourceItems = (items: SourceRecord[]) => (
    <ul className="source-list">
      {items.map((source) => (
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

  return (
    <div className="source-groups">
      {candidates.map((candidate) => {
        const candidateSources = sources.filter((source) =>
          sourceOwners.get(source.source_id)?.has(candidate.code),
        );
        if (!candidateSources.length) return null;

        return (
          <section className="source-group" key={candidate.code}>
            <h3>{candidate.name}</h3>
            <p className="caption">연결된 참고자료 {candidateSources.length}건</p>
            {sourceItems(candidateSources)}
          </section>
        );
      })}
      {(() => {
        const commonSources = sources.filter(
          (source) => !sourceOwners.has(source.source_id),
        );
        if (!commonSources.length) return null;

        return (
          <section className="source-group">
            <h3>공통 참고자료</h3>
            <p className="caption">테마 정의·미국 시장·운용사 등 업체 공통 자료 {commonSources.length}건</p>
            {sourceItems(commonSources)}
          </section>
        );
      })()}
    </div>
  );
}
