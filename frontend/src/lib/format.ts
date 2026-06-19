export const fmt = {
  usd: (value = 0, decimals = 2) =>
    value.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: decimals }),
  krw: (value = 0) =>
    value.toLocaleString("ko-KR", { style: "currency", currency: "KRW", maximumFractionDigits: 0 }),
  pct: (value = 0, decimals = 2) => `${value > 0 ? "+" : ""}${value.toFixed(decimals)}%`,
  rate: (value = 0) => `₩${value.toLocaleString("ko-KR", { maximumFractionDigits: 2 })}`
};

export const pnlClass = (value = 0) => (value > 0 ? "gain" : value < 0 ? "loss" : "neutral");

