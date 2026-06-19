import {
  Activity,
  BarChart3,
  Coins,
  Gauge,
  LineChart,
  ReceiptText,
  RefreshCcw,
  Settings,
  TrendingDown
} from "lucide-react";
import { useState } from "react";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { BuyTimingPage } from "./pages/BuyTimingPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DrawdownPage, ExchangeRatePage } from "./pages/MarketPages";
import { RebalancePage } from "./pages/RebalancePage";
import { SettingsPage } from "./pages/SettingsPage";
import { TransactionsPage } from "./pages/TransactionsPage";

type PageKey = "dashboard" | "buy" | "analytics" | "transactions" | "rebalance" | "drawdown" | "exchange" | "settings";

const navItems: { key: PageKey; label: string; icon: React.ComponentType<{ size?: number }> }[] = [
  { key: "dashboard", label: "대시보드", icon: Gauge },
  { key: "buy", label: "매수 타이밍", icon: Coins },
  { key: "analytics", label: "성과 분석", icon: BarChart3 },
  { key: "transactions", label: "거래 내역", icon: ReceiptText },
  { key: "rebalance", label: "리밸런싱", icon: RefreshCcw },
  { key: "drawdown", label: "하락폭", icon: TrendingDown },
  { key: "exchange", label: "환율", icon: LineChart },
  { key: "settings", label: "설정", icon: Settings }
];

export function App() {
  const [page, setPage] = useState<PageKey>("dashboard");
  const Page = {
    dashboard: DashboardPage,
    buy: BuyTimingPage,
    analytics: AnalyticsPage,
    transactions: TransactionsPage,
    rebalance: RebalancePage,
    drawdown: DrawdownPage,
    exchange: ExchangeRatePage,
    settings: SettingsPage
  }[page];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark" />
          <div>
            <div>ssohee-eco</div>
            <div className="subtle">Portfolio System</div>
          </div>
        </div>
        <nav className="nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button key={item.key} className={page === item.key ? "active" : ""} onClick={() => setPage(item.key)}>
                <Icon size={18} />
                {item.label}
              </button>
            );
          })}
        </nav>
        <div className="card" style={{ marginTop: 18, padding: 12 }}>
          <div className="split">
            <span className="subtle">API</span>
            <Activity size={16} className="success" />
          </div>
          <div className="subtle" style={{ marginTop: 8 }}>FastAPI + Neon</div>
        </div>
      </aside>
      <main className="content">
        <Page />
      </main>
    </div>
  );
}
