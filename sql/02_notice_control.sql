WITH notice_check AS (
    SELECT
        application_id,
        decision_date,
        NULLIF(notice_date, '') AS notice_date,
        reason_code,
        CAST(
            julianday(NULLIF(notice_date, '')) - julianday(decision_date)
            AS INTEGER
        ) AS days_to_notice,
        CASE
            WHEN NULLIF(notice_date, '') IS NULL
                 AND julianday(:as_of_date) - julianday(decision_date) > 5
                THEN 'NOTICE_MISSING_OVERDUE'
            WHEN NULLIF(notice_date, '') IS NOT NULL
                 AND julianday(notice_date) - julianday(decision_date) > 5
                THEN 'NOTICE_LATE'
            WHEN TRIM(COALESCE(reason_code, '')) = ''
                THEN 'REASON_MISSING'
        END AS exception_reason
    FROM applications
    WHERE decision = 'DECLINED'
      AND decision_date <> ''
      AND decision_date <= :as_of_date
)
SELECT
    *,
    CASE WHEN exception_reason IS NULL THEN 0 ELSE 1 END AS exception_flag
FROM notice_check;