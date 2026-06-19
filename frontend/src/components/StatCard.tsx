interface StatCardProps {
  label: string;
  value: string;
  helper?: string;
  tone?: "gain" | "loss" | "success" | "warning" | "neutral";
}

export function StatCard({ label, value, helper, tone = "neutral" }: StatCardProps) {
  return (
    <div className="card">
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${tone}`}>{value}</div>
      {helper ? <div className="subtle">{helper}</div> : null}
    </div>
  );
}

