# Power BI Model — Healthcare Denials Dashboard

`healthcare-denials-dashboard.pbix` · two tables: `FactClaims` (4,200 rows, from SQL Server)
and `_Measures` (measure container, its only column is hidden). Every measure below was checked
against the SQL output in `sql/results/`.

## Power Query — `FactClaims`

Navigates to `dbo.claims` rather than passing a native SQL string, so the query folds
and Power BI doesn't ask for native-query approval.

```m
let
    Source = Sql.Database(".\SQLEXPRESS", "Healthcare_Denials"),
    claims = Source{[Schema = "dbo", Item = "claims"]}[Data],
    #"Changed Types" = Table.TransformColumnTypes(claims, {
        {"claim_id", type text}, {"payer_name", type text}, {"cpt_code", type text},
        {"diagnosis_code", type text}, {"billed_amount", Currency.Type}, {"claim_status", type text},
        {"denial_reason", type text}, {"denial_date", type date}, {"appeal_filed", type text},
        {"appeal_outcome", type text}, {"days_in_ar", Int64.Type}, {"service_date", type date}
    }),
    #"Added IsDenied" = Table.AddColumn(#"Changed Types", "IsDenied", each if [claim_status] = "Denied" then 1 else 0, Int64.Type),
    #"Added Denial Code" = Table.AddColumn(#"Added IsDenied", "Denial Code", each if [denial_reason] = null then null else Text.BeforeDelimiter([denial_reason], " "), type text),
    #"Added Service Month" = Table.AddColumn(#"Added Denial Code", "Service Month", each Date.StartOfMonth([service_date]), type date)
in
    #"Added Service Month"
```

- `Denial Code` keeps just the CARC code (`CO-50`, `CO-96`…) for readable chart labels;
  the full description stays in `denial_reason`.
- `Service Month` drives the monthly trend line.

## Measures — `_Measures`

| Measure | DAX | Format | Value (all data) | SQL check |
|---|---|---|---|---|
| Total Claims | `COUNTROWS ( FactClaims )` | `#,0` | 4,200 | 00 |
| Denied Claims | `CALCULATE ( COUNTROWS ( FactClaims ), FactClaims[claim_status] = "Denied" )` | `#,0` | 1,198 | 00 |
| Total Billed Amount | `SUM ( FactClaims[billed_amount] )` | `$#,0` | $719,233 | 00 |
| Total Denied Amount | `CALCULATE ( SUM ( FactClaims[billed_amount] ), FactClaims[claim_status] = "Denied" )` | `$#,0` | $201,184 | 01 |
| **Denial Rate** | `DIVIDE ( [Denied Claims], [Total Claims], 0 )` | `0.0%` | 28.5% | 01 |
| Denied Dollar Rate | `DIVIDE ( [Total Denied Amount], [Total Billed Amount], 0 )` | `0.0%` | 28.0% | — |
| Decided Appeals | `CALCULATE ( COUNTROWS ( FactClaims ), FactClaims[appeal_outcome] IN { "overturned", "upheld" } )` | `#,0` | 557 | 04 |
| Overturned Appeals | `CALCULATE ( COUNTROWS ( FactClaims ), FactClaims[appeal_outcome] = "overturned" )` | `#,0` | 309 | 04 |
| **Overturn Rate** | `DIVIDE ( [Overturned Appeals], [Decided Appeals] )` | `0.0%` | 55.5% | 04 |
| Recovered Amount | `CALCULATE ( SUM ( FactClaims[billed_amount] ), FactClaims[appeal_outcome] = "overturned" )` | `$#,0` | $51,049 | — |
| Overturn Recovery Rate | `DIVIDE ( [Recovered Amount], [Total Denied Amount], 0 )` | `0.0%` | 25.4% | — |
| Average Days in AR | `AVERAGE ( FactClaims[days_in_ar] )` | `0.0` | 39.0 | 05 |
| Avg Days in AR (Denied) | `CALCULATE ( AVERAGE ( FactClaims[days_in_ar] ), FactClaims[claim_status] = "Denied" )` | `0.0` | 78.9 | 05 |
| **Revenue at Risk** | `CALCULATE ( SUM ( FactClaims[billed_amount] ), FactClaims[claim_status] = "Denied", FactClaims[appeal_outcome] IN { "upheld", "pending", "not appealed" } )` | `$#,0` | $150,135 | 06 |
| At-Risk Claims | same filters, `COUNTROWS ( FactClaims )` | `#,0` | 889 | 06 |

## Choices that differ from the original build spec

- **Column names follow the real data.** The spec used `claim_amount`, `denial_status`,
  `denial_reason_code`, `appeal_status` and `recovered_amount`; the CSV (and the six SQL scripts)
  use `billed_amount`, `claim_status`, `denial_reason`, `appeal_filed`, `appeal_outcome`.
- **Denial Rate is claim-based** (denied claims ÷ claims) so it matches the SQL and the README
  findings — Liberty 42.5%, overall 28.5%. The dollar-based version is kept as *Denied Dollar Rate*.
- **No recovered-amount column exists**, so *Recovered Amount* is the billed amount of claims
  overturned on appeal. Real remits would replace this with paid-after-appeal dollars.
- **Overturn Rate uses decided appeals only** (pending excluded), the same rule as `sql/04`.
- **Appeal outcomes are lowercase** in the data (`overturned`, `upheld`, `pending`, `not appealed`);
  DAX string comparison is case-insensitive, but the measures use the exact values anyway.

## Theme

`reports/denials-theme-dark.json` — dark slate background `#0F172A`, card surfaces `#1E293B`,
teal/amber/red palette. Import with **View → Themes → Browse for themes**.
