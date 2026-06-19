import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { OrdersTable } from "../components/OrdersTable";
import { PortfolioTable } from "../components/PortfolioTable";
import { StatCard } from "../components/StatCard";
import { fmt } from "../lib/format";

export function RebalancePage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["rebalance"], queryFn: () => api.rebalance() });
  const allocation = useQuery({ queryKey: ["allocation"], queryFn: api.allocation });
  const groups = useQuery({ queryKey: ["assetGroups"], queryFn: api.assetGroups });
  const execute = useMutation({
    mutationFn: async () => {
      if (!data) return;
      for (const order of data.plan.orders) {
        await api.createTransaction({
          side: order.side,
          symbol: order.symbol,
          quantity: order.quantity,
          price: order.value / order.quantity,
          fee: 0,
          exchange_rate: data.exchange_rate || undefined
        });
      }
    },
    onSuccess: () => queryClient.invalidateQueries()
  });

  if (isLoading) return <div className="loading">리밸런싱을 계산하는 중입니다.</div>;
  if (!data) return <div className="error">리밸런싱 데이터를 불러오지 못했습니다.</div>;

  return (
    <>
      <div className="page-header">
        <div>
          <h1>리밸런싱 제안</h1>
          <p>목표 비중과 threshold를 기준으로 주문 후보를 계산합니다.</p>
        </div>
        <button className="button primary" disabled={!data.plan.orders.length || execute.isPending} onClick={() => execute.mutate()}>
          주문을 거래로 등록
        </button>
      </div>
      <div className="grid cols-3">
        <StatCard label="현재 총자산" value={fmt.usd(data.before_snapshot.total_value)} />
        <StatCard label="현재 현금" value={fmt.usd(data.before_snapshot.cash)} />
        <StatCard label="주문 수" value={`${data.plan.orders.length}건`} />
      </div>
      <div className="card" style={{ marginTop: 14 }}>
        <h2>주문 제안</h2>
        <OrdersTable orders={data.plan.orders} />
      </div>
      <div className="grid cols-2" style={{ marginTop: 14 }}>
        <div className="card">
          <h2>리밸런싱 전</h2>
          <PortfolioTable snapshot={data.before_snapshot} targetAllocation={allocation.data?.weights} assetGroups={groups.data} />
        </div>
        <div className="card">
          <h2>리밸런싱 후</h2>
          <PortfolioTable snapshot={data.after_snapshot} targetAllocation={allocation.data?.weights} assetGroups={groups.data} />
        </div>
      </div>
    </>
  );
}

