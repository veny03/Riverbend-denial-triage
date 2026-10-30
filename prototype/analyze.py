"""
Analyze the claim lines like a biller: headline rates, denials by reason and payer,
and a hunt for the four planted root causes.

This script is for understanding the clinic problem. It is NOT part of the running
system. Run from the data/ folder:  python ../prototype/analyze.py
"""
import pandas as pd

# IMPORTANT: read codes as text. CPT codes are labels, not numbers.
df = pd.read_csv("riverbend_claim_lines.csv",
                 dtype={"cpt": str, "modifier": str},
                 parse_dates=["date_of_service", "submitted_date", "denial_date"])
df["modifier"] = df.modifier.fillna("")

decided = df[df.status != "Pending"]
denied = df[df.status == "Denied"]

# One row per claim, for claim-level rates
claims = decided.groupby("claim_id").agg(
    provider=("provider", "first"), payer=("payer", "first"),
    denied=("status", lambda s: (s == "Denied").any()),
    co16=("carc_code", lambda s: (s == "CO-16").any()),
    co27=("carc_code", lambda s: (s == "CO-27").any()))

print("=== HEADLINE NUMBERS ===")
print("Claims:", df.claim_id.nunique(), "| Lines:", len(df),
      "| Pending lines:", (df.status == "Pending").sum())
print("Line denial rate:        ", round(len(denied) / len(decided) * 100, 1), "%")
print("Claim denial rate:       ", round(claims.denied.mean() * 100, 1), "%")
print("Clean claim rate (proxy):", round((1 - claims.denied.mean()) * 100, 1), "%")
print("Dollar denial rate:      ", round(denied.allowed_amount.sum() / decided.allowed_amount.sum() * 100, 1), "%")
print("Allowed $ denied:        ", round(denied.allowed_amount.sum(), 2))

print("\n=== DENIALS BY REASON (ranked by dollars) ===")
print(denied.groupby(["carc_code", "denial_reason"])
      .agg(lines=("claim_id", "size"), claims=("claim_id", "nunique"),
           dollars=("allowed_amount", "sum"))
      .sort_values("dollars", ascending=False).round(2))

print("\n=== LINE DENIAL RATE BY PAYER (%) ===")
print((decided.assign(d=decided.status.eq("Denied")).groupby("payer").d.mean() * 100).round(1).sort_values(ascending=False))

print("\n=== PATTERN HUNT ===")
mri = decided[(decided.cpt == "72148") & decided.payer.isin(["UnitedHealthcare", "Aetna", "Cigna", "BlueCross"])]
print("\n1) MRI prior-auth denial rate by payer (%):")
print((mri.assign(x=mri.carc_code.eq("CO-197")).groupby("payer").x.mean() * 100).round(1))

print("\n2) 'Missing information' claim rate by provider (%):")
print((claims.groupby("provider").co16.mean() * 100).round(1))

print("\n3) 'Coverage terminated' claim rate by payer (%):")
print((claims.groupby("payer").co27.mean() * 100).round(1))

inj = df[df.cpt == "20610"].claim_id
em = decided[(decided.cpt == "99213") & decided.claim_id.isin(inj)]
print("\n4) Injection visits missing modifier 25, by provider (%):")
print((em.assign(missing=em.modifier.eq("")).groupby("provider").missing.mean() * 100).round(1))
