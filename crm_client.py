import os
import requests


# ============================================================
# BELLHAVEN CRM API
# ============================================================

BASE_URL = (
    "https://analyst-assessment-production.up.railway.app/api/v1"
)


# ============================================================
# HEADERS
# ============================================================

def get_headers():
    """
    Build the API request headers.

    The API token is read from the environment variable
    BELLHAVEN_API_TOKEN.

    The token is intentionally NOT stored in this file.
    """

    token = os.getenv(
        "BELLHAVEN_API_TOKEN"
    )

    if not token:

        raise RuntimeError(
            "BELLHAVEN_API_TOKEN is not set.\n"
            "Set the API token in the terminal before "
            "running the program."
        )

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# ============================================================
# GET ALL ACCOUNTS
# ============================================================

def get_accounts():
    """
    Download all CRM accounts using pagination.
    """

    all_accounts = []

    page = 1

    page_size = 50


    while True:

        url = (
            f"{BASE_URL}/accounts"
        )

        response = requests.get(
            url,
            headers=get_headers(),
            params={
                "page": page,
                "page_size": page_size,
            },
            timeout=30,
        )

        response.raise_for_status()

        result = response.json()

        data = result.get(
            "data",
            [],
        )

        if not data:
            break

        all_accounts.extend(
            data
        )

        total = result.get(
            "total",
            len(all_accounts),
        )

        print(
            f"Downloaded page {page}: "
            f"{len(data)} accounts "
            f"({len(all_accounts)}/{total})"
        )

        if len(all_accounts) >= total:
            break

        page += 1


    return all_accounts


# ============================================================
# GET ONE ACCOUNT
# ============================================================

def get_account(account_id):
    """
    Retrieve a single CRM account.
    """

    url = (
        f"{BASE_URL}/accounts/{account_id}"
    )

    response = requests.get(
        url,
        headers=get_headers(),
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# UPDATE ACCOUNT
# ============================================================

def update_account(
    account_id,
    updates,
):
    """
    Update an existing CRM account.

    Example:

        update_account(
            "001ABC...",
            {
                "billing_zip": "45662"
            }
        )

    This sends a PATCH request to the CRM API.
    """

    url = (
        f"{BASE_URL}/accounts/{account_id}"
    )

    response = requests.patch(
        url,
        headers=get_headers(),
        json=updates,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# CREATE ACCOUNT
# ============================================================

def create_account(
    account_data,
):
    """
    Create a new CRM account.

    This function is available for the future
    NO_CRM_ACCOUNT workflow.

    We are NOT calling it from the review app yet because
    the API documentation did not expose the exact POST
    request-body schema.
    """

    url = (
        f"{BASE_URL}/accounts"
    )

    response = requests.post(
        url,
        headers=get_headers(),
        json=account_data,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# CONNECTION TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Testing Bellhaven CRM connection..."
    )

    print()

    try:

        accounts = get_accounts()

        print()

        print(
            "CRM connection successful."
        )

        print()

        print(
            "Number of accounts:",
            len(accounts),
        )

        if (
            isinstance(
                accounts,
                list,
            )
            and accounts
        ):

            print()

            print(
                "First account:"
            )

            print(
                accounts[0]
            )


    except requests.exceptions.HTTPError as error:

        print()

        print(
            "CRM API returned an error:"
        )

        print(
            error
        )

        if (
            error.response
            is not None
        ):

            print(
                "Response:"
            )

            print(
                error.response.text
            )


    except Exception as error:

        print()

        print(
            "Error:"
        )

        print(
            error
        )