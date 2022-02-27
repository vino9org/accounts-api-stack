import requests


def run_query(endpoint, auth, query):
    response = requests.post(endpoint, json={"query": query}, auth=auth)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.content}")


def test_query_account(api_url, api_auth):
    query = """
    query test1 {
        getAccountsForCustomer(
            customerId: "1234"
        ) {
            avail_balance
            currency
        }
    }
"""
    response = run_query(
        api_url,
        api_auth,
        query,
    )

    accounts = response["data"]["getAccountsForCustomer"]
    assert len(accounts) == 1
    assert accounts[0]["currency"] == "SGD"
