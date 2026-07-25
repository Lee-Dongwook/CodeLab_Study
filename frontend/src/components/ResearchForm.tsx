import { FormEvent, useState } from "react";

interface ResearchFormProps {
  disabled: boolean;
  onSubmit: (theme: string, topN: number) => void;
}

export function ResearchForm({ disabled, onSubmit }: ResearchFormProps) {
  const [theme, setTheme] = useState("");
  const [topN, setTopN] = useState(3);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit(theme, topN);
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
        최대 비교 종목 수
        <input
          type="number"
          min="1"
          value={topN}
          onChange={(event) => setTopN(Number(event.target.value))}
          required
        />
      </label>
      <button type="submit" disabled={disabled}>
        {disabled ? "분석 중..." : "국내 테마 분석"}
      </button>
    </form>
  );
}
