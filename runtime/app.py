import json
import os
from decimal import Decimal
from typing import Any, Dict

import boto3
from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError

import utils

logger, metrics, tracer = utils.init_monitoring()


def get_ddb_table():
    table_name = os.environ.get("DDB_TABLE")
    if not table_name:
        raise "DDB_TABLE is not set"
    ddb = boto3.resource("dynamodb")
    return ddb.Table(table_name)


@tracer.capture_method
def process_transfer_event(event_detail: Dict[str, Any], ddb_table=None) -> bool:
    # to prevent eventbridge from retrying requests
    # unneccessarily, we need to handle exceptions thrown
    # from processing logic
    try:
        transaction_id = event_detail["transaction_id"]
        customer_id = event_detail["customer_id"]
        account_id = event_detail["account_id"]
        currency = event_detail["currency"]
        memo = event_detail["memo"]
        status = event_detail["status"]
        transaction_date = event_detail["transaction_date"]
        amount = Decimal(str(event_detail["transfer_amount"]))
        new_bal = Decimal(str(event_detail["new_balance"]))
        new_avail_bal = Decimal(str(event_detail["new_avail_balance"]))

        ddb_table.put_item(
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

        ddb_table.update_item(
            Key={
                "id": customer_id,
                "sid": account_id,
            },
            UpdateExpression="""
                SET avail_balance = :new_avail_balance,
                    ledger_balance  = :new_ledger_balance,
                    updated_at = :new_timestamp
            """,
            ExpressionAttributeValues={
                ":new_avail_balance": new_avail_bal,
                ":new_ledger_balance": new_bal,
                ":new_timestamp": utils.iso_timestamp(),
            },
        )

        return True
    except KeyError as e:
        logger.warning("event does not have required attribute %s", e)
    except ClientError as e:
        logger.warning("AWS API exception during processing: %s", e)
    except Exception as e:
        raise e

    return False


def lambda_handler(event: Dict[str, Any], context: LambdaContext):
    logger.info(event)
    eb_event = EventBridgeEvent(event)
    detail = json.loads(eb_event.detail)
    ddb_table = get_ddb_table()
    return process_transfer_event(detail, ddb_table)
