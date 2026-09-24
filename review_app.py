import json
from pathlib import Path

import streamlit as st

from crm_client import create_account, update_account


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="Bellhaven CRM Review",
    page_icon="🏥",
    layout="wide",
)


# ============================================================
# FILE PATHS
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent

MATCH_RESULTS_FILE = (
    BASE_DIR / "match_results.json"
)

DECISIONS_FILE = (
    BASE_DIR / "review_decisions.json"
)


# ============================================================
# DARK THEME
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #0b1118;
    }

    [data-testid="stSidebar"] {
        background-color: #0a1017;
    }

    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #e8f0f7 !important;
    }

    .stMarkdown,
    .stText,
    p,
    label {
        color: #d5e0e9;
    }

    [data-testid="stMetric"] {
        background-color: #111b24;
        border: 1px solid #243441;
        border-radius: 10px;
        padding: 15px;
    }

    [data-testid="stMetricLabel"] {
        color: #8fa3b5 !important;
    }

    [data-testid="stMetricValue"] {
        color: #e7f0f6 !important;
    }

    div[data-testid="stExpander"] {
        background-color: #101820;
        border: 1px solid #253541;
        border-radius: 10px;
    }

    .stButton > button {
        border-radius: 8px;
        min-height: 42px;
        font-weight: 600;
    }

    hr {
        border-color: #24323e;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# JSON HELPERS
# ============================================================

def load_json(
    file_path,
    default_value,
):
    """
    Load a JSON file safely.
    """

    if not file_path.exists():

        return default_value


    try:

        with open(
            file_path,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(
                file
            )


    except Exception as error:

        st.error(
            f"Could not read "
            f"{file_path.name}: "
            f"{error}"
        )

        return default_value


def save_json(
    file_path,
    data,
):
    """
    Save JSON safely.
    """

    try:

        with open(
            file_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )


    except Exception as error:

        st.error(
            f"Could not save "
            f"{file_path.name}: "
            f"{error}"
        )


# ============================================================
# LOAD MATCH RESULTS
# ============================================================

results = load_json(
    MATCH_RESULTS_FILE,
    [],
)


if not results:

    st.error(
        "match_results.json was not found "
        "or contains no results."
    )

    st.stop()


# ============================================================
# LOAD DECISIONS
# ============================================================

if "decisions" not in st.session_state:

    st.session_state.decisions = load_json(
        DECISIONS_FILE,
        {},
    )


decisions = (
    st.session_state.decisions
)


# ============================================================
# BASIC HELPERS
# ============================================================

def get_website(item):

    return item.get(
        "website",
        {},
    ) or {}


def get_match(item):

    return item.get(
        "best_match",
        {},
    ) or {}


def get_classification(item):

    return str(
        item.get(
            "classification",
            "UNKNOWN",
        )
    ).upper()


def get_score(item):

    match = get_match(
        item
    )

    try:

        return float(
            match.get(
                "score",
                0,
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        return 0


def get_revenue(item):

    match = get_match(
        item
    )

    try:

        return float(
            match.get(
                "lifetime_revenue",
                0,
            )
            or 0
        )

    except (
        TypeError,
        ValueError,
    ):

        return 0


def get_ar(item):

    match = get_match(
        item
    )

    try:

        return float(
            match.get(
                "outstanding_ar",
                0,
            )
            or 0
        )

    except (
        TypeError,
        ValueError,
    ):

        return 0


def extract_account_id(response):

    if not isinstance(
        response,
        dict,
    ):
        return None

    if response.get("id"):
        return response.get("id")

    if response.get("account_id"):
        return response.get("account_id")

    data = response.get(
        "data",
        {},
    )

    if isinstance(
        data,
        dict,
    ):

        if data.get("id"):
            return data.get("id")

        if data.get("account_id"):
            return data.get("account_id")

    account = response.get(
        "account",
        {},
    )

    if isinstance(
        account,
        dict,
    ):

        if account.get("id"):
            return account.get("id")

        if account.get("account_id"):
            return account.get("account_id")

    return None


# ============================================================
# DECISION KEY
# ============================================================

def make_decision_key(
    item,
    index,
):
    """
    Create a stable review-decision key.
    """

    website = get_website(
        item
    )

    match = get_match(
        item
    )

    account_id = match.get(
        "account_id"
    )

    website_url = website.get(
        "url"
    )


    if (
        account_id
        and website_url
    ):

        return (
            f"{account_id}|"
            f"{website_url}"
        )


    website_name = website.get(
        "name",
        f"location_{index}",
    )


    return (
        f"{website_name}|"
        f"{index}"
    )


# ============================================================
# FIELD DIFFERENCES
# ============================================================

def get_field_changes(item):
    """
    Compare website information against CRM information.

    NO_CRM_ACCOUNT is intentionally excluded.
    """

    classification = (
        get_classification(
            item
        )
    )


    if (
        classification
        == "NO_CRM_ACCOUNT"
    ):

        return []


    website = get_website(
        item
    )

    match = get_match(
        item
    )


    if not match:

        return []


    changes = []


    # --------------------------------------------------------
    # STREET
    # --------------------------------------------------------

    website_address = str(
        website.get(
            "address",
            "",
        )
        or ""
    ).strip()


    crm_address = str(
        match.get(
            "crm_address",
            "",
        )
        or ""
    ).strip()


    if (
        website_address
        and website_address
        != crm_address
    ):

        changes.append(
            (
                "billing_street",
                crm_address or "—",
                website_address,
            )
        )


    # --------------------------------------------------------
    # CITY
    # --------------------------------------------------------

    website_city = str(
        website.get(
            "city",
            "",
        )
        or ""
    ).strip()


    crm_city = str(
        match.get(
            "crm_city",
            "",
        )
        or ""
    ).strip()


    if (
        website_city
        and website_city
        != crm_city
    ):

        changes.append(
            (
                "billing_city",
                crm_city or "—",
                website_city,
            )
        )


    # --------------------------------------------------------
    # STATE
    # --------------------------------------------------------

    website_state = str(
        website.get(
            "state",
            "",
        )
        or ""
    ).strip()


    crm_state = str(
        match.get(
            "crm_state",
            "",
        )
        or ""
    ).strip()


    if (
        website_state
        and website_state
        != crm_state
    ):

        changes.append(
            (
                "billing_state",
                crm_state or "—",
                website_state,
            )
        )


    # --------------------------------------------------------
    # ZIP
    # --------------------------------------------------------

    website_zip = str(
        website.get(
            "zip",
            "",
        )
        or ""
    ).strip()


    crm_zip = str(
        match.get(
            "crm_zip",
            "",
        )
        or ""
    ).strip()


    if (
        website_zip
        and website_zip
        != crm_zip
    ):

        changes.append(
            (
                "billing_zip",
                crm_zip or "—",
                website_zip,
            )
        )


    return changes


# ============================================================
# DETERMINE PROPOSED ACTION
# ============================================================

def determine_action(item):

    classification = (
        get_classification(
            item
        )
    )

    match = get_match(
        item
    )


    # --------------------------------------------------------
    # NO CRM ACCOUNT
    # --------------------------------------------------------

    if (
        classification
        == "NO_CRM_ACCOUNT"
    ):

        return (
            "CREATE NEW ACCOUNT",
            (
                "No existing CRM account was "
                "identified for this website "
                "location. A new CRM account "
                "should be created after "
                "review and approval."
            ),
        )


    # --------------------------------------------------------
    # NO MATCH OBJECT
    # --------------------------------------------------------

    if not match:

        return (
            "NO CRM ACCOUNT",
            (
                "No matching CRM account "
                "was found."
            ),
        )


    # --------------------------------------------------------
    # BILLING RULE
    # --------------------------------------------------------

    revenue = get_revenue(
        item
    )

    ar = get_ar(
        item
    )


    if (
        revenue > 0
        and ar > 0
    ):

        return (
            "CREATE NEW ACCOUNT + CHOW",
            (
                "The existing account has "
                "lifetime revenue and "
                "outstanding AR. The existing "
                "account must be preserved. "
                "A new account should be "
                "created under the correct "
                "parent and "
                "chow_current_account should "
                "point to it."
            ),
        )


    # --------------------------------------------------------
    # NORMAL UPDATE
    # --------------------------------------------------------

    return (
        "UPDATE EXISTING ACCOUNT",
        (
            "The existing account has no "
            "lifetime revenue and no "
            "outstanding AR. A direct "
            "correction can be considered "
            "after approval."
        ),
    )


# ============================================================
# BUILD CRM UPDATE
# ============================================================

def build_crm_update(item):
    """
    Build the PATCH payload.

    This function prepares the update only.
    The actual API request happens only after
    the user clicks Approve.
    """

    classification = (
        get_classification(
            item
        )
    )


    # --------------------------------------------------------
    # NO CRM ACCOUNT
    # --------------------------------------------------------

    if (
        classification
        == "NO_CRM_ACCOUNT"
    ):

        return None


    match = get_match(
        item
    )


    if not match:

        return None


    website = get_website(
        item
    )


    updates = {}


    # --------------------------------------------------------
    # BILLING STREET
    # --------------------------------------------------------

    website_address = str(
        website.get(
            "address",
            "",
        )
        or ""
    ).strip()


    crm_address = str(
        match.get(
            "crm_address",
            "",
        )
        or ""
    ).strip()


    if (
        website_address
        and website_address
        != crm_address
    ):

        updates[
            "billing_street"
        ] = website_address


    # --------------------------------------------------------
    # BILLING CITY
    # --------------------------------------------------------

    website_city = str(
        website.get(
            "city",
            "",
        )
        or ""
    ).strip()


    crm_city = str(
        match.get(
            "crm_city",
            "",
        )
        or ""
    ).strip()


    if (
        website_city
        and website_city
        != crm_city
    ):

        updates[
            "billing_city"
        ] = website_city


    # --------------------------------------------------------
    # BILLING STATE
    # --------------------------------------------------------

    website_state = str(
        website.get(
            "state",
            "",
        )
        or ""
    ).strip()


    crm_state = str(
        match.get(
            "crm_state",
            "",
        )
        or ""
    ).strip()


    if (
        website_state
        and website_state
        != crm_state
    ):

        updates[
            "billing_state"
        ] = website_state


    # --------------------------------------------------------
    # BILLING ZIP
    # --------------------------------------------------------

    website_zip = str(
        website.get(
            "zip",
            "",
        )
        or ""
    ).strip()


    crm_zip = str(
        match.get(
            "crm_zip",
            "",
        )
        or ""
    ).strip()


    if (
        website_zip
        and website_zip
        != crm_zip
    ):

        updates[
            "billing_zip"
        ] = website_zip


    return updates


# ============================================================
# HEADER
# ============================================================

st.title(
    "🏥 Bellhaven CRM Review"
)

st.caption(
    "Review website-to-CRM matches before making CRM changes."
)


st.warning(
    "Approved existing-account changes can update the "
    "CRM. Please verify the proposed field changes "
    "before clicking Approve."
)


# ============================================================
# SUMMARY
# ============================================================

total_locations = len(
    results
)


approved = sum(
    1
    for value in decisions.values()
    if value == "approved"
)


rejected = sum(
    1
    for value in decisions.values()
    if value == "rejected"
)


pending = (
    total_locations
    - approved
    - rejected
)


col1, col2, col3, col4 = (
    st.columns(4)
)


with col1:

    st.metric(
        "Total Locations",
        total_locations,
    )


with col2:

    st.metric(
        "Approved",
        approved,
    )


with col3:

    st.metric(
        "Rejected",
        rejected,
    )


with col4:

    st.metric(
        "Pending",
        pending,
    )


st.divider()


# ============================================================
# FILTER
# ============================================================

filter_value = st.selectbox(
    "Filter locations",
    [
        "All",
        "Pending",
        "Approved",
        "Rejected",
        "Confident Matches",
        "Needs Review",
        "No CRM Account",
    ],
)


# ============================================================
# LOCATION LOOP
# ============================================================

for index, item in enumerate(
    results
):

    website = get_website(
        item
    )

    match = get_match(
        item
    )

    classification = (
        get_classification(
            item
        )
    )

    score = get_score(
        item
    )

    decision_key = (
        make_decision_key(
            item,
            index,
        )
    )

    current_decision = (
        decisions.get(
            decision_key
        )
    )


    # ========================================================
    # FILTER
    # ========================================================

    show = True


    if (
        filter_value
        == "Pending"
    ):

        show = (
            current_decision
            not in [
                "approved",
                "rejected",
            ]
        )


    elif (
        filter_value
        == "Approved"
    ):

        show = (
            current_decision
            == "approved"
        )


    elif (
        filter_value
        == "Rejected"
    ):

        show = (
            current_decision
            == "rejected"
        )


    elif (
        filter_value
        == "Confident Matches"
    ):

        show = (
            classification
            == "CONFIDENT_MATCH"
        )


    elif (
        filter_value
        == "Needs Review"
    ):

        show = (
            classification
            == "NEEDS_REVIEW"
        )


    elif (
        filter_value
        == "No CRM Account"
    ):

        show = (
            classification
            == "NO_CRM_ACCOUNT"
        )


    if not show:

        continue


    # ========================================================
    # LOCATION TITLE
    # ========================================================

    location_name = website.get(
        "name",
        f"Location {index + 1}",
    )


    st.header(
        location_name
    )


    # ========================================================
    # STATUS
    # ========================================================

    status_col1, status_col2 = (
        st.columns(2)
    )


    with status_col1:

        if (
            classification
            == "CONFIDENT_MATCH"
        ):

            st.success(
                "CONFIDENT MATCH"
            )

        elif (
            classification
            == "NEEDS_REVIEW"
        ):

            st.warning(
                "NEEDS REVIEW"
            )

        elif (
            classification
            == "NO_CRM_ACCOUNT"
        ):

            st.error(
                "NO CRM ACCOUNT"
            )

        else:

            st.info(
                classification
            )


    with status_col2:

        if (
            current_decision
            == "approved"
        ):

            st.success(
                "✓ APPROVED"
            )

        elif (
            current_decision
            == "rejected"
        ):

            st.warning(
                "✕ REJECTED"
            )

        else:

            st.info(
                "PENDING REVIEW"
            )


    # ========================================================
    # WEBSITE URL
    # ========================================================

    if website.get(
        "url"
    ):

        st.caption(
            website["url"]
        )


    # ========================================================
    # SCORE + ACTION
    # ========================================================

    score_col, action_col = (
        st.columns(2)
    )


    with score_col:

        st.metric(
            "Match Score",
            f"{score * 100:.0f}%",
        )


    with action_col:

        (
            action_name,
            action_description,
        ) = determine_action(
            item
        )


        st.subheader(
            "Proposed Action"
        )


        st.write(
            action_name
        )


        st.caption(
            action_description
        )


    # ========================================================
    # WEBSITE / CRM
    # ========================================================

    website_col, crm_col = (
        st.columns(2)
    )


    # ========================================================
    # WEBSITE SOURCE OF TRUTH
    # ========================================================

    with website_col:

        st.subheader(
            "Website Source of Truth"
        )


        st.write(
            f"**Name:** "
            f"{website.get('name', '—')}"
        )


        st.write(
            f"**Address:** "
            f"{website.get('address', '—')}"
        )


        st.write(
            f"**City:** "
            f"{website.get('city', '—')}"
        )


        st.write(
            f"**State:** "
            f"{website.get('state', '—')}"
        )


        st.write(
            f"**ZIP:** "
            f"{website.get('zip', '—')}"
        )


        care_offerings = (
            website.get(
                "care_offerings",
                [],
            )
        )


        if isinstance(
            care_offerings,
            list,
        ):

            care_text = ", ".join(
                care_offerings
            )

        else:

            care_text = str(
                care_offerings
            )


        st.write(
            f"**Care Offerings:** "
            f"{care_text or '—'}"
        )


    # ========================================================
    # CRM MATCH
    # ========================================================

    with crm_col:

        st.subheader(
            "CRM Match"
        )


        # ----------------------------------------------------
        # NO CRM ACCOUNT
        # ----------------------------------------------------

        if (
            classification
            == "NO_CRM_ACCOUNT"
        ):

            st.warning(
                "No existing CRM account was found."
            )


            st.caption(
                "The matching algorithm may have "
                "identified nearby candidates, but "
                "those candidates are not treated "
                "as an actual CRM match."
            )


        # ----------------------------------------------------
        # EXISTING CRM MATCH
        # ----------------------------------------------------

        elif match:

            st.write(
                f"**Account ID:** "
                f"{match.get('account_id', '—')}"
            )


            st.write(
                f"**CRM Name:** "
                f"{match.get('crm_name', '—')}"
            )


            st.write(
                f"**Address:** "
                f"{match.get('crm_address', '—')}"
            )


            st.write(
                f"**City:** "
                f"{match.get('crm_city', '—')}"
            )


            st.write(
                f"**State:** "
                f"{match.get('crm_state', '—')}"
            )


            st.write(
                f"**ZIP:** "
                f"{match.get('crm_zip', '—')}"
            )


            st.write(
                f"**Parent:** "
                f"{match.get('crm_parent_name', '—')}"
            )


            st.write(
                f"**Lifetime Revenue:** "
                f"${get_revenue(item):,.2f}"
            )


            st.write(
                f"**Outstanding AR:** "
                f"${get_ar(item):,.2f}"
            )


        else:

            st.warning(
                "No CRM account found."
            )


    # ========================================================
    # PROPOSED FIELD CHANGES
    # ========================================================

    st.subheader(
        "Proposed CRM Field Changes"
    )


    if (
        classification
        == "NO_CRM_ACCOUNT"
    ):

        st.info(
            "No existing CRM account to update. "
            "This location requires a new-account workflow."
        )


    else:

        field_changes = (
            get_field_changes(
                item
            )
        )


        if field_changes:

            for (
                field,
                current_value,
                proposed_value,
            ) in field_changes:

                (
                    change_col1,
                    change_col2,
                    change_col3,
                ) = st.columns(
                    [1.5, 0.3, 2.5]
                )


                with change_col1:

                    st.write(
                        f"**{field}**"
                    )


                with change_col2:

                    st.write(
                        "→"
                    )


                with change_col3:

                    st.write(
                        f"`{current_value}` "
                        f"→ "
                        f"**{proposed_value}**"
                    )


        else:

            st.success(
                "No address field differences detected."
            )


    # ========================================================
    # BILLING RULE
    # ========================================================

    if (
        classification
        != "NO_CRM_ACCOUNT"
        and match
    ):

        revenue = get_revenue(
            item
        )

        ar = get_ar(
            item
        )


        if (
            revenue > 0
            and ar > 0
        ):

            st.error(
                "Billing preservation rule: lifetime "
                "revenue and outstanding AR are both "
                "greater than zero. The existing account "
                "must be preserved. Do NOT directly "
                "re-parent this account."
            )


        else:

            st.info(
                "Billing check: lifetime revenue "
                "and outstanding AR are both zero."
            )


    # ========================================================
    # MATCHING EVIDENCE
    # ========================================================

    with st.expander(
        "View matching evidence"
    ):

        if (
            match
            and classification
            != "NO_CRM_ACCOUNT"
        ):

            evidence = match.get(
                "evidence",
                {},
            )


            if evidence:

                for (
                    field,
                    value,
                ) in evidence.items():

                    readable_name = (
                        field
                        .replace(
                            "_",
                            " ",
                        )
                        .title()
                    )


                    st.write(
                        f"**{readable_name}:** "
                        f"{value}"
                    )


            else:

                st.write(
                    "No detailed evidence available."
                )


        else:

            st.write(
                "No confirmed CRM match exists. "
                "Any low-confidence candidate was "
                "not treated as an existing account."
            )


    # ========================================================
    # PREPARED CRM PAYLOAD
    # ========================================================

    if (
        classification
        != "NO_CRM_ACCOUNT"
    ):

        prepared_updates = (
            build_crm_update(
                item
            )
        )


        with st.expander(
            "View prepared CRM update payload"
        ):

            if prepared_updates:

                st.json(
                    {
                        "account_id": match.get(
                            "account_id"
                        ),
                        "updates": prepared_updates,
                    }
                )

            else:

                st.write(
                    "No CRM update payload prepared."
                )


    # ========================================================
    # REVIEW DECISION
    # ========================================================

    st.subheader(
        "Review Decision"
    )


    # ========================================================
    # ALREADY APPROVED
    # ========================================================

    if (
        current_decision
        == "approved"
    ):

        st.success(
            "✓ Approved and processed."
        )


    # ========================================================
    # ALREADY REJECTED
    # ========================================================

    elif (
        current_decision
        == "rejected"
    ):

        st.warning(
            "✕ Rejected — saved locally. "
            "CRM was not changed."
        )


    # ========================================================
    # PENDING
    # ========================================================

    else:

        approve_col, reject_col = (
            st.columns(2)
        )


        # ====================================================
        # APPROVE
        # ====================================================

        with approve_col:

            if st.button(
                "✓ Approve",
                key=f"approve_{index}",
                use_container_width=True,
            ):

                classification = (
                    get_classification(
                        item
                    )
                )


                # ============================================
                # NO CRM ACCOUNT
                # ============================================

                if (
                    classification
                    == "NO_CRM_ACCOUNT"
                ):

                    website = item["website"]

                    create_payload = {
                        "name": website["name"],
                        "parent_id": "0015QAPLGS3FVYEEEM",
                        "billing_street": website["address"],
                        "billing_city": website["city"],
                        "billing_state": website["state"],
                        "billing_zip": website["zip"],
                        "care_type": ", ".join(
                            website.get(
                                "care_offerings",
                                [],
                            )
                        ),
                        "status": "Active",
                    }

                    st.write(
                        "New CRM account that will be created:"
                    )

                    st.json(
                        create_payload
                    )

                    try:

                        with st.spinner(
                            "Creating CRM account..."
                        ):

                            result = create_account(
                                create_payload
                            )

                        decisions[
                            decision_key
                        ] = "approved"

                        save_json(
                            DECISIONS_FILE,
                            decisions,
                        )

                        st.success(
                            "✓ Approved and new CRM "
                            "account created successfully."
                        )

                        st.json(
                            result
                        )

                    except Exception as error:

                        st.error(
                            "CRM account creation failed. "
                            "The review decision was NOT saved."
                        )

                        st.code(
                            str(error)
                        )


                # ============================================
                # EXISTING ACCOUNT
                # ============================================

                else:

                    match = get_match(
                        item
                    )


                    account_id = (
                        match.get(
                            "account_id"
                        )
                    )


                    revenue = get_revenue(
                        item
                    )


                    ar = get_ar(
                        item
                    )


                    # ========================================
                    # BILLING PROTECTION
                    # ========================================

                    if (
                        revenue > 0
                        and ar > 0
                    ):

                        website = get_website(
                            item
                        )

                        chow_create_payload = {
                            "name": website.get(
                                "name",
                                "Bellhaven Location",
                            ),
                            "parent_id": "0015QAPLGS3FVYEEEM",
                            "billing_street": website.get(
                                "address",
                                "",
                            ),
                            "billing_city": website.get(
                                "city",
                                "",
                            ),
                            "billing_state": website.get(
                                "state",
                                "",
                            ),
                            "billing_zip": website.get(
                                "zip",
                                "",
                            ),
                            "care_type": ", ".join(
                                website.get(
                                    "care_offerings",
                                    [],
                                )
                            ),
                            "status": "Active",
                        }

                        st.warning(
                            "CHOW workflow: the existing "
                            "account will be preserved. "
                            "A new account will be created "
                            "and then linked from the old "
                            "account using chow_current_account."
                        )

                        st.write(
                            "New CRM account that will be created:"
                        )

                        st.json(
                            chow_create_payload
                        )

                        try:

                            with st.spinner(
                                "Creating new CRM account..."
                            ):

                                new_account_result = (
                                    create_account(
                                        chow_create_payload
                                    )
                                )

                            new_account_id = (
                                extract_account_id(
                                    new_account_result
                                )
                            )

                            if not new_account_id:

                                raise ValueError(
                                    "The CRM create-account response "
                                    "did not contain a new account ID."
                                )

                            chow_update = {
                                "chow_current_account":
                                    new_account_id
                            }

                            st.write(
                                "CHOW update that will be sent "
                                "to the existing account:"
                            )

                            st.json(
                                {
                                    "account_id": account_id,
                                    "updates": chow_update,
                                }
                            )

                            with st.spinner(
                                "Linking old account to new account..."
                            ):

                                chow_result = (
                                    update_account(
                                        account_id,
                                        chow_update,
                                    )
                                )

                            decisions[
                                decision_key
                            ] = "approved"

                            save_json(
                                DECISIONS_FILE,
                                decisions,
                            )

                            st.success(
                                "✓ Approved. New CRM account "
                                "created and chow_current_account "
                                "updated successfully."
                            )

                            st.json(
                                {
                                    "old_account_id":
                                        account_id,
                                    "new_account_id":
                                        new_account_id,
                                    "new_account":
                                        new_account_result,
                                    "chow_update":
                                        chow_update,
                                    "chow_response":
                                        chow_result,
                                }
                            )

                            st.rerun()

                        except Exception as error:

                            st.error(
                                "CHOW workflow failed. "
                                "The review decision was NOT saved."
                            )

                            st.code(
                                str(error)
                            )


                    else:

                        updates = (
                            build_crm_update(
                                item
                            )
                        )


                        # ====================================
                        # NO UPDATE REQUIRED
                        # ====================================

                        if not updates:

                            decisions[
                                decision_key
                            ] = "approved"

                            save_json(
                                DECISIONS_FILE,
                                decisions,
                            )

                            st.success(
                                "✓ Approved. No CRM field changes "
                                "were needed."
                            )

                            st.rerun()


                        # ====================================
                        # UPDATE CRM
                        # ====================================

                        else:

                            st.write(
                                "CRM update that will be sent:"
                            )


                            st.json(
                                {
                                    "account_id": account_id,
                                    "updates": updates,
                                }
                            )


                            try:

                                with st.spinner(
                                    "Updating CRM..."
                                ):

                                    result = (
                                        update_account(
                                            account_id,
                                            updates,
                                        )
                                    )


                                decisions[
                                    decision_key
                                ] = "approved"


                                save_json(
                                    DECISIONS_FILE,
                                    decisions,
                                )


                                st.success(
                                    "✓ Approved and CRM "
                                    "updated successfully."
                                )


                                st.json(
                                    {
                                        "account_id": (
                                            account_id
                                        ),
                                        "updates": (
                                            updates
                                        ),
                                        "crm_response": (
                                            result
                                        ),
                                    }
                                )


                            except Exception as error:

                                st.error(
                                    "CRM update failed. "
                                    "The review decision "
                                    "was NOT saved."
                                )


                                st.code(
                                    str(error)
                                )


        # ====================================================
        # REJECT
        # ====================================================

        with reject_col:

            if st.button(
                "✕ Reject",
                key=f"reject_{index}",
                use_container_width=True,
            ):

                decisions[
                    decision_key
                ] = "rejected"


                save_json(
                    DECISIONS_FILE,
                    decisions,
                )


                st.rerun()


    st.divider()



# ============================================================
# DUPLICATE REVIEW
# ============================================================

DUPLICATE_DECISIONS_FILE = BASE_DIR / "duplicate_decisions.json"

DUPLICATE_GROUPS = [
    {
        "group": "Owosso",
        "survivor_id": "001EGU7BMJ942ZTRE6",
        "survivor_name": "Bellhaven of Owosso",
        "losers": [("001QU150PM4Z15UA71", "Bellhaven of Owosso")],
        "evidence": "Same name and same physical address: 1120 W Main St / 1120 West Main Street, Owosso, MI 48867. Both accounts have $0 revenue and $0 AR.",
    },
    {
        "group": "Sandusky",
        "survivor_id": "001SXSF4ELF0Z2LGDM",
        "survivor_name": "Bellhaven of Sandusky",
        "losers": [("0017JP8Z1UQ763BVK3", "Millstone Care of Sandusky")],
        "evidence": "Same physical address: 2715 Columbus Ave, Sandusky, OH 44870. Bellhaven account has revenue/AR; the Millstone account has $0 revenue and $0 AR.",
    },
    {
        "group": "Port Clinton",
        "survivor_id": "001UELXDAKFRKB8932",
        "survivor_name": "Bellhaven of Port Clinton",
        "losers": [("001JD2MWRA74LTSN24", "Harborview Nursing & Rehab of Port Clinton")],
        "evidence": "Same physical address: 1420 Harbor Point Dr / 1420 Harbor Point Drive, Port Clinton, OH 43452. The Harborview account has $0 revenue and $0 AR.",
    },
    {
        "group": "Monroe",
        "survivor_id": "001U1750VLVJAGG1S5",
        "survivor_name": "Bellhaven Gardens of Monroe",
        "losers": [
            ("00159PL81N38KM4FHM", "Monroe Gardens Care Center"),
            ("0011AB44D05WLA9HTX", "Cedar Trail of Monroe"),
        ],
        "evidence": "Same physical address: 750 Stewart Rd / 750 Stewart Road, Monroe, MI 48162. The two non-Bellhaven accounts have $0 revenue and $0 AR.",
    },
]

duplicate_decisions = load_json(DUPLICATE_DECISIONS_FILE, {})

st.divider()
st.header("🔁 Duplicate Review")
st.caption(
    "Approve only when the evidence supports that the listed loser is a duplicate. "
    "Approval marks the losing account Inactive and sets duplicate_of_account to the survivor."
)

for dup_index, group in enumerate(DUPLICATE_GROUPS):
    decision_key = f"{group['survivor_id']}|duplicate_group|{group['group']}"
    current = duplicate_decisions.get(decision_key)

    with st.expander(
        f"{group['group']} — {group['survivor_name']}",
        expanded=(current is None),
    ):
        st.write(f"**Keep / survivor:** {group['survivor_name']}")
        st.code(group["survivor_id"])

        st.write("**Duplicate account(s) to deactivate:**")
        for loser_id, loser_name in group["losers"]:
            st.write(f"- {loser_name} — `{loser_id}`")

        st.info(f"Evidence: {group['evidence']}")

        if current == "approved":
            st.success("✓ Duplicate decision approved and processed.")
            continue

        if current == "rejected":
            st.warning("✕ Duplicate decision rejected. No CRM change was made.")
            continue

        approve_dup, reject_dup = st.columns(2)

        with approve_dup:
            if st.button(
                "✓ Approve Duplicate",
                key=f"approve_dup_{dup_index}",
                use_container_width=True,
            ):
                try:
                    for loser_id, loser_name in group["losers"]:
                        update_account(
                            loser_id,
                            {
                                "duplicate_of_account": group["survivor_id"],
                                "status": "Inactive",
                            },
                        )

                    duplicate_decisions[decision_key] = "approved"
                    save_json(DUPLICATE_DECISIONS_FILE, duplicate_decisions)

                    st.success(
                        "✓ Duplicate accounts marked Inactive and linked to the survivor."
                    )
                    st.rerun()

                except Exception as error:
                    st.error(
                        "Duplicate update failed. No duplicate decision was saved."
                    )
                    st.code(str(error))

        with reject_dup:
            if st.button(
                "✕ Reject Duplicate",
                key=f"reject_dup_{dup_index}",
                use_container_width=True,
            ):
                duplicate_decisions[decision_key] = "rejected"
                save_json(DUPLICATE_DECISIONS_FILE, duplicate_decisions)
                st.rerun()

# ============================================================
# PROJECT PROGRESS
# ============================================================

st.subheader(
    "Project Progress"
)


st.write(
    "✅ Website locations scraped — 35 locations"
)


st.write(
    "✅ CRM accounts downloaded — 121 accounts"
)


st.write(
    "✅ Website-to-CRM matching completed"
)


st.write(
    "✅ Human review interface"
)


st.write(
    "🔄 Existing-account CRM write-back"
)


st.write(
    "✅ New-account creation"
)


st.write(
    "⏳ Duplicate handling"
)


st.write(
    "⏳ Safe daily reruns"
)