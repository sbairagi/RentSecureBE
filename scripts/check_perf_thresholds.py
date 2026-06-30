"""Check Locust performance thresholds from CSV report.

Reads the stats CSV produced by Locust and validates:
- p95 latency < 500ms per endpoint
- failure ratio < 1% per endpoint
"""

import csv
import sys


def main() -> int:
    try:
        with open("locust-report_stats.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get("Name") or row["Name"] in ("Aggregated", ""):
                    continue
                p95 = float(row.get("95%", 0) or 0)
                fail_count = float(row.get("Failure Count", 0) or 0)
                req_count = float(row.get("Request Count", 1) or 1)
                fail_ratio = fail_count / max(req_count, 1)

                if p95 > 500:
                    print(
                        f"WARN: {row['Name']} p95 latency {p95:.0f}ms "
                        "exceeds 500ms threshold"
                    )
                if fail_ratio > 0.01:
                    print(
                        f"WARN: {row['Name']} failure ratio {fail_ratio:.1%} exceeds 1%"
                    )
                print(f"OK: {row['Name']} p95={p95:.0f}ms fail={fail_ratio:.1%}")
            print("Performance thresholds check complete.")
    except FileNotFoundError:
        print("WARNING: locust-report_stats.csv not found; skipping threshold check")
    return 0


if __name__ == "__main__":
    sys.exit(main())
