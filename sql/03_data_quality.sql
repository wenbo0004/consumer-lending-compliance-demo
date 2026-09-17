-- Synthetic source-data assumption: this fictional product expects APR from 0% to 100%.
-- Values outside this demo contract are quarantined for source verification.
-- This is not a universal APR limit or a legal requirement.
SELECT
    'LOAN' AS entity,
    loan_id AS record_id,
    'INVALID_APR' AS issue
FROM loans
WHERE apr IS NULL OR apr < 0 OR apr > 100

UNION ALL

SELECT
    'LOAN' AS entity,
    loan_id AS record_id,
    'DUPLICATE_LOAN_ID' AS issue
FROM loans
GROUP BY loan_id
HAVING COUNT(*) > 1

UNION ALL

SELECT
    'LOAN' AS entity,
    l.loan_id AS record_id,
    'ORPHAN_APPLICATION' AS issue
FROM loans l
LEFT JOIN applications a
    ON l.application_id = a.application_id
WHERE a.application_id IS NULL

UNION ALL
SELECT 'APPLICATION', application_id, 'DUPLICATE_APPLICATION_ID'
FROM applications
GROUP BY application_id
HAVING COUNT(*) > 1

UNION ALL
SELECT 'APPLICATION', application_id, 'MISSING_DECISION'
FROM applications
WHERE decision IS NULL OR TRIM(decision) = ''

UNION ALL
SELECT 'APPLICATION', application_id, 'MISSING_DECISION_DATE'
FROM applications
WHERE decision_date IS NULL OR decision_date = ''

UNION ALL
SELECT 'APPLICATION', application_id, 'NOTICE_BEFORE_DECISION'
FROM applications
WHERE notice_date IS NOT NULL
  AND notice_date <> ''
  AND decision_date <> ''
  AND notice_date < decision_date;
