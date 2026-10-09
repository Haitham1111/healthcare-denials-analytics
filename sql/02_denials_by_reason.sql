-- Business question: What is actually driving our denials?
-- Table: claims (denial_reason uses CARC-style codes, e.g. CO-50, CO-96)

SELECT
    denial_reason,
    COUNT(*) AS denied_claims,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_denials,
    ROUND(SUM(billed_amount), 2) AS billed_at_risk
FROM claims
WHERE claim_status = 'Denied'
GROUP BY denial_reason
ORDER BY denied_claims DESC;
