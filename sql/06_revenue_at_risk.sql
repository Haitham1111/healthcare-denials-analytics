-- Business question: How much billed revenue is currently at risk, by payer?
-- Table: claims. "At risk" = denied AND not overturned on appeal
-- (upheld, still pending, or never appealed).

SELECT
    payer_name,
    COUNT(*) AS at_risk_claims,
    ROUND(SUM(billed_amount), 2) AS revenue_at_risk,
    ROUND(100.0 * SUM(billed_amount) / SUM(SUM(billed_amount)) OVER (), 1) AS pct_of_total_at_risk
FROM claims
WHERE claim_status = 'Denied'
  AND (appeal_outcome IN ('upheld', 'pending') OR appeal_filed = 'N')
GROUP BY payer_name
ORDER BY revenue_at_risk DESC;
