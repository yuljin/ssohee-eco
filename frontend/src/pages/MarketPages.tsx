import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../lib/api";
import { fmt } from "../lib/format";
import { StatCard } from "../components/StatCard";

export function DrawdownPage() {
  const [weeks, setWeeks] = useState(52);
  const { data, isLoading } = useQuery({ queryKey: ["drawdown", weeks], queryFn: () => api.drawdown(weeks) });
  if (isLoading) return <div className="loading">하락폭을 분석하는 중입니다.</div>;
  if (!data) return <div className="error">하락폭 데이터를 불러오지 못했습니다.</div>;
  return (
    <>
      <div className="page-header">
        <div><h1>하락폭 분석</h1><p>기간별 고점 대비 현재 하락폭입니다.</p></div>
        <select className="input" value={weeks} onChange={(e) => setWeeks(Number(e.target.value))}>
          <option value={13}>3개월</option>
          <option value={26}>6개월</option>
          <option value={52}>1년</option>
        </select>
      </div>
      <div className="grid cols-3">
        <StatCard label="분석 종목" value={`${data.total_symbols}개`} />
        <StatCard label="적극 매수" value={`${data.buy_signals}개`} tone="loss" />
        <StatCard label="매수 고려" value={`${data.consider_signals}개`} tone="warning" />
      </div>
      <div className="card" style={{ marginTop: 14 }}>
        <h2>상세</h2>
        <div className="table-wrap responsive-table">
          <table>
            <thead><tr><th>종목</th><th>현재가</th><th>고점</th><th>하락폭</th><th>고점 이후</th><th>시그널</th></tr></thead>
            <tbody>{data.symbols.map((row) => (
              <tr key={row.symbol}>
                <td data-label="종목"><strong>{row.symbol}</strong></td>
                <td data-label="현재가">{fmt.usd(row.current_price)}</td>
                <td data-label="고점">{fmt.usd(row.high_52w)}<div className="subtle">{row.high_52w_date}</div></td>
                <td data-label="하락폭" className={row.drawdown_pct <= -20 ? "danger" : row.drawdown_pct <= -10 ? "warning" : "success"}>{fmt.pct(row.drawdown_pct)}</td>
                <td data-label="고점 이후">{row.days_since_high}일</td>
                <td data-label="시그널"><span className={`tag ${row.signal_color === "red" ? "red" : row.signal_color === "yellow" ? "orange" : "green"}`}>{row.signal}</span></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </div>
    </>
  );
}

export function ExchangeRatePage() {
  const [period, setPeriod] = useState(365);
  const { data, isLoading } = useQuery({ queryKey: ["exchange", period], queryFn: () => api.exchangeRate(period) });
  const guide = useQuery({ queryKey: ["exchangeGuide"], queryFn: api.exchangeGuide, staleTime: 10 * 60 * 1000 });
  const referenceLines = [
    { label: "3개월 평균", value: guide.data?.["3개월"]?.average, color: "#a6da95" },
    { label: "6개월 평균", value: guide.data?.["6개월"]?.average, color: "#eed49f" },
    { label: "1년 평균", value: guide.data?.["1년"]?.average, color: "#ed8796" }
  ].filter((item): item is { label: string; value: number; color: string } => Boolean(item.value));
  if (isLoading) return <div className="loading">환율을 분석하는 중입니다.</div>;
  if (!data) return <div className="error">환율 데이터를 불러오지 못했습니다.</div>;
  return (
    <>
      <div className="page-header">
        <div><h1>환율 분석</h1><p>USD/KRW 환율의 평균 대비 위치를 확인합니다.</p></div>
        <select className="input" value={period} onChange={(e) => setPeriod(Number(e.target.value))}>
          <option value={90}>3개월</option>
          <option value={180}>6개월</option>
          <option value={365}>1년</option>
          <option value={1095}>3년</option>
        </select>
      </div>
      <div className="grid cols-4">
        <StatCard label="현재 환율" value={fmt.rate(data.current_rate)} />
        <StatCard label="고점 대비" value={fmt.pct(data.from_high_pct)} tone="success" />
        <StatCard label="평균 대비" value={fmt.pct(data.from_avg_pct)} tone={data.from_avg_pct <= 0 ? "success" : "loss"} />
        <StatCard label="시그널" value={data.signal} helper={data.recommendation} />
      </div>
      <div className="card" style={{ marginTop: 14 }}>
        <h2>환율 추이</h2>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={data.history}>
            <XAxis dataKey="date" stroke="#8f98aa" />
            <YAxis stroke="#8f98aa" domain={["auto", "auto"]} />
            <Tooltip formatter={(v) => fmt.rate(Number(v ?? 0))} />
            {referenceLines.map((line) => (
              <ReferenceLine
                key={line.label}
                y={line.value}
                stroke={line.color}
                strokeDasharray="5 5"
                label={{ value: line.label, fill: line.color, fontSize: 12, position: "insideTopRight" }}
              />
            ))}
            <Line type="monotone" dataKey="rate" stroke="#8aadf4" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
        {referenceLines.length ? (
          <div className="reference-list">
            {referenceLines.map((line) => (
              <span key={line.label}>
                <i style={{ background: line.color }} />
                {line.label} {fmt.rate(line.value)}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </>
  );
}
