-- Business question: Which payers deny the highest share of our claims?
-- Table: claims (claim_status = 'Denied' / 'Paid')
-- Run top-to-bottom on a SQL Server database with data/claims.csv loaded.

SELECT TOP 10
    payer_name,
    COUNT(*) AS total_claims,
    SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) AS denied_claims,
    ROUND(100.0 * SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) / COUNT(*), 1) AS denial_rate_pct,
    ROUND(SUM(CASE WHEN claim_status = 'Denied' THEN billed_amount ELSE 0 END), 2) AS denied_billed_amount
FROM claims
GROUP BY payer_name
HAVING COUNT(*) >= 100
ORDER BY denial_rate_pct DESC;
