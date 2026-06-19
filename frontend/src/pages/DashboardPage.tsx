import { useQuery } from "@tanstack/react-query";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { api } from "../lib/api";
import { fmt, pnlClass } from "../lib/format";
import { PortfolioTable } from "../components/PortfolioTable";
import { StatCard } from "../components/StatCard";

const COLORS = ["#8aadf4", "#a6da95", "#eed49f", "#ed8796", "#c6a0f6", "#8bd5ca"];

export function DashboardPage() {
  const snapshot = useQuery({ queryKey: ["snapshot"], queryFn: () => api.snapshot() });
  const metrics = useQuery({ queryKey: ["metrics"], queryFn: api.metrics });
  const allocation = useQuery({ queryKey: ["allocation"], queryFn: api.allocation });
  const groups = useQuery({ queryKey: ["assetGroups"], queryFn: api.assetGroups });

  if (snapshot.isLoading) return <div className="loading">포트폴리오를 불러오는 중입니다.</div>;
  if (!snapshot.data) return <div className="error">포트폴리오 데이터를 불러오지 못했습니다.</div>;

  const snap = snapshot.data;
  const metric = metrics.data;
  const pieData = Object.entries(snap.value_by_symbol)
    .filter(([, value]) => value > 0)
    .map(([name, value]) => ({ name, value }));

  return (
    <>
      <div className="page-header">
        <div>
          <h1>현재 포트폴리오</h1>
          <p>거래 내역에서 계산한 평가와 목표 비중입니다. 현재는 최근 거래 가격 기준 추정값입니다.</p>
        </div>
      </div>
      <div className="grid cols-4">
        <StatCard label="총 자산" value={fmt.usd(snap.total_value)} helper={fmt.krw(snap.total_value * snap.exchange_rate)} />
        <StatCard label="현금" value={fmt.usd(snap.cash)} helper={`${(snap.weight_by_symbol.CASH * 100).toFixed(1)}%`} />
        <StatCard label="USD/KRW" value={fmt.rate(snap.exchange_rate)} />
        <StatCard
          label="총 손익"
          value={metric?.total_return_pct == null ? "-" : fmt.pct(metric.total_return_pct)}
          helper={metric ? fmt.usd(metric.total_pnl) : undefined}
          tone={pnlClass(metric?.total_pnl ?? 0)}
        />
      </div>
      <div className="grid cols-2" style={{ marginTop: 14 }}>
        <div className="card">
          <h2>자산 비중</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={105} label>
                {pieData.map((_, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
              </Pie>
              <Tooltip formatter={(value) => fmt.usd(Number(value ?? 0))} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h2>투자 정보</h2>
          <div className="grid">
            <div className="split"><span className="subtle">순투자금</span><strong>{metric ? fmt.usd(metric.net_invested) : "-"}</strong></div>
            <div className="split"><span className="subtle">원화 순투자금</span><strong>{metric ? fmt.krw(metric.net_invested_krw) : "-"}</strong></div>
            <div className="split"><span className="subtle">투자 기간</span><strong>{metric ? `${metric.days_elapsed}일` : "-"}</strong></div>
            <div className="split"><span className="subtle">평균 입금 환율</span><strong>{metric ? fmt.rate(metric.avg_deposit_exchange_rate) : "-"}</strong></div>
          </div>
        </div>
      </div>
      <div className="card" style={{ marginTop: 14 }}>
        <h2>포트폴리오 구성</h2>
        <PortfolioTable snapshot={snap} targetAllocation={allocation.data?.weights} assetGroups={groups.data} />
      </div>
    </>
  );
}
