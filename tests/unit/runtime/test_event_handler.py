import json
import uuid
from typing import Tuple

import app


def gen_test_event_detail() -> Tuple[str, str]:
    trx_id = uuid.uuid1().hex
    detail = (
        """
        {
            "customer_id": "CUS_01FWWSK432VY3X1T8A4VNYRTGR",
            "account_id": "ACC_01FWWSNA9DA3N3EQ2JHPQ4WTNR",
            "transaction_id": "%s",
            "transfer_amount": 1234.56,
            "previous_balance": 10000.00,
            "previous_avail_balance": 10000.00,
            "new_balance": 11234.56,
            "new_avail_balance" :11234.56,
            "currency": "SGD",
            "memo": "to some random account",
            "transaction_date": "2022-02-27",
            "status": "completed"
        }
    """
        % trx_id
    )

    return trx_id, detail


def test_handler_for_eventbridge(ddb_table):
    _, event_detail = gen_test_event_detail()
    ret = app.process_transfer_event(json.loads(event_detail), ddb_table)
    assert ret
