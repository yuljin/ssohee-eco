import type { TradeOrder } from "../lib/api";
import { fmt } from "../lib/format";

export function OrdersTable({ orders }: { orders: TradeOrder[] }) {
  if (!orders.length) return <div className="empty">현재 포트폴리오는 리밸런싱 범위 안에 있습니다.</div>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>구분</th>
            <th>종목</th>
            <th>수량</th>
            <th>금액</th>
            <th>원화 환산</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((order, index) => (
            <tr key={`${order.symbol}-${order.side}-${index}`}>
              <td><span className={`tag ${order.side.toLowerCase()}`}>{order.side}</span></td>
              <td><strong>{order.symbol}</strong></td>
              <td>{order.quantity.toLocaleString("en-US", { maximumFractionDigits: 6 })}</td>
              <td>{fmt.usd(order.value)}</td>
              <td>{order.value_krw ? fmt.krw(order.value_krw) : "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

