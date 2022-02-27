import test_utils as utils


def test_query_account(api_url, api_auth):
    query = """
    query test1 {
        getAccountsForCustomer(
            customerId: "%s"
        ) {
            id
            avail_balance
            currency
        }
    }
    """ % (
        utils.TEST_CUSTOMER_ID_1
    )

    response = utils.run_query(
        api_url,
        api_auth,
        query,
    )

    accounts = response["data"]["getAccountsForCustomer"]
    assert len(accounts) == 1
    assert accounts[0]["id"] == utils.TEST_ACCOUNT_ID_1
