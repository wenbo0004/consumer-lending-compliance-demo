-- Fictional rule: funded loans in MIRA must have APR <= 24.00%.
-- Grain: one row per loan_id.

SELECT
    loan_id,
    application_id,
    jurisdiction,
    origination_date,
    apr,
    CASE
        WHEN apr > 24.00 THEN 1
        ELSE 0
    END AS exception_flag
FROM loans
WHERE status = 'FUNDED'
  AND jurisdiction = 'MIRA';