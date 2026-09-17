"""Create deterministic, wholly fictional source data for this demo."""

import csv
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BASE = date(2026, 4, 1)


def iso(day):
    return day.isoformat() if day else ""


def write_csv(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main():
    applications = []
    for i in range(1, 201):
        submitted = BASE + timedelta(days=(i * 3) % 75)
        decision_date = submitted + timedelta(days=1)
        declined = i % 3 == 0
        notice_date = decision_date + timedelta(days=2) if declined else None
        applications.append({
            "application_id": f"A{i:04d}",
            "submitted_date": iso(submitted),
            "decision": "DECLINED" if declined else "APPROVED",
            "decision_date": iso(decision_date),
            "notice_date": iso(notice_date),
            "reason_code": "DEMO_CREDIT_POLICY" if declined else "",
        })

    by_app = {row["application_id"]: row for row in applications}
    for number in (3, 6):
        row = by_app[f"A{number:04d}"]
        row["notice_date"] = iso(date.fromisoformat(row["decision_date"]) + timedelta(days=5))
    for number in (9, 12):
        row = by_app[f"A{number:04d}"]
        row["notice_date"] = iso(date.fromisoformat(row["decision_date"]) + timedelta(days=6))
    for number in (15, 18):
        by_app[f"A{number:04d}"]["notice_date"] = ""
    for number in (21, 24):
        by_app[f"A{number:04d}"]["reason_code"] = ""
    by_app["A0027"]["notice_date"] = iso(
        date.fromisoformat(by_app["A0027"]["decision_date"]) - timedelta(days=1)
    )
    by_app["A0040"]["decision"] = ""
    applications.append(dict(by_app["A0200"]))

    approved_ids = [i for i in range(1, 201) if i % 3 != 0 and i != 40]
    loans = []
    for i, app_num in enumerate(approved_ids[:120], 1):
        app = by_app[f"A{app_num:04d}"]
        origination = date.fromisoformat(app["decision_date"]) + timedelta(days=1)
        loans.append({
            "loan_id": f"L{i:04d}",
            "application_id": app["application_id"],
            "jurisdiction": ("MIRA", "TALA", "ORIN")[i % 3],
            "status": "FUNDED",
            "origination_date": iso(origination),
            "apr": f"{18 + (i % 6):.2f}",
        })

    by_loan = {row["loan_id"]: row for row in loans}
    for number, apr in ((3, "24.00"), (6, "24.01"), (9, "27.00")):
        by_loan[f"L{number:04d}"]["apr"] = apr
    by_loan["L0015"]["apr"] = "105.00"
    by_loan["L0018"]["application_id"] = "A9999"
    loans.append(dict(by_loan["L0120"]))

    write_csv(DATA / "applications.csv", [
        "application_id", "submitted_date", "decision", "decision_date",
        "notice_date", "reason_code"
    ], applications)
    write_csv(DATA / "loans.csv", [
        "loan_id", "application_id", "jurisdiction", "status",
        "origination_date", "apr"
    ], loans)
    print(f"Generated {len(applications)} application rows and {len(loans)} loan rows")


if __name__ == "__main__":
    main()
