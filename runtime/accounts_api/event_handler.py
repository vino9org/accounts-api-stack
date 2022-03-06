import os
from typing import Any, Dict

import boto3
import utils
from botocore.exceptions import ClientError

logger, metrics, tracer = utils.init_monitoring()


@tracer.capture_method
def handle_event(event_detail: Dict[str, Any]) -> bool:
    # to prevent eventbridge from retrying requests
    # unneccessarily, we need to handle exceptions thrown
    # from processing logic
    try:
        transaction_id = event_detail["transaction_id"]
        customer_id = event_detail["customer_id"]
        account_id = event_detail["account_id"]
        currency = event_detail["currency"]
        amount = event_detail["transfer_amount"]
        memo = event_detail["memo"]
        status = event_detail["status"]
        new_bal = event_detail["new_balance"]
        new_avail_bal = event_detail["new_avail_balance"]

        transaction_date = event_detail["transaction_date"]

        ddb = boto3.resource("dynamodb")
        account_table = ddb.Table(os.environ.get("DDB_TABLE", ""))

        account_table.put_item(
            Item={
                "id": account_id,
                "sid": f"TRX_{transaction_id}",
                "memo": memo,
                "amount": amount,
                "currency": currency,
                "status": status,
                "transaction_date": transaction_date,
                "updated_at": utils.iso_timestamp(),
            }
        )

        account_table.update_item(
            Key={
                "id": customer_id,
                "sid": account_id,
            },
            UpdateExpression="""
                SET avail_balance = :new_avail_balance,
                    ledger_balance  = :new_ledger_balance,
                    updated_at = :new_timestamp,
            """,
            ExpressionAttributeValues={
                "customer_id": customer_id,
                "account_id": f"ACC_{account_id}",
                "new_avail_balance": new_avail_bal,
                "new_bal": new_bal,
                "new_timestamp": utils.iso_timestamp(),
            },
        )

        return True
    except KeyError:
        logger.warn("event does not have req_id attribute set %s", event_detail)
    except ClientError as e:
        logger.warn("AWS API exception during processing: %s", e)

    return False
