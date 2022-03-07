import os

import aws_cdk as cdk
import aws_cdk.assertions as assertions
import pytest
from aws_cdk.assertions import Template

from accounts_api_stack import AccountsApiStack


@pytest.fixture(scope="session")
def stack() -> Template:
    stack_name = os.environ.get("TESTING_STACK_NAME", "AccountsApiStack")
    app = cdk.App()
    stack = AccountsApiStack(app, stack_name).build()
    return assertions.Template.from_stack(stack)


def test_iam_roles_created(stack) -> None:
    assert len(stack.find_resources("AWS::IAM::Role")) == 4


def test_lambda_created(stack) -> None:
    all_funcs = stack.find_resources("AWS::Lambda::Function")
    func = next(iter(all_funcs.values()))
    assert "python" in func["Properties"]["Runtime"]


def test_dyanmodb_table_created(stack) -> None:
    all_tables = stack.find_resources("AWS::DynamoDB::Table")
    table_name = next(iter(all_tables.keys()))
    assert "AccountsApiStack" in table_name
