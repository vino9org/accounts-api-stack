import os
from decimal import Decimal
from typing import List

import boto3
import pytest
import test_utils as utils
from botocore.exceptions import ClientError
from requests_aws4auth import AWS4Auth

_stack_outputs_: List[str] = {}


@pytest.fixture(scope="session")
def api_auth() -> str:
    return iam_auth_for_service("appsync")


@pytest.fixture(scope="session")
def api_url() -> str:
    return stack_outputs_for_key("AccountsApiUrl")[0]


@pytest.fixture(scope="session")
def accounts_table_name() -> str:
    return stack_outputs_for_key("AccountsTableName")[0]


@pytest.fixture(scope="session")
def transactions_table_name() -> str:
    return stack_outputs_for_key("TransactionsTableName")[0]


@pytest.fixture(autouse=True)
def seed_data(accounts_table_name, transactions_table_name):
    """ensure seed data is in database"""
    print("......seeding test data.....")
    ddb = boto3.resource("dynamodb")
    accounts_table = ddb.Table(accounts_table_name)
    accounts_table.put_item(
        Item={
            "customer_id": utils.TEST_CUSTOMER_ID_1,
            "id": utils.TEST_ACCOUNT_ID_1,
            "name": "Magic Saving Account",
            "prod_code": "SAV001",
            "ledger_balance": Decimal(12345678.90),
            "avail_balance": Decimal(12345600.01),
            "currency": "SGD",
            "status": "active",
            "updated_at": "2022-02-27T13:20:03.126945Z",
        }
    )

    transactions_table = ddb.Table(transactions_table_name)
    transactions_table.put_item(
        Item={
            "account_id": utils.TEST_ACCOUNT_ID_1,
            "id": "i4HGdW4JhpiadPtawWgt9j",
            "memo": "To Vinobank account (abcde)",
            "amount": Decimal(123),
            "currency": "SGD",
            "status": "completed",
            "transaction_date": "2022-02-27",
            "updated_at": "2022-02-27T21:20:06.126012Z",
        }
    )
    transactions_table.put_item(
        Item={
            "account_id": utils.TEST_ACCOUNT_ID_1,
            "id": "B8BKqeDR9S8EDgvpB9WLL5",
            "memo": "Mobile topup (01233)",
            "amount": Decimal(88),
            "currency": "SGD",
            "status": "completed",
            "transaction_date": "2022-02-27",
            "updated_at": "2022-02-27T21:22:07.214031Z",
        }
    )


def stack_outputs_for_key(key: str) -> List[str]:
    """
    helper funciton to get output values from a Cloudformation stack
    can be used by a fixture to retrieve output values and inject
    into tests

    e.g.

    # in conftest.py
    @pytest.fixture(scope="session")
    def api_base_url() -> str:
        return _stack_outputs__for_key("RestApiEndpoint")[0]

    # in tests
    import requests
    def test_restapi(api_base_url):
        response = requests.get(f"{api_base_url}/ping")
        assert response.status_code == 200

    """

    global _stack_outputs_

    region = os.environ.get("TESTING_REGION", "us-west-2")
    stack_name = os.environ.get("TESTING_STACK_NAME", "AccountsApiStack")
    client = boto3.client("cloudformation", region_name=region)

    if not _stack_outputs_:
        try:
            response = client.describe_stacks(StackName=stack_name)
            _stack_outputs_ = response["Stacks"][0]["Outputs"]
        except ClientError as e:
            raise Exception(f"Cannot find stack {stack_name} in region {region}") from e

    output_values = [item["OutputValue"] for item in _stack_outputs_ if key in item["OutputKey"]]
    if not output_values:
        raise Exception(f"There is no output with key {key} in stack {stack_name} in region {region}")

    return output_values


def iam_auth_for_service(service: str) -> AWS4Auth:
    """
    create the auth object for signing a HTTP request with AWS IAM v4 signature
    can be used create fixture for test cases where IAM authentication is used

    e.g.

    # in conftest.py
    @pytest.fixture(scope="session")
    def http_api_authj() -> str:
        return iam_auth_for_service("execute-api")

    # in tests
    def test_restapi(api_base_url, http_api_auth):
        response = requests.get(f"{api_base_url}/ping", auth=http_api_auth)
        assert response.status_code == 200

    """
    session = boto3.Session()
    credentials = session.get_credentials()
    return AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        session.region_name,
        service,
    )
