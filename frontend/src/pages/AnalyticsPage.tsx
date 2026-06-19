import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../lib/api";
import { fmt, pnlClass } from "../lib/format";
import { StatCard } from "../components/StatCard";

export function AnalyticsPage() {
  const metrics = useQuery({ queryKey: ["metrics"], queryFn: api.metrics });
  const monthly = useQuery({ queryKey: ["monthlyReturns"], queryFn: api.monthlyReturns });

  if (metrics.isLoading) return <div className="loading">성과 지표를 계산하는 중입니다.</div>;
  if (!metrics.data) return <div className="error">성과 지표를 불러오지 못했습니다.</div>;

  const m = metrics.data;
  return (
    <>
      <div className="page-header">
        <div>
          <h1>성과 분석</h1>
          <p>입출금과 현재 평가액을 기준으로 수익률을 계산합니다.</p>
        </div>
      </div>
      <div className="grid cols-4">
        <StatCard label="총 수익률" value={m.total_return_pct == null ? "-" : fmt.pct(m.total_return_pct)} helper={fmt.usd(m.total_pnl)} tone={pnlClass(m.total_pnl)} />
        <StatCard label="원화 수익률" value={m.total_return_pct_krw == null ? "-" : fmt.pct(m.total_return_pct_krw)} helper={fmt.krw(m.total_pnl_krw)} tone={pnlClass(m.total_pnl_krw)} />
        <StatCard label="순투자금" value={fmt.usd(m.net_invested)} helper={fmt.krw(m.net_invested_krw)} />
        <StatCard label="투자 기간" value={`${m.days_elapsed}일`} helper={`${m.start_date}부터`} />
      </div>
      <div className="grid cols-2" style={{ marginTop: 14 }}>
        <div className="card">
          <h2>월별 수익률</h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={monthly.data ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2e3b" />
              <XAxis dataKey="month" stroke="#8f98aa" />
              <YAxis stroke="#8f98aa" tickFormatter={(v) => `${v}%`} />
              <Tooltip formatter={(v) => fmt.pct(Number(v ?? 0))} />
              <ReferenceLine y={0} stroke="#8f98aa" />
              <Bar dataKey="return_pct" fill="#8aadf4" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h2>누적 수익률</h2>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={monthly.data ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2e3b" />
              <XAxis dataKey="month" stroke="#8f98aa" />
              <YAxis stroke="#8f98aa" tickFormatter={(v) => `${v}%`} />
              <Tooltip formatter={(v) => fmt.pct(Number(v ?? 0))} />
              <Line type="monotone" dataKey="cumulative_return_pct" stroke="#ed8796" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  );
}
