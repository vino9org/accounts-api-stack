import json
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Tuple

import app
import utils


def gen_test_event() -> Tuple[str, Dict[Any, Any]]:
    trx_id = uuid.uuid1().hex
    transfer = app.FundTransfer(
        transaction_id=trx_id,
        debit_customer_id=utils.TEST_CUSTOMER_ID_1,
        debit_account_id=utils.TEST_ACCOUNT_ID_1,
        currency="SGD",
        credit_customer_id="omitted",
        credit_account_id="omitted",
        transfer_amount=Decimal("99.98"),
        memo="test transfer from pytest",
        transaction_date="2022-03-21",
        debit_prev_balance=Decimal("1000.12"),
        debit_prev_avail_balance=Decimal("1000.12"),
        debit_balance=Decimal("900.14"),
        debit_avail_balance=Decimal("900.14"),
        credit_prev_balance=Decimal("2000.00"),
        credit_prev_avail_balance=Decimal("2000.00"),
        credit_balance=Decimal("2099.98"),
        credit_avail_balance=Decimal("2099.98"),
        status="completed",
        limits_req_id="AAAA",
    )

    event = {
        "Time": datetime.now(),
        "Source": "service.fund_transfer",
        "DetailType": "transfer",
        "EventBusName": "default",
        "Detail": transfer.json(),
    }

    return trx_id, event


def test_handler_for_eventbridge(ddb_table):
    _, event = gen_test_event()
    transfer = app.FundTransfer(**json.loads(event["Detail"]))
    result = app.process_transfer_event(transfer, ddb_table)
    assert result
