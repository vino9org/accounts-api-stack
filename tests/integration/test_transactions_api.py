import test_utils as utils


def test_query_transactions(api_url, api_auth):
    query = """
    query MyQuery {
    getTransactionsForAccount(
        accountId: "%s"
    ){
        id
        account_id
        amount
        currency
        memo
        status
        transaction_date
     }
    }
    """ % (
        utils.TEST_ACCOUNT_ID_1
    )

    response = utils.run_query(
        api_url,
        api_auth,
        query,
    )

    accounts = response["data"]["getTransactionsForAccount"]
    assert len(accounts) == 2
