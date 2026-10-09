"""
Synthetic claim-level dataset generator for the healthcare-denials-analytics
portfolio project.

WHAT THIS IS: 100% synthetic data. Every payer name is fictional, every claim
is invented by this script with random.seed(42) for reproducibility. It is
modeled on real behavioral-health revenue-cycle workflows (claim submission ->
payer adjudication -> denial with CARC-style reason -> appeal -> resolution),
but no real patient, payer, provider, or employer data is used anywhere.

Run: python3 data/generate_synthetic_data.py
Output: data/claims.csv (~4,200 rows)
"""
import csv
import random
from datetime import date, timedelta

random.seed(42)

# ----------------------------------------------------------------------------
# Fictional payers. Names are invented; any resemblance to a real payer is
# coincidental. Each payer has a distinct adjudication "personality" so the
# data tells a realistic story.
# ----------------------------------------------------------------------------
PAYERS = {
    "Summit Behavioral Health Plan": {
        "share": 0.28, "deny_rate": 0.28,
        "appeal_rate": 0.62, "overturn_rate": 0.65,   # appeals usually win -> appeal everything
        "ar_paid": (12, 30), "ar_denied": (50, 95),
        "reasons": [("CO-50", 0.22), ("CO-96", 0.14), ("CO-97", 0.16),
                    ("CO-18", 0.10), ("CO-29", 0.10), ("CO-16", 0.12),
                    ("PR-27", 0.05), ("CO-109", 0.05), ("CO-197", 0.04), ("OA-23", 0.02)],
    },
    "Liberty Care PPO": {
        "share": 0.18, "deny_rate": 0.42,            # highest denier
        "appeal_rate": 0.58, "overturn_rate": 0.38,
        "ar_paid": (18, 40), "ar_denied": (65, 110),  # slowest to resolve
        "reasons": [("CO-50", 0.45), ("CO-96", 0.10), ("CO-97", 0.10),   # CO-50 heavy:
                    ("CO-18", 0.06), ("CO-29", 0.08), ("CO-16", 0.08),   # "not medically necessary"
                    ("PR-27", 0.04), ("CO-109", 0.04), ("CO-197", 0.03), ("OA-23", 0.02)],
    },
    "Apex Medicare Advantage": {
        "share": 0.16, "deny_rate": 0.18,            # low denier...
        "appeal_rate": 0.45, "overturn_rate": 0.25,  # ...but appeals rarely win
        "ar_paid": (14, 32), "ar_denied": (55, 100),
        "reasons": [("CO-50", 0.18), ("CO-96", 0.16), ("CO-97", 0.14),
                    ("CO-18", 0.10), ("CO-29", 0.12), ("CO-16", 0.12),
                    ("PR-27", 0.06), ("CO-109", 0.06), ("CO-197", 0.04), ("OA-23", 0.02)],
    },
    "Gateway Health Cooperative": {
        "share": 0.14, "deny_rate": 0.25,
        "appeal_rate": 0.55, "overturn_rate": 0.52,
        "ar_paid": (14, 34), "ar_denied": (55, 100),
        "reasons": [("CO-50", 0.20), ("CO-96", 0.14), ("CO-97", 0.14),
                    ("CO-18", 0.10), ("CO-29", 0.12), ("CO-16", 0.12),
                    ("PR-27", 0.05), ("CO-109", 0.06), ("CO-197", 0.05), ("OA-23", 0.02)],
    },
    "Pinnacle Commercial Plan": {
        "share": 0.14, "deny_rate": 0.38,            # second-highest denier
        "appeal_rate": 0.50, "overturn_rate": 0.45,
        "ar_paid": (16, 36), "ar_denied": (60, 105),
        "reasons": [("CO-50", 0.16), ("CO-96", 0.38), ("CO-97", 0.10),   # CO-96 heavy:
                    ("CO-18", 0.08), ("CO-29", 0.08), ("CO-16", 0.08),   # "non-covered charges"
                    ("PR-27", 0.04), ("CO-109", 0.04), ("CO-197", 0.02), ("OA-23", 0.02)],
    },
    "Harbor State Medicaid": {
        "share": 0.10, "deny_rate": 0.15,            # lowest denier, fastest
        "appeal_rate": 0.60, "overturn_rate": 0.58,
        "ar_paid": (10, 24), "ar_denied": (45, 85),
        "reasons": [("CO-50", 0.16), ("CO-96", 0.12), ("CO-97", 0.14),
                    ("CO-18", 0.10), ("CO-29", 0.14), ("CO-16", 0.14),
                    ("PR-27", 0.06), ("CO-109", 0.06), ("CO-197", 0.06), ("OA-23", 0.02)],
    },
}

REASON_TEXT = {
    "CO-50":  "CO-50 Non-covered service - deemed not medically necessary",
    "CO-96":  "CO-96 Non-covered charges",
    "CO-97":  "CO-97 Payment included in another service already adjudicated",
    "CO-18":  "CO-18 Duplicate claim/service",
    "CO-29":  "CO-29 Timely filing - claim submitted past deadline",
    "CO-16":  "CO-16 Claim lacks information needed for adjudication",
    "PR-27":  "PR-27 Expenses incurred after coverage terminated",
    "CO-109": "CO-109 Claim not covered by this payer/contractor",
    "CO-197": "CO-197 Precertification/authorization absent",
    "OA-23":  "OA-23 Impact of prior payer adjudication",
}

# CPT -> (low $, high $, description, volume weight). Behavioral-health mix.
CPTS = {
    "90791": (250, 350, "Psychiatric diagnostic evaluation", 0.14),
    "90792": (280, 380, "Psych eval with medical services", 0.06),
    "90832": (90, 130, "Psychotherapy 30 min", 0.10),
    "90834": (120, 180, "Psychotherapy 45 min", 0.30),
    "90837": (160, 220, "Psychotherapy 60 min", 0.16),
    "90853": (60, 90, "Group psychotherapy", 0.08),
    "96127": (25, 40, "Brief emotional/behavioral assessment", 0.10),
    "96130": (180, 260, "Psychological testing evaluation", 0.06),
}

DIAGNOSES = ["F32.1", "F41.1", "F33.1", "F90.0", "F43.12", "F31.30"]

N_CLAIMS = 4200
START = date(2025, 1, 6)   # first service date


def weighted_choice(pairs):
    r = random.random()
    cum = 0.0
    for key, w in pairs:
        cum += w
        if r < cum:
            return key
    return pairs[-1][0]


def main():
    payer_names = list(PAYERS.keys())
    payer_weights = [(n, PAYERS[n]["share"]) for n in payer_names]
    cpt_weights = [(c, CPTS[c][3]) for c in CPTS]

    rows = []
    for i in range(1, N_CLAIMS + 1):
        payer = weighted_choice(payer_weights)
        P = PAYERS[payer]
        cpt = weighted_choice(cpt_weights)
        lo, hi, _desc, _w = CPTS[cpt]
        billed = round(random.uniform(lo, hi), 2)
        dx = random.choice(DIAGNOSES)
        service_date = START + timedelta(days=random.randint(0, 250))

        # Denial probability: payer base + CPT-specific pressure points.
        deny_p = P["deny_rate"]
        if payer == "Liberty Care PPO" and cpt == "90837":
            deny_p += 0.16   # Liberty targets 60-min sessions with CO-50
        if payer == "Pinnacle Commercial Plan" and cpt in ("96127", "96130"):
            deny_p += 0.18   # Pinnacle barely covers testing (CO-96)
        denied = random.random() < deny_p

        if not denied:
            rows.append([f"CLM-2025-{i:06d}", payer, cpt, dx, billed, "Paid",
                         "", "", "N", "", random.randint(*P["ar_paid"]),
                         service_date.isoformat()])
            continue

        # Denied: pick a CARC-style reason (CPT-conditional overrides).
        if payer == "Liberty Care PPO" and cpt == "90837":
            code = "CO-50"
        elif payer == "Pinnacle Commercial Plan" and cpt in ("96127", "96130"):
            code = "CO-96"
        else:
            code = weighted_choice(P["reasons"])
        denial_date = service_date + timedelta(days=random.randint(12, 30))

        appealed = random.random() < P["appeal_rate"]
        if appealed:
            r = random.random()
            if r < 0.15:
                outcome = "pending"
            elif r < 0.15 + P["overturn_rate"]:
                outcome = "overturned"
            else:
                outcome = "upheld"
            appeal_filed = "Y"
        else:
            outcome = "not appealed"
            appeal_filed = "N"

        rows.append([f"CLM-2025-{i:06d}", payer, cpt, dx, billed, "Denied",
                     REASON_TEXT[code], denial_date.isoformat(), appeal_filed,
                     outcome, random.randint(*P["ar_denied"]),
                     service_date.isoformat()])

    header = ["claim_id", "payer_name", "cpt_code", "diagnosis_code",
              "billed_amount", "claim_status", "denial_reason", "denial_date",
              "appeal_filed", "appeal_outcome", "days_in_ar", "service_date"]
    with open("data/claims.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

    denied = sum(1 for r in rows if r[5] == "Denied")
    print(f"Wrote data/claims.csv: {len(rows)} claims, {denied} denied "
          f"({100.0 * denied / len(rows):.1f}% denial rate)")


if __name__ == "__main__":
    main()
