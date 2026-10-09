-- 00_setup_database.sql -- run once before 01..06
-- Server: .\SQLEXPRESS | Creates database Healthcare_Denials and loads data/claims.csv into dbo.claims.
-- Edit the BULK INSERT path below if the repo lives somewhere else. The SQL Server service
-- account needs read access to that folder (C:\Users\Public works on a default install).

IF NOT EXISTS (SELECT 1 FROM sys.databases WHERE name = 'Healthcare_Denials')
    CREATE DATABASE Healthcare_Denials;
GO

USE Healthcare_Denials;
GO

DROP TABLE IF EXISTS dbo.claims;
CREATE TABLE dbo.claims (
    claim_id        VARCHAR(20)   NOT NULL PRIMARY KEY,
    payer_name      VARCHAR(60)   NOT NULL,
    cpt_code        VARCHAR(10)   NOT NULL,
    diagnosis_code  VARCHAR(10)   NULL,
    billed_amount   DECIMAL(10,2) NOT NULL,
    claim_status    VARCHAR(10)   NOT NULL,   -- 'Paid' / 'Denied'
    denial_reason   VARCHAR(90)   NULL,       -- CARC code + description, NULL when paid
    denial_date     DATE          NULL,
    appeal_filed    CHAR(1)       NOT NULL,   -- 'Y' / 'N'
    appeal_outcome  VARCHAR(20)   NULL,       -- overturned / upheld / pending / not appealed
    days_in_ar      INT           NOT NULL,
    service_date    DATE          NOT NULL
);
GO

BULK INSERT dbo.claims
FROM 'C:\Users\Public\healthcare-denials\claims.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDTERMINATOR = ',', ROWTERMINATOR = '0x0a', TABLOCK);
GO

-- Empty CSV fields arrive as '' for text columns; store them as NULL.
UPDATE dbo.claims SET denial_reason  = NULLIF(denial_reason, ''),
                      appeal_outcome = NULLIF(appeal_outcome, '');
GO

-- Sanity check: expect 4,200 claims, 1,198 denied (28.5%).
SELECT COUNT(*) AS total_claims,
       SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) AS denied_claims,
       CAST(100.0 * SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) / COUNT(*) AS DECIMAL(4,1)) AS denial_rate_pct
FROM dbo.claims;
