import test_utils

import utils


def test_query_account(api_url, api_auth):
    query = """
    query test1 {
        getAccountsForCustomer(
            customerId: "%s"
        ) {
            id
            sid
            avail_balance
            currency
        }
    }
    """ % (
        utils.TEST_CUSTOMER_ID_1
    )

    response = test_utils.run_query(
        api_url,
        api_auth,
        query,
    )

    accounts = response["data"]["getAccountsForCustomer"]

    assert accounts is not None
    assert len(accounts) == 1
    assert accounts[0]["sid"] == utils.TEST_ACCOUNT_ID_1


def test_query_transactions(api_url, api_auth):
    query = """
    query test2 {
    getTransactionsForAccount(
        accountId: "%s"
    ){
        id
        sid
        amount
        currency
        memo
        status
        transaction_date
     }
    }
    """ % (
        utils.TEST_ACCOUNT_ID_1,
    )

    response = test_utils.run_query(
        api_url,
        api_auth,
        query,
    )

    transactions = response["data"]["getTransactionsForAccount"]

    assert transactions is not None
    assert len(transactions) >= 2
