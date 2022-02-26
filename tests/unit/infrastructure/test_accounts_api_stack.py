import aws_cdk as core
import aws_cdk.assertions as assertions
from accounts_api_stack import AccountsApiStack


def test_stack_created():
    app = core.App()
    stack = AccountsApiStack(app, "AccountsApiStack")
    template = assertions.Template.from_stack(stack)
    assert template
