# Bellhaven CRM Reconciliation & Review Workflow

## Overview

This project reconciles Bellhaven Senior Living website locations against the provided CRM data.

The workflow was designed to safely identify matching CRM accounts, missing accounts, potential duplicates, stale Bellhaven accounts, and billing-sensitive account relationships while requiring human review before CRM changes.

## Data Sources

- Bellhaven Senior Living website
- Provided CRM REST API
- CRM API authentication through an environment variable
- Website location data and CRM account data stored locally as JSON for matching and review

## Workflow

### 1. Website Scraping

Scraped the Bellhaven website and extracted:

- Location name
- Street address
- City
- State
- ZIP code
- Care offerings

A total of **35 website locations** were identified and saved to:

`website_locations.json`

### 2. CRM Data Retrieval

Retrieved the available CRM accounts through the provided API.

The CRM dataset contained **121 accounts** and included fields such as:

- Account ID
- Account name
- Parent account
- Billing address
- Care type
- Status
- Lifetime revenue
- Outstanding AR
- CHOW current account
- Duplicate account reference

The retrieved data was saved locally for matching and verification.

### 3. Location Matching

Each website location was compared against CRM accounts using evidence including:

- Location name similarity
- Street/address similarity
- City
- State
- ZIP code
- Parent organization
- Care offering where relevant

The matching workflow classified locations into actions such as:

- Update existing CRM account
- Create new CRM account
- Review / potential duplicate
- No CRM account

The proposed matches and supporting evidence were displayed through the Streamlit review application.

### 4. Human Review Interface

A Streamlit application was created to provide a review layer before CRM write-back.

The interface displays:

- Website location
- Proposed CRM account
- Match evidence
- Address comparison
- Revenue and outstanding AR
- Proposed action
- Approval/rejection controls
- Review status and project progress

CRM changes are only performed after the corresponding review decision.

Review decisions are stored locally so that previously resolved items are not repeatedly proposed during subsequent runs.

### 5. Missing CRM Accounts

Four website locations did not have corresponding CRM accounts and were reviewed and approved for creation:

- Bellhaven of Batavia
- Bellhaven at Union Square
- Bellhaven of Carlisle
- Amberly Manor

These accounts were created through the CRM API after approval.

### 6. Duplicate Handling

Potential duplicate/same-location CRM records were reviewed individually.

Approved duplicate actions included:

- Bellhaven of Owosso
- Millstone Care of Sandusky
- Harborview Nursing & Rehab of Port Clinton

For approved duplicates:

- The surviving account was retained.
- The duplicate account was marked `Inactive`.
- `duplicate_of_account` was set to the surviving account ID.

A Monroe same-address cluster was also reviewed. The duplicate proposal was **rejected**, so no CRM change was made to those accounts.

No merge or delete operation was used.

### 7. Billing / CHOW Protection

A critical billing rule was implemented for accounts where:

`lifetime_revenue > 0 AND outstanding_ar > 0`

These accounts must not be directly re-parented because historical billing information needs to remain with the original account.

For the applicable Marietta account:

- Existing billing account was preserved.
- Lifetime revenue of **51,250** was preserved.
- Outstanding AR of **3,800** was preserved.
- A new account was created under the correct Bellhaven Senior Living parent.
- The original account's `chow_current_account` was updated to reference the new account.
- The new account was verified through the CRM API.

This preserves the historical billing record while establishing the correct current ownership.

### 8. Stale Bellhaven Accounts

Bellhaven-parent accounts that were not represented on the current website were reviewed.

Two $0 revenue / $0 AR accounts were confirmed as no longer represented on the website:

- Bellhaven Care Center of Alliance
- Bellhaven of Coldwater

After review and approval, both were changed to:

`status = Inactive`

Accounts with existing revenue and/or outstanding AR were not deactivated solely because they were not direct website matches.

### 9. Safe Reruns

The workflow stores review decisions separately from the source data.

This allows the process to be rerun without unnecessarily proposing the same already-decided actions again.

The design also separates:

- Data retrieval
- Matching
- Proposed actions
- Human approval
- CRM write-back
- Verification

This makes the workflow safer for repeated operational use.

## Final CRM Verification

After the approved changes were applied, the affected CRM records were queried again through the API to verify:

- Created accounts
- Account status
- Duplicate relationships
- `duplicate_of_account`
- `chow_current_account`
- Parent account
- Revenue
- Outstanding AR

The final state was verified against the required business rules.

## Project Files

| File | Purpose |
|---|---|
| `review_app.py` | Streamlit human review and CRM write-back application |
| `crm_client.py` | CRM API client and account operations |
| `match_locations.py` | Website-to-CRM matching workflow |
| `website_locations.json` | Scraped website locations |
| `all_crm_accounts.json` | Retrieved CRM account dataset |
| `match_results.json` | Website-to-CRM matching results |
| `review_decisions.json` | Approved/rejected website-location decisions |
| `duplicate_decisions.json` | Duplicate review decisions |
| `requirements.txt` | Python dependencies |
| `README.md` | Project documentation |

## AI Usage

AI assistance was used throughout development for:

- Designing the reconciliation workflow
- Writing and debugging Python code
- Developing the CRM API client
- Developing the matching logic
- Building the Streamlit review interface
- Troubleshooting API and application issues
- Reviewing business-rule implementation
- Preparing documentation and submission materials

AI assistance did not replace the approval step. CRM-changing actions were reviewed before execution and the resulting CRM records were verified through the API.

## Production Improvements / Next Steps

For production use, I would add:

1. Scheduled daily execution.
2. Stronger entity-resolution and fuzzy matching.
3. Automated unit and integration tests.
4. Persistent audit logging for every proposed and approved change.
5. Better exception handling and retry logic for API failures.
6. Monitoring and alerting for unexpected CRM changes.
7. Centralized configuration and secret management.
8. A production database instead of local JSON decision files.
9. Role-based access for CRM approvals.
10. Automated reconciliation reports showing new, changed, duplicate, and stale accounts.

## Final Result

A total of **35 Bellhaven website locations** were processed through the reconciliation workflow.

The final CRM state was updated only after review/approval and was subsequently verified through the CRM API.

Actual time spent: approximately **3.5 hours**.