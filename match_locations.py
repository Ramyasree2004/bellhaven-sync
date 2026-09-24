import json
import re
from difflib import SequenceMatcher

# -----------------------------
# Load our two datasets
# -----------------------------

with open("website_locations.json", "r") as f:
    website_locations = json.load(f)

with open("all_crm_accounts.json", "r") as f:
    crm_data = json.load(f)

crm_accounts = crm_data


# -----------------------------
# Text cleaning
# -----------------------------

def normalize(text):
    if not text:
        return ""

    text = str(text).lower().strip()

    # Common address/name variations
    replacements = {
        " street": " st",
        " road": " rd",
        " avenue": " ave",
        " boulevard": " blvd",
        " drive": " dr",
        " lane": " ln",
        " center": " centre",
        " healthcare": " health care",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove punctuation
    text = re.sub(r"[^a-z0-9 ]", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


def similarity(a, b):
    return SequenceMatcher(
        None,
        normalize(a),
        normalize(b)
    ).ratio()


# -----------------------------
# Calculate match score
# -----------------------------

def calculate_score(website, crm):

    website_zip = normalize(website.get("zip"))
    crm_zip = normalize(crm.get("billing_zip"))

    website_city = normalize(website.get("city"))
    crm_city = normalize(crm.get("billing_city"))

    website_street = normalize(website.get("address"))
    crm_street = normalize(crm.get("billing_street"))

    website_name = normalize(website.get("name"))
    crm_name = normalize(crm.get("name"))

    zip_match = (
        website_zip != ""
        and website_zip == crm_zip
    )

    city_match = (
        website_city != ""
        and website_city == crm_city
    )

    street_similarity = similarity(
        website_street,
        crm_street
    )

    name_similarity = similarity(
        website_name,
        crm_name
    )

    # Strong signals: ZIP + street
    if zip_match and street_similarity >= 0.85:
        score = 0.98

    elif zip_match and street_similarity >= 0.65:
        score = 0.90

    elif city_match and street_similarity >= 0.85:
        score = 0.88

    else:
        score = (
            (0.35 if zip_match else 0)
            + (0.15 if city_match else 0)
            + (0.30 * street_similarity)
            + (0.20 * name_similarity)
        )

    evidence = {
        "zip_match": zip_match,
        "city_match": city_match,
        "street_similarity": round(street_similarity, 3),
        "name_similarity": round(name_similarity, 3),
    }

    return round(score, 3), evidence


# -----------------------------
# Match every website location
# -----------------------------

results = []

for website in website_locations:

    candidates = []

    for crm in crm_accounts:

        score, evidence = calculate_score(
            website,
            crm
        )

        candidates.append({
            "account_id": crm.get("account_id"),
            "crm_name": crm.get("name"),
            "crm_parent_id": crm.get("parent_id"),
            "crm_parent_name": crm.get("parent_name"),
            "crm_address": crm.get("billing_street"),
            "crm_city": crm.get("billing_city"),
            "crm_state": crm.get("billing_state"),
            "crm_zip": crm.get("billing_zip"),
            "status": crm.get("status"),
            "lifetime_revenue": crm.get("lifetime_revenue", 0),
            "outstanding_ar": crm.get("outstanding_ar", 0),
            "score": score,
            "evidence": evidence
        })

    candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    best = candidates[0]

    if best["score"] >= 0.90:
        classification = "CONFIDENT_MATCH"

    elif best["score"] >= 0.70:
        classification = "NEEDS_REVIEW"

    else:
        classification = "NO_CRM_ACCOUNT"

    results.append({
        "website": website,
        "classification": classification,
        "best_match": best,
        "top_candidates": candidates[:3]
    })


# -----------------------------
# Save results
# -----------------------------

with open("match_results.json", "w") as f:
    json.dump(
        results,
        f,
        indent=2
    )

print()
print("Matching complete!")
print()
print("Website locations:", len(website_locations))
print("CRM accounts:", len(crm_accounts))
print("Results:", len(results))
print()
print("Saved as: match_results.json")
print()

for result in results:
    website = result["website"]

    print(
        f"{result['classification']:18} | "
        f"{website['name']} | "
        f"{result['best_match']['crm_name']} | "
        f"score={result['best_match']['score']}"
    )
