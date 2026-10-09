-- Business question: Which services (CPT codes) get denied the most?
-- Table: claims

SELECT TOP 10
    cpt_code,
    COUNT(*) AS total_claims,
    SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) AS denied_claims,
    ROUND(100.0 * SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) / COUNT(*), 1) AS denial_rate_pct,
    ROUND(SUM(CASE WHEN claim_status = 'Denied' THEN billed_amount ELSE 0 END), 2) AS denied_billed_amount
FROM claims
GROUP BY cpt_code
HAVING COUNT(*) >= 50
ORDER BY denial_rate_pct DESC;
