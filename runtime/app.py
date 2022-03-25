import os
import sys
from decimal import Decimal
from typing import Any, Dict

import boto3
from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError
from pydantic import BaseModel

import utils

logger, metrics, tracer = utils.init_monitoring()


class FundTransfer(BaseModel):
    transaction_id: str

    debit_customer_id: str
    debit_account_id: str
    debit_prev_balance: Decimal
    debit_prev_avail_balance: Decimal
    debit_balance: Decimal
    debit_avail_balance: Decimal

    credit_customer_id: str
    credit_account_id: str
    credit_prev_balance: Decimal
    credit_prev_avail_balance: Decimal
    credit_balance: Decimal
    credit_avail_balance: Decimal

    transfer_amount: Decimal
    currency: str
    memo: str
    transaction_date: str
    status: str

    limits_req_id: str


def get_ddb_table():
    table_name = os.environ.get("DDB_TABLE_NAME")
    if not table_name:
        raise "DDB_TABLE_NAME is not set"
    ddb = boto3.resource("dynamodb")
    return ddb.Table(table_name)


@tracer.capture_method
def process_transfer_event(event_detail: FundTransfer, ddb_table=None) -> bool:
    # to prevent eventbridge from retrying requests
    # unneccessarily, we need to handle exceptions thrown
    # from processing logic
    try:
        transaction_id = event_detail.transaction_id
        debit_customer_id = event_detail.debit_customer_id
        debit_account_id = event_detail.debit_account_id
        debit_bal = Decimal(str(event_detail.debit_balance))
        debit_avail_bal = Decimal(str(event_detail.credit_avail_balance))

        credit_customer_id = event_detail.credit_customer_id
        credit_account_id = event_detail.credit_account_id
        credit_bal = Decimal(str(event_detail.credit_balance))
        credit_avail_bal = Decimal(str(event_detail.credit_avail_balance))
        currency = event_detail.currency
        memo = event_detail.memo
        status = event_detail.status
        transaction_date = event_detail.transaction_date
        amount = Decimal(str(event_detail.transfer_amount))
        now = utils.iso_timestamp()

        # create transaction record for debit account
        ddb_table.put_item(
            Item={
                "id": debit_account_id,
                "sid": f"TRX_{transaction_id}_1",
                "memo": f"transfer {transaction_id} to {credit_account_id}\n{memo}",
                "amount": amount,
                "currency": currency,
                "status": status,
                "transaction_date": transaction_date,
                "updated_at": now,
            }
        )

        # create transaction record for credit account
        ddb_table.put_item(
            Item={
                "id": credit_account_id,
                "sid": f"TRX_{transaction_id}_2",
                "memo": f"transfer {transaction_id} to {credit_account_id}\n{memo}",
                "amount": amount,
                "currency": currency,
                "status": status,
                "transaction_date": transaction_date,
                "updated_at": now,
            }
        )

        # update balance credit account
        ddb_table.update_item(
            Key={
                "id": debit_customer_id,
                "sid": debit_account_id,
            },
            UpdateExpression="""
                SET avail_balance = :new_avail_balance,
                    ledger_balance  = :new_ledger_balance,
                    updated_at = :new_timestamp
            """,
            ExpressionAttributeValues={
                ":new_avail_balance": debit_avail_bal,
                ":new_ledger_balance": debit_bal,
                ":new_timestamp": now,
            },
        )

        # update balance credit account
        ddb_table.update_item(
            Key={
                "id": credit_customer_id,
                "sid": credit_account_id,
            },
            UpdateExpression="""
                SET avail_balance = :new_avail_balance,
                    ledger_balance  = :new_ledger_balance,
                    updated_at = :new_timestamp
            """,
            ExpressionAttributeValues={
                ":new_avail_balance": credit_avail_bal,
                ":new_ledger_balance": credit_bal,
                ":new_timestamp": now,
            },
        )

        logger.info(f"processed event for transaction {transaction_id}")
        return True
    except KeyError as e:
        logger.warning("event does not have required attribute %s", e)
    except ClientError as e:
        logger.warning("AWS API exception during processing: %s", e)
    except Exception as e:
        raise e
    except:  # noqa
        logger.warning("Unexpected error:", sys.exc_info()[0])

    logger.info(f"unable to processed event for transaction {transaction_id}")
    return False


def lambda_handler(event: Dict[str, Any], context: LambdaContext):
    logger.info(event)
    eb_event = EventBridgeEvent(event)
    transfer = FundTransfer(**eb_event.detail)
    return process_transfer_event(transfer, get_ddb_table())
