from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.core.db import Base, SessionLocal, engine
from app.models.transaction import Transaction


def parse_datetime(value: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return datetime.fromisoformat(value)


def import_csv(path: Path, preserve_id: bool = True, replace: bool = False) -> int:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if replace:
            db.query(Transaction).delete()
        count = 0
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                payload = {
                    "side": row["side"].upper(),
                    "symbol": row["symbol"].upper(),
                    "quantity": float(row["quantity"]),
                    "price": float(row["price"]),
                    "fee": float(row["fee"] or 0),
                    "exchange_rate": float(row["exchange_rate"]) if row.get("exchange_rate") else None,
                    "executed_at": parse_datetime(row["executed_at"]),
                    "memo": row.get("memo") or None,
                }
                if preserve_id:
                    payload["id"] = int(row["id"])
                db.add(Transaction(**payload))
                count += 1
        db.commit()
        return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Import transactions CSV into configured DATABASE_URL.")
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--no-preserve-id", action="store_true")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    count = import_csv(args.csv, preserve_id=not args.no_preserve_id, replace=args.replace)
    print(f"Imported {count} transactions")


if __name__ == "__main__":
    main()
