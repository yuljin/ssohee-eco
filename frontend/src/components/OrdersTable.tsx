import type { TradeOrder } from "../lib/api";
import { fmt } from "../lib/format";

export function OrdersTable({ orders }: { orders: TradeOrder[] }) {
  if (!orders.length) return <div className="empty">현재 포트폴리오는 리밸런싱 범위 안에 있습니다.</div>;
  return (
    <div className="table-wrap responsive-table">
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
              <td data-label="구분"><span className={`tag ${order.side.toLowerCase()}`}>{order.side}</span></td>
              <td data-label="종목"><strong>{order.symbol}</strong></td>
              <td data-label="수량">{order.quantity.toLocaleString("en-US", { maximumFractionDigits: 6 })}</td>
              <td data-label="금액">{fmt.usd(order.value)}</td>
              <td data-label="원화 환산">{order.value_krw ? fmt.krw(order.value_krw) : "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
