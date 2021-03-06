import os
import os.path
import uuid
from dataclasses import dataclass

import aws_cdk.aws_dynamodb as dynamodb
import boto3
import pytest
from botocore.exceptions import ClientError

import utils


# create a test table before test execution
@pytest.fixture(scope="session")
def ddb_table() -> dynamodb.Table:
    local_dynamodb_url = os.environ.get("LOCAL_DYNAMODB_URL")
    if not (local_dynamodb_url and utils.is_http_url(local_dynamodb_url)):
        print("LOCAL_DYNAMODB_URL not defined or malformed, fall back to default AWS endpoint")
        return boto3.resource("dynamodb").Table(os.environ.get("DDB_TABLE_NAME"))

    ddb = boto3.resource("dynamodb", endpoint_url=local_dynamodb_url)
    table_name = f"accounts-api-{uuid.uuid1().hex}"
    try:
        ddb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "id", "KeyType": "HASH"},  # Partition key
                {"AttributeName": "sid", "KeyType": "RANGE"},  # Sort key
            ],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "sid", "AttributeType": "S"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 10, "WriteCapacityUnits": 10},
        )
        print(f": created temporary test table {table_name} on {local_dynamodb_url}")

    except ClientError as e:
        print("Test table already exits..", e)

    return ddb.Table(table_name)


@pytest.fixture
def lambda_context():
    @dataclass
    class LambdaContext:
        function_name: str = "test_func"
        memory_limit_in_mb: int = 128
        invoked_function_arn: str = "arn:aws:lambda:eu-west-1:809313241:function:test"
        aws_request_id: str = "52fdfc07-2182-154f-163f-5f0f9a621d72"

    return LambdaContext()
