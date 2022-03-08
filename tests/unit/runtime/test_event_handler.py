import json
import uuid
from datetime import datetime
from typing import Any, Dict, Tuple

import app
import utils


def gen_test_event() -> Tuple[str, Dict[Any, Any]]:
    trx_id = uuid.uuid1().hex
    detail = json.dumps(
        {
            "customer_id": utils.TEST_CUSTOMER_ID_1,
            "account_id": utils.TEST_ACCOUNT_ID_1,
            "transaction_id": trx_id,
            "transfer_amount": 1234.56,
            "previous_balance": 10000.00,
            "previous_avail_balance": 10000.00,
            "new_balance": 11234.56,
            "new_avail_balance": 11234.56,
            "currency": "SGD",
            "memo": "to some random account",
            "transaction_date": "2022-02-27",
            "status": "completed",
        }
    )

    event = {
        "Time": datetime.now(),
        "Source": "service.fund_transfer",
        "DetailType": "transfer",
        "EventBusName": "default",
        "Detail": detail,
    }

    return trx_id, event


def test_handler_for_eventbridge(ddb_table):
    _, event = gen_test_event()
    result = app.process_transfer_event(json.loads(event["Detail"]), ddb_table)
    assert result
