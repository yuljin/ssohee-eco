import type { PortfolioSnapshot } from "../lib/api";
import { fmt, pnlClass } from "../lib/format";

interface Props {
  snapshot: PortfolioSnapshot;
  targetAllocation?: Record<string, number>;
  assetGroups?: Record<string, string[]>;
}

export function PortfolioTable({ snapshot, targetAllocation = {}, assetGroups = {} }: Props) {
  const grouped = new Set(Object.values(assetGroups).flat());
  const rows = Object.entries(snapshot.value_by_symbol)
    .filter(([symbol]) => !grouped.has(symbol))
    .map(([symbol, value]) => ({ symbol, value }));

  for (const [group, members] of Object.entries(assetGroups)) {
    const value = members.reduce((sum, symbol) => sum + (snapshot.value_by_symbol[symbol] ?? 0), 0);
    if (value > 0) rows.push({ symbol: `${group} 합산`, value });
  }

  rows.sort((a, b) => b.value - a.value);

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>종목</th>
            <th>수량</th>
            <th>평가금액</th>
            <th>평단가</th>
            <th>손익</th>
            <th>현재 비중</th>
            <th>목표 비중</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ symbol, value }) => {
            const baseSymbol = symbol.replace(" 합산", "");
            const quantity = snapshot.quantity_by_symbol[baseSymbol] ?? 0;
            const pnlPct = snapshot.pnl_pct_by_symbol[baseSymbol] ?? 0;
            const pnlAmount = snapshot.pnl_amount_by_symbol[baseSymbol] ?? 0;
            const weight = snapshot.weight_by_symbol[baseSymbol] ?? value / snapshot.total_value;
            const avgCost = snapshot.avg_cost_by_symbol[baseSymbol] ?? 0;
            return (
              <tr key={symbol}>
                <td><strong>{symbol}</strong></td>
                <td>{quantity ? quantity.toLocaleString("en-US", { maximumFractionDigits: 6 }) : "-"}</td>
                <td>
                  {fmt.usd(value)}
                  <div className="subtle">{snapshot.exchange_rate ? fmt.krw(value * snapshot.exchange_rate) : ""}</div>
                </td>
                <td>{avgCost ? fmt.usd(avgCost) : "-"}</td>
                <td className={pnlClass(pnlPct)}>
                  {fmt.pct(pnlPct)}
                  <div>{fmt.usd(pnlAmount)}</div>
                </td>
                <td>{(weight * 100).toFixed(2)}%</td>
                <td>{((targetAllocation[baseSymbol] ?? 0) * 100).toFixed(1)}%</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

