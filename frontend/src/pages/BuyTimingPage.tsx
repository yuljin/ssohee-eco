import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { fmt } from "../lib/format";
import { StatCard } from "../components/StatCard";

export function BuyTimingPage() {
  const [monthlyAmount, setMonthlyAmount] = useState(1000);
  const guide = useQuery({ queryKey: ["buyTiming", monthlyAmount], queryFn: () => api.buyTiming(monthlyAmount) });
  if (guide.isLoading) return <div className="loading">매수 타이밍을 분석하는 중입니다.</div>;
  if (!guide.data) return <div className="error">매수 타이밍 데이터를 불러오지 못했습니다.</div>;

  return (
    <>
      <div className="page-header">
        <div>
          <h1>매수 타이밍</h1>
          <p>하락폭, 환율, 목표 비중 부족분을 합산한 투입 가이드입니다.</p>
        </div>
        <div className="toolbar">
          <input className="input" type="number" value={monthlyAmount} onChange={(e) => setMonthlyAmount(Number(e.target.value))} />
        </div>
      </div>
      <div className="grid cols-4">
        <StatCard label="현재 환율" value={fmt.rate(guide.data.exchange_rate)} />
        <StatCard label="평균 대비" value={fmt.pct(guide.data.exchange_from_avg_pct)} tone={guide.data.exchange_from_avg_pct <= 0 ? "success" : "loss"} />
        <StatCard label="적용 비율" value={`×${guide.data.actual_ratio.toFixed(2)}`} />
        <StatCard label="추천 투입액" value={fmt.usd(guide.data.actual_amount, 0)} />
      </div>
      {guide.data.warning ? <div className="card warning" style={{ marginTop: 14 }}>{guide.data.warning}</div> : null}
      <div className="card" style={{ marginTop: 14 }}>
        <h2>자산별 가이드</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>종목</th><th>하락폭</th><th>비중</th><th>종합점수</th><th>매수비율</th><th>추천투입</th><th>시그널</th></tr>
            </thead>
            <tbody>
              {guide.data.asset_guides.map((row) => (
                <tr key={row.symbol}>
                  <td><strong>{row.symbol}</strong></td>
                  <td className={row.drawdown_pct <= -20 ? "danger" : "neutral"}>{fmt.pct(row.drawdown_pct, 1)}</td>
                  <td>{row.current_weight.toFixed(1)}% / {row.target_weight.toFixed(1)}%</td>
                  <td>
                    <strong>{row.total_score.toFixed(0)}</strong>
                    <div className="progress"><span style={{ width: `${Math.min(row.total_score, 100)}%` }} /></div>
                  </td>
                  <td>×{row.buy_ratio.toFixed(2)}</td>
                  <td>{fmt.usd(row.recommended_amount, 0)}</td>
                  <td><span className={`tag ${row.signal_color}`}>{row.signal}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

