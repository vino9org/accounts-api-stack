import os
import os.path
import uuid
from dataclasses import dataclass

import boto3
import pytest
from botocore.exceptions import ClientError

from accounts_api import utils


# create a test table before test execution
@pytest.fixture(scope="session", autouse=True)
def ddb_table() -> None:
    suffix = uuid.uuid1().replace("-", "")
    local_dynamodb_url = os.environ.get("LOCAL_DYNAMODB_URL")
    if not (local_dynamodb_url and utils.is_http_url(local_dynamodb_url)):
        print("LOCAL_DYNAMODB_URL not defined or malformed, fall back to default AWS endpoint")
        return

    ddb = boto3.resource("dynamodb", endpoint_url=local_dynamodb_url)
    table_name = f"limits-manager-{suffix}"
    try:
        ddb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "customer_id", "KeyType": "HASH"},  # Partition key
                {"AttributeName": "request_id", "KeyType": "RANGE"},  # Sort key
            ],
            AttributeDefinitions=[
                {"AttributeName": "customer_id", "AttributeType": "S"},
                {"AttributeName": "request_id", "AttributeType": "S"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 10, "WriteCapacityUnits": 10},
        )
        print(f": created temporary test table {table_name} on {local_dynamodb_url}")

    except ClientError as e:
        print("Test table already exits..", e)

    os.environ.put("DDB_TABLE", table_name)


@pytest.fixture
def lambda_context():
    @dataclass
    class LambdaContext:
        function_name: str = "test_func"
        memory_limit_in_mb: int = 128
        invoked_function_arn: str = "arn:aws:lambda:eu-west-1:809313241:function:test"
        aws_request_id: str = "52fdfc07-2182-154f-163f-5f0f9a621d72"

    return LambdaContext()
