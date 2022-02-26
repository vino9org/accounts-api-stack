import os

import aws_cdk as cdk
from accounts_api_stack import AccountsApiStack

stack_name = os.environ.get("TESTING_STACK_NAME", "AccountsApiStack")
app = cdk.App()
AccountsApiStack(app, stack_name).build()
app.synth()
