-- Business question: Which payers are slowest to pay, and how much slower are denied claims?
-- Table: claims (days_in_ar = days from service date to payment or to today if unresolved)

SELECT
    payer_name,
    COUNT(*) AS total_claims,
    ROUND(AVG(CASE WHEN claim_status = 'Paid' THEN CAST(days_in_ar AS FLOAT) END), 1) AS avg_days_paid,
    ROUND(AVG(CASE WHEN claim_status = 'Denied' THEN CAST(days_in_ar AS FLOAT) END), 1) AS avg_days_denied,
    ROUND(AVG(CAST(days_in_ar AS FLOAT)), 1) AS avg_days_overall
FROM claims
GROUP BY payer_name
ORDER BY avg_days_denied DESC;
