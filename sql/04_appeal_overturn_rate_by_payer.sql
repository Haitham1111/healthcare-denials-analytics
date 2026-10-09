-- Business question: Where do appeals actually pay off?
-- Table: claims (appeal_outcome = 'overturned' / 'upheld' / 'pending' / 'not appealed')
-- Overturn rate is computed on decided appeals only (pending excluded).

SELECT
    payer_name,
    COUNT(*) AS denied_claims,
    SUM(CASE WHEN appeal_filed = 'Y' THEN 1 ELSE 0 END) AS appeals_filed,
    ROUND(100.0 * SUM(CASE WHEN appeal_filed = 'Y' THEN 1 ELSE 0 END) / COUNT(*), 1) AS appeal_rate_pct,
    SUM(CASE WHEN appeal_outcome IN ('overturned', 'upheld') THEN 1 ELSE 0 END) AS decided_appeals,
    SUM(CASE WHEN appeal_outcome = 'overturned' THEN 1 ELSE 0 END) AS overturned,
    ROUND(100.0 * SUM(CASE WHEN appeal_outcome = 'overturned' THEN 1 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN appeal_outcome IN ('overturned', 'upheld') THEN 1 ELSE 0 END), 0), 1) AS overturn_rate_pct
FROM claims
WHERE claim_status = 'Denied'
GROUP BY payer_name
ORDER BY overturn_rate_pct DESC;
