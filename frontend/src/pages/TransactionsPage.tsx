import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, TransactionCreate } from "../lib/api";
import { fmt } from "../lib/format";

const symbols = ["VOO", "QQQ", "TLT", "GLDM", "GOLD-KRX", "BTC", "CASH"];

export function TransactionsPage() {
  const queryClient = useQueryClient();
  const { data = [], isLoading } = useQuery({ queryKey: ["transactions"], queryFn: api.transactions });
  const [form, setForm] = useState<TransactionCreate>({
    side: "BUY",
    symbol: "VOO",
    quantity: 1,
    price: 0,
    fee: 0,
    exchange_rate: undefined,
    memo: ""
  });
  const create = useMutation({
    mutationFn: api.createTransaction,
    onSuccess: () => {
      queryClient.invalidateQueries();
      setForm({ side: "BUY", symbol: "VOO", quantity: 1, price: 0, fee: 0, memo: "" });
    }
  });
  const remove = useMutation({
    mutationFn: api.deleteTransaction,
    onSuccess: () => queryClient.invalidateQueries()
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    create.mutate(form);
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1>거래 내역</h1>
          <p>거래를 추가하면 보유 수량, 평단가, 현금이 자동 재계산됩니다.</p>
        </div>
      </div>
      <div className="card">
        <h2>거래 추가</h2>
        <form className="toolbar" onSubmit={submit}>
          <select className="input" value={form.side} onChange={(e) => setForm({ ...form, side: e.target.value as TransactionCreate["side"] })}>
            <option value="BUY">BUY</option>
            <option value="SELL">SELL</option>
            <option value="DIVIDEND">DIVIDEND</option>
          </select>
          <select className="input" value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })}>
            {symbols.map((symbol) => <option key={symbol}>{symbol}</option>)}
          </select>
          <input className="input" type="number" step="0.000001" placeholder="수량" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: Number(e.target.value) })} />
          <input className="input" type="number" step="0.01" placeholder="가격 USD" value={form.price} onChange={(e) => setForm({ ...form, price: Number(e.target.value) })} />
          <input className="input" type="number" step="0.01" placeholder="수수료" value={form.fee} onChange={(e) => setForm({ ...form, fee: Number(e.target.value) })} />
          <input className="input" type="number" step="0.1" placeholder="환율" value={form.exchange_rate ?? ""} onChange={(e) => setForm({ ...form, exchange_rate: e.target.value ? Number(e.target.value) : undefined })} />
          <input className="input" placeholder="메모" value={form.memo ?? ""} onChange={(e) => setForm({ ...form, memo: e.target.value })} />
          <button className="button primary" type="submit">저장</button>
        </form>
      </div>
      <div className="card" style={{ marginTop: 14 }}>
        <h2>목록</h2>
        {isLoading ? <div className="loading">불러오는 중입니다.</div> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>ID</th><th>일시</th><th>구분</th><th>종목</th><th>수량</th><th>가격</th><th>수수료</th><th>환율</th><th>메모</th><th></th></tr>
              </thead>
              <tbody>
                {data.map((tx) => (
                  <tr key={tx.id}>
                    <td>{tx.id}</td>
                    <td>{new Date(tx.executed_at).toLocaleString("ko-KR")}</td>
                    <td><span className={`tag ${tx.side === "BUY" ? "buy" : "sell"}`}>{tx.side}</span></td>
                    <td><strong>{tx.symbol}</strong></td>
                    <td>{tx.quantity.toLocaleString("en-US", { maximumFractionDigits: 8 })}</td>
                    <td>{fmt.usd(tx.price)}</td>
                    <td>{fmt.usd(tx.fee)}</td>
                    <td>{tx.exchange_rate ? fmt.rate(tx.exchange_rate) : "-"}</td>
                    <td>{tx.memo ?? ""}</td>
                    <td><button className="button danger" onClick={() => remove.mutate(tx.id)}>삭제</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}

