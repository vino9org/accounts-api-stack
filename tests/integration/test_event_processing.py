from time import sleep
from typing import Dict, List, Union

import boto3
import test_utils

import utils
from tests.unit.runtime.test_event_handler import gen_test_event


def invoke_get_transactions_api(api_url, api_auth) -> Union[List[Dict], None]:
    query = """
    query test3 {
    getTransactionsForAccount(
        accountId: "%s"
    ){
        id
        sid
        amount
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

    return response["data"]["getTransactionsForAccount"]


def send_fund_transfer_event() -> str:
    trx_id, rand_event = gen_test_event()

    client = boto3.client("events")
    response = client.put_events(Entries=[rand_event])

    assert response["FailedEntryCount"] == 0

    return trx_id


def test_fund_transfer_event(api_url, api_auth):
    """
    send event to event bus, then check if the event has been processed
    and included in transaction query
    """
    trx_id = send_fund_transfer_event()
    # try 3 times in case the processing is slower than we expect
    for i in range(6):
        sleep(5 * i)
        transactions = invoke_get_transactions_api(api_url, api_auth)
        transaction_ids = [t["sid"] for t in transactions]
        if f"TRX_{trx_id}_1" in transaction_ids:
            return
        else:
            print("transactions returned:", transaction_ids)

    assert False, f"event {trx_id} not processed in time"
