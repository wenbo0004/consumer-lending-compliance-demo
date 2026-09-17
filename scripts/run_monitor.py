import csv
from collections import Counter
import sqlite3
from pathlib import Path

root = Path(__file__).resolve().parents[1]

db = sqlite3.connect(":memory:")
db.row_factory = sqlite3.Row
db.execute("""
    CREATE TABLE loans (
        loan_id TEXT,
        application_id TEXT,
        jurisdiction TEXT,
        status TEXT,
        origination_date TEXT,
        apr REAL
    )
""")

with (root / "data" / "loans.csv").open(newline="", encoding="utf-8") as file:
    source_rows = list(csv.DictReader(file))

db.executemany(
    """INSERT INTO loans VALUES (
        :loan_id, :application_id, :jurisdiction,
        :status, :origination_date, :apr
    )""",
    source_rows,
)

db.execute("""
    CREATE TABLE applications (
        application_id TEXT,
        submitted_date TEXT,
        decision TEXT,
        decision_date TEXT,
        notice_date TEXT,
        reason_code TEXT
    )
""")

with (root / "data" / "applications.csv").open(
    newline="", encoding="utf-8"
) as file:
    application_rows = list(csv.DictReader(file))

db.executemany(
    """INSERT INTO applications VALUES (
        :application_id, :submitted_date, :decision,
        :decision_date, :notice_date, :reason_code
    )""",
    application_rows,
)

query = (root / "sql" / "01_apr_control.sql").read_text(encoding="utf-8")
results = [dict(row) for row in db.execute(query)]

print(f"Source loan rows: {len(source_rows)}")
print(f"APR population: {len(results)}")
print("Preliminary flags before DQ:")
for row in results:
    if row["exception_flag"] == 1:
        print(row["loan_id"], row["apr"])

dq_query = (root / "sql" / "03_data_quality.sql").read_text(encoding="utf-8")
dq_results = [dict(row) for row in db.execute(dq_query)]

print("DQ issues:")
for row in dq_results:
    print(row["record_id"], row["issue"])
dq_loan_ids = {
    row["record_id"]
    for row in dq_results
    if row["entity"] == "LOAN"
}

quarantined = [
    row for row in results if row["loan_id"] in dq_loan_ids
]
apr_evaluated = [
    row for row in results if row["loan_id"] not in dq_loan_ids
]

assert len(results) == len(apr_evaluated) + len(quarantined)

print(
    f"APR reconciliation: {len(results)} in scope = "
    f"{len(apr_evaluated)} evaluated + {len(quarantined)} quarantined"
)
print("Potential APR exceptions after DQ:")
for row in apr_evaluated:
    if row["exception_flag"] == 1:
        print(row["loan_id"], row["apr"])
notice_query = (root / "sql" / "02_notice_control.sql").read_text(
    encoding="utf-8"
)
notice_results = [
    dict(row)
    for row in db.execute(notice_query, {"as_of_date": "2026-06-30"})
]

print(f"Notice population before DQ: {len(notice_results)}")
print("Preliminary notice exceptions before DQ:")
for row in notice_results:
    if row["exception_flag"] == 1:
        print(row["application_id"], row["exception_reason"])

dq_application_ids = {
    row["record_id"]
    for row in dq_results
    if row["entity"] == "APPLICATION"
}

notice_quarantined = [
    row for row in notice_results
    if row["application_id"] in dq_application_ids
]
notice_evaluated = [
    row for row in notice_results
    if row["application_id"] not in dq_application_ids
]

raw_declined_count = sum(
    row["decision"] == "DECLINED" for row in application_rows
)
assert raw_declined_count == len(notice_results)
assert len(notice_results) == len(notice_evaluated) + len(notice_quarantined)

print(
    f"Notice reconciliation: {len(notice_results)} in scope = "
    f"{len(notice_evaluated)} evaluated + "
    f"{len(notice_quarantined)} quarantined"
)
print("Potential notice exceptions after DQ:")
for row in notice_evaluated:
    if row["exception_flag"] == 1:
        print(row["application_id"], row["exception_reason"])

# Validate actual output against intended scope and known boundaries.
def find(rows, key, value):
    return next(row for row in rows if row[key] == value)

checks = {
    "apr_scope": Counter(row["loan_id"] for row in results) == Counter(
        row["loan_id"] for row in source_rows
        if row["status"] == "FUNDED" and row["jurisdiction"] == "MIRA"
    ),
    "notice_scope": Counter(row["application_id"] for row in notice_results) == Counter(
        row["application_id"] for row in application_rows
        if row["decision"] == "DECLINED"
    ),
    "evaluated_grain_and_dq": (
        len({row["loan_id"] for row in apr_evaluated}) == len(apr_evaluated)
        and len({row["application_id"] for row in notice_evaluated}) == len(notice_evaluated)
        and all(row["loan_id"] not in dq_loan_ids for row in apr_evaluated)
        and all(row["application_id"] not in dq_application_ids for row in notice_evaluated)
    ),
    "apr_boundary": (
        find(apr_evaluated, "loan_id", "L0003")["exception_flag"] == 0
        and find(apr_evaluated, "loan_id", "L0006")["exception_flag"] == 1
    ),
    "notice_boundary": (
        find(notice_evaluated, "application_id", "A0003")["exception_flag"] == 0
        and find(notice_evaluated, "application_id", "A0009")["exception_flag"] == 1
    ),
}
validation_rows = [
    {"check_name": name, "passed": int(passed)} for name, passed in checks.items()
]

output = root / "output"
output.mkdir(exist_ok=True)

def save_csv(name, rows, columns):
    with (output / name).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

save_csv("apr_evaluated.csv", apr_evaluated, [
    "loan_id", "application_id", "jurisdiction", "origination_date", "apr", "exception_flag",
])
save_csv("notice_evaluated.csv", notice_evaluated, [
    "application_id", "decision_date", "notice_date", "reason_code",
    "days_to_notice", "exception_reason", "exception_flag",
])
save_csv("dq_exceptions.csv", dq_results, ["entity", "record_id", "issue"])

excluded = [
    {"control": "APR", "record_id": row["loan_id"]} for row in quarantined
] + [
    {"control": "NOTICE", "record_id": row["application_id"]}
    for row in notice_quarantined
]
save_csv("population_exclusions.csv", excluded, ["control", "record_id"])

apr_flags = [row for row in apr_evaluated if row["exception_flag"] == 1]
notice_flags = [row for row in notice_evaluated if row["exception_flag"] == 1]
review = [
    {"control": "APR", "record_id": row["loan_id"],
     "event_date": row["origination_date"], "reason": "APR_ABOVE_FICTIONAL_LIMIT"}
    for row in apr_flags
] + [
    {"control": "NOTICE", "record_id": row["application_id"],
     "event_date": row["decision_date"], "reason": row["exception_reason"]}
    for row in notice_flags
] + [
    {"control": "DQ", "record_id": row["record_id"],
     "event_date": "", "reason": row["issue"]}
    for row in dq_results
]
save_csv("exceptions.csv", review, ["control", "record_id", "event_date", "reason"])

save_csv("validation.csv", validation_rows, ["check_name", "passed"])
print(f"Validation: {sum(checks.values())}/{len(checks)} checks passed")
print(f"Review queue: {len(review)} rows in output/exceptions.csv")
if not all(checks.values()):
    raise SystemExit("Validation failed; inspect output/validation.csv")
