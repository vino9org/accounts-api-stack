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


def test_stack_created(stack) -> None:
    assert stack
