import { FormEvent, useState } from "react";

interface ResearchFormProps {
  disabled: boolean;
  onSubmit: (theme: string, topN: number) => void;
}

export function ResearchForm({ disabled, onSubmit }: ResearchFormProps) {
  const [theme, setTheme] = useState("");
  const [topN, setTopN] = useState("3");
  const [topNError, setTopNError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const parsedTopN = Number(topN);
    if (!Number.isInteger(parsedTopN) || parsedTopN < 1 || parsedTopN > 10) {
      setTopNError("비교 종목 수는 1~10 사이의 정수여야 합니다.");
      return;
    }
    setTopNError(null);
    onSubmit(theme, parsedTopN);
  }

  return (
    <form className="research-form" onSubmit={handleSubmit}>
      <label>
        테마 또는 국내 종목명
        <input
          value={theme}
          onChange={(event) => setTheme(event.target.value)}
          placeholder="예: 로봇, 두산로보틱스"
          required
        />
      </label>
      <label>
        비교 종목 수 (1~10개)
        <input
          type="number"
          min="1"
          max="10"
          step="1"
          value={topN}
          onChange={(event) => {
            const value = event.target.value;
            // 앞자리 0·소수·범위 밖 값은 반영하지 않는다.
            if (/^(?:[1-9]|10)?$/.test(value)) {
              setTopN(value);
              setTopNError(null);
            }
          }}
          aria-label="비교 종목 수"
          aria-invalid={Boolean(topNError)}
          aria-describedby={topNError ? "top-n-error" : undefined}
        />
        {topNError && <small id="top-n-error" className="input-error">{topNError}</small>}
      </label>
      <button type="submit" disabled={disabled}>
        {disabled ? "분석 중..." : "국내 테마 분석"}
      </button>
    </form>
  );
}
