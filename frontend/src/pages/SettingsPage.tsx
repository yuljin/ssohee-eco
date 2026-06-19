import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";

export function SettingsPage() {
  const queryClient = useQueryClient();
  const allocation = useQuery({ queryKey: ["allocation"], queryFn: api.allocation });
  const [weights, setWeights] = useState<Record<string, number>>({});
  const [threshold, setThreshold] = useState(10);
  const total = Object.values(weights).reduce((sum, value) => sum + value, 0);
  const valid = Math.abs(total - 100) < 0.1;
  const save = useMutation({
    mutationFn: () => api.updateAllocation({
      weights: Object.fromEntries(Object.entries(weights).map(([key, value]) => [key, value / 100])),
      threshold: threshold / 100
    }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["allocation"] })
  });

  useEffect(() => {
    if (!allocation.data) return;
    setWeights(Object.fromEntries(Object.entries(allocation.data.weights).map(([key, value]) => [key, value * 100])));
    setThreshold(allocation.data.threshold * 100);
  }, [allocation.data]);

  if (allocation.isLoading) return <div className="loading">설정을 불러오는 중입니다.</div>;

  return (
    <>
      <div className="page-header">
        <div><h1>설정</h1><p>목표 비중과 리밸런싱 임계값을 조정합니다. 서버 재시작 시 기본값으로 돌아갑니다.</p></div>
        <button className="button primary" disabled={!valid || save.isPending} onClick={() => save.mutate()}>저장</button>
      </div>
      <div className="grid cols-2">
        <div className="card">
          <h2>목표 비중</h2>
          <div className="grid">
            {Object.entries(weights).map(([symbol, value]) => (
              <label className="split" key={symbol}>
                <strong>{symbol}</strong>
                <input className="input" type="number" min="0" max="100" step="0.5" value={value} onChange={(e) => setWeights({ ...weights, [symbol]: Number(e.target.value) })} />
              </label>
            ))}
          </div>
          <p className={valid ? "success" : "danger"}>합계: {total.toFixed(1)}%</p>
        </div>
        <div className="card">
          <h2>Threshold</h2>
          <label className="split">
            <span className="subtle">리밸런싱 허용 편차</span>
            <input className="input" type="number" min="1" max="50" value={threshold} onChange={(e) => setThreshold(Number(e.target.value))} />
          </label>
          <p className="subtle">예: 10%이면 목표 40% 자산은 30~50% 범위를 벗어날 때 매도 후보가 됩니다.</p>
        </div>
      </div>
    </>
  );
}

