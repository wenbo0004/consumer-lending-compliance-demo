# Consumer Lending Compliance Monitoring Demo

A small, explainable portfolio sample: CSV source data → SQLite SQL controls → Python runner → validation and exception review → one-page Streamlit dashboard.

**Everything here is synthetic and fictional.** The company, jurisdictions, records, thresholds, and timelines are invented for demonstration. No rule here claims to state actual law or policy. This project does not use employer or interview assessment data.

## Monitoring design

| Step | APR example | Notice example |
|---|---|---|
| Requirement | Fictional MIRA funded-loan APR limit: 24.00% | Fictional declined-application notice SLA: 5 calendar days, with a reason code |
| Population | FUNDED loans in MIRA | DECLINED applications |
| Source of truth | data/loans.csv | data/applications.csv |
| Rule | APR > 24.00% is flagged | Missing overdue notice, late notice, or missing reason is flagged |
| Exception | Potential finding after DQ screening | Potential finding after DQ screening |
| Investigation | Confirm APR, jurisdiction, and source record | Confirm decision, delivery date, and reason |
| Remediation / evidence | Correct data or investigate pricing; retain source and resolution | Correct data or investigate notice process; retain source and resolution |

The as-of date is **2026-06-30**. The fictional APR source-data contract accepts values from 0% through 100%; values outside that range are DQ review items. This is a *demo-specific assumption*, not a universal statement about valid APRs.

## Run in GitHub Codespaces

In the repository terminal, run these commands in order:

~~~bash
python3 -m pip install -r requirements.txt
python3 scripts/run_monitor.py
python3 -m streamlit run dashboard.py
~~~

Open the forwarded Streamlit port when Codespaces offers it. Run the Python command again after changing source data or SQL, then refresh the dashboard.

## Files to present

- sql/01_apr_control.sql: an example of translating a fictional requirement into a scoped SQL control. The notice and DQ SQL files complete the three control types.
- output/validation.csv: five checks for APR and notice scope, evaluated grain and DQ separation, and rule boundaries. A value of 1 means pass.
- output/exceptions.csv: review queue with control, record_id, event_date, and reason.
- dashboard.py: four KPIs, exceptions by control, event-month trend, and review detail.

Other CSVs in output/ preserve evaluated records and DQ exclusions for investigation. They are evidence, not separate interview talking points.

## Validation and interpretation

The runner compares the **multiset of IDs** returned by each control with the intended source population, so a missing or repeated ID changes the check. It also checks that evaluated records have unique IDs and no DQ-flagged ID; known boundary examples confirm the exact limit passes and the next value fails. These safeguards do not prove every possible input is correct.

A potential control exception is not a confirmed violation. DQ-flagged records are reviewed first, corrected if needed, and then re-run. The review queue supports an analyst's investigation and documented disposition.

## Suggested 2-minute walkthrough

1. State the fictional requirement and population.
2. Show one SQL control and explain its grain and boundary.
3. Explain why DQ issues are separated from potential control exceptions.
4. Show validation.csv, exceptions.csv, and the dashboard. End with the human investigation and evidence trail.
