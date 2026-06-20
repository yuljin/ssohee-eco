export interface PortfolioSnapshot {
  total_value: number;
  value_by_symbol: Record<string, number>;
  weight_by_symbol: Record<string, number>;
  cash: number;
  avg_cost_by_symbol: Record<string, number>;
  pnl_pct_by_symbol: Record<string, number>;
  pnl_amount_by_symbol: Record<string, number>;
  pnl_pct_krw_by_symbol: Record<string, number>;
  pnl_amount_krw_by_symbol: Record<string, number>;
  quantity_by_symbol: Record<string, number>;
  exchange_rate: number;
  avg_exchange_rate_by_symbol: Record<string, number>;
}

export interface Transaction {
  id: number;
  side: "BUY" | "SELL" | "DIVIDEND";
  symbol: string;
  quantity: number;
  price: number;
  fee: number;
  exchange_rate?: number;
  executed_at: string;
  memo?: string;
}

export type TransactionCreate = Omit<Transaction, "id" | "executed_at">;

export interface TargetAllocation {
  weights: Record<string, number>;
  threshold: number;
}

export interface TradeOrder {
  symbol: string;
  side: "BUY" | "SELL";
  quantity: number;
  value: number;
  value_krw: number;
}

export interface RebalanceSimulationResult {
  before_snapshot: PortfolioSnapshot;
  plan: { orders: TradeOrder[] };
  after_snapshot: PortfolioSnapshot;
  exchange_rate: number;
}

export interface PortfolioMetrics {
  total_deposit: number;
  total_withdrawal: number;
  net_invested: number;
  current_value: number;
  total_pnl: number;
  total_return_pct: number | null;
  annualized_return_pct: number | null;
  total_deposit_krw: number;
  total_withdrawal_krw: number;
  net_invested_krw: number;
  current_value_krw: number;
  total_pnl_krw: number;
  total_return_pct_krw: number | null;
  annualized_return_pct_krw: number | null;
  start_date: string;
  end_date: string;
  days_elapsed: number;
  exchange_rate: number;
  avg_deposit_exchange_rate: number;
}

export interface MonthlyReturn {
  month: string;
  start_value: number;
  end_value: number;
  net_deposit: number;
  return_pct: number;
  cumulative_return_pct: number;
}

export interface DrawdownInfo {
  symbol: string;
  current_price: number;
  high_52w: number;
  high_52w_date: string;
  drawdown_pct: number;
  signal: string;
  signal_color: string;
  days_since_high: number;
}

export interface DrawdownAnalysis {
  symbols: DrawdownInfo[];
  analysis_date: string;
  total_symbols: number;
  buy_signals: number;
  consider_signals: number;
}

export interface ExchangeRateAnalysis {
  current_rate: number;
  high: number;
  low: number;
  average: number;
  from_high_pct: number;
  from_low_pct: number;
  from_avg_pct: number;
  signal: string;
  signal_color: string;
  recommendation: string;
  history: { date: string; rate: number }[];
}

export type ExchangeRateGuide = Record<string, ExchangeRateAnalysis>;

export interface AssetBuyGuide {
  symbol: string;
  current_price: number;
  drawdown_pct: number;
  drawdown_score: number;
  exchange_score: number;
  weight_score: number;
  total_score: number;
  buy_ratio: number;
  target_weight: number;
  current_weight: number;
  base_amount: number;
  recommended_amount: number;
  signal: string;
  signal_color: string;
  signal_desc: string;
}

export interface BuyTimingGuide {
  exchange_rate: number;
  exchange_from_avg_pct: number;
  exchange_score: number;
  monthly_amount: number;
  asset_guides: AssetBuyGuide[];
  reference_ratio: number;
  reference_amount: number;
  actual_ratio: number;
  actual_amount: number;
  is_floor_applied: boolean;
  message: string;
  warning: string;
}

export interface DashboardData {
  snapshot: PortfolioSnapshot;
  metrics: PortfolioMetrics;
  allocation: TargetAllocation;
  asset_groups: Record<string, string[]>;
  live_market_data: boolean;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || response.statusText);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  dashboard: (liveMarketData = true, goldKrxPrice?: number) => {
    const params = new URLSearchParams({ live_market_data: String(liveMarketData) });
    if (goldKrxPrice) params.set("gold_krx_price", String(goldKrxPrice));
    return request<DashboardData>(`/api/v1/analytics/dashboard?${params}`);
  },
  snapshot: (goldKrxPrice?: number) =>
    request<PortfolioSnapshot>(`/portfolio/snapshot${goldKrxPrice ? `?gold_krx_price=${goldKrxPrice}` : ""}`),
  metrics: () => request<PortfolioMetrics>("/api/v1/analytics/portfolio-metrics"),
  monthlyReturns: () => request<MonthlyReturn[]>("/api/v1/analytics/monthly-returns"),
  transactions: () => request<Transaction[]>("/api/v1/transactions"),
  createTransaction: (payload: TransactionCreate) =>
    request<Transaction>("/api/v1/transactions", { method: "POST", body: JSON.stringify(payload) }),
  updateTransaction: (id: number, payload: TransactionCreate) =>
    request<Transaction>(`/api/v1/transactions/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteTransaction: (id: number) => request<void>(`/api/v1/transactions/${id}`, { method: "DELETE" }),
  allocation: () => request<TargetAllocation>("/rebalance/config/allocation"),
  updateAllocation: (payload: TargetAllocation) =>
    request<TargetAllocation>("/rebalance/config/allocation", { method: "PUT", body: JSON.stringify(payload) }),
  assetGroups: () => request<Record<string, string[]>>("/rebalance/config/asset-groups"),
  rebalance: (mode?: boolean, goldKrxPrice?: number) => {
    const params = new URLSearchParams();
    if (mode !== undefined) params.set("enable_tax_loss_harvesting", String(mode));
    if (goldKrxPrice) params.set("gold_krx_price", String(goldKrxPrice));
    return request<RebalanceSimulationResult>(`/rebalance/simulate?${params}`);
  },
  drawdown: (weeks = 52) => request<DrawdownAnalysis>(`/api/v1/drawdown/analysis?weeks=${weeks}`),
  cashGuide: (cash: number, weeks = 52) =>
    request<Record<string, number>>(`/api/v1/drawdown/cash-guide?available_cash=${cash}&weeks=${weeks}`),
  exchangeRate: (periodDays = 365) =>
    request<ExchangeRateAnalysis>(`/api/v1/exchange-rate/analysis?period_days=${periodDays}`),
  exchangeGuide: () => request<ExchangeRateGuide>("/api/v1/exchange-rate/guide"),
  buyTiming: (monthlyAmount = 1000, goldKrxPrice?: number) => {
    const params = new URLSearchParams({ monthly_amount: String(monthlyAmount) });
    if (goldKrxPrice) params.set("gold_krx_price", String(goldKrxPrice));
    return request<BuyTimingGuide>(`/api/v1/buy-timing/guide?${params}`);
  }
};
