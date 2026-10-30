"""
Generate synthetic claim-line data for the fictional Riverbend Family Clinic.

Every row is fake. The data is built from clinically coherent visit scenarios
(a diagnosis paired with the services that plausibly go with it) and has four
planted root causes for the dashboard to find:
  1. UnitedHealthcare denies many MRIs for missing prior authorization.
  2. Dr. Brooks has a high rate of "missing information" denials.
  3. Medicaid has many "coverage terminated" denials (eligibility not re-checked).
  4. Dr. Patel often forgets modifier 25 on injection visits.

Run from the data/ folder:  python ../prototype/generate_claims.py
Output: riverbend_claim_lines.csv
"""
import random
import pandas as pd
from datetime import date, timedelta

random.seed(7)
today = date.today()

providers = {"Dr. Adams": 18, "Dr. Okafor": 18, "Dr. Patel": 18,
             "Dr. Nguyen": 16, "Dr. Silva": 15, "Dr. Brooks": 15}

# payer: (share of patients, fraction of the charge the payer allows, filing limit in days)
# Filing limits are ASSUMED for this demo; real ones come from each payer contract.
payers = {"UnitedHealthcare": (24, 0.80, 90), "Aetna": (14, 0.82, 180),
          "Cigna": (12, 0.78, 90), "BlueCross": (20, 0.85, 180),
          "Medicare": (20, 0.60, 365), "Medicaid": (10, 0.50, 365)}
commercial = ["UnitedHealthcare", "Aetna", "Cigna", "BlueCross"]

# The clinic's chargemaster (fixed price list)
charges = {"99213": 150, "99214": 220, "99396": 260, "93000": 50, "85025": 30,
           "80053": 40, "80048": 35, "83036": 35, "80061": 45, "36415": 15,
           "71046": 120, "72100": 110, "72148": 900, "20610": 180, "87880": 30}

# (scenario, frequency weight, diagnosis, services)
scenarios = [
    ("Diabetes follow-up",     14, "E11.9",  ["99214", "83036", "36415"]),
    ("Hypertension follow-up", 16, "I10",    ["99213", "80048", "36415"]),
    ("Hypertension + ECG",      6, "I10",    ["99214", "93000", "80048", "36415"]),
    ("Cholesterol check",       8, "E78.5",  ["99213", "80061", "36415"]),
    ("Sore throat",             8, "J02.9",  ["99213", "87880"]),
    ("Cold / URI",              8, "J06.9",  ["99213"]),
    ("Chest pain workup",       6, "R07.9",  ["99214", "93000", "71046"]),
    ("Back pain visit",         8, "M54.50", ["99213", "72100"]),
    ("Back pain MRI",           4, "M54.50", ["99214", "72148"]),
    ("Knee injection",          8, "M17.11", ["99213", "20610"]),
    ("Annual physical",        10, "Z00.00", ["99396", "80061", "80053", "36415"]),
    ("Anemia workup",           4, "D64.9",  ["99213", "85025", "36415"]),
]

# Each patient keeps the same insurer across visits
patients = {f"PT{1000 + i}": random.choices(list(payers), weights=[p[0] for p in payers.values()])[0]
            for i in range(450)}

rows = []
for n in range(1, 1201):
    claim_id = f"CLM{n:05d}"
    patient = random.choice(list(patients))
    payer = patients[patient]
    _, allow_pct, filing_limit = payers[payer]
    provider = random.choices(list(providers), weights=list(providers.values()))[0]
    scen = random.choices(scenarios, weights=[s[1] for s in scenarios])[0]
    dx, cpts = scen[2], scen[3]

    # Dates: most claims go out within 10 days, a few are submitted very late
    dos = today - timedelta(days=random.randint(10, 270))
    lag = random.randint(1, 10) if random.random() > 0.04 else random.randint(60, 150)
    submitted = dos + timedelta(days=lag)
    if submitted > today:
        lag = random.randint(1, 5)
        submitted = dos + timedelta(days=lag)
    decision = submitted + timedelta(days=random.randint(14, 35))   # payer adjudication
    pending = decision > today

    # Claim-level problems hit every line on the claim
    claim_level = None
    if lag > filing_limit:
        claim_level = ("CO-29", "Timely filing expired")
    elif random.random() < (0.13 if payer == "Medicaid" else 0.015):
        claim_level = ("CO-27", "Coverage terminated")
    elif random.random() < (0.12 if provider == "Dr. Brooks" else 0.025):
        claim_level = ("CO-16", "Claim lacks information")
    elif random.random() < 0.015:
        claim_level = ("CO-18", "Duplicate claim")

    for line_no, cpt in enumerate(cpts, 1):
        modifier, icd, denial = "", dx, claim_level

        # A visit billed with a procedure the same day needs modifier 25
        if cpt == "99213" and "20610" in cpts:
            if random.random() < (0.35 if provider == "Dr. Patel" else 0.05):
                denial = denial or ("CO-4", "Modifier missing or inconsistent")
            else:
                modifier = "25"

        # Line-level problems
        if denial is None:
            if (cpt == "72148" and payer in commercial
                    and random.random() < (0.55 if payer == "UnitedHealthcare" else 0.12)):
                denial = ("CO-197", "Prior authorization missing")
            elif cpt in ("72148", "93000", "71046") and random.random() < (0.10 if cpt == "72148" else 0.04):
                denial = ("CO-50", "Not medically necessary")
            elif random.random() < 0.01:
                denial = ("CO-11", "Diagnosis inconsistent with procedure")
                icd = random.choice([d for d in ["J06.9", "D64.9", "Z00.00"] if d != dx])

        billed = charges[cpt]
        allowed = round(billed * allow_pct, 2)
        code = reason = ""
        denial_date = None
        if pending:
            status, paid, pt_resp = "Pending", 0, 0
        elif denial:
            status, paid, pt_resp = "Denied", 0, 0
            code, reason = denial
            denial_date = decision
        else:
            status = "Paid"
            if payer == "Medicaid":
                pt_resp = 0
            elif payer == "Medicare":
                pt_resp = round(allowed * 0.20, 2)
            else:
                pt_resp = round(allowed * random.choice([0, 0, 0.1, 0.2]), 2)
            paid = round(allowed - pt_resp, 2)

        rows.append({"claim_id": claim_id, "line_no": line_no, "patient_id": patient,
                     "provider": provider, "payer": payer, "cpt": cpt, "modifier": modifier,
                     "icd10": icd, "billed_amount": billed, "allowed_amount": allowed,
                     "paid_amount": paid, "patient_resp": pt_resp,
                     "date_of_service": dos, "submitted_date": submitted,
                     "status": status, "carc_code": code, "denial_reason": reason,
                     "denial_date": denial_date})

df = pd.DataFrame(rows)
df.to_csv("riverbend_claim_lines.csv", index=False)

# Sanity checks, worth doing on any dataset
print("Claims:", df.claim_id.nunique(), "| Service lines:", len(df))
print(df.status.value_counts())
print("Denial dates in the future:", (pd.to_datetime(df.denial_date) > pd.Timestamp(today)).sum())
